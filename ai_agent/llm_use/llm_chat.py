import os
import sqlite3
import dashscope
from dotenv import load_dotenv
from http import HTTPStatus
from langchain_community.utilities import SQLDatabase

# 加载环境变量
load_dotenv()

# 初始化阿里云百炼平台客户端
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
model = os.getenv("LLM_MODEL", "qwen-max")

# 初始化数据库连接
# 注意：在生产环境中，应该使用更安全的数据库连接方式
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db.sqlite3')
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")


# 在这里构建特殊需求的提示词模板
# 例如，添加指令来限制响应长度、指定输出格式等

async def get_llm_response(prompt):
    """
    获取LLM的流式响应
    :param prompt: 提示词
    :return: 流式响应生成器
    """
    try:
        messages = [
            {"role": "system", "content": ""},
            {"role": "user", "content": prompt}
        ]
        
        # 使用流式调用
        # 流式调用是指一次发送一个完整的提示词，然后等待LLM返回一个响应片段，再继续发送下一个提示词
        responses = dashscope.Generation.call(
            model=model,
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True
        )
        
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                if response.output.choices and len(response.output.choices) > 0:
                    content = response.output.choices[0]['message']['content']
                    if content:
                        yield content # 使其成为一个生成器函数，每次返回一个响应片段
                        # 生成器函数是一种特殊的函数，它可以在每次调用时返回一个值，而不是一次返回所有值
                        # 这使得我们可以在需要时逐个处理响应片段，而不是等待所有响应完成
            else:
                yield f"Error: {response.message}"
                break
    except Exception as e:
        yield f"Error: {str(e)}"

def get_debt_analysis(debt_data, customer_id=None):
    """
    获取债务分析
    :param debt_data: 债务数据
    :param customer_id: 客户ID（可选）
    :return: 分析结果
    """
    # 如果提供了客户ID，从数据库获取客户的详细信息
    if customer_id:
        try:
            # 使用自然语言查询获取客户信息
            question = f"获取ID为{customer_id}的客户的所有债务信息，包括信用卡、贷款和月供出款记录"
            sql_query = get_sql_query(question)
            debt_data = execute_sql_query(sql_query)
        except Exception as e:
            debt_data = f"无法获取客户数据: {str(e)}"
    
    prompt = f"""
    请根据以下债务信息提供分析和优化建议：
    
    债务信息：
    {debt_data}
    
    请提供以下信息：
    1. 债务总览（总债务、平均利率等）
    2. 还款优先级建议
    3. 债务优化策略
    4. 风险提示
    """
    
    try:
        messages = [
            {"role": "system", "content": "你是一个专业的债务优化顾问，擅长分析个人或企业的债务情况并提供优化建议。"},
            {"role": "user", "content": prompt}
        ]
        
        response = dashscope.Generation.call(
            model=model,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0]['message']['content']
        else:
            return f"分析过程中出现错误: {response.message}"
    except Exception as e:
        return f"分析过程中出现错误: {str(e)}"

def get_repayment_plan(debt_data, monthly_budget, customer_id=None):
    """
    获取还款计划
    :param debt_data: 债务数据
    :param monthly_budget: 月度预算
    :param customer_id: 客户ID（可选）
    :return: 还款计划
    """
    # 如果提供了客户ID，从数据库获取客户的详细信息
    if customer_id:
        try:
            # 使用自然语言查询获取客户信息
            question = f"获取ID为{customer_id}的客户的所有债务信息，包括信用卡、贷款和月供出款记录"
            sql_query = get_sql_query(question)
            debt_data = execute_sql_query(sql_query)
        except Exception as e:
            debt_data = f"无法获取客户数据: {str(e)}"
    
    prompt = f"""
    请根据以下债务信息和月度预算制定还款计划：
    
    债务信息：
    {debt_data}
    
    月度预算：{monthly_budget}元
    
    请提供以下信息：
    1. 每月还款分配建议
    2. 预计还清时间
    3. 总利息支出
    4. 优化建议
    """
    
    try:
        messages = [
            {"role": "system", "content": "你是一个专业的财务规划师，擅长制定债务还款计划。"},
            {"role": "user", "content": prompt}
        ]
        
        response = dashscope.Generation.call(
            model=model,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0]['message']['content']
        else:
            return f"制定还款计划时出现错误: {response.message}"
    except Exception as e:
        return f"制定还款计划时出现错误: {str(e)}"

def get_financial_advice(financial_situation, customer_id=None):
    """
    获取财务建议
    :param financial_situation: 财务状况描述
    :param customer_id: 客户ID（可选）
    :return: 财务建议
    """
    # 如果提供了客户ID，从数据库获取客户的详细信息
    if customer_id:
        try:
            # 使用自然语言查询获取客户信息
            question = f"获取ID为{customer_id}的客户的完整财务信息，包括所有债务、出款记录和财务指标"
            sql_query = get_sql_query(question)
            financial_situation = execute_sql_query(sql_query)
        except Exception as e:
            financial_situation = f"无法获取客户数据: {str(e)}"
    
    prompt = f"""
    请根据以下财务状况提供专业建议：
    
    财务状况：
    {financial_situation}
    
    请提供以下信息：
    1. 财务健康度评估
    2. 改进建议
    3. 投资建议（如适用）
    4. 风险提示
    """
    
    try:
        messages = [
            {"role": "system", "content": "你是一个专业的财务顾问，擅长分析个人或企业的财务状况并提供专业建议。"},
            {"role": "user", "content": prompt}
        ]
        
        response = dashscope.Generation.call(
            model=model,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0]['message']['content']
        else:
            return f"提供财务建议时出现错误: {response.message}"
    except Exception as e:
        return f"提供财务建议时出现错误: {str(e)}"
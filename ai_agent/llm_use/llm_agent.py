import os
import logging
from functools import lru_cache
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.checkpoint.memory import InMemorySaver  


# 创建缓存字典用于存储常见问题的答案
common_questions_cache = {}

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 加载环境变量
load_dotenv()

# 初始化数据库连接
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'db.sqlite3')
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")


model = ChatOpenAI(
    model="qwen-max",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1,  # 温度参数，用于控制模型的随机程度，默认值为0.1
    max_tokens=1000,  # 最大输出token数，默认值为1000
    timeout=30,  # 请求超时时间，单位为秒，默认值为30
    max_retries=2,  # 最大重试次数
    # ... (other params)
)

toolkit = SQLDatabaseToolkit(db=db, llm=model)

tools_sql = toolkit.get_tools()

# 创建多个工具
@tool(description="用于回答与数据库无关的通用问题，如解释业务流程、定义术语、提供帮助等。")
def answer_general_question(question: str) -> str:
    """
    回答与数据库无关的通用问题
    :param question: 用户的问题
    :return: 大模型生成的回答
    """
    try:
        # 检查缓存中是否已有答案
        if question in common_questions_cache:
            return common_questions_cache[question]
        
        # 构造专门用于回答通用问题的提示词
        general_prompt = f"""
                        你是一个专业的业务助手，请用中文回答以下问题。
                        提供准确、简洁且有帮助的回答。
                        如果问题涉及具体客户数据、账单信息等，请说明需要通过数据库查询获取。
                        如果不确定答案，请诚实说明。

                        问题：{question}

                        请回答：
                        """
        
        # 调用大模型获取回答，设置超时时间
        response = model.invoke(
            [{"role": "user", "content": general_prompt}],
            timeout=30  # 设置30秒超时
        )

        # 返回模型的回答
        if hasattr(response, 'content'):
            result = response.content
        else:
            result = str(response)
            
        # 将结果存入缓存
        common_questions_cache[question] = result
        return result
    except Exception as e:
        # 如果出现错误，返回错误信息
        error_msg = f"抱歉，回答问题时出现错误：{str(e)}"
        return error_msg


def handle_tool_errors(request, handler):
    """处理工具执行错误，返回自定义错误消息。"""
    try:
        return handler(request)
    except Exception as e:
        # 返回一个自定义错误消息给模型
        return ToolMessage(
            content=f"工具执行错误：请检查您的输入并重试。({str(e)})",
            # 返回错误消息给模型，包含工具调用ID
            tool_call_id=request.tool_call["id"]
        )


# 定义系统提示（增强判断能力）
# 系统提示：引导 LLM 正确使用工具（尤其强调 query_checker 和 schema）
system_prompt = """
你是一个智能业务助手，可以查询公司数据库或回答通用问题。

📌 重要业务定义：
- “财务状况”指客户的以下信息组合：
  • 信用卡总授信额度（core_creditcard.total_limit）
  • 贷款余额（core_loan.balance）
- “客户信息”包括：姓名、电话、融资日期、签约日期等（来自 core_customer）

可用工具：
- sql_db_list_tables: 获取所有表名（输入：空字符串）
- sql_db_schema: 查看表结构（输入：表名，如 "core_customer"）
- sql_db_query: 执行 SELECT 查询（仅限 SELECT，输入：合法 SQL）
# 新增或强调：
**⚠️ 警告：生成的 SQL 语句在 JSON 字符串内，绝对不能以分号 (;) 结尾。**
- answer_general_question: 回答非数据问题（如解释术语、流程）

工具选择规则：
1. 当问题涉及具体客户、金额、日期、账单等 → 使用 SQL 工具。
   - 示例：“张三的财务状况？” → 查询 core_customer, core_creditcard, core_loan 相关字段
2. 当问题无法转化为具体字段（如“他有钱吗？”）→ 使用 answer_general_question 解释限制。
3. 如果 SQL 查询失败（如字段不存在）→ 先用 sql_db_schema 确认结构，或转为通用回答。
4. 所有表名必须带 'core_' 前缀。
5. 回答必须用中文，简洁明了。如果数据缺失，明确告知用户。
6. 对于客户财务状况查询，需要关联多个表：
   - 首先确认客户是否存在：SELECT * FROM core_customer WHERE name = '客户名'
   - 然后关联查询相关信息：
     * core_customer: 客户基本信息
     * core_loan: 客户贷款信息
     * core_creditcard: 客户信用卡信息
     * core_monthlypayment: 客户月供信息
7. 如果查询不到客户信息，应明确告知用户该客户不存在。

示例：
- 问：“李四的财务状况？” → 生成 JOIN 查询，获取客户、信用卡、贷款信息
- 问：“融资日期是什么意思？” → 调用 answer_general_question
- 问：“怎么评估客户风险？” → 调用 answer_general_question，解释需结合多维度
- 问：“李瀚文的财务状况怎么样？” → 先查询core_customer表确认客户存在，再关联其他表获取完整信息
"""

# 动态系统提示（根据用户角色调整行为）
# @dynamic_prompt
# def user_role_prompt(request: ModelRequest) -> str:
#     """Generate system prompt based on user role."""
#     user_role = request.runtime.context.get("user_role", "user")
#     base_prompt = "You are a helpful assistant."

#     if user_role == "expert":
#         return f"{base_prompt} Provide detailed technical responses."
#     elif user_role == "beginner":
#         return f"{base_prompt} Explain concepts simply and avoid jargon."

#     return base_promp


agent = create_agent(
    model, 
    # 定义要使用的工具列表
    tools=[answer_general_question, *tools_sql ],
    # 定义系统提示，用于引导模型行为
    system_prompt=system_prompt,
    checkpointer=InMemorySaver(),  
    # checkpointer=MemorySaver()  # 可选，用于记忆
    )

async def get_llm_response_agent(prompt, conversation_id):
    """
    获取LLM的流式响应
    :param prompt: 提示词
    :param conversation_id: 会话ID
    :return: 流式响应生成器
    """
    try:
        conversation_id = str(conversation_id)
        
        # 使用SQL Agent执行查询
        response = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            {"configurable": {"thread_id": conversation_id}},  
        )
        
        # LangGraph 默认返回 {"messages": [...]}
        messages = response.get("messages", [])
        if messages:
            last_message = messages[-1]
            # 最终回答通常在最后一条 AIMessage 的 content 中
            if hasattr(last_message, 'content'):
                result = str(last_message.content)
                yield result
            else:
                error_msg = "无法解析模型响应。"
                yield error_msg
        else:
            warning_msg = "抱歉，我没有找到相关信息。"
            yield warning_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        yield error_msg
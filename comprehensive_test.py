import sys
import os
import asyncio

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

import logging
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 导入修改后的模块
from ai_agent.llm_use.llm_agent import get_llm_response_agent, common_questions_cache

async def test_cache_mechanism():
    """测试缓存机制"""
    print("=== 测试缓存机制 ===")
    
    # 清空缓存
    common_questions_cache.clear()
    print(f"缓存清空，当前缓存大小: {len(common_questions_cache)}")
    
    question = "什么是债务优化？"
    
    # 第一次调用
    print(f"\n第一次调用: {question}")
    response1 = ""
    async for response in get_llm_response_agent(question):
        response1 = response
        print(f"回答: {response}")
    
    # 检查缓存
    print(f"第一次调用后缓存大小: {len(common_questions_cache)}")
    if question in common_questions_cache:
        print("问题已缓存")
    else:
        print("问题未缓存")
    
    # 第二次调用
    print(f"\n第二次调用: {question}")
    response2 = ""
    async for response in get_llm_response_agent(question):
        response2 = response
        print(f"回答: {response}")
    
    # 验证缓存是否生效
    print(f"第二次调用后缓存大小: {len(common_questions_cache)}")
    if response1 == response2:
        print("缓存机制正常工作 - 两次响应相同")
    else:
        print("缓存机制异常 - 两次响应不同")

async def test_financial_query():
    """测试客户财务状况查询功能"""
    print("\n=== 测试客户财务状况查询功能 ===")
    
    # 测试查询特定客户的财务状况
    test_questions = [
        "叶竞玫的财务状况怎么样？",
        "谢佳欣的贷款情况如何？",
        "刘杰的信用卡信息是什么？"
    ]
    
    for question in test_questions:
        print(f"\n--- 测试问题: {question} ---")
        try:
            async for response in get_llm_response_agent(question):
                print(f"回答: {response}")
        except Exception as e:
            print(f"查询出错: {e}")

async def test_timeout_handling():
    """测试超时处理"""
    print("\n=== 测试超时处理 ===")
    
    # 使用一个可能需要较长时间处理的问题
    question = "请详细解释债务优化的各个方面，包括其原理、方法和实际应用案例。"
    print(f"测试问题: {question}")
    
    try:
        async for response in get_llm_response_agent(question):
            print(f"回答: {response}")
    except Exception as e:
        print(f"正确捕获到异常: {type(e).__name__}: {e}")

async def main():
    """主测试函数"""
    print("开始全面测试所有优化功能...")
    
    # 测试缓存机制
    await test_cache_mechanism()
    
    # 测试客户财务状况查询
    await test_financial_query()
    
    # 测试超时处理
    await test_timeout_handling()
    
    print("\n所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
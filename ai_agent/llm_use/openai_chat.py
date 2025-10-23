import os
import dashscope
from dotenv import load_dotenv
from http import HTTPStatus
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
# 加载环境变量
load_dotenv()
# 初始化数据库连接
# 注意：在生产环境中，应该使用更安全的数据库连接方式
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db.sqlite3')
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

llm = ChatOpenAI(
    model="qwen-max",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7
)

agent = create_sql_agent(
    llm=llm,
    toolkit=SQLDatabaseToolkit(db=db, llm=llm),
    agent_type="openai-tools",  # ✅ 支持 function calling
    verbose=True
)
# 初始化阿里云百炼平台客户端
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
model = os.getenv("LLM_MODEL", "qwen-max")



# 在这里构建特殊需求的提示词模板
# 例如，添加指令来限制响应长度、指定输出格式等

async def get_llm_response_openai(prompt):
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
        responses = agent.invoke(
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
import os
import dashscope
from dotenv import load_dotenv
from http import HTTPStatus
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
# 加载环境变量
load_dotenv()

# # 初始化阿里云百炼平台客户端
# dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
# model = os.getenv("LLM_MODEL", "qwen-max")

# 初始化数据库连接
# 注意：在生产环境中，应该使用更安全的数据库连接方式
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'db.sqlite3')
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

# 使用 DashScope 的 OpenAI 兼容接口
llm = ChatOpenAI(
    model="qwen-max",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# 创建 SQL Agent（官方推荐方式）
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",  # 必须使用支持 function calling 的 agent 类型
    verbose=True,
    system_prompt="""你是一个能够回答关于SQL数据库问题的智能助手。数据库包含以下表格：
1. core_company：公司信息表
   - id (INTEGER)：公司ID
   - name (varchar(100))：公司名称
   - created_at (datetime)：创建时间

2. core_customer：客户信息表
   - id (INTEGER)：客户ID
   - company_id (bigint)：公司ID（关联core_company表的id字段）
   - name (varchar(100))：客户姓名
   - phone (varchar(50))：电话及微信号
   - notes (TEXT)：备注
   - created_at (datetime)：创建时间
   - financing_date (date)：融资日期
   - contract_date (date)：签约日期
   - last_reminder_date (date)：上一次提醒日期
   - credit_card_multiplier (decimal)：信用卡倍率
   - monthly_payment_multiplier (decimal)：月供倍率
   - is_archived (bool)：是否已归档

3. core_creditcard：信用卡账单明细表
   - id (INTEGER)：ID
   - customer_id (bigint)：客户ID（关联core_customer表的id字段）
   - bank (varchar(50))：银行渠道
   - total_limit (decimal)：总授信额度
   - has_installment (bool)：有无分期
   - installment_amount (decimal)：分期金额
   - billing_date (smallint unsigned)：账单日
   - repayment_date (smallint unsigned)：还款日

4. core_loan：信用贷款账单明细表
   - id (INTEGER)：ID
   - customer_id (bigint)：客户ID（关联core_customer表的id字段）
   - bank (varchar(50))：银行渠道
   - total_limit (decimal)：总授信额度
   - balance (decimal)：贷款余额
   - monthly_payment (decimal)：月还款
   - due_date (date)：到期时间
   - repayment_date (smallint unsigned)：还款日

5. core_monthlypayment：月供出款记录表
   - id (INTEGER)：ID
   - customer_id (bigint)：客户ID（关联core_customer表的id字段）
   - payment_date (date)：出款时间
   - amount (decimal)：出款金额
   - notes (varchar(200))：备注
   - is_private (bool)：是否私人借款
   - cost (decimal)：资金使用成本
   - days_used (integer)：资金使用天数

6. core_creditcardpayment：信用卡出款记录表
   - id (INTEGER)：ID
   - customer_id (bigint)：客户ID（关联core_customer表的id字段）
   - bank (varchar(50))：银行
   - payment_date (date)：出款时间
   - payment_amount (decimal)：出款金额
   - withdrawal_amount (decimal)：刷出金额
   - withdrawal_date (date)：刷出时间
   - notes (varchar(200))：备注
   - fee (decimal)：信用卡费率

7. core_customerimage：客户图片表
   - id (INTEGER)：ID
   - customer_id (bigint)：客户ID（关联core_customer表的id字段）
   - title (varchar(100))：图片标题
   - image (varchar)：图片文件路径
   - uploaded_at (datetime)：上传时间

在生成SQL查询时，请始终使用正确的表名（包括'core_'前缀）和正确的字段名。当需要从多个表获取信息时，请使用适当的JOIN操作。"""
)

async def get_llm_response_database(prompt):
    """
    获取LLM的流式响应
    :param prompt: 提示词
    :return: 流式响应生成器
    """
    try:
        # 使用SQL Agent执行查询
        response = agent_executor.invoke({"input": prompt})
        
        # 返回响应结果
        if "output" in response:
            yield response["output"]
        else:
            yield "抱歉，我没有找到相关信息。"
    except Exception as e:
        yield f"Error: {str(e)}"
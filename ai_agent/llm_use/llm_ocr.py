import os
import logging
import base64
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
from langchain_openai import ChatOpenAI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

model = ChatOpenAI(
    # model="qwen-vl-ocr-latest",
    model="qwen3-vl-plus",
    # model="qwen-vl-ocr",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1,  # 温度参数，用于控制模型的随机程度，默认值为0.1
    max_tokens=1000,  # 最大输出token数，默认值为1000
    timeout=30,  # 请求超时时间，单位为秒，默认值为30
    max_retries=2,  # 最大重试次数
    # ... (other params)
)

def image_to_base64(image_bytes: bytes) -> str:
    """将图像字节转为 base64 URL（兼容 OpenAI 多模态格式）"""
    try:
        # 确保是 RGB 格式（避免 RGBA/P 通道问题）
        img = Image.open(BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        raise ValueError(f"图像处理失败: {e}")

async def get_llm_response_ocr(prompt: str, image_bytes: bytes = None):
    """
    支持文本 + 图像的多模态请求
    :param prompt: 用户文字提示（如“请提取发票总金额”）
    :param image_bytes: 上传的图像二进制数据（可选）
    :return: 流式响应生成器
    """
    try:
        
        # 构造多模态消息
        message_content = [{"type": "text", "text": prompt}]
        if image_bytes:
            image_url = image_to_base64(image_bytes)
            message_content.append({"type": "image_url", "image_url": {"url": image_url}})

        # 直接调用模型（绕过不支持图像的 Agent）
        response = await model.ainvoke([
            {"role": "user", "content": message_content}
        ])

        result = str(response.content).strip()
        yield result

    except Exception as e:
        error_msg = f"处理请求时出错: {str(e)}"
        yield error_msg
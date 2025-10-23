import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .temp_storage import get_temp_image, delete_temp_image
from .llm_use.llm_ocr import get_llm_response_ocr
from .llm_use.llm_agent import get_llm_response_agent

logger = logging.getLogger(__name__)

# 集成OCR和智能体功能

class AgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.task_id = self.scope['url_route']['kwargs']['task_id']
            self.room_group_name = f'agent_{self.task_id}'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            print(f"WebSocket connected for task {self.task_id}")
        except Exception as e:
            print(f"WebSocket connection failed for task {self.task_id}: {e}", exc_info=True)
            # 可选：主动关闭
            await self.close()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for task {self.task_id}")

    # 接受 WebSocket 消息
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            # 从前端发送的数据中获取content字段，而不是message字段
            print(f"Received message: {data}")
            message = data.get('content')
            conversation_id = data.get('conversation_id')
            image_id = data.get('image_id') # 新增：从前端获取图片ID
            message_type = data.get('type')
            
            if message:
                # Send message to room group
                # 发送消息到房间组为什么？因为我们需要将用户发送的消息广播给所有连接到该房间组的客户端（包括前端）
                # 消息分发方法（事件处理器）为什么？因为我们需要根据用户发送的消息类型，调用不同的事件处理器来处理消息
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat.message', # 前端发送的消息类型
                        'message': message, # 前端发送的消息内容
                        'sender': 'user', # 前端发送的消息发送者
                        'conversation_id': conversation_id # 前端发送的消息所属的对话ID
                    }
                )
                
                # Process the request and get AI response with streaming
                # 处理用户请求并获取AI响应（流式）
                # await self.process_request(message)
                # 🔥 关键修改：启动后台任务，不要 await！
                asyncio.create_task(self.process_request(message, conversation_id, image_id))
            else:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat.error',
                        'message': '请输入有效消息',
                        'sender': 'system'
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def process_request(self, message, conversation_id, image_id=None):
        """
        Process the user request and return AI response with streaming
        """
        # 构建提示词
        # 构建提示词为什么？因为我们需要根据用户发送的消息构建一个提示词，以便LLM能够理解用户的意图
        print("开始处理请求，构建提示词")
        prompt = self.build_prompt(message)
        
        # 获取图片字节
        image_bytes = None
        if image_id:
            # 从临时存储中获取图片字节
            image_bytes = await asyncio.get_event_loop().run_in_executor(
                None,
                get_temp_image,
                image_id
            )
            if not image_bytes:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat.error',
                        'message': '图片不存在，请重新上传图片',
                        'sender': 'system'
                    }
                )
                return
        
        # Send typing indicator
        # 发送思考指示器为什么？因为我们需要告诉前端用户正在思考中，以便用户知道服务器正在处理请求
    
        # === 阶段 1: 分析债务 ===
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.thinking',
                'content': '正在分析图片内容...' if image_bytes else '正在分析您的债务情况...',
                'sender': 'system'
            }
        )
        # 模拟短延迟（可选，提升感知）
        await asyncio.sleep(0.5)

        # === 阶段 2: 生成建议 ===
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.thinking',
                'content': '正在生成基于图片内容的建议...' if image_bytes else '正在生成个性化还款建议...',
                'sender': 'system'
            }
        )
        await asyncio.sleep(0.3)

        # === 阶段 3: 调用 LLM 流式响应 ===
        try:
            full_response = ""
            print(f"开始处理请求，调用 LLM 流式响应，提示词: {prompt}，会话ID: {conversation_id}，图片ID: {image_id}")
            
            # 根据是否有图片选择不同的LLM处理函数
            if image_bytes:
                # 有图片，调用OCR处理函数
                async for chunk in get_llm_response_ocr(prompt, image_bytes):
                    full_response += chunk
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat.message_chunk',
                            'chunk': chunk,
                            'sender': 'ai'
                        }
                    )
            else:
                # 没有图片，调用普通agent处理函数
                async for chunk in get_llm_response_agent(prompt, conversation_id):
                    full_response += chunk
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat.message_chunk',
                            'chunk': chunk,
                            'sender': 'ai'
                        }
                    )
            
            # 删除临时图片（如果有）
            if image_id:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    delete_temp_image,
                    image_id
                )
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat.message_complete',
                    'message': full_response,
                    'sender': 'ai'
                }
            )
        except Exception as e:
            error_msg = f"处理请求时出现错误: {str(e)}"
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat.error',
                    'message': error_msg,
                    'sender': 'system'
                }
            )
        finally:
            # 可选：发送结束信号（前端已用 response_end，可省略）
            pass

    # === 新增/修正事件处理器 ===

    async def chat_thinking(self, event):
        """处理 'thinking' 类型消息"""
        await self.send(text_data=json.dumps({
            'type': 'thinking',
            'content': event['content'],
            'sender': event.get('sender', 'system')
        }))

    async def chat_message(self, event):
        """现在用于广播用户消息（非 error）"""
        await self.send(text_data=json.dumps({
            'type': 'user_message',  # 或保留为 'chat_message'，但前端需监听
            'content': event['message'],
            'sender': event.get('sender', 'user'),
            'conversation_id': event.get('conversation_id')
        }))

    async def chat_error(self, event):
        """专用错误处理器"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': event['message'],
            'sender': event.get('sender', 'system')
        }))

# 注意：保留原有的 chat_message_chunk / chat_message_complete / chat_typing
# 但 chat_typing 目前未被前端使用，可考虑移除或用于其他用途
    
    async def chat_message_chunk(self, event):
        # Send message chunk to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'response_chunk',
            'content': event['chunk'],
            'sender': event.get('sender', 'ai')
        }))

    async def chat_message_complete(self, event):
        # Send complete message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'response_end',
            'content': event['message'],
            'sender': event.get('sender', 'ai')
        }))

    async def chat_typing(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'start_thinking',
            'is_typing': event['is_typing']
        }))
        
    def build_prompt(self, message):
        """
        Build the prompt for the LLM based on the user message
        """
        return f"用户消息: {message}\n"
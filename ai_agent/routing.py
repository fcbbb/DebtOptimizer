from django.urls import re_path
from . import consumers
from . import chat_consumers
from . import ocr_consumer

websocket_urlpatterns = [
    re_path(r'ws/agent/(?P<task_id>[0-9a-f-]+)/$', consumers.AgentConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<task_id>[0-9a-f-]+)/$', chat_consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/ocr/(?P<task_id>[0-9a-f-]+)/$', ocr_consumer.OcrConsumer.as_asgi()),
]
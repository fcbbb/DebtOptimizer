import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DebtOptimizer.settings')

# 导入ai_agent的WebSocket路由
from ai_agent import routing as ai_agent_routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            ai_agent_routing.websocket_urlpatterns
        )
    ),
})
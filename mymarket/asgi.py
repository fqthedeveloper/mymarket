import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import marketplace.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mymarket.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": AuthMiddlewareStack(
        URLRouter(
            marketplace.routing.websocket_urlpatterns
        )
    ),
})
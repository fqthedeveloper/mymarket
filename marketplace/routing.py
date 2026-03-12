from django.urls import re_path
from . import consumers

websocket_urlpatterns = [

    # Chat room websocket
    re_path(
        r"ws/chat/(?P<conversation_id>\d+)/$",
        consumers.ChatConsumer.as_asgi()
    ),

    # Chat list websocket (buyer & seller list auto update)
    re_path(
        r"ws/chat-list/$",
        consumers.ChatListConsumer.as_asgi()
    ),

]
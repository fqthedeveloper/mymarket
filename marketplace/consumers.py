import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.contrib.auth.models import User

from .models import Message, Conversation


# ===============================
# CHAT ROOM CONSUMER
# ===============================

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        self.room_group_name = f"chat_{self.conversation_id}"

        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):

        data = json.loads(text_data)

        message_text = data["message"]

        user = self.scope["user"]

        conversation = await self.get_conversation(self.conversation_id)

        msg = await self.create_message(
            conversation,
            user,
            message_text
        )

        # Send message to chat room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_text,
                "sender": user.username,
                "timestamp": str(msg.timestamp),
            }
        )

        # Notify buyer chat list
        await self.channel_layer.group_send(
            f"user_{conversation.buyer.id}_chatlist",
            {
                "type": "chat_list_update"
            }
        )

        # Notify seller chat list
        await self.channel_layer.group_send(
            f"user_{conversation.seller.id}_chatlist",
            {
                "type": "chat_list_update"
            }
        )


    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "timestamp": event["timestamp"]
        }))


    @database_sync_to_async
    def get_conversation(self, cid):

        return Conversation.objects.get(id=cid)


    @database_sync_to_async
    def create_message(self, conversation, user, text):

        return Message.objects.create(
            conversation=conversation,
            sender=user,
            text=text
        )


# ===============================
# CHAT LIST CONSUMER
# ===============================

class ChatListConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{self.user.id}_chatlist"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )


    async def chat_list_update(self, event):

        await self.send(text_data=json.dumps({
            "type": "update"
        }))
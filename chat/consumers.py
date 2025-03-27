import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    room_users = {}

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']
        print(f"[CONNECT] room: {self.room_name}, user: {self.user}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        if self.user.is_authenticated:
            ChatConsumer.room_users.setdefault(self.room_name, set()).add(self.user.username)
            await self.send_user_list()

    async def disconnect(self, close_code):
        print(f"[DISCONNECT] room: {self.room_name}, user: {self.user}")

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        if self.user.is_authenticated and self.room_name in ChatConsumer.room_users:
            ChatConsumer.room_users[self.room_name].discard(self.user.username)
            await self.send_user_list()

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope['user']

        if data.get('type') == 'typing':
            if user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'username': user.username
                    }
                )
            return

        if data.get('type') == 'chat':
            message = data.get('message')
            print(f"[RECEIVE] user: {user}, message: {message}")

            if user and not isinstance(user, AnonymousUser):
                await self.save_message(user, self.room_name, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': user.username if user.is_authenticated else 'Anonymous'
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': f"{event['username']}: {event['message']}"
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username']
        }))

    async def user_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'users',
            'users': event['users']
        }))

    async def send_user_list(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_list',
                'users': list(ChatConsumer.room_users.get(self.room_name, []))
            }
        )

    @sync_to_async
    def save_message(self, user, room, content):
        Message.objects.create(user=user, room=room, content=content)

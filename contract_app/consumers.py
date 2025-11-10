# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from accounts.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_name = f"chat_{min(self.user.id, self.other_user_id)}_{max(self.user.id, self.other_user_id)}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            message = data['message']
            saved_msg = await self.save_message(message)
            await self.channel_layer.group_send(self.room_name, {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.user.id,
                'sender_contact': self.user.get_contact(),
                'sender_name': self.user.full_name,
                'account_type': self.user.account_type,
                'timestamp': saved_msg.timestamp.isoformat()
            })

        elif msg_type == 'call_initiate':
            await self.channel_layer.group_send(self.room_name, {
                'type': 'incoming_call',
                'from_id': self.user.id,
                'from_contact': self.user.get_contact(),
                'from_name': self.user.full_name
            })

        elif msg_type == 'call_offer':
            await self.channel_layer.group_send(self.room_name, {
                'type': 'call_offer',
                'offer': data['offer'],
                'from': self.user.get_contact()
            })

        elif msg_type == 'call_answer':
            await self.channel_layer.group_send(self.room_name, {
                'type': 'call_answer',
                'answer': data['answer']
            })

        elif msg_type == 'ice_candidate':
            await self.channel_layer.group_send(self.room_name, {
                'type': 'ice_candidate',
                'candidate': data['candidate']
            })

        elif msg_type == 'call_end':
            await self.channel_layer.group_send(self.room_name, {
                'type': 'call_end'
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_contact': event['sender_contact'],
            'sender_name': event['sender_name'],
            'account_type': event['account_type'],
            'timestamp': event['timestamp']
        }))

    async def incoming_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'from_id': event['from_id'],
            'from_contact': event['from_contact'],
            'from_name': event['from_name']
        }))

    async def call_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_offer',
            'offer': event['offer'],
            'from': event['from']
        }))

    async def call_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_answer',
            'answer': event['answer']
        }))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate']
        }))

    async def call_end(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_end'
        }))

    @database_sync_to_async
    def save_message(self, message):
        receiver = User.objects.get(id=self.other_user_id)
        return Message.objects.create(sender=self.user, receiver=receiver, message=message)
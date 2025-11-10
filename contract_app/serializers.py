# chat/serializers.py
from rest_framework import serializers
from .models import Message
from accounts.models import User

class UserContactSerializer(serializers.ModelSerializer):
    contact = serializers.SerializerMethodField()
    account_type = serializers.CharField(source='account_type')

    class Meta:
        model = User
        fields = ['id', 'contact', 'account_type', 'full_name']

    def get_contact(self, obj):
        return obj.get_contact()

class MessageSerializer(serializers.ModelSerializer):
    sender = UserContactSerializer()
    receiver = UserContactSerializer()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'message', 'timestamp', 'is_read']
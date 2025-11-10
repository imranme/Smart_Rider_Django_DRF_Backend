# chat/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Message
from .serializers import MessageSerializer
from django.shortcuts import get_object_or_404
from accounts.models import User

class MessageListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        other_user = get_object_or_404(User, id=user_id)
        messages = Message.objects.filter(
            sender=request.user, receiver=other_user
        ) | Message.objects.filter(
            sender=other_user, receiver=request.user
        )
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, user_id):
        receiver = get_object_or_404(User, id=user_id)
        message = request.data.get('message')
        if not message:
            return Response({"error": "Message is required"}, status=400)

        msg = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            message=message
        )
        return Response(MessageSerializer(msg).data, status=201)

class ContractListView(APIView):
    def get(self, request):
        return Response({
            "message": "Contract App is working!",
            "status": "success"
        })
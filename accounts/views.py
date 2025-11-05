from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from twilio.rest import Client
import requests

from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, SendOTPSerializer,
    VerifyOTPSerializer, DeleteAccountSerializer, UserSerializer
)

User = get_user_model()

def get_user_by_identifier(identifier):
    if '@' in identifier:
        return User.objects.filter(email=identifier).first()
    else:
        return User.objects.filter(phone=identifier).first()

def send_otp_verification(user, purpose='general'):
    otp = user.otp_code
    if user.phone:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = f"Your OTP: {otp}. Expires in 10 mins."
            if purpose == 'password_reset':
                message = f"Password reset OTP: {otp}"
            elif purpose == 'deletion':
                message = f"Delete account OTP: {otp}"
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=user.phone
            )
            return True, "SMS sent"
        except Exception as e:
            return False, str(e)
    elif user.email:
        try:
            subject = "Your OTP - Riding App"
            message = f"Your OTP: {otp}. Expires in 10 mins."
            if purpose == 'password_reset':
                subject = "Password Reset OTP"
            elif purpose == 'deletion':
                subject = "Account Deletion OTP"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            return True, "Email sent"
        except Exception as e:
            return False, str(e)
    return False, "No contact"


class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.generate_otp()
            user.save()

            send_otp_verification(user)
            print(f"OTP: {user.otp_code}")  # প্রোডাকশনে মুছে ফেলো

            return Response({
                'message': 'Registered. OTP sent.',
                'contact': user.phone or user.email,
                'otp': user.otp_code if settings.DEBUG else None
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.validated_data['contact']
            otp = serializer.validated_data['otp']
            user = get_user_by_identifier(contact)
            if not user or not user.verify_otp(otp):
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_verified = True
            user.clear_otp()
            user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Verified',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_user_by_identifier(identifier):
    if '@' in identifier:
        return User.objects.filter(email=identifier).first()
    else:
        return User.objects.filter(phone=identifier).first()

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login success',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            user.last_password_change = timezone.now()
            user.save()
            return Response({'message': 'Password changed'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.validated_data['contact']
            user = get_user_by_identifier(contact)
            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            user.generate_otp()
            user.save()
            send_otp_verification(user, 'password_reset')
            return Response({
                'message': 'OTP sent for reset',
                'otp': user.otp_code if settings.DEBUG else None
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.validated_data['contact']
            otp = serializer.validated_data['otp']
            password = serializer.validated_data['password']
            user = get_user_by_identifier(contact)
            if not user or not user.verify_otp(otp):
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.clear_otp()
            user.save()
            return Response({'message': 'Password reset'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Updated', 'user': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.generate_otp()
        user.save()
        cache.set(f'delete_{user.id}', True, 600)
        send_otp_verification(user, 'deletion')
        return Response({
            'message': 'OTP sent for deletion',
            'otp': user.otp_code if settings.DEBUG else None
        })


class ConfirmDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        otp = request.data.get('otp')
        if not user.verify_otp(otp):
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        cache.delete(f'delete_{user.id}')
        return Response({'message': 'Account deleted'})  
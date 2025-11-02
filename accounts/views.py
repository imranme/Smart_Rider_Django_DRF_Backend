from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import User, DriverProfile
from .serializers import (
    UserSerializer, SignUpSerializer, VerifyOTPSerializer,
    LoginSerializer, ResendOTPSerializer, RiderProfileSerializer,
    DriverProfileSerializer, SetupDriverProfileSerializer
)
# from .utils import send_otp_sms

User = get_user_model()

def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Send OTP via SMS (in development, just print it)
            otp_sent = send_otp_sms(user.phone_number, user.otp)
            
            return Response({
                'message': 'User registered successfully. OTP sent to your phone.',
                'phone_number': user.phone_number,
                'otp': user.otp,  # Remove this in production!
                'user_type': user.user_type
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'Phone number verified successfully',
                'tokens': tokens,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            # Get profile data
            profile_data = None
            if user.user_type == 'rider':
                profile = RiderProfile.objects.filter(user=user).first()
                if profile:
                    profile_data = RiderProfileSerializer(profile).data
            elif user.user_type == 'driver':
                profile = DriverProfile.objects.filter(user=user).first()
                if profile:
                    profile_data = DriverProfileSerializer(profile).data
            
            return Response({
                'message': 'Login successful',
                'tokens': tokens,
                'user': UserSerializer(user).data,
                'profile': profile_data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            user = User.objects.get(phone_number=phone_number)
            
            # Generate new OTP
            otp = user.generate_otp()
            
            # Send OTP via SMS
            otp_sent = send_otp_sms(user.phone_number, otp)
            
            return Response({
                'message': 'OTP resent successfully',
                'otp': otp  # Remove this in production!
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get profile based on user type
        profile_data = None
        if user.user_type == 'rider':
            profile = RiderProfile.objects.filter(user=user).first()
            if profile:
                profile_data = RiderProfileSerializer(profile).data
        elif user.user_type == 'driver':
            profile = DriverProfile.objects.filter(user=user).first()
            if profile:
                profile_data = DriverProfileSerializer(profile).data
        
        return Response({
            'user': UserSerializer(user).data,
            'profile': profile_data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        user = request.user
        
        # Update user information
        user_serializer = UserSerializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        
        # Update profile based on user type
        profile_data = None
        if user.user_type == 'rider':
            profile = RiderProfile.objects.get(user=user)
            profile_serializer = RiderProfileSerializer(profile, data=request.data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()
                profile_data = profile_serializer.data
        
        elif user.user_type == 'driver':
            profile = DriverProfile.objects.get(user=user)
            profile_serializer = DriverProfileSerializer(profile, data=request.data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()
                profile_data = profile_serializer.data
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(user).data,
            'profile': profile_data
        }, status=status.HTTP_200_OK)

class SetupDriverProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.user_type != 'driver':
            return Response({
                'error': 'Only drivers can setup driver profile'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SetupDriverProfileSerializer(data=request.data)
        if serializer.is_valid():
            # Update driver profile
            profile = DriverProfile.objects.get(user=user)
            
            for field, value in serializer.validated_data.items():
                setattr(profile, field, value)
            
            profile.save()
            
            return Response({
                'message': 'Driver profile setup completed',
                'profile': DriverProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response({
                'error': 'Both old and new passwords are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(old_password):
            return Response({
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
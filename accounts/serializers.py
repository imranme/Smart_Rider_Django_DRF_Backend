from rest_framework import serializers
from .models import User, RiderProfile, DriverProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'full_name', 'user_type', 
                  'profile_picture', 'is_verified', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at']

class SignUpSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    full_name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    user_type = serializers.ChoiceField(choices=['rider', 'driver'])
    password = serializers.CharField(write_only=True, required=False)
    
    def validate_phone_number(self, value):
        # Remove any spaces or special characters
        phone = value.replace(' ', '').replace('-', '').replace('+', '')
        
        # Check if phone number already exists
        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError("This phone number is already registered")
        
        return phone
    
    def create(self, validated_data):
        phone_number = validated_data['phone_number']
        password = validated_data.pop('password', None)
        
        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            **validated_data
        )
        
        # Generate OTP
        user.generate_otp()
        
        # Create profile based on user type
        if user.user_type == 'rider':
            RiderProfile.objects.create(user=user)
        elif user.user_type == 'driver':
            DriverProfile.objects.create(
                user=user,
                vehicle_type='car',
                vehicle_model='',
                vehicle_number='',
                license_number=''
            )
        
        return user

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    
    def validate(self, data):
        phone_number = data.get('phone_number')
        otp = data.get('otp')
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        if not user.verify_otp(otp):
            raise serializers.ValidationError("Invalid or expired OTP")
        
        data['user'] = user
        return data

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, required=False)
    
    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found with this phone number")
        
        if not user.is_verified:
            raise serializers.ValidationError("Please verify your phone number first")
        
        if password and not user.check_password(password):
            raise serializers.ValidationError("Invalid password")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        
        data['user'] = user
        return data

class ResendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    
    def validate_phone_number(self, value):
        try:
            user = User.objects.get(phone_number=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        return value

class RiderProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = RiderProfile
        fields = '__all__'

class DriverProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DriverProfile
        fields = '__all__'
        
class SetupDriverProfileSerializer(serializers.Serializer):
    vehicle_type = serializers.ChoiceField(choices=['car', 'bike'])
    vehicle_model = serializers.CharField(max_length=100)
    vehicle_number = serializers.CharField(max_length=20)
    vehicle_color = serializers.CharField(max_length=50, required=False)
    license_number = serializers.CharField(max_length=50)
    license_image = serializers.ImageField(required=False)
    vehicle_registration = serializers.ImageField(required=False)
    insurance_document = serializers.ImageField(required=False)
    
    def validate_vehicle_number(self, value):
        # Check if vehicle number already exists
        if DriverProfile.objects.filter(vehicle_number=value).exists():
            raise serializers.ValidationError("This vehicle number is already registered")
        return value
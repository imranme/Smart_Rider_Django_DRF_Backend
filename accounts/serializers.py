from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['public_id', 'username', 'full_name', 'email', 'phone', 'account_type',
                  'is_verified', 'profile_picture', 'id_number', 'payment_method',
                  'license_photo', 'car_photo', 'car_name', 'plate_number']
        read_only_fields = ['public_id', 'is_verified']

class UserRegistrationSerializer(serializers.ModelSerializer):
    contact = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['contact', 'password', 'full_name', 'account_type']

    def create(self, validated_data):
        contact = validated_data.pop('contact')
        password = validated_data.pop('password')
        if '@' in contact:
            return User.objects.create_user(email=contact, password=password, **validated_data)
        else:
            return User.objects.create_user(phone=contact, password=password, **validated_data)

class UserLoginSerializer(serializers.Serializer):
    contact = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = User.objects.filter(email=data['contact']).first() or User.objects.filter(phone=data['contact']).first()
        if user and user.check_password(data['password']):
            data['user'] = user
            return data
        raise serializers.ValidationError("Invalid credentials")

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Wrong password")
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class ForgotPasswordSerializer(serializers.Serializer):
    contact = serializers.CharField()

class ResetPasswordSerializer(serializers.Serializer):
    contact = serializers.CharField()
    otp = serializers.CharField()
    password = serializers.CharField()

class SendOTPSerializer(serializers.Serializer):
    contact = serializers.CharField()

class VerifyOTPSerializer(serializers.Serializer):
    contact = serializers.CharField()
    otp = serializers.CharField()

class DeleteAccountSerializer(serializers.Serializer):
    otp = serializers.CharField()
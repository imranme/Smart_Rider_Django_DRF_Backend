from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
import re

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    email_or_phone = serializers.CharField(max_length=100, write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['full_name', 'account_type', 'email_or_phone', 'password']
        extra_kwargs = {
            'full_name': {'required': False, 'allow_blank': True},
        }

    def validate_email_or_phone(self, value):
        if '@' in value:
            # Email validation
            try:
                serializers.EmailField().run_validation(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Enter a valid email address.")
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already registered.")
            return value
        else:
            # Phone validation
            if not re.match(r'^\+?\d{7,20}$', value):
                raise serializers.ValidationError("Invalid phone format. Use +8801711111111")
            if User.objects.filter(phone=value).exists():
                raise serializers.ValidationError("This phone is already registered.")
            return value

    def create(self, validated_data):
        email_or_phone = validated_data.pop('email_or_phone')
        password = validated_data.pop('password')

        if '@' in email_or_phone:
            email = email_or_phone
            phone = None
        else:
            email = None
            phone = email_or_phone

        user = User.objects.create_user(
            email=email,
            phone=phone,
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email_or_phone = data.get('email_or_phone')
        password = data.get('password')

        if not email_or_phone or not password:
            raise serializers.ValidationError("Both fields are required.")

        user = None
        if '@' in email_or_phone:
            user = User.objects.filter(email=email_or_phone).first()
        else:
            user = User.objects.filter(phone=email_or_phone).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("Account is not verified.")
            data['user'] = user
            return data
        raise serializers.ValidationError("Invalid credentials.")

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match.")
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError("New password must be different.")
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=100)

    def validate_contact(self, value):
        user = None
        if '@' in value:
            user = User.objects.filter(email=value).first()
        else:
            user = User.objects.filter(phone=value).first()

        if not user:
            raise serializers.ValidationError("No account found with this contact.")
        self.context['user'] = user
        return value


class ResetPasswordSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=100)
    otp = serializers.CharField(max_length=6, min_length=6)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value


class SendOTPSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=100)

    def validate_contact(self, value):
        user = None
        if '@' in value:
            user = User.objects.filter(email=value).first()
        else:
            user = User.objects.filter(phone=value).first()

        if not user:
            raise serializers.ValidationError("User not found.")
        self.context['user'] = user
        return value

class VerifyOTPSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=100)
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        contact = data.get('contact')
        otp = data.get('otp')

        user = None
        if '@' in contact:
            user = User.objects.filter(email=contact).first()
        else:
            user = User.objects.filter(phone=contact).first()

        if not user or not user.verify_otp(otp):
            raise serializers.ValidationError("Invalid or expired OTP.")
        data['user'] = user
        return data

class DeleteAccountSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'account_type',
            'is_verified', 'date_joined', 'updated_at',
            'profile_picture', 'id_number', 'payment_method',
            'license_photo', 'car_photo', 'car_name', 'plate_number'
        ]
        read_only_fields = [
            'id', 'username', 'is_verified', 'date_joined', 'updated_at'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.email:
            data.pop('email', None)
        if not instance.phone:
            data.pop('phone', None)
        return data
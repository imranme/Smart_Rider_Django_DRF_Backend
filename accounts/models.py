from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import random


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("Email or phone is required")
        if email and phone:
            raise ValueError("Only one of email or phone allowed")

        if email:
            email = self.normalize_email(email)
            username = email
        else:
            username = phone

        user = self.model(username=username, email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('account_type', 'user')

        return self.create_user(email=email, phone=phone, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class AccountType(models.TextChoices):
        USER = 'user', 'User'
        DRIVER = 'driver', 'Driver'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'credit_card', 'Credit Card'

    # public_id = models.UUIDField(c default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    account_type = models.CharField(max_length=10, choices=AccountType.choices, default=AccountType.USER)

    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    id_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, blank=True, null=True)

    license_photo = models.ImageField(upload_to='licenses/', blank=True, null=True)
    car_photo = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    car_name = models.CharField(max_length=100, blank=True, null=True)
    plate_number = models.CharField(max_length=20, blank=True, null=True)

    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'custom_user'

    def clean(self):
        if not self.email and not self.phone:
            raise ValidationError("Email or phone required")
        if self.email and self.phone:
            raise ValidationError("Only one contact allowed")

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email or self.phone
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    def generate_otp(self):
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save(update_fields=['otp_code', 'otp_created_at'])
        return self.otp_code

    def verify_otp(self, code):
        if self.otp_code != code:
            return False
        if not self.otp_created_at:
            return False
        if timezone.now() > self.otp_created_at + timedelta(minutes=10):
            return False
        return True

    def clear_otp(self):
        self.otp_code = None
        self.otp_created_at = None
        self.is_verified = True
        self.save(update_fields=['otp_code', 'otp_created_at', 'is_verified'])
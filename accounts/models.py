import uuid
import random
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


# ==========================
# USER MANAGER
# ==========================
class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("User must provide either email or phone number.")
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email=email, password=password, **extra_fields)


# ==========================
# USER MODEL
# ==========================
class User(AbstractBaseUser, PermissionsMixin):
    class AccountType(models.TextChoices):
        REGULAR = 'R', 'Regular'
        DRIVER = 'D', 'Driver'

    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    username = models.CharField(max_length=100, unique=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, null=True, blank=True)
    account_type = models.CharField(max_length=1, choices=AccountType.choices, default=AccountType.REGULAR)
    address = models.CharField(max_length=200, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    def __str__(self):
        return self.email or self.phone or self.username


# ==========================
# OTP MODEL (Signup / Password Reset)
# ==========================
class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20,
        choices=[
            ("signup", "Signup Verification"),
            ("reset", "Password Reset"),
        ],
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f"OTP({self.user.username}) - {self.purpose}"


# ==========================
# VEHICLE MODEL
# ==========================
class Vehicle(models.Model):
    class Type(models.TextChoices):
        BIKE = 'BIKE', 'Bike'
        CAR_SEDAN = 'SEDAN', 'Car Sedan'
        CAR_SUV = 'SUV', 'Car SUV'
        RIKSHAW = 'RIK', 'Rikshaw'
        BUS = 'BUS', 'Bus'

    vehicle_number = models.CharField(max_length=50, unique=True)
    seat_capacity = models.IntegerField(null=True, blank=True)
    mileage = models.FloatField(null=True, blank=True)
    vehicle_type = models.CharField(max_length=10, choices=Type.choices, default=Type.CAR_SEDAN)
    vehicle_photo = models.ImageField(upload_to='vehicles/', null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle_type} - {self.vehicle_number}"


# ==========================
# DRIVER PROFILE MODEL
# ==========================
class DriverProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'P', 'Pending'
        VERIFIED = 'V', 'Verified'
        REJECTED = 'R', 'Rejected'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50, null=True, blank=True)
    license_photo = models.ImageField(upload_to='drivers/license/', null=True, blank=True)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=30, choices=[('cash', 'Cash'), ('card', 'Card')], default='cash')
    verification_status = models.CharField(max_length=1, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)
    verified_at = models.DateTimeField(null=True, blank=True)

    def mark_verified(self):
        self.verification_status = self.VerificationStatus.VERIFIED
        self.verified_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Driver: {self.user.name} ({self.get_verification_status_display()})"

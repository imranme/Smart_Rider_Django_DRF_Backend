from django.contrib import admin
from .models import User, UserOTP, Vehicle, DriverProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'account_type', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('account_type', 'is_verified', 'is_staff', 'is_active')

@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'purpose', 'is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'otp_code', 'purpose')
    list_filter = ('purpose', 'is_used')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'vehicle_type', 'seat_capacity', 'mileage')
    search_fields = ('vehicle_number',)
    list_filter = ('vehicle_type',)

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'vehicle', 'verification_status', 'verified_at')
    search_fields = ('user__username', 'license_number')
    list_filter = ('verification_status', 'payment_method')

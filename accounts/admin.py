from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from .models import User


class UserCreationForm(forms.ModelForm):
    contact = forms.CharField(max_length=150, help_text="Enter email or phone")

    class Meta:
        model = User
        fields = ('contact', 'full_name', 'account_type', 'password')

    def clean_contact(self):
        value = self.cleaned_data['contact']
        if '@' in value:
            try:
                forms.EmailField().clean(value)
                if User.objects.filter(email=value).exists():
                    raise forms.ValidationError("Email already exists.")
                return value
            except:
                raise forms.ValidationError("Invalid email.")
        else:
            if User.objects.filter(phone=value).exists():
                raise forms.ValidationError("Phone already exists.")
            return value

    def save(self, commit=True):
        user = super().save(commit=False)
        value = self.cleaned_data['contact']
        if '@' in value:
            user.email = value
            user.phone = None
        else:
            user.phone = value
            user.email = None
        user.username = value
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('username', 'get_contact', 'full_name', 'account_type', 'is_verified', 'is_staff')
    list_filter = ('account_type', 'is_verified', 'is_staff')
    search_fields = ('username', 'email', 'phone', 'full_name')
    ordering = ('-date_joined',)
    readonly_fields = ('username', 'date_joined', 'updated_at')

    fieldsets = (
        ('Login Info', {'fields': ('username', 'password')}),
        ('Personal', {'fields': ('full_name', 'email', 'phone', 'account_type')}),
        ('Media', {'fields': ('profile_picture', 'license_photo', 'car_photo')}),
        ('Driver', {'fields': ('car_name', 'plate_number', 'id_number')}),
        ('Payment', {'fields': ('payment_method',)}),
        ('Status', {'fields': ('is_verified', 'is_staff', 'is_active')}),
        ('Dates', {'fields': ('date_joined', 'updated_at')}),
    )

    add_fieldsets = (
        ('Create User', {'fields': ('contact', 'full_name', 'account_type', 'password')}),
        ('Permissions', {'fields': ('is_verified', 'is_staff')}),
    )

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)

    def get_contact(self, obj):
        return obj.email or obj.phone
    get_contact.short_description = "Contact"

    actions = ['verify_selected', 'unverify_selected']

    def verify_selected(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} users verified.")
    verify_selected.short_description = "Verify"

    def unverify_selected(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"{updated} users unverified.")
    unverify_selected.short_description = "Unverify"
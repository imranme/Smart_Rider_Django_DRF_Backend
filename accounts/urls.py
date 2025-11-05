from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view()), #done
    path('verify-otp/', views.VerifyOTPView.as_view()), #phone verify not working
    path('login/', views.UserLoginView.as_view()), #done
    path('change-password/', views.ChangePasswordView.as_view()), #not working 
    path('forgot-password/', views.ForgotPasswordView.as_view()), #
    path('reset-password/', views.ResetPasswordView.as_view()),
    path('profile/', views.UserProfileView.as_view()),
    path('delete-account/', views.DeleteAccountView.as_view()),
    path('confirm-delete/', views.ConfirmDeleteView.as_view()),
]
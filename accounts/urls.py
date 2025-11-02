# from django.urls import path
# from . import views
# from rest_framework_simplejwt.views import TokenRefreshView

# urlpatterns = [
#     # path('', views.user_home),
#     path('register', views.SignUpView.as_view(), name='register'),
#     path('login', views.LoginView.as_view(), name='login'),
#     # path('logout', views.LogoutView.as_view(), name='logout'),
#     path('refresh-token', TokenRefreshView.as_view(), name='token_refresh'),
#     path('delete', views.user_delete),
#     path('update', views.user_update),
#     path('update/password', views.user_update_password),
#     path('forget/password', views.user_forget_password),
# ]


# ...existing code...
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # path('', views.user_home),
    path('register/', views.SignUpView.as_view(), name='register'),
    path('login', views.LoginView.as_view(), name='login'),
    # path('logout', views.LogoutView.as_view(), name='logout'),
    path('refresh-token', TokenRefreshView.as_view(), name='token_refresh'),
    # Replace missing function views with existing class-based views
    path('profile', views.ProfileView.as_view(), name='profile'), 
    path('profile/setup-driver', views.SetupDriverProfileView.as_view(), name='setup_driver_profile'),
    path('change-password', views.ChangePasswordView.as_view(), name='change_password'),
    path('forget/password', views.ResendOTPView.as_view(), name='forget_password'),
]

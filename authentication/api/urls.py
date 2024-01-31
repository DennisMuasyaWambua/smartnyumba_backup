from django.urls import path
from . import views
urlpatterns = [
    path('admin-login/', views.AdminLoginAPIView.as_view(), name='login-api'),
    path('admin-logout/', views.AdminLogoutAPIView.as_view(), name='user-logout-api'),
    path('admin-forgot-password/', views.ForgotPasswordAPIView.as_view(), name='forgot-password-api'),
    path('verify-change-password/', views.VerifyChangePasswordAPIView.as_view(), name='verify-change-password-api'),
    path('resend-otp/', views.ResendOtpAPIView.as_view(), name='resend-otp'),
    path('new-password/', views.NewPasswordAPIView.as_view(), name='new-password-api'),

    path('user-register/', views.UserRegisterAPIView.as_view(), name='user-register-api'),
    path('user-register-verification/', views.UserRegisterVerificationAPIView.as_view(), name='user-register-verification-api'),
    path('user-login/', views.UserLoginAPIView.as_view(), name='user-login-api'),
    path('user-logout/', views.UserLogoutAPIView.as_view(), name='user-logout-api'),
    path('user-forgot-password/', views.UserForgotPasswordAPIView.as_view(), name='forgot-password-api'),
    path('user-verify-change-password/', views.UserVerifyChangePasswordAPIView.as_view(), name='verify-change-password-api'),
    path('user-resend-otp/', views.UserResendOtpAPIView.as_view(), name='resend-otp'),
    path('user-new-password/', views.UserNewPasswordAPIView.as_view(), name='new-password-api'),

    #-----PROFILE--------#
    path('user-profile/', views.UserProfileAPIView.as_view(), name='new-password-api'),
]
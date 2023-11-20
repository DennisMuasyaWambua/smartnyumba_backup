from django.urls import path
from . import views

urlpatterns = [
    path('create-accounts/', views.CreateAccountsStaffAPIView.as_view(), name='create-accounts-profile-api'),
    path('approve-accounts/', views.ApproveAccountsStaffAPIView.as_view(), name='approve-accounts-api'),
    path('suspend-accounts/', views.SuspendAccountsStaffAPIView.as_view(), name='suspend-accounts-api'),
    path('reactivate-accounts/', views.ReactivateAccountsStaffAPIView.as_view(), name='reactivate-accounts-api'),
    path('delete-accounts/', views.DeleteAccountsStaffAPIView.as_view(), name='delete-accounts-api'),

    #--------------------AUTH APIS FOR ACCOUNTS PROFILE--------------------------

    path('accounts-login/', views.AdminLoginAccountsAPIView.as_view(), name='login-api'),
    path('accounts-logout/', views.AdminLogoutAccountsAPIView.as_view(), name='user-logout-api'),
    path('accounts-forgot-password/', views.ForgotPasswordAccountsAPIView.as_view(), name='forgot-password-api'),
    path('accounts-verify-change-password/', views.VerifyChangePasswordAccountsAPIView.as_view(), name='verify-change-password-api'),
    path('accounts-resend-otp/', views.ResendOtpAccountsAPIView.as_view(), name='resend-otp'),
    path('accounts-new-password/', views.NewPasswordAccountsAPIView.as_view(), name='new-password-api'),
]
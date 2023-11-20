from django.urls import path
from . import views

urlpatterns = [
    path('create-block-landlord/', views.CreateBlockLandlordAPIView.as_view(), name='create-accounts-profile-api'),
    path('approve-block-landlord/', views.ApproveBlockLandlordAPIView.as_view(), name='approve-accounts-api'),
    path('suspend-block-landlord/', views.SuspendBlockLandlordStaffView.as_view(), name='suspend-accounts-api'),
    path('reactivate-block-landlord/', views.ReactivateBlockLandlordAPIView.as_view(), name='reactivate-accounts-api'),
    path('delete-block-landlord/', views.DeleteBlockLandlordAPIView.as_view(), name='delete-accounts-api'),

    #--------------------AUTH APIS FOR ACCOUNTS PROFILE--------------------------

    path('block-landlord-login/', views.LoginBlockLandlordAPIView.as_view(), name='login-api'),
    path('block-landlord-logout/', views.LogoutBlockLandlordAPIView.as_view(), name='user-logout-api'),
    path('block-landlord-forgot-password/', views.ForgotPasswordBlockLandlordAPIView.as_view(), name='forgot-password-api'),
    path('block-landlord-verify-change-password/', views.VerifyChangePasswordBlockLandlordAPIView.as_view(), name='verify-change-password-api'),
    path('block-landlord-resend-otp/', views.ResendOtpPasswordBlockLandlordAPIView.as_view(), name='resend-otp'),
    path('block-landlord-new-password/', views.NewPasswordPasswordBlockLandlordAPIView.as_view(), name='new-password-api'),

    #---------------------All Tenants -------------------------------------------
    path('view-all-tenats/', views.AllTenantsAPIView.as_view(), name='view-all-tenants')
]
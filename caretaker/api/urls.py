from django.urls import path
from . import views

urlpatterns = [
    path('create-caretaker/', views.CreateCaretakerAPIView.as_view(), name='create-accounts-profile-api'),
    path('approve-caretaker/', views.ApproveCaretakerAPIView.as_view(), name='approve-accounts-api'),
    path('suspend-caretaker/', views.SuspendCaretakerView.as_view(), name='suspend-accounts-api'),
    path('reactivate-caretaker/', views.ReactivateCaretakerAPIView.as_view(), name='reactivate-accounts-api'),
    path('delete-caretaker/', views.DeleteCaretakerAPIView.as_view(), name='delete-accounts-api'),

    #--------------------AUTH APIS FOR ACCOUNTS PROFILE--------------------------

    path('caretaker-login/', views.LoginCaretakerAPIView.as_view(), name='login-api'),
    path('caretaker-logout/', views.LogoutCaretakerAPIView.as_view(), name='user-logout-api'),
    path('caretaker-forgot-password/', views.ForgotPasswordCaretakerAPIView.as_view(), name='forgot-password-api'),
    path('caretaker-verify-change-password/', views.VerifyChangePasswordCaretakerAPIView.as_view(), name='verify-change-password-api'),
    path('caretaker-resend-otp/', views.ResendOtpPasswordCaretakerAPIView.as_view(), name='resend-otp'),
    path('caretaker-new-password/', views.NewPasswordPasswordCaretakerAPIView.as_view(), name='new-password-api'),
]
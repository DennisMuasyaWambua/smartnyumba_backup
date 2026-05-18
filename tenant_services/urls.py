from django.urls import path
from . import views


urlpatterns = [
    path('pay-service/', views.PayServiceAPIView.as_view(), name='service-pay-serializer'),
    path('all-transactions/', views.AllTransactionsAPIView.as_view(), name='all-transactions-api'),


    #---------Lipa na mpesa Callback-------------------
    path('mpesa-callback/', views.MpesaCallBackAPIView.as_view(), name='mpesa-callback-data-api'),
    path('check-subscription-status/', views.CheckTransactionStatusAPIView.as_view(), name='check-status-api'),

    #---------Rent Payment Endpoints-------------------
    path('pay-rent/', views.PayRentAPIView.as_view(), name='pay-rent'),
    path('rent-mpesa-callback/', views.RentMpesaCallBackAPIView.as_view(), name='rent-mpesa-callback'),
    path('rent-transactions/', views.AllRentTransactionsAPIView.as_view(), name='rent-transactions'),

    #---------Pesapal Payment Endpoints-------------------
    path('pesapal/ipn/', views.PesapalIPNView.as_view(), name='pesapal-ipn'),
    path('pesapal-callback/', views.PesapalIPNView.as_view(), name='pesapal-callback'),
    path('pesapal-rent-callback/', views.PesapalIPNView.as_view(), name='pesapal-rent-callback'),
    path('check-payment-status/', views.CheckPaymentStatusAPIView.as_view(), name='check-payment-status'),
    path('check-rent-payment-status/', views.CheckPaymentStatusAPIView.as_view(), name='check-rent-payment-status'),
]
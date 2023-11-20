from django.urls import path
from . import views

urlpatterns = [
    path('tenant-request-repair/', views.TenantRequestRepairAPIView.as_view(), name='tenant-request-repair-api'),
    path('all-repairs/', views.AllTenantRepairsAPIView.as_view(), name='all-repairs-api')
]

from . import views
from django.urls import path

urlpatterns = [

    # path('create-admin/', views.CreateAdminAPIView.as_view(), name='create-admin-profile-api'),
    # path('approve-admin/', views.ApproveAdminAPIView.as_view(), name='approve-admin-api'),
    # path('suspend-admin/', views.SuspendAdminView.as_view(), name='suspend-admin-api'),
    # path('reactivate-admin/', views.ReactivateAdminAPIView.as_view(), name='reactivate-admin-api'),
    # path('delete-admin/', views.DeleteAdminAPIView.as_view(), name='delete-admin-api'),

    path('all-tenant-payments/', views.AllTenantPaymentsAPIView.as_view(), name='all-tenant-payments'),

]



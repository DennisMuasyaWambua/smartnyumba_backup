"""admin_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('apps/admin/api/v1/smartnyumba', admin.site.urls),
    path('apps/admin/api/v1/auth/', include('authentication.api.urls')),
    path('apps/admin/api/v1/staff-accounts/', include('staff_accounts.api.urls')),
    path('apps/admin/api/v1/block-landlord/', include('block_landlord.api.urls')),
    path('apps/admin/api/v1/properties/', include('properties.api.urls')),
    path('apps/admin/api/v1/caretaker/', include('caretaker.api.urls')),
    path('apps/admin/api/v1/tenant-services/', include('tenant_services.urls')),

]

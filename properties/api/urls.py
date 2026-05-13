from django.urls import path
from . import views

urlpatterns = [
    path('add-property/', views.AddPropertyAPIView.as_view(), name='add-property-api'),
    path('add-block-houses/', views.AddBlockHousesAPIView.as_view(), name='add-block-houses-api'),

    # Landlord property management
    path('landlord-add-property/', views.LandlordAddPropertyAPIView.as_view(), name='landlord-add-property'),
    path('landlord-properties/', views.LandlordPropertiesListAPIView.as_view(), name='landlord-properties-list'),
]
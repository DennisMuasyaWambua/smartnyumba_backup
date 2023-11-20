from django.urls import path
from . import views

urlpatterns = [
    path('add-property/', views.AddPropertyAPIView.as_view(), name='add-property-api'),
    path('add-block-houses/', views.AddBlockHousesAPIView.as_view(), name='add-block-houses-api')
]
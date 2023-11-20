from django.urls import path
from  . import views
urlpatterns = [
    path('add-goods/', views.AddGoodsAPIView.as_view(), name='add-goods-api'),
    path('publish-goods-estate/', views.UploadGoodsToEstateAPIView.as_view(), name='publish-to-estate-api'),
    path('view-unpublished-goods-estate/', views.ViewAllUnpublishedGoodsAPIView.as_view(), name='view-all-unpublised-goods-api'),
    path('view-published-goods-estate/', views.ViewAllPublishedGoodsAPIView.as_view(), name='view-all-publised-goods-api'),
    path('view-all-goods-estate/', views.ViewAllGoodsAPIView.as_view(), name='view-all-goods-api'),
    path('delete-goods/', views.DeleteGoodsAPIView.as_view(), name='publish-to-estate-api'),
]
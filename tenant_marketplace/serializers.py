from rest_framework import serializers

from .models import MarketPlace

class AddGoodsSerializer(serializers.Serializer):
    goods_name = serializers.CharField()
    goods_description = serializers.CharField()
    goods_quantity = serializers.CharField()
    any_offer = serializers.CharField()

class UploadGoodsToEstateSerializer(serializers.Serializer):
    goods_id = serializers.IntegerField()

class ViewAllUnpublishedGoodsSerializer(serializers.ModelSerializer):

    class Meta:
        model = MarketPlace
        fields = '__all__'
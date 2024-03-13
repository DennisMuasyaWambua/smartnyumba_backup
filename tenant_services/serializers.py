from rest_framework import serializers
from authentication.api.serializers import UserProfileSerializer
from properties.models import PropertyBlock

from tenant_services.models import services

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = services
        fields = '__all__'


class PayServiceSerializer(serializers.Serializer):
    email = serializers.EmailField()
    mobile_number = serializers.CharField(required=False, allow_blank=True)
    pay_via = serializers.CharField()


class AllTRansactionsSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()
    
    class Meta:
        model = services
        fields = '__all__'

class TransactionCheckSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ServiceFeeAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyBlock
        fields = '__all__'
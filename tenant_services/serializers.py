from rest_framework import serializers
from authentication.api.serializers import UserProfileSerializer
from authentication.models import Tenant, User
from properties.models import Property, PropertyBlock

from tenant_services.models import services

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = services
        fields = '__all__'


class PayServiceSerializer(serializers.Serializer):
    email = serializers.EmailField()
    mobile_number = serializers.CharField(required=False, allow_blank=True)
    pay_via = serializers.CharField()

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('block_number',)

class PropertyBlockSerializer(serializers.ModelSerializer):
    block = PropertySerializer()
    class Meta:
        model = PropertyBlock
        fields = ('house_number', 'block')


class TenantSerializer(serializers.ModelSerializer):
    PropertyBlock = PropertyBlockSerializer()
    class Meta:
        model = Tenant
        fields = ('PropertyBlock',)

class UserSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(source='tenant.all', many=True)

    def get_tenant(self, obj):
        # Access the related Tenant instance through the user's tenant relation
        tenant_instance = obj.tenant.first()  # Assuming there's only one tenant per user
        if tenant_instance:
            return TenantSerializer(tenant_instance).data
        return None

    class Meta:
        model = User
        fields = ('tenant', 'email', 'username', 'role', 'mobile_number', 'status')


class AllTRansactionsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = services
        fields = '__all__'

class TransactionCheckSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ServiceFeeAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyBlock
        fields = '__all__'
from rest_framework import serializers

from authentication.models import Tenant, PropertyBlock
from properties.models import Property

class CreateBlockLandlordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    id_number = serializers.IntegerField()
    role = serializers.IntegerField()
    approver = serializers.EmailField()


class ApproveBlockLandlordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()


class SuspendBlockLandlordSerializer(serializers.Serializer):
    email = serializers.EmailField()



#-------AUTH SERIALIZER FOR ACCOUNTS PROFILE-----------------

class BlockAdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class BlockLandlordLogOutSerializer(serializers.Serializer):
    email = serializers.EmailField()


class BlockLandlordForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class BlockLandlordVerifyChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()

class BlockLandlordResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

    
class BlockLandlordNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)
    confirm_new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class ReactivateBlockLandlordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class DeleteBlockLandlordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class AllPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = Property
        fields = '__all__'


class AllPropertyBlockSerializer(serializers.ModelSerializer):
    block = AllPropertySerializer()

    class Meta:
        model = PropertyBlock
        fields = '__all__'

class AllTenantSerializer(serializers.ModelSerializer):
    PropertyBlock = AllPropertyBlockSerializer()

    class Meta:
        model = Tenant
        fields = '__all__'
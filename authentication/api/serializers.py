from rest_framework import serializers
from authentication.models import Tenant, staffAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


from properties.models import Property, PropertyBlock

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class AdminLogOutSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()

class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

    
class NewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)
    confirm_new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)


#---USER-----

class UserRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    mobile_number = serializers.CharField()
    id_number = serializers.CharField()
    block_number = serializers.CharField()
    house_number = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)


class UserRegisterVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class UserLogOutSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()

class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

    
class NewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)
    confirm_new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class UserBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyBlock
        fields = '__all__'


class TenantProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()
    PropertyBlock = UserBlockSerializer()
    class Meta:
        model = Tenant
        fields = '__all__'

class AdminProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = staffAdmin
        fields = '__all__'


class AllProperiesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Property
        fields = ['location', 'block_number']
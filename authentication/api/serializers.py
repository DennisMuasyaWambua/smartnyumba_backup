from rest_framework import serializers
from authentication.models import Tenant, staffAdmin, ActivationPayment, ActivationTransaction
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
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    mobile_number = serializers.CharField()
    id_number = serializers.CharField()
    block_number = serializers.CharField(required=False)
    house_number = serializers.CharField(required=False)
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False, required=False)
    role = serializers.CharField(default='tenant', required=False)
    approver = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    location = serializers.CharField(required=False)

    def validate(self, data):
        role = data.get('role', 'tenant')

        # Validate role is one of the allowed values
        allowed_roles = ['tenant', 'landlord', 'accounts', 'caretaker']
        if role not in allowed_roles:
            raise serializers.ValidationError({
                'role': f'Invalid role. Must be one of: {", ".join(allowed_roles)}'
            })

        # Tenant-specific validation
        if role == 'tenant':
            required_fields = ['password', 'block_number', 'house_number', 'first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: f'{field} is required for tenant registration'
                    })

        # Landlord-specific validation
        elif role == 'landlord':
            required_fields = ['approver', 'phone_number', 'location', 'block_number', 'first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: f'{field} is required for landlord registration'
                    })

        # Other non-tenant roles (accounts, caretaker)
        else:
            required_fields = ['approver', 'phone_number', 'first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: f'{field} is required for {role} registration'
                    })

        return data


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


# Activation payment serializers
class InitiateActivationPaymentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    mobile_number = serializers.CharField(required=False, allow_blank=True)


class CheckActivationStatusSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ActivationPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivationPayment
        fields = '__all__'


class ActivationTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivationTransaction
        fields = '__all__'


# Landlord subordinate creation serializer
class LandlordCreateSubordinateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    mobile_number = serializers.CharField(max_length=15)
    id_number = serializers.CharField(max_length=8)
    role = serializers.ChoiceField(choices=['accounts', 'caretaker'])
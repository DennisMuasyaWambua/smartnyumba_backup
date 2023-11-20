from rest_framework import serializers

class CreateAccountsSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    id_number = serializers.IntegerField()
    role = serializers.IntegerField()
    approver = serializers.EmailField()


class ApproveAccountsStaffSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()


class SuspendAccountsStaffSerializer(serializers.Serializer):
    email = serializers.EmailField()



#-------AUTH SERIALIZER FOR ACCOUNTS PROFILE-----------------

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
from rest_framework import serializers

class CreateCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    id_number = serializers.IntegerField()
    role = serializers.IntegerField()
    approver = serializers.EmailField()


class ApproveCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()


class SuspendCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()



#-------AUTH SERIALIZER FOR ACCOUNTS PROFILE-----------------

class LoginCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class LogoutCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyChangePasswordCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()

class ResendOtpPasswordCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()

    
class NewPasswordPasswordCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)
    confirm_new_password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class ReactivateCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()

class DeleteCaretakerSerializer(serializers.Serializer):
    email = serializers.EmailField()
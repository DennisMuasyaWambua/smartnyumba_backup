import random
import re
from rest_framework. views import APIView as APIVIEW
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from django.contrib.auth import get_user_model, authenticate
from authentication.models import LoginOTP, OtpVerificationCode, Role, Tenant, staffAdmin
from email_service.email_service import send_forgot_password_otp, send_otp_message
from properties.models import Property, PropertyBlock


User = get_user_model()

from authentication.api.serializers import AdminLogOutSerializer, ForgotPasswordSerializer, LoginSerializer, NewPasswordSerializer, ResendOtpSerializer, TenantProfileSerializer, UserLogOutSerializer, UserRegisterSerializer, UserRegisterVerificationSerializer, VerifyChangePasswordSerializer


class AdminLoginAPIView(APIVIEW):
    serializer_class = LoginSerializer

    def post(self, request):
        try:
            data = request.data
            serializer = self.serializer_class(data=data)

            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')
            password = request.data.get('password')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)


            user = User.objects.filter(email=email)
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'user does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            admin = staffAdmin.objects.filter(email=email)
            
            if not admin.exists():
                return Response({
                    'status': False,
                    'message': 'admin with this email does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            allowed_roles = ['admin']
            user = user.first()
            if not user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': f"You cannot access this portal with user role!. Please contact customer care"
                })
            if user.status == 0:
                return Response({
                    'status': False,
                    'message': 'Account not approved'
                })
            if user.status == 2:
                return Response({
                    'status': False,
                    'message': 'Your account was rejected. Kindly contact Admin.'
                })
            if user.status == 3:
                return Response({
                    'status': False,
                    'message': 'Your account was suspended. Kindly contact Admin.'
                })
            
            user = authenticate(username=email, password=password)

            if user is None:
                return Response({
                    'status': False,
                    'message': 'Please provide correct username or password',
                })
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                    "status": True,
                    "message": "Login Successful",
                    'access_token': str(refresh.access_token),
                    'role':user.role.short_name,
                    'expires_in': '3600',
                    'token_type': 'Bearer'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Cannot log you in'
            }, status=status.HTTP_403_FORBIDDEN)
        
class AdminLogoutAPIView(APIVIEW):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminLogOutSerializer
    
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid credentials provided.',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            email = request.data.get('email')
        
            print(email)
            if not email:
                return Response({
                    'status': False,
                    'message': 'Unauthorized.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            else:
                user = User.objects.filter(email=email)
                print(user)
                if not user.exists():
                    return Response({
                        'status': False,
                        'message': 'A user does exists.'
                    })
                else:
                    user = user.first()
                    user_outstanding_tokens = OutstandingToken.objects.filter(
                        user=user)
                    if not len(user_outstanding_tokens):
                        return Response(
                            {'status': False,
                             'message': 'The token is not valid.'
                             }, status=status.HTTP_400_BAD_REQUEST)

                    else:
                        user_outstanding_tokens.delete()
                        return Response({'status': True,
                                        'message': 'User successfully signed out.'
                                        }, status=status.HTTP_200_OK)
        except Exception as error:
            print('ERROR:', str(error))
            return Response({
                'status': False,
                'message': 'Failed to logout'
            })

class ForgotPasswordAPIView(APIVIEW):
    authentication_classes=[]
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        try:
            
            data = request.data
            serializer = self.serializer_class(data=data)
            
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided.',
                    'error': serializer.errors
                }, status=status.HTTP_403_FORBIDDEN)
                
            email = request.data.get('email')
            
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = User.objects.filter(email=email)
            
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with this email does not exist.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = user.first()
            
            otp = random.randint(1111, 9999)
            OtpVerificationCode.objects.create(email=user, otp=otp, validated=False)
            email_response = send_forgot_password_otp(email=user,otp=otp)
            
            
            if not email_response:
                return Response({
                    'status': False,
                    'message': 'error sending otp'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                    'status': True,
                    'message': 'forgot password otp sent'
                }, status=status.HTTP_200_OK)
        except Exception as error:
            print(str(error))
            return Response({
                'status': False,
                'message': 'Could not reset password.'
            }, status=status.HTTP_403_FORBIDDEN)
        

class VerifyChangePasswordAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = VerifyChangePasswordSerializer
    
    def post(self, request):
        try:
            
            data = request.data
            serializer = self.serializer_class(data=data)
            
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided.'
                }, status=status.HTTP_403_FORBIDDEN)
                
            email = request.data.get('email')
            otp = request.data.get('otp')
            
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = User.objects.filter(email=email)
            
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with this email does not exist.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = user.first()
            
            verify_otp = OtpVerificationCode.objects.filter(
                    email=user, validated=False)
            if not verify_otp.exists():
                return Response({
                    'status': False,
                    'message': 'OTP does not exist.'
                }, status=status.HTTP_404_NOT_FOUND)
            verify_otp = verify_otp.last()
            if verify_otp.otp != str(otp):
                return Response({
                    'status': False,
                    'message': 'OTP does not match.'
                }, status=status.HTTP_403_FORBIDDEN)
            verify_otp.validated = True
            verify_otp.save()
            return Response({
                'status': True,
                'message': 'OTP verified successfully',
            }, status=status.HTTP_200_OK)
            
        except Exception as error:
            print(str(error))
            return Response({
                'status': False,
                'message': 'Could not reset password.'
            }, status=status.HTTP_403_FORBIDDEN)


class ResendOtpAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = ResendOtpSerializer
    
    def post(self, request):
        try:
            data = request.data
            
            serializer = self.serializer_class(data=data)
            
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'error': serializer.errors
                },status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = User.objects.filter(email=email)
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with this email does not exist.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = user.first()
            
            verify_otp = OtpVerificationCode.objects.filter(email=user, validated=False)
            if not verify_otp.exists():
                return Response({
                    'status': False,
                    'message': 'OTP does not exist.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            verify_otp = verify_otp.last()
            verify_otp.delete()

            otp = random.randint(1111, 9999)
            OtpVerificationCode.objects.create(email=user, otp=otp, validated=False)
            email_response = send_forgot_password_otp(email=user,otp=otp)
            
            
            if not email_response:
                return Response({
                    'status': False,
                    'message': 'error sending otp'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                    'status': True,
                    'message': 'otp resent'
                }, status=status.HTTP_200_OK)
            
        except Exception as error:
            print(str(error))
            
            return Response({
                'status': False,
                'message': 'We could not send otp'
            }, status=status.HTTP_403_FORBIDDEN)

class NewPasswordAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = NewPasswordSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided.',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            confirm_new_password = request.data.get('confirm_new_password')
            new_password = request.data.get('new_password')
            email = request.data.get('email')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to continue'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(new_password) < 5:
                return Response({
                    "status": False,
                    "message": "Password should be atleast 5 characters"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                if new_password != confirm_new_password:
                    return Response({
                        'status': False,
                        'message': 'Passwords not same check and try again'
                    }, status=status.HTTP_403_FORBIDDEN)
                user = User.objects.filter(
                    email=email)
                if not user.exists():
                    return Response({
                        'status': False,
                        'message': 'user account does not exist'
                    }, status=status.HTTP_404_NOT_FOUND)
                user = user.first()
                
                user.set_password(new_password)
                user.save()

                body = f'Your arronax media password changed successfully'
                
                return Response({
                    "status": True,
                    "message": "Password changed successfully."
                }, status=status.HTTP_200_OK)
        except Exception as error:
            print('ERROR:', str(error))
            return Response({
                'status': False,
                'message': 'Error resetting password.',
                'detail': str(error)
            }, status=status.HTTP_400_BAD_REQUEST)
        
#----USER

class UserRegisterAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = UserRegisterSerializer
    
    def post(self, request):
        
        try:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid credentials provided.',
                    'detail': serializer.errors
                })
            with transaction.atomic():
                email = request.data.get('email')
                first_name = request.data.get('first_name')
                last_name = request.data.get('last_name')
                id_number = request.data.get('id_number')
                password = request.data.get('password')
                mobile_number = request.data.get('mobile_number')
                block_number = request.data.get('block_number')
                house_number = request.data.get('house_number')

                mobile_number = mobile_number[-9:]
                mobile_number = f'+254{mobile_number}'

                name = f'{first_name} {last_name}'

                
                if len(first_name) > 20:
                    return Response ({
                        'status': False,
                        'message': 'Username too long'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                valid_email = re.fullmatch(email_regex, email)
                if not valid_email:
                    return Response({
                        'status': False,
                        'message': 'Provide a valid email to login'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                block = Property.objects.filter(block_number=block_number)
                print(block)

                if not block.exists():
                    return Response({
                        'status': False,
                        'message': 'Block not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                block = block.first()

                property_block = PropertyBlock.objects.filter(block=block)

                if not property_block.exists():
                    return Response({
                        'status': False,
                        'message': 'Block property not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                check_user = User.objects.filter(email=email)
                if check_user.exists():
                    return Response({
                        'status': False,
                        'message': 'User with this email already registered.'
                    }, status=status.HTTP_403_FORBIDDEN)
                tenant = 'tenant'
                role = Role.objects.filter(short_name=tenant)
                role = role.first()
                user = User(
                        username=email,
                        first_name=first_name,
                        email=email,
                        role=role,
                        mobile_number=mobile_number,
                    )
                print('user',user)
                user.save()
                user.set_password(password)
                user.is_staff = False
                user.is_active = False
                user.status = 0
                user.save()
                print(block_number)
                
                property_block = property_block.first()

                tenant = Tenant.objects.create(user=user, name=name, id_number=id_number,  email=email, is_active=0, PropertyBlock=property_block)
                print('Smart nyumba tenant created', tenant)
                otp = random.randint(1111, 9999)

                email_response = send_otp_message(email=email,otp=otp)

                if not email_response:
                    return Response({
                        'status': False,
                        'message': 'Error sending otp'
                    }, status=status.HTTP_400_BAD_REQUEST)

                body = f'Use otp {otp} to complete registration'

                LoginOTP.objects.create(mobile_number=user.mobile_number, otp=otp)
                
                return Response({
                    'status': True,
                    'message': 'Smart nyumba tenant created successfully'
                }, status=status.HTTP_200_OK)
                        
        except Exception as error:
            print('ERROR:', str(error))
            return Response({
                'status': False,
                'message': 'Sorry. We could not register you',
                'detail': str(error)
            }, status=status.HTTP_403_FORBIDDEN)
    
class UserRegisterVerificationAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = UserRegisterVerificationSerializer
    
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid credentials provided.',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            email = request.data.get('email')
            otp = request.data.get('otp')

            check_user = User.objects.filter(email=email)
            print(check_user)
            if not check_user.exists():
                return Response({
                    'status': False,
                    'message': 'User does not exist.'
                }, status=status.HTTP_404_NOT_FOUND)
            user = check_user.first()
            print(user)
            if user.is_active:
                return Response({
                    'status': False,
                    'message':'Account has already been activated'
                }, status=status.HTTP_403_FORBIDDEN)
            
            role = Role.objects.filter(short_name='tenant')
            if not role.exists():
                return Response({
                    'status': False,
                    'message': 'Role not found.'
                }, status=status.HTTP_404_NOT_FOUND)
                
            role = role.first()
            print(role)
            print(user.mobile_number)
            login_otp = LoginOTP.objects.filter(mobile_number=user.mobile_number)
            if not login_otp.exists():
                return Response({
                    'status': False,
                    'message': 'OTP does not exist.'
                }, status=status.HTTP_404_NOT_FOUND)
            login_otp = login_otp.last()
            if login_otp.otp != str(otp):
                return Response({
                    'status': False,
                    'message': 'OTP does not match.'
                }, status=status.HTTP_403_FORBIDDEN)

            smart_nyumba_user = Tenant.objects.filter(user=user)
            if not smart_nyumba_user.exists():
                return Response({
                    'status': False,
                    'message': 'Arronax user profile not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            smart_nyumba_user = smart_nyumba_user.first()
            print(smart_nyumba_user)
            smart_nyumba_user.is_active=1
            smart_nyumba_user.save()
            user.status=1
            user.role = role
            user.is_active=1
            user.save()
            return Response({
                'status': True,
                'message': 'Account activated. Navigate to login',
            }, status=status.HTTP_200_OK)
            
        except Exception as error:
            print(str(error))
            return Response({
                'status': False,
                'message': 'Couldnt be able to send otp'
            }, status=status.HTTP_403_FORBIDDEN)

class UserLoginAPIView(APIVIEW):
    serializer_class = LoginSerializer

    def post(self, request):
        try:
            data = request.data
            serializer = self.serializer_class(data=data)

            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')
            password = request.data.get('password')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)


            user = User.objects.filter(email=email)
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'user does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            tenant = Tenant.objects.filter(email=email)
            
            if not tenant.exists():
                return Response({
                    'status': False,
                    'message': 'tenant with this email does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            allowed_roles = ['tenant']
            
            user = user.first()
            print(user.role.short_name)
            if not user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': f"You cannot access this portal with user role!. Please contact customer care"
                })
            if user.status == 0:
                return Response({
                    'status': False,
                    'message': 'Account not approved'
                })
            if user.status == 2:
                return Response({
                    'status': False,
                    'message': 'Your account was rejected. Kindly contact Admin.'
                })
            if user.status == 3:
                return Response({
                    'status': False,
                    'message': 'Your account was suspended. Kindly contact Admin.'
                })
            
            user = authenticate(username=email, password=password)

            if user is None:
                return Response({
                    'status': False,
                    'message': 'Please provide correct username or password',
                })
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                    "status": True,
                    "message": "Login Successful",
                    'access_token': str(refresh.access_token),
                    'role':user.role.short_name,
                    'expires_in': '3600',
                    'token_type': 'Bearer'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Cannot log you in'
            }, status=status.HTTP_403_FORBIDDEN)
        
class UserLogoutAPIView(APIVIEW):
    permission_classes = [IsAuthenticated]
    serializer_class = UserLogOutSerializer
    
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid credentials provided.',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            email = request.data.get('email')
        
            print(email)
            if not email:
                return Response({
                    'status': False,
                    'message': 'Unauthorized.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            else:
                user = User.objects.filter(email=email)
                print(user)
                if not user.exists():
                    return Response({
                        'status': False,
                        'message': 'A user does exists.'
                    })
                else:
                    user = user.first()
                    user_outstanding_tokens = OutstandingToken.objects.filter(
                        user=user)
                    if not len(user_outstanding_tokens):
                        return Response(
                            {'status': False,
                             'message': 'The token is not valid.'
                             }, status=status.HTTP_400_BAD_REQUEST)

                    else:
                        user_outstanding_tokens.delete()
                        return Response({'status': True,
                                        'message': 'User successfully signed out.'
                                        }, status=status.HTTP_200_OK)
        except Exception as error:
            print('ERROR:', str(error))
            return Response({
                'status': False,
                'message': 'Failed to logout'
            })

class UserForgotPasswordAPIView(APIVIEW):
    authentication_classes=[]
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        try:
            
            data = request.data
            serializer = self.serializer_class(data=data)
            
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided.',
                    'error': serializer.errors
                }, status=status.HTTP_403_FORBIDDEN)
                
            email = request.data.get('email')
            
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = User.objects.filter(email=email)
            
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with this email does not exist.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = user.first()
            
            otp = random.randint(1111, 9999)
            OtpVerificationCode.objects.create(email=user, otp=otp, validated=False)
            email_response = send_forgot_password_otp(email=user,otp=otp)
            
            
            if not email_response:
                return Response({
                    'status': False,
                    'message': 'error sending otp'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                    'status': True,
                    'message': 'forgot password otp sent'
                }, status=status.HTTP_200_OK)
        except Exception as error:
            print(str(error))
            return Response({
                'status': False,
                'message': 'Could not reset password.'
            }, status=status.HTTP_403_FORBIDDEN)
        

class UserVerifyChangePasswordAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = VerifyChangePasswordSerializer
    
    def post(self, request):
        try:
            
            data = request.data
            serializer = self.serializer_class(data=data)
            
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided.'
                }, status=status.HTTP_403_FORBIDDEN)
                
            email = request.data.get('email')
            otp = request.data.get('otp')
            
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = User.objects.filter(email=email)
            
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with this email does not exist.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = user.first()
            
            verify_otp = OtpVerificationCode.objects.filter(
                    email=user, validated=False)
            if not verify_otp.exists():
                return Response({
                    'status': False,
                    'message': 'OTP does not exist.'
                }, status=status.HTTP_404_NOT_FOUND)
            verify_otp = verify_otp.last()
            if verify_otp.otp != str(otp):
                return Response({
                    'status': False,
                    'message': 'OTP does not match.'
                }, status=status.HTTP_403_FORBIDDEN)
            verify_otp.validated = True
            verify_otp.save()
            return Response({
                'status': True,
                'message': 'OTP verified successfully',
            }, status=status.HTTP_200_OK)
            
        except Exception as error:
            print(str(error))
            return Response({
                'status': False,
                'message': 'Could not reset password.'
            }, status=status.HTTP_403_FORBIDDEN)


class UserResendOtpAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = ResendOtpSerializer
    
    def post(self, request):
        try:
            data = request.data
            
            serializer = self.serializer_class(data=data)
            
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'error': serializer.errors
                },status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = User.objects.filter(email=email)
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with this email does not exist.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = user.first()
            
            verify_otp = OtpVerificationCode.objects.filter(email=user, validated=False)
            if not verify_otp.exists():
                return Response({
                    'status': False,
                    'message': 'OTP does not exist.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            verify_otp = verify_otp.last()
            verify_otp.delete()

            otp = random.randint(1111, 9999)
            OtpVerificationCode.objects.create(email=user, otp=otp, validated=False)
            email_response = send_forgot_password_otp(email=user,otp=otp)
            
            
            if not email_response:
                return Response({
                    'status': False,
                    'message': 'error sending otp'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                    'status': True,
                    'message': 'otp resent'
                }, status=status.HTTP_200_OK)
            
        except Exception as error:
            print(str(error))
            
            return Response({
                'status': False,
                'message': 'We could not send otp'
            }, status=status.HTTP_403_FORBIDDEN)

class UserNewPasswordAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = NewPasswordSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided.',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            confirm_new_password = request.data.get('confirm_new_password')
            new_password = request.data.get('new_password')
            email = request.data.get('email')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to continue'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(new_password) < 5:
                return Response({
                    "status": False,
                    "message": "Password should be atleast 5 characters"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                if new_password != confirm_new_password:
                    return Response({
                        'status': False,
                        'message': 'Passwords not same check and try again'
                    }, status=status.HTTP_403_FORBIDDEN)
                user = User.objects.filter(
                    email=email)
                if not user.exists():
                    return Response({
                        'status': False,
                        'message': 'user account does not exist'
                    }, status=status.HTTP_404_NOT_FOUND)
                user = user.first()
                
                user.set_password(new_password)
                user.save()

                body = f'Your arronax media password changed successfully'
                
                return Response({
                    "status": True,
                    "message": "Password changed successfully."
                }, status=status.HTTP_200_OK)
        except Exception as error:
            print('ERROR:', str(error))
            return Response({
                'status': False,
                'message': 'Error resetting password.',
                'detail': str(error)
            }, status=status.HTTP_400_BAD_REQUEST)
        
class UserProfileAPIView(APIVIEW):
    permission_classes = [IsAuthenticated]
    serializer_class = TenantProfileSerializer

    def get(self, request):
        try:
            current_user = request.user

            current_user = request.user
            allowed_roles = ['tenant']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = Tenant.objects.filter(email=current_user)
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            user = user.first()

            serializer = self.serializer_class(user)

            return Response({
                'status': False,
                'profile': serializer.data 
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not view tenant profile'
            }, status=status.HTTP_400_BAD_REQUEST)
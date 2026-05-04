import random
import re
from rest_framework. views import APIView as APIVIEW
from rest_framework import status
from django.db import IntegrityError

from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from authentication.models import LoginOTP, OtpVerificationCode, Role, Tenant, staffAdmin
from block_landlord.models import BlockLandlord
from staff_accounts.models import staffAccounts
from caretaker.models import Caretaker
from email_service.email_service import send_forgot_password_otp, send_otp_message, send_creation_email, approve_accounts_profile
from properties.models import Property, PropertyBlock


User = get_user_model()

from authentication.api.serializers import AdminLogOutSerializer, AdminProfileSerializer, AllProperiesSerializer, ForgotPasswordSerializer, LoginSerializer, NewPasswordSerializer, ResendOtpSerializer, TenantProfileSerializer, UserLogOutSerializer, UserRegisterSerializer, UserRegisterVerificationSerializer, VerifyChangePasswordSerializer


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
            with transaction.atomic():
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

            # Check authentication requirement for non-tenant roles
            role_name = request.data.get('role', 'tenant')
            if role_name != 'tenant':
                if not request.user.is_authenticated:
                    return Response({
                        'status': False,
                        'message': 'Authentication required for this role registration'
                    }, status=status.HTTP_401_UNAUTHORIZED)

            with transaction.atomic():
                email = request.data.get('email')
                id_number = request.data.get('id_number')
                mobile_number = request.data.get('mobile_number')

                # Email validation
                email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                valid_email = re.fullmatch(email_regex, email)
                if not valid_email:
                    return Response({
                        'status': False,
                        'message': 'Provide a valid email'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if user already exists
                check_user = User.objects.filter(email=email)
                if check_user.exists():
                    return Response({
                        'status': False,
                        'message': 'User with this email already registered.'
                    }, status=status.HTTP_403_FORBIDDEN)

                # Get role object
                role = Role.objects.filter(short_name=role_name)
                if not role.exists():
                    return Response({
                        'status': False,
                        'message': f'Role {role_name} not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                role = role.first()

                # Branch based on role
                if role_name == 'tenant':
                    # TENANT REGISTRATION FLOW
                    first_name = request.data.get('first_name')
                    last_name = request.data.get('last_name')
                    password = request.data.get('password')
                    block_number = request.data.get('block_number')
                    house_number = request.data.get('house_number')

                    if len(first_name) > 20:
                        return Response({
                            'status': False,
                            'message': 'Username too long'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Validate block and property
                    block = Property.objects.filter(block_number=block_number)
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
                    property_block = property_block.first()

                    # Format mobile number for tenant
                    mobile_number = mobile_number[-9:]
                    mobile_number = f'+254{mobile_number}'

                    name = f'{first_name} {last_name}'

                    # Create User
                    user = User(
                        username=email,
                        first_name=first_name,
                        email=email,
                        role=role,
                        mobile_number=mobile_number,
                    )
                    user.save()
                    user.set_password(password)
                    user.is_staff = False
                    user.is_active = False
                    user.status = 0
                    user.save()

                    # Create Tenant profile
                    tenant = Tenant.objects.create(
                        user=user,
                        name=name,
                        id_number=id_number,
                        email=email,
                        is_active=0,
                        PropertyBlock=property_block
                    )

                    # Generate OTP and send to user
                    otp = random.randint(1111, 9999)
                    email_response = send_otp_message(email=email, otp=otp)

                    if not email_response:
                        return Response({
                            'status': False,
                            'message': 'Error sending otp'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    LoginOTP.objects.create(mobile_number=user.mobile_number, otp=otp)

                    return Response({
                        'status': True,
                        'message': 'Smart nyumba tenant created successfully'
                    }, status=status.HTTP_200_OK)

                else:
                    # NON-TENANT REGISTRATION FLOW (landlord, accounts, caretaker)
                    phone_number = request.data.get('phone_number')
                    approver = request.data.get('approver')

                    # Validate approver email format
                    valid_approver_email = re.fullmatch(email_regex, approver)
                    if not valid_approver_email:
                        return Response({
                            'status': False,
                            'message': 'Provide a valid approver email'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Validate approver exists in staffAdmin
                    check_approver = staffAdmin.objects.filter(email=approver)
                    if not check_approver.exists():
                        return Response({
                            'status': False,
                            'message': 'Approver not found in system'
                        }, status=status.HTTP_404_NOT_FOUND)

                    # Validate ID number length
                    if len(str(id_number)) > 8:
                        return Response({
                            'status': False,
                            'message': 'ID number cannot exceed 8 characters'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Format phone number for non-tenant
                    phone_number = phone_number[:9]
                    mobile_number = f'254{phone_number}'

                    # Generate random password
                    password = random.randint(1111, 9999)
                    encrypted_password = make_password(str(password))

                    # Create User
                    user = User(
                        email=email,
                        username=email,
                        role=role,
                        mobile_number=mobile_number,
                        password=encrypted_password
                    )
                    user.save()
                    user.status = 0
                    user.save()

                    # Create role-specific profile
                    if role_name == 'landlord':
                        # Check if location and block_number are provided
                        location = request.data.get('location')
                        block_number = request.data.get('block_number')

                        # Create landlord profile
                        profile = BlockLandlord.objects.create(
                            user=user,
                            email=email,
                            phone_number=phone_number,
                            id_number=id_number,
                            approver=approver,
                            is_active=0
                        )

                        # If location and block_number are provided, create the property
                        if location and block_number:
                            # Check if block already exists
                            check_block = Property.objects.filter(block_number=block_number)
                            if check_block.exists():
                                return Response({
                                    'status': False,
                                    'message': 'Estate/Block with this name already exists'
                                }, status=status.HTTP_400_BAD_REQUEST)

                            # Create the property
                            # Generate a random business number for now
                            business_number = random.randint(100000, 999999)
                            new_property = Property.objects.create(
                                block_number=block_number,
                                location=location,
                                service_charge_business_number=business_number
                            )

                            # Link property to landlord
                            profile.property.add(new_property)
                    elif role_name == 'accounts':
                        profile = staffAccounts.objects.create(
                            user=user,
                            email=email,
                            phone_number=phone_number,
                            id_number=id_number,
                            approver=approver,
                            is_active=0
                        )
                    elif role_name == 'caretaker':
                        profile = Caretaker.objects.create(
                            user=user,
                            email=email,
                            phone_number=phone_number,
                            id_number=id_number,
                            approver=approver,
                            is_active=0
                        )

                    # Send password email to user
                    email_response = send_creation_email(email=email, password=password)

                    # Generate OTP and send to approver
                    otp = random.randint(1111, 9999)
                    OtpVerificationCode.objects.create(email=user, otp=otp, validated=False)

                    otp_email_response = approve_accounts_profile(otp=otp, email=approver, accounts_email=email)

                    if not otp_email_response:
                        return Response({
                            'status': False,
                            'message': 'Error sending approval OTP'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    return Response({
                        'status': True,
                        'message': f'Smart nyumba {role_name} created successfully. Password sent to user, OTP sent to approver.'
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
                    'expires_in': '3600',
                    'token_type': 'Bearer',
                    "role":user.role.short_name,

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
        
class AdminProfileAPIView(APIVIEW):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminProfileSerializer

    def get(self, request):
        try:
            current_user = request.user

            current_user = request.user
            allowed_roles = ['admin']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = staffAdmin.objects.filter(email=current_user)
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
        
class AllPropertiesAPIView(APIVIEW):
    authentication_classes = []
    serializer_class = AllProperiesSerializer

    def get(self, request):
        try:

            all_properties = Property.objects.all().order_by('-id')
            serializer = self.serializer_class(all_properties, many=True)

            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except IntegrityError as e:
            print("An integrity error occured")

        
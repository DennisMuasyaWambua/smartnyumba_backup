import random
import re
import calendar
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from authentication.models import OtpVerificationCode, Role, Tenant, staffAdmin
from block_landlord.api.serializers import AllTenantSerializer, ApproveBlockLandlordSerializer, BlockAdminLoginSerializer, BlockLandlordForgotPasswordSerializer, BlockLandlordLogOutSerializer, BlockLandlordNewPasswordSerializer, BlockLandlordResendOtpSerializer, BlockLandlordVerifyChangePasswordSerializer, CreateBlockLandlordSerializer, DeleteBlockLandlordSerializer, ReactivateBlockLandlordSerializer, SuspendBlockLandlordSerializer
from block_landlord.models import BlockLandlord
from email_service.email_service import approve_accounts_profile, send_creation_email, send_forgot_password_otp
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken
from rest_framework.permissions import IsAuthenticated

from staff_accounts.models import staffAccounts

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import datetime

from tenant_services.models import RentTransaction, serviceTransactions, RentPayment, services
from properties.models import PropertyBlock

User = get_user_model()

class CreateBlockLandlordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateBlockLandlordSerializer

    def post(self, request):
        try:
            data = request.data
            serializer = self.serializer_class(data=data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'errror': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')
            phone_number = request.data.get('phone_number')
            id_number = request.data.get('id_number')
            role_id = request.data.get('role')
            approver = request.data.get('approver')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, approver)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid approver email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            registered_email = User.objects.filter(email=email)

            if registered_email.exists():
                return Response({
                    'status': False,
                    'message': 'User already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            phone_number = phone_number[:9]
            mobile_number = f'254{phone_number}'

            if len(id_number) > 8:
                return Response({
                    'status': False,
                    'message': 'Max digit supposed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            role = Role.objects.filter(id=role_id)
            print("role:",role)
            if not role.exists():
                return Response({
                    'status': False,
                    'message': 'Role not found'
                }, status=status.HTTP_404_NOT_FOUND)
            role = role.first()
            password = random.randint(1111, 9999)

            encrypted_password = make_password(str(password))
            
            user = User(
                email = email,
                username = email,
                role=role,
                mobile_number = mobile_number,
                password=encrypted_password
            )
            user.save()

            print('User saved successfully!')

            approver = staffAdmin.objects.filter(email=approver).first()
            approver = approver.email
            print("approver",approver)
            
            staff_account = BlockLandlord.objects.create(
                user=user,
                email=email,
                phone_number=phone_number,
                id_number=id_number,
                approver = approver
            )
            staff_account.save()

            print('Block Landlord account created sucessfully!')

            send_creation_email(email=email, password=password)
            approver_email = approver

            otp = random.randint(1111, 9999)
            OtpVerificationCode.objects.create(email=user.email, otp=str(otp), validated=False)
            
            email_response = approve_accounts_profile(email=approver_email,otp=otp, accounts_email=email)
            
            
            if not email_response:
                return Response({
                    'status': False,
                    'message': 'error sending approval otp'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': False,
                'message': "Block Landlord profile created sucessfully"
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': "Could not create accounts profile"
            }, status=status.HTTP_400_BAD_REQUEST)


class ApproveBlockLandlordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ApproveBlockLandlordSerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.data
            serializer = self.serializer_class(data=data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'errror': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')
            otp = request.data.get('otp')

            otp = str(otp)

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=email)
            accounts_profile = BlockLandlord.objects.filter(email=email)

            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with that email does exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not accounts_profile.exists():
                return Response({
                    'status': False,
                    'message': 'Block admin account profile with that email does exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = user.first()
            accounts_profile = accounts_profile.first()

            if user.status == 1:
                return Response({
                    'status': False,
                    'message': 'Block admin account already active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if user.status == 2:
                return Response({
                    'status': False,
                    'message': 'Block admin is suspended, check with admin'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            current_logged_in_admin = User.objects.filter(email=current_user).first()
            
            if current_logged_in_admin == accounts_profile.approver:
                return Response({
                    'status': False,
                    'message': 'You cannot approve a Block Landlord you created.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            saved_otp = OtpVerificationCode.objects.filter(email=email, validated=False)
            if not saved_otp:
                return Response({
                    'status': False,
                    'message': 'Otp does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            saved_otp = saved_otp.last()
            print(type(saved_otp.otp))
            print(type(otp))

            if saved_otp.otp != otp:
                return Response({
                    'status': False,
                    'message': 'Otp does not match'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            accounts_profile.is_active = 1
            accounts_profile.save()

            user.status = 1
            user.save()

            saved_otp.validated=True
            saved_otp.save()

            print('Block landlord approved!')

            return Response({
                'status': True,
                'message': 'Block landlord approved!'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not approve Block landlord profile'
            }, status=status.HTTP_400_BAD_REQUEST)


class SuspendBlockLandlordStaffView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SuspendBlockLandlordSerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.data
            serializer = self.serializer_class(data=data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'errror': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')


            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
            

            
            user = User.objects.filter(email=email)
            accounts_profile = BlockLandlord.objects.filter(email=email)
            print(accounts_profile)

            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with that email does exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not accounts_profile.exists():
                return Response({
                    'status': False,
                    'message': 'Accounts profile with that email does exist'
                }, status=status.HTTP_404_NOT_FOUND)
        
            
            user = user.first()
            accounts_profile = accounts_profile.first()

            
            if user.status == 2:
                return Response({
                    'status': False,
                    'message': 'Account is already suspended, check with admin'
                }, status=status.HTTP_400_BAD_REQUEST)
            current_user = current_user['email']
            current_logged_in_admin = User.objects.filter(email=current_user)

            if not current_logged_in_admin.exists():
                return Response({
                    'status': False,
                    'message': 'Admin profile with that email does exist'
                }, status=status.HTTP_404_NOT_FOUND)
            

            
            accounts_profile.is_active = 2
            accounts_profile.save()

            user.status = 2
            user.save()

            print('Block Landlord account profile suspended!')

            return Response({
                'status': True,
                'message': 'Block Landlord profile suspended!!'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not suspended Block Admin profile !!'
            }, status=status.HTTP_400_BAD_REQUEST)


class ReactivateBlockLandlordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReactivateBlockLandlordSerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.user
            serializer = self.serializer_class(data=data)

            if not serializer.is_valid():
                return Response({
                'status': False,
                'message': 'Invalid data provided',
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

            email = request.data.get('email')


            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
            

            
            user = User.objects.filter(email=email)
            block_admin_profile = BlockLandlord.objects.filter(email=email)
            print(block_admin_profile)

            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with that email does exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not block_admin_profile.exists():
                return Response({
                    'status': False,
                    'message': 'Block landlord profile with that email does exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            user = user.first()
            block_admin_profile = block_admin_profile.first()

            
            if user.status == 1:
                return Response({
                    'status': False,
                    'message': 'Account is already active'
                }, status=status.HTTP_400_BAD_REQUEST)
            current_user = current_user
            print(current_user)
            current_logged_in_admin = User.objects.filter(email=current_user)

            if not current_logged_in_admin.exists():
                return Response({
                    'status': False,
                    'message': 'Admin profile with that email does exist'
                }, status=status.HTTP_404_NOT_FOUND)
            

            
            block_admin_profile.is_active = 1
            block_admin_profile.save()

            user.status = 1
            user.save() 


            print('Block Landlord account profile re-activated!')

            return Response({
                'status': True,
                'message': 'Block Landlord profile re-activated!!'
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not reactivate block landlord profile'
            }, status=status.HTTP_400_BAD_REQUEST)

class DeleteBlockLandlordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteBlockLandlordSerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.user
            serializer = self.serializer_class(data=data)

            if not serializer.is_valid():
                return Response({
                'status': False,
                'message': 'Invalid data provided',
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

            email = request.data.get('email')


            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to login'
                }, status=status.HTTP_400_BAD_REQUEST)
            

            
            user = User.objects.filter(email=email)
            block_admin_profile = BlockLandlord.objects.filter(email=email)
            print(block_admin_profile)

            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with that email does exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not block_admin_profile.exists():
                return Response({
                    'status': False,
                    'message': 'Block landlord profile with that email does exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            user = user.first()
            block_admin_profile = block_admin_profile.first()

            current_logged_in_admin = User.objects.filter(email=current_user)

            if not current_logged_in_admin.exists():
                return Response({
                    'status': False,
                    'message': 'Admin profile with that email does exist'
                }, status=status.HTTP_404_NOT_FOUND)
            

            
            block_admin_profile.delete()

            user.delete() 


            print('Block Landlord account profile deleted!')

            return Response({
                'status': True,
                'message': 'Block Landlord profile delete!!'
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not reactivate block landlord profile'
            }, status=status.HTTP_400_BAD_REQUEST)



#----------------AUTH VIEWS FOR ACCOUNTS PROFILE--------

class LoginBlockLandlordAPIView(APIView):
    serializer_class = BlockAdminLoginSerializer

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

            
            blockadmin = BlockLandlord.objects.filter(email=email)
            
            if not blockadmin.exists():
                return Response({
                    'status': False,
                    'message': 'admin with this email does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            allowed_roles = ['accounts', 'admin', 'landlord']
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
                    'expires_in': '3600',
                    'token_type': 'Bearer'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Cannot log you in'
            }, status=status.HTTP_403_FORBIDDEN)
        
class LogoutBlockLandlordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlockLandlordLogOutSerializer
    
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
                    allowed_roles = ['accounts', 'admin', 'landlord']
                    user = user.first()
                    if not user.role.short_name in allowed_roles:
                        return Response({
                            'status': False,
                            'message': f"You cannot access this portal with user role!. Please contact customer care"
                        })
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

class ForgotPasswordBlockLandlordAPIView(APIView):
    authentication_classes=[]
    serializer_class = BlockLandlordForgotPasswordSerializer
    
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
            OtpVerificationCode.objects.create(email=user.email, otp=str(otp), validated=False)
            email_response = send_forgot_password_otp(email=user.email, otp=otp)
            
            
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
        

class VerifyChangePasswordBlockLandlordAPIView(APIView):
    authentication_classes = []
    serializer_class = BlockLandlordVerifyChangePasswordSerializer
    
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
                
            allowed_roles = ['landlord']
            user = user.first()
            if not user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': f"You cannot access this portal with user role!. Please contact customer care"
                })
            
            verify_otp = OtpVerificationCode.objects.filter(
                    email=user.email, validated=False)
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


class ResendOtpPasswordBlockLandlordAPIView(APIView):
    authentication_classes = []
    serializer_class = BlockLandlordResendOtpSerializer
    
    def post(self, request):
        # try:
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
        print(user)
        if not user.exists():
            return Response({
                'status': False,
                'message': 'User with this email does not exist.'
            }, status=status.HTTP_400_BAD_REQUEST)
        user = user.first()

        verify_otp = OtpVerificationCode.objects.filter(email=user.email, validated=False)
        if not verify_otp.exists():
            return Response({
                'status': False,
                'message': 'OTP does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)

        verify_otp = verify_otp.last()
        print(verify_otp)
        verify_otp.delete()

        otp = random.randint(1111, 9999)
        OtpVerificationCode.objects.create(email=user.email, otp=str(otp), validated=False)
        email_response = send_forgot_password_otp(email=user.email, otp=otp)
        
        
        if not email_response:
            return Response({
                'status': False,
                'message': 'error sending otp'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
                'status': True,
                'message': 'otp resent'
            }, status=status.HTTP_200_OK)
            
        # except Exception as error:
        #     print(str(error))
            
        #     return Response({
        #         'status': False,
        #         'message': 'We could not send otp'
        #     }, status=status.HTTP_403_FORBIDDEN)

class NewPasswordPasswordBlockLandlordAPIView(APIView):
    authentication_classes = []
    serializer_class = BlockLandlordNewPasswordSerializer

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
                allowed_roles = ['landlord']
                user = user.first()
                if not user.role.short_name in allowed_roles:
                    return Response({
                        'status': False,
                        'message': f"You cannot access this portal with user role!. Please contact customer care"
                    })
                
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
        

class AllTenantsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AllTenantSerializer

    def get(self, request):
        try:
            user = request.user
            allowed_roles = ['admin', 'landlord']

            if not user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access the resource.'
                }, status=status.HTTP_403_FORBIDDEN)

            # If landlord, only show their tenants
            if user.role.short_name == 'landlord':
                # Get landlord's properties
                landlord_profile = BlockLandlord.objects.filter(user=user).first()
                if not landlord_profile:
                    return Response({
                        'status': False,
                        'message': 'Landlord profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)

                # Get properties associated with this landlord
                properties = landlord_profile.property.all()

                # Get tenants in these properties
                tenant = Tenant.objects.filter(PropertyBlock__block__in=properties).order_by('-id')
            else:
                # Admin sees all tenants
                tenant = Tenant.objects.all().order_by('-id')

            serializer = self.serializer_class(tenant, many=True)

            return Response({
                'status': True,
                'tenant': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not view the tenant list'
            }, status=status.HTTP_400_BAD_REQUEST)


class LandlordTenantManagementAPIView(APIView):
    """
    Tenant Management API for landlords
    Returns list of all tenants with payment status and property information
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Verify user is a landlord
            if user.role.short_name != 'landlord':
                return Response({
                    'status': False,
                    'message': 'Only landlords can access tenant data'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get landlord profile
            landlord = BlockLandlord.objects.filter(user=user).first()
            if not landlord:
                return Response({
                    'status': False,
                    'message': 'Landlord profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get all landlord's properties
            landlord_properties = landlord.property.all()
            property_ids = [prop.id for prop in landlord_properties]

            # Get all property blocks for these properties
            property_blocks = PropertyBlock.objects.filter(block_id__in=property_ids)
            block_ids = [block.id for block in property_blocks]

            # Get filters from query params
            property_filter = request.GET.get('property_id')
            payment_status = request.GET.get('payment_status')  # 'paid', 'pending'

            # Build filter for tenants
            tenant_filter = Q(PropertyBlock_id__in=block_ids)
            if property_filter:
                blocks_for_property = PropertyBlock.objects.filter(block_id=property_filter)
                tenant_filter = Q(PropertyBlock_id__in=[b.id for b in blocks_for_property])

            # Get all tenants
            from tenant_services.models import RentPayment
            tenants = Tenant.objects.filter(tenant_filter).select_related('user', 'PropertyBlock')

            tenant_list = []
            current_month = datetime.now().month
            current_year = datetime.now().year

            for tenant in tenants:
                # Get latest rent payment status
                latest_payment = RentPayment.objects.filter(
                    user=tenant.user,
                    month=current_month,
                    year=current_year
                ).first()

                has_paid = latest_payment is not None

                # Apply payment status filter
                if payment_status == 'paid' and not has_paid:
                    continue
                if payment_status == 'pending' and has_paid:
                    continue

                # Get property block info
                property_block = tenant.PropertyBlock
                property_info = property_block.block if property_block else None

                tenant_data = {
                    'id': tenant.id,
                    'email': tenant.user.email if tenant.user else 'N/A',
                    'first_name': tenant.user.firstName if tenant.user else '',
                    'last_name': tenant.user.lastName if tenant.user else '',
                    'mobile_number': tenant.user.mobile_number if tenant.user else '',
                    'house_number': property_block.house_number if property_block else 'N/A',
                    'block_number': property_info.block_number if property_info else 'N/A',
                    'location': property_info.location if property_info else 'N/A',
                    'rent_amount': float(property_block.rent_charged) if property_block and property_block.rent_charged else 0.0,
                    'service_charge': float(property_block.service_charge) if property_block and property_block.service_charge else 0.0,
                    'payment_status': 'paid' if has_paid else 'pending',
                    'last_payment_date': latest_payment.rent_transaction.last().date_paid.strftime('%Y-%m-%d') if has_paid and latest_payment.rent_transaction.exists() else None,
                }
                tenant_list.append(tenant_data)

            # Statistics
            total_tenants = len(tenant_list)
            paid_count = sum(1 for t in tenant_list if t['payment_status'] == 'paid')
            pending_count = total_tenants - paid_count

            response_data = {
                'status': True,
                'data': {
                    'tenants': tenant_list,
                    'statistics': {
                        'total_tenants': total_tenants,
                        'paid_count': paid_count,
                        'pending_count': pending_count,
                    },
                    'properties': [
                        {
                            'id': prop.id,
                            'block_number': prop.block_number,
                            'location': prop.location,
                        }
                        for prop in landlord_properties
                    ]
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'status': False,
                'message': f'Error fetching tenant data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LandlordTransactionReportsAPIView(APIView):
    """
    Transaction Reports API for landlords
    Returns filterable transaction history
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Verify user is a landlord
            if user.role.short_name != 'landlord':
                return Response({
                    'status': False,
                    'message': 'Only landlords can access transaction reports'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get landlord profile
            landlord = BlockLandlord.objects.filter(user=user).first()
            if not landlord:
                return Response({
                    'status': False,
                    'message': 'Landlord profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get all landlord's properties
            landlord_properties = landlord.property.all()
            property_ids = [prop.id for prop in landlord_properties]

            # Get all property blocks
            property_blocks = PropertyBlock.objects.filter(block_id__in=property_ids)
            block_ids = [block.id for block in property_blocks]

            # Get filters from query params
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            property_filter = request.GET.get('property_id')
            transaction_type = request.GET.get('type')  # 'rent', 'service', 'all'

            # Build filters
            rent_filter = Q(rent_payment__property_block_id__in=block_ids, status=1)
            service_filter = Q(service_instance__block_id__in=property_ids, status=1)

            if start_date and end_date:
                rent_filter &= Q(date_paid__range=[start_date, end_date])
                service_filter &= Q(date_paid__range=[start_date, end_date])

            if property_filter:
                blocks_for_property = PropertyBlock.objects.filter(block_id=property_filter)
                property_block_ids = [b.id for b in blocks_for_property]
                rent_filter = Q(rent_payment__property_block_id__in=property_block_ids, status=1)
                service_filter = Q(service_instance__block_id=property_filter, status=1)

            # Get transactions
            transactions = []

            if transaction_type in ['rent', 'all', None]:
                rent_transactions = RentTransaction.objects.filter(rent_filter).select_related(
                    'rent_payment', 'rent_payment__user', 'rent_payment__property_block'
                ).order_by('-date_paid')

                for trans in rent_transactions:
                    transactions.append({
                        'id': trans.id,
                        'type': 'rent',
                        'amount': float(trans.rent_payment.rent_amount),
                        'commission': float(trans.commission_amount),
                        'payout': float(trans.landlord_payout_amount),
                        'tenant_email': trans.rent_payment.user.email if trans.rent_payment.user else 'N/A',
                        'payment_method': trans.payment_method or 'mpesa',
                        'date': trans.date_paid.strftime('%Y-%m-%d %H:%M:%S'),
                        'month': trans.rent_payment.month,
                        'year': trans.rent_payment.year,
                        'house_number': trans.rent_payment.property_block.house_number if trans.rent_payment.property_block else 'N/A',
                        'confirmation_code': trans.confirmation_code or 'N/A',
                    })

            if transaction_type in ['service', 'all', None]:
                service_transactions = serviceTransactions.objects.filter(service_filter).select_related(
                    'service_instance', 'service_instance__user', 'service_instance__block'
                ).order_by('-date_paid')

                for trans in service_transactions:
                    transactions.append({
                        'id': trans.id,
                        'type': 'service',
                        'amount': float(trans.service_instance.amount),
                        'commission': float(trans.commission_amount),
                        'payout': float(trans.landlord_payout_amount),
                        'tenant_email': trans.service_instance.user.email if trans.service_instance.user else 'N/A',
                        'payment_method': trans.payment_method or 'mpesa',
                        'date': trans.date_paid.strftime('%Y-%m-%d %H:%M:%S'),
                        'service_name': trans.service_instance.service_name,
                        'confirmation_code': trans.confirmation_code or 'N/A',
                    })

            # Sort by date
            transactions.sort(key=lambda x: x['date'], reverse=True)

            # Calculate totals
            total_amount = sum(t['amount'] for t in transactions)
            total_commission = sum(t['commission'] for t in transactions)
            total_payout = sum(t['payout'] for t in transactions)

            response_data = {
                'status': True,
                'data': {
                    'transactions': transactions,
                    'summary': {
                        'total_transactions': len(transactions),
                        'total_amount': float(total_amount),
                        'total_commission': float(total_commission),
                        'total_payout': float(total_payout),
                    }
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'status': False,
                'message': f'Error fetching transaction reports: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LandlordPropertyDetailsAPIView(APIView):
    """
    Property Details API for landlords
    Returns detailed metrics for a specific property
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, property_id):
        try:
            user = request.user

            # Verify user is a landlord
            if user.role.short_name != 'landlord':
                return Response({
                    'status': False,
                    'message': 'Only landlords can access property details'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get landlord profile
            landlord = BlockLandlord.objects.filter(user=user).first()
            if not landlord:
                return Response({
                    'status': False,
                    'message': 'Landlord profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Verify property belongs to landlord
            from properties.models import Property
            property_obj = Property.objects.filter(id=property_id).first()
            if not property_obj or property_obj not in landlord.property.all():
                return Response({
                    'status': False,
                    'message': 'Property not found or does not belong to you'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get property blocks
            property_blocks = PropertyBlock.objects.filter(block=property_obj)
            block_ids = [block.id for block in property_blocks]

            # Get tenants
            tenants = Tenant.objects.filter(PropertyBlock_id__in=block_ids)
            total_units = property_blocks.count()
            occupied_units = tenants.count()
            vacancy_rate = ((total_units - occupied_units) / total_units * 100) if total_units > 0 else 0

            # Get revenue data
            rent_revenue = RentTransaction.objects.filter(
                rent_payment__property_block_id__in=block_ids,
                status=1
            ).aggregate(total=Sum('rent_payment__rent_amount'))['total'] or Decimal('0')

            service_revenue = serviceTransactions.objects.filter(
                service_instance__block=property_obj,
                status=1
            ).aggregate(total=Sum('service_instance__amount'))['total'] or Decimal('0')

            # Get tenant list with payment status
            current_month = datetime.now().month
            current_year = datetime.now().year
            tenant_list = []

            for tenant in tenants:
                latest_payment = RentPayment.objects.filter(
                    user=tenant.user,
                    month=current_month,
                    year=current_year
                ).first()

                property_block = tenant.PropertyBlock
                tenant_list.append({
                    'id': tenant.id,
                    'email': tenant.user.email if tenant.user else 'N/A',
                    'first_name': tenant.user.firstName if tenant.user else '',
                    'last_name': tenant.user.lastName if tenant.user else '',
                    'house_number': property_block.house_number if property_block else 'N/A',
                    'rent_amount': float(property_block.rent_charged) if property_block and property_block.rent_charged else 0.0,
                    'payment_status': 'paid' if latest_payment else 'pending',
                })

            response_data = {
                'status': True,
                'data': {
                    'property': {
                        'id': property_obj.id,
                        'block_number': property_obj.block_number,
                        'location': property_obj.location,
                        'total_units': total_units,
                        'occupied_units': occupied_units,
                        'vacant_units': total_units - occupied_units,
                        'occupancy_rate': round(100 - vacancy_rate, 2),
                    },
                    'revenue': {
                        'total_revenue': float(rent_revenue + service_revenue),
                        'rent_revenue': float(rent_revenue),
                        'service_revenue': float(service_revenue),
                    },
                    'tenants': tenant_list,
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'status': False,
                'message': f'Error fetching property details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LandlordFinancialSummaryAPIView(APIView):
    """
    Financial Dashboard API for landlords
    Returns comprehensive financial metrics including revenue, commissions, and trends
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Verify user is a landlord
            if user.role.short_name != 'landlord':
                return Response({
                    'status': False,
                    'message': 'Only landlords can access financial data'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get landlord profile
            landlord = BlockLandlord.objects.filter(user=user).first()
            if not landlord:
                return Response({
                    'status': False,
                    'message': 'Landlord profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get all landlord's properties
            landlord_properties = landlord.property.all()
            property_ids = [prop.id for prop in landlord_properties]

            # Get all property blocks for these properties
            property_blocks = PropertyBlock.objects.filter(block_id__in=property_ids)
            block_ids = [block.id for block in property_blocks]

            # Get time filters from query params
            period = request.GET.get('period', 'all')  # all, month, year
            year = request.GET.get('year', datetime.now().year)
            month = request.GET.get('month', datetime.now().month)

            # Build filter for transactions
            rent_filter = Q(rent_payment__property_block_id__in=block_ids, status=1)
            service_filter = Q(service_instance__block_id__in=property_ids, status=1)

            if period == 'month':
                rent_filter &= Q(rent_payment__month=month, rent_payment__year=year)
                service_filter &= Q(date_paid__month=month, date_paid__year=year)
            elif period == 'year':
                rent_filter &= Q(rent_payment__year=year)
                service_filter &= Q(date_paid__year=year)

            # RENT REVENUE
            rent_data = RentTransaction.objects.filter(rent_filter).aggregate(
                total_rent=Sum('rent_payment__rent_amount'),
                total_rent_commission=Sum('commission_amount'),
                total_rent_payout=Sum('landlord_payout_amount'),
                rent_count=Count('id')
            )

            # SERVICE CHARGE REVENUE
            service_data = serviceTransactions.objects.filter(service_filter).aggregate(
                total_service=Sum('service_instance__amount'),
                total_service_commission=Sum('commission_amount'),
                total_service_payout=Sum('landlord_payout_amount'),
                service_count=Count('id')
            )

            # Calculate totals
            total_revenue = (rent_data['total_rent'] or Decimal('0')) + (service_data['total_service'] or Decimal('0'))
            total_commission = (rent_data['total_rent_commission'] or Decimal('0')) + (service_data['total_service_commission'] or Decimal('0'))
            total_landlord_payout = (rent_data['total_rent_payout'] or Decimal('0')) + (service_data['total_service_payout'] or Decimal('0'))

            # Get monthly trends for the current year
            monthly_trends = []
            current_year = int(year)
            for m in range(1, 13):
                month_rent = RentTransaction.objects.filter(
                    rent_payment__property_block_id__in=block_ids,
                    rent_payment__month=m,
                    rent_payment__year=current_year,
                    status=1
                ).aggregate(total=Sum('rent_payment__rent_amount'))['total'] or Decimal('0')

                month_service = serviceTransactions.objects.filter(
                    service_instance__block_id__in=property_ids,
                    date_paid__month=m,
                    date_paid__year=current_year,
                    status=1
                ).aggregate(total=Sum('service_instance__amount'))['total'] or Decimal('0')

                monthly_trends.append({
                    'month': m,
                    'month_name': calendar.month_abbr[m],
                    'rent': float(month_rent),
                    'service': float(month_service),
                    'total': float(month_rent + month_service)
                })

            # Get recent transactions (last 10)
            recent_rent_transactions = RentTransaction.objects.filter(
                rent_payment__property_block_id__in=block_ids,
                status=1
            ).select_related('rent_payment', 'rent_payment__user').order_by('-date_paid')[:10]

            recent_service_transactions = serviceTransactions.objects.filter(
                service_instance__block_id__in=property_ids,
                status=1
            ).select_related('service_instance', 'service_instance__user').order_by('-date_paid')[:10]

            # Format recent transactions
            recent_transactions = []

            for trans in recent_rent_transactions:
                recent_transactions.append({
                    'id': trans.id,
                    'type': 'rent',
                    'amount': float(trans.rent_payment.rent_amount),
                    'commission': float(trans.commission_amount),
                    'payout': float(trans.landlord_payout_amount),
                    'tenant_email': trans.rent_payment.user.email if trans.rent_payment.user else 'N/A',
                    'payment_method': trans.payment_method or 'mpesa',
                    'date': trans.date_paid.strftime('%Y-%m-%d'),
                    'month': trans.rent_payment.month,
                    'year': trans.rent_payment.year
                })

            for trans in recent_service_transactions:
                recent_transactions.append({
                    'id': trans.id,
                    'type': 'service',
                    'amount': float(trans.service_instance.amount),
                    'commission': float(trans.commission_amount),
                    'payout': float(trans.landlord_payout_amount),
                    'tenant_email': trans.service_instance.user.email if trans.service_instance.user else 'N/A',
                    'payment_method': trans.payment_method or 'mpesa',
                    'date': trans.date_paid.strftime('%Y-%m-%d'),
                    'service_name': trans.service_instance.service_name
                })

            # Sort by date
            recent_transactions.sort(key=lambda x: x['date'], reverse=True)
            recent_transactions = recent_transactions[:10]

            # Get property summary
            property_summary = []
            for prop in landlord_properties:
                blocks = PropertyBlock.objects.filter(block=prop)
                block_ids_for_prop = [b.id for b in blocks]

                prop_rent = RentTransaction.objects.filter(
                    rent_payment__property_block_id__in=block_ids_for_prop,
                    status=1
                ).aggregate(total=Sum('rent_payment__rent_amount'))['total'] or Decimal('0')

                prop_service = serviceTransactions.objects.filter(
                    service_instance__block=prop,
                    status=1
                ).aggregate(total=Sum('service_instance__amount'))['total'] or Decimal('0')

                # Count tenants
                tenant_count = Tenant.objects.filter(PropertyBlock_id__in=block_ids_for_prop).count()

                property_summary.append({
                    'property_id': prop.id,
                    'block_number': prop.block_number,
                    'location': prop.location,
                    'total_revenue': float(prop_rent + prop_service),
                    'rent_revenue': float(prop_rent),
                    'service_revenue': float(prop_service),
                    'tenant_count': tenant_count
                })

            # Response data
            response_data = {
                'status': True,
                'data': {
                    'summary': {
                        'total_revenue': float(total_revenue),
                        'total_commission': float(total_commission),
                        'total_landlord_payout': float(total_landlord_payout),
                        'commission_rate': 0.05,  # 5%
                        'total_rent_revenue': float(rent_data['total_rent'] or 0),
                        'total_service_revenue': float(service_data['total_service'] or 0),
                        'rent_transaction_count': rent_data['rent_count'],
                        'service_transaction_count': service_data['service_count']
                    },
                    'monthly_trends': monthly_trends,
                    'recent_transactions': recent_transactions,
                    'property_summary': property_summary,
                    'period': period,
                    'year': int(year),
                    'month': int(month) if period == 'month' else None
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'status': False,
                'message': f'Error fetching financial data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BlockLandlordProfileAPIView(APIView):
    """
    Get landlord profile with their properties
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user

            # Verify user is a landlord
            if current_user.role.short_name != 'landlord':
                return Response({
                    'status': False,
                    'message': 'Only landlords can access this endpoint'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get landlord profile
            landlord = BlockLandlord.objects.filter(user=current_user).first()
            if not landlord:
                return Response({
                    'status': False,
                    'message': 'Landlord profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get landlord's properties
            properties = landlord.property.all()
            properties_data = []
            for prop in properties:
                # Count total houses for this property
                total_houses = PropertyBlock.objects.filter(block=prop).count()
                
                properties_data.append({
                    'id': prop.id,
                    'block_number': prop.block_number,
                    'location': prop.location,
                    'total_houses': total_houses,
                    'registration_date': prop.registration_date.isoformat() if prop.registration_date else None
                })

            return Response({
                'status': True,
                'message': 'Profile retrieved successfully',
                'profile': {
                    'user': {
                        'first_name': current_user.first_name,
                        'last_name': current_user.last_name,
                        'email': current_user.email,
                        'mobile_number': current_user.mobile_number
                    },
                    'landlord': {
                        'email': landlord.email,
                        'phone_number': landlord.phone_number,
                        'id_number': landlord.id_number,
                        'is_active': landlord.is_active
                    },
                    'properties': properties_data
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'status': False,
                'message': f'Error fetching profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LandlordTransactionsAPIView(APIView):
    """
    Get all transactions (rent and service charges) for landlord's properties.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user

            # Only landlords can access this
            if current_user.role.short_name != 'landlord':
                return Response({
                    'status': False,
                    'message': 'Only landlords can access this resource'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get landlord profile
            block_landlord = BlockLandlord.objects.filter(user=current_user).first()
            if not block_landlord:
                return Response({
                    'status': False,
                    'message': 'Landlord profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get all properties owned by this landlord
            properties = block_landlord.property.all()

            # Import transaction models
            from tenant_services.models import ServiceChargePayment, RentPayment
            from authentication.models import Tenant

            # Get all houses in landlord's properties
            from properties.models import PropertyBlock
            all_houses = PropertyBlock.objects.filter(block__in=properties)

            # Get all tenants in these houses
            tenants = Tenant.objects.filter(PropertyBlock__in=all_houses)

            # Get rent payments
            rent_transactions = []
            rent_payments = RentPayment.objects.filter(tenant__in=tenants).order_by('-date_paid')

            for payment in rent_payments:
                rent_transactions.append({
                    'id': payment.id,
                    'amount': str(payment.amount),
                    'date_paid': payment.date_paid.isoformat() if payment.date_paid else None,
                    'payment_method': payment.payment_method,
                    'tenant_email': payment.tenant.email if payment.tenant else None,
                    'house_number': payment.tenant.PropertyBlock.house_number if payment.tenant and payment.tenant.PropertyBlock else None,
                    'block_number': payment.tenant.PropertyBlock.block.block_number if payment.tenant and payment.tenant.PropertyBlock and payment.tenant.PropertyBlock.block else None,
                    'transaction_reference': payment.transaction_reference if hasattr(payment, 'transaction_reference') else None,
                })

            # Get service charge payments
            service_transactions = []
            service_payments = ServiceChargePayment.objects.filter(tenant__in=tenants).order_by('-date')

            for payment in service_payments:
                service_transactions.append({
                    'id': payment.id,
                    'amount': str(payment.amount),
                    'date': payment.date.isoformat() if payment.date else None,
                    'payment_method': payment.payment_method,
                    'tenant_email': payment.tenant.email if payment.tenant else None,
                    'house_number': payment.tenant.PropertyBlock.house_number if payment.tenant and payment.tenant.PropertyBlock else None,
                    'block_number': payment.tenant.PropertyBlock.block.block_number if payment.tenant and payment.tenant.PropertyBlock and payment.tenant.PropertyBlock.block else None,
                    'transaction_reference': payment.transaction_reference if hasattr(payment, 'transaction_reference') else None,
                })

            return Response({
                'status': True,
                'rent_transactions': rent_transactions,
                'service_transactions': service_transactions,
                'total_rent_transactions': len(rent_transactions),
                'total_service_transactions': len(service_transactions),
                'total_properties': properties.count(),
                'total_houses': all_houses.count(),
                'total_tenants': tenants.count()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not retrieve transactions',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

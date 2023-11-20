import random
import re
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from authentication.models import OtpVerificationCode, Role, staffAdmin
from caretaker.api.serializers import ApproveCaretakerSerializer, CreateCaretakerSerializer, DeleteCaretakerSerializer, ForgotPasswordCaretakerSerializer, LoginCaretakerSerializer, LogoutCaretakerSerializer, NewPasswordPasswordCaretakerSerializer, ReactivateCaretakerSerializer, ResendOtpPasswordCaretakerSerializer, SuspendCaretakerSerializer, VerifyChangePasswordCaretakerSerializer
from caretaker.models import Caretaker
from email_service.email_service import approve_accounts_profile, send_creation_email, send_forgot_password_otp
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken
from rest_framework.permissions import IsAuthenticated

from staff_accounts.models import staffAccounts

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password

User = get_user_model()

class CreateCaretakerAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateCaretakerSerializer

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
            
            staff_account = Caretaker.objects.create(
                user=user,
                email=email,
                phone_number=phone_number,
                id_number=id_number,
                approver = approver
            )
            staff_account.save()

            print('Caretaker account created sucessfully!')

            send_creation_email(email=email, password=password)
            approver_email = approver
            
            otp = random.randint(1111, 9999)
            OtpVerificationCode.objects.create(email=user, otp=otp, validated=False)
            
            email_response = approve_accounts_profile(email=approver_email,otp=otp, accounts_email=email)
            
            
            if not email_response:
                return Response({
                    'status': False,
                    'message': 'error sending approval otp'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': False,
                'message': "Caretaker profile created sucessfully"
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': "Could not create accounts profile"
            }, status=status.HTTP_400_BAD_REQUEST)


class ApproveCaretakerAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ApproveCaretakerSerializer

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
            accounts_profile = Caretaker.objects.filter(email=email)

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
                    'message': 'You cannot approve a Caretaker you created.'
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

            print('Caretaker approved!')

            return Response({
                'status': True,
                'message': 'Caretaker approved!'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not approve Caretaker profile'
            }, status=status.HTTP_400_BAD_REQUEST)


class SuspendCaretakerView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SuspendCaretakerSerializer

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
            accounts_profile = Caretaker.objects.filter(email=email)
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

            print('Caretaker account profile suspended!')

            return Response({
                'status': True,
                'message': 'Caretaker profile suspended!!'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not suspended Caretaker profile !!'
            }, status=status.HTTP_400_BAD_REQUEST)


class ReactivateCaretakerAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReactivateCaretakerSerializer

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
            block_admin_profile = Caretaker.objects.filter(email=email)
            print(block_admin_profile)

            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with that email does exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not block_admin_profile.exists():
                return Response({
                    'status': False,
                    'message': 'Caretaker profile with that email does exist'
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


            print('Caretaker account profile re-activated!')

            return Response({
                'status': True,
                'message': 'Caretaker profile re-activated!!'
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not reactivate caretaker profile'
            }, status=status.HTTP_400_BAD_REQUEST)

class DeleteCaretakerAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteCaretakerSerializer

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
            block_admin_profile = Caretaker.objects.filter(email=email)
            print(block_admin_profile)

            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'User with that email does exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not block_admin_profile.exists():
                return Response({
                    'status': False,
                    'message': 'Caretaker profile with that email does exist'
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


            print('Caretaker account profile deleted!')

            return Response({
                'status': True,
                'message': 'Caretaker profile deleted!!'
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not reactivate Caretaker profile'
            }, status=status.HTTP_400_BAD_REQUEST)



#----------------AUTH VIEWS FOR ACCOUNTS PROFILE--------

class LoginCaretakerAPIView(APIView):
    serializer_class = LoginCaretakerSerializer

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

            
            staffAccount = staffAccounts.objects.filter(email=email)
            
            if not staffAccount.exists():
                return Response({
                    'status': False,
                    'message': 'admin with this email does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            allowed_roles = ['accounts', 'admin', 'landlord', 'caretaker']
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
        
class LogoutCaretakerAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutCaretakerSerializer
    
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
                    allowed_roles = ['accounts', 'admin', 'landlord', 'caretaker']
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

class ForgotPasswordCaretakerAPIView(APIView):
    authentication_classes=[]
    serializer_class = ForgotPasswordCaretakerSerializer
    
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
        

class VerifyChangePasswordCaretakerAPIView(APIView):
    authentication_classes = []
    serializer_class = VerifyChangePasswordCaretakerSerializer
    
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
                
            allowed_roles = ['accounts', 'admin']
            user = user.first()
            if not user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': f"You cannot access this portal with user role!. Please contact customer care"
                })
            
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


class ResendOtpPasswordCaretakerAPIView(APIView):
    authentication_classes = []
    serializer_class = ResendOtpPasswordCaretakerSerializer
    
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
        
        verify_otp = OtpVerificationCode.objects.filter(email=user, validated=False)
        if not verify_otp.exists():
            return Response({
                'status': False,
                'message': 'OTP does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        verify_otp = verify_otp.last()
        print(verify_otp)
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
            
        # except Exception as error:
        #     print(str(error))
            
        #     return Response({
        #         'status': False,
        #         'message': 'We could not send otp'
        #     }, status=status.HTTP_403_FORBIDDEN)

class NewPasswordPasswordCaretakerAPIView(APIView):
    authentication_classes = []
    serializer_class = NewPasswordPasswordCaretakerSerializer

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
                allowed_roles = ['accounts', 'admin']
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
import random
import re
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from tenant_services.models import services
from tenant_services.serializers import AllTRansactionsSerializer
# from django.contrib.auth.hashers import make_password
# from admin_api.models import Admin
# from admin_api.serializers import ApproveAdminSerializer, CreateAdminSerializer, DeleteAdminSerializer, ReactivateAdminSerializer, SuspendAdminSerializer

# from authentication.models import OtpVerificationCode, Role
# from email_service.email_service import approve_accounts_profile, send_admin_creation_email


from django.contrib.auth import get_user_model

User = get_user_model()

# class CreateAdminAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = CreateAdminSerializer

#     def post(self, request):
#         try:
#             data = request.data
#             serializer = self.serializer_class(data=data)
#             if not serializer.is_valid():
#                 return Response({
#                     'status': False,
#                     'message': 'Invalid data provided',
#                     'errror': serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             email = request.data.get('email')
#             phone_number = request.data.get('phone_number')
#             id_number = request.data.get('id_number')
#             role_id = request.data.get('role')
#             approver = request.data.get('approver')

#             email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#             valid_email = re.fullmatch(email_regex, email)
#             if not valid_email:
#                 return Response({
#                     'status': False,
#                     'message': 'Provide a valid email to login'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#             valid_email = re.fullmatch(email_regex, approver)
#             if not valid_email:
#                 return Response({
#                     'status': False,
#                     'message': 'Provide a valid approver email to login'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             registered_email = User.objects.filter(email=email)

#             if registered_email.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'User already exists'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             phone_number = phone_number[:9]
#             mobile_number = f'254{phone_number}'

#             if len(id_number) > 8:
#                 return Response({
#                     'status': False,
#                     'message': 'Max digit supposed'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             role = Role.objects.filter(id=role_id)
#             print("role:",role)
#             if not role.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Role not found'
#                 }, status=status.HTTP_404_NOT_FOUND)
#             role = role.first()
#             password = random.randint(1111, 9999)

#             encrypted_password = make_password(str(password))
            
#             user = User(
#                 email = email,
#                 username = email,
#                 role=role,
#                 mobile_number = mobile_number,
#                 password=encrypted_password
#             )
#             user.save()

#             print('User saved successfully!')

#             approver = Admin.objects.filter(email=approver).first()
#             approver = approver.email
#             print("approver",approver)
            
#             staff_account = Admin.objects.create(
#                 user=user,
#                 email=email,
#                 phone_number=phone_number,
#                 id_number=id_number,
#                 approver = approver
#             )
#             staff_account.save()

#             print('Block Landlord account created sucessfully!')

#             send_admin_creation_email(email=email, password=password)
#             approver_email = approver
            
#             otp = random.randint(1111, 9999)
#             OtpVerificationCode.objects.create(email=user, otp=otp, validated=False)
            
#             email_response = approve_accounts_profile(email=approver_email,otp=otp, accounts_email=email)
            
            
#             if not email_response:
#                 return Response({
#                     'status': False,
#                     'message': 'error sending approval otp'
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             return Response({
#                 'status': False,
#                 'message': "Block Landlord profile created sucessfully"
#             }, status=status.HTTP_200_OK)


#         except Exception as e:
#             print(str(e))
#             return Response({
#                 'status': False,
#                 'message': "Could not create accounts profile"
#             }, status=status.HTTP_400_BAD_REQUEST)

# class ApproveAdminAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = ApproveAdminSerializer

#     def post(self, request):
#         try:
#             data = request.data
#             current_user = request.data
#             serializer = self.serializer_class(data=data)
#             if not serializer.is_valid():
#                 return Response({
#                     'status': False,
#                     'message': 'Invalid data provided',
#                     'errror': serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             email = request.data.get('email')
#             otp = request.data.get('otp')

#             otp = str(otp)

#             email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#             valid_email = re.fullmatch(email_regex, email)
#             if not valid_email:
#                 return Response({
#                     'status': False,
#                     'message': 'Provide a valid email to login'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             user = User.objects.filter(email=email)
#             accounts_profile = Admin.objects.filter(email=email)

#             if not user.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'User with that email does exist'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if not accounts_profile.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Block admin account profile with that email does exist'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             user = user.first()
#             accounts_profile = accounts_profile.first()

#             if user.status == 1:
#                 return Response({
#                     'status': False,
#                     'message': 'Block admin account already active'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if user.status == 2:
#                 return Response({
#                     'status': False,
#                     'message': 'Block admin is suspended, check with admin'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             current_logged_in_admin = User.objects.filter(email=current_user).first()
            
#             if current_logged_in_admin == accounts_profile.approver:
#                 return Response({
#                     'status': False,
#                     'message': 'You cannot approve a Block Landlord you created.'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             saved_otp = OtpVerificationCode.objects.filter(email=email, validated=False)
#             if not saved_otp:
#                 return Response({
#                     'status': False,
#                     'message': 'Otp does not exist'
#                 }, status=status.HTTP_404_NOT_FOUND)
#             saved_otp = saved_otp.last()
#             print(type(saved_otp.otp))
#             print(type(otp))

#             if saved_otp.otp != otp:
#                 return Response({
#                     'status': False,
#                     'message': 'Otp does not match'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
            
#             accounts_profile.is_active = 1
#             accounts_profile.save()

#             user.status = 1
#             user.save()

#             saved_otp.validated=True
#             saved_otp.save()

#             print('Block landlord approved!')

#             return Response({
#                 'status': True,
#                 'message': 'Block landlord approved!'
#             }, status=status.HTTP_200_OK)
            
#         except Exception as e:
#             print(str(e))
#             return Response({
#                 'status': False,
#                 'message': 'Could not approve Block landlord profile'
#             }, status=status.HTTP_400_BAD_REQUEST) 

# class SuspendAdminView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = SuspendAdminSerializer

#     def post(self, request):
#         try:
#             data = request.data
#             current_user = request.data
#             serializer = self.serializer_class(data=data)
#             if not serializer.is_valid():
#                 return Response({
#                     'status': False,
#                     'message': 'Invalid data provided',
#                     'errror': serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             email = request.data.get('email')


#             email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#             valid_email = re.fullmatch(email_regex, email)
#             if not valid_email:
#                 return Response({
#                     'status': False,
#                     'message': 'Provide a valid email to login'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            

            
#             user = User.objects.filter(email=email)
#             accounts_profile = Admin.objects.filter(email=email)
#             print(accounts_profile)

#             if not user.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'User with that email does exist'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if not accounts_profile.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Accounts profile with that email does exist'
#                 }, status=status.HTTP_404_NOT_FOUND)
        
            
#             user = user.first()
#             accounts_profile = accounts_profile.first()

            
#             if user.status == 2:
#                 return Response({
#                     'status': False,
#                     'message': 'Account is already suspended, check with admin'
#                 }, status=status.HTTP_400_BAD_REQUEST)
#             current_user = current_user['email']
#             current_logged_in_admin = User.objects.filter(email=current_user)

#             if not current_logged_in_admin.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Admin profile with that email does exist'
#                 }, status=status.HTTP_404_NOT_FOUND)
            

            
#             accounts_profile.is_active = 2
#             accounts_profile.save()

#             user.status = 2
#             user.save()

#             print('Block Landlord account profile suspended!')

#             return Response({
#                 'status': True,
#                 'message': 'Block Landlord profile suspended!!'
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             print(str(e))
#             return Response({
#                 'status': False,
#                 'message': 'Could not suspended Block Admin profile !!'
#             }, status=status.HTTP_400_BAD_REQUEST)


# class ReactivateAdminAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = ReactivateAdminSerializer

#     def post(self, request):
#         try:
#             data = request.data
#             current_user = request.user
#             serializer = self.serializer_class(data=data)

#             if not serializer.is_valid():
#                 return Response({
#                 'status': False,
#                 'message': 'Invalid data provided',
#                 'error': serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)

#             email = request.data.get('email')


#             email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#             valid_email = re.fullmatch(email_regex, email)
#             if not valid_email:
#                 return Response({
#                     'status': False,
#                     'message': 'Provide a valid email to login'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            

            
#             user = User.objects.filter(email=email)
#             block_admin_profile = Admin.objects.filter(email=email)
#             print(block_admin_profile)

#             if not user.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'User with that email does exist'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if not block_admin_profile.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Block landlord profile with that email does exist'
#                 }, status=status.HTTP_404_NOT_FOUND)
            
#             user = user.first()
#             block_admin_profile = block_admin_profile.first()

            
#             if user.status == 1:
#                 return Response({
#                     'status': False,
#                     'message': 'Account is already active'
#                 }, status=status.HTTP_400_BAD_REQUEST)
#             current_user = current_user
#             print(current_user)
#             current_logged_in_admin = User.objects.filter(email=current_user)

#             if not current_logged_in_admin.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Admin profile with that email does exist'
#                 }, status=status.HTTP_404_NOT_FOUND)
            

            
#             block_admin_profile.is_active = 1
#             block_admin_profile.save()

#             user.status = 1
#             user.save() 


#             print('Block Landlord account profile re-activated!')

#             return Response({
#                 'status': True,
#                 'message': 'Block Landlord profile re-activated!!'
#             }, status=status.HTTP_200_OK)


#         except Exception as e:
#             print(str(e))

#             return Response({
#                 'status': False,
#                 'message': 'Could not reactivate block landlord profile'
#             }, status=status.HTTP_400_BAD_REQUEST) 

# class DeleteAdminAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = DeleteAdminSerializer

#     def post(self, request):
#         try:
#             data = request.data
#             current_user = request.user
#             serializer = self.serializer_class(data=data)

#             if not serializer.is_valid():
#                 return Response({
#                 'status': False,
#                 'message': 'Invalid data provided',
#                 'error': serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)

#             email = request.data.get('email')


#             email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#             valid_email = re.fullmatch(email_regex, email)
#             if not valid_email:
#                 return Response({
#                     'status': False,
#                     'message': 'Provide a valid email to login'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            

            
#             user = User.objects.filter(email=email)
#             block_admin_profile = Admin.objects.filter(email=email)
#             print(block_admin_profile)

#             if not user.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'User with that email does exist'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if not block_admin_profile.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Block landlord profile with that email does exist'
#                 }, status=status.HTTP_404_NOT_FOUND)
            
#             user = user.first()
#             block_admin_profile = block_admin_profile.first()

#             current_logged_in_admin = User.objects.filter(email=current_user)

#             if not current_logged_in_admin.exists():
#                 return Response({
#                     'status': False,
#                     'message': 'Admin profile with that email does exist'
#                 }, status=status.HTTP_404_NOT_FOUND)
            

            
#             block_admin_profile.delete()

#             user.delete() 


#             print('Block Landlord account profile deleted!')

#             return Response({
#                 'status': True,
#                 'message': 'Block Landlord profile delete!!'
#             }, status=status.HTTP_200_OK)


#         except Exception as e:
#             print(str(e))

#             return Response({
#                 'status': False,
#                 'message': 'Could not reactivate block landlord profile'
#             }, status=status.HTTP_400_BAD_REQUEST)


class AllTenantPaymentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AllTRansactionsSerializer

    def get(self, request):
        try:
            current_user = request.user
            print(current_user)
            allowed_roles = ['admin']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            all_services = services.objects.filter(status=1).order_by('-id')

            serializer = self.serializer_class(all_services, many=True)

            return Response({
                'status': True,
                'transactions': serializer.data
            }, status=status.HTTP_200_OK)
        

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not fetch all transactions!'
            }, status=status.HTTP_400_BAD_REQUEST)
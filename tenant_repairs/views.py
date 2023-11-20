import re
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from email_service.email_service import repairs_email

from repairs.models import Repair

User = get_user_model()

from repairs.api.serializers import AllTenantRepairsSerializer, TenantRequestRepairSerializer

class TenantRequestRepairAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TenantRequestRepairSerializer

    def post(self, request):
        try:
            data = request.data

            current_user = request.user

            serializer = self.serializer_class(data=data)

            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided!',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            allowed_roles = ['tenant']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')
            broken_property = request.data.get('broken_property')
            description_broken_property = request.data.get('description_broken_property')

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
                    'message': 'tenant with this email does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            user = user.first()
            if user.is_active == 0:
                return Response({
                    'status': False,
                    'message': 'tenant account is inactive'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not Repair.objects.create(email=email, broken_property=broken_property, description_broken_property=description_broken_property):
                return Response({
                    'status': False,
                    'message': 'error saving repair to db'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not repairs_email(email, broken_property):
                return Response({
                    'status': False,
                    'message': 'error sending email to tenant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            return Response({
                    'status': True,
                    'message': 'Repair sent to admin!'
                }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not make repair request!'
            }, status=status.HTTP_200_OK)
        
class AllTenantRepairsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AllTenantRepairsSerializer

    def get(self, request):
        try:
            current_user = request.user
            allowed_roles = ['tenant']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            all_repair = Repair.objects.filter(email=current_user).order_by('-id')

            serializer = self.serializer_class(all_repair, many=True)

            return Response({
                'status': True,
                'transactions': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not retrive repair list'
            })
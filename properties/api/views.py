from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from authentication.models import staffAdmin
from block_landlord.models import BlockLandlord
from properties.models import Property, PropertyBlock

User = get_user_model()
from properties.api.serializers import AddBlockHousesSerializer, AddPropertySerializer

class AddPropertyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddPropertySerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.user

            serializer =  self.serializer_class(data=data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            allowed_roles = ['admin']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Operation not allowed check logged in user role'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            block_number = request.data.get('block_number')
            block_landlord_email = request.data.get('block_landlord_email')
            location = request.data.get('location')

            check_block_number = Property.objects.filter(block_number=block_number)
            if check_block_number.exists():
                return Response({
                    'status': False,
                    'message': 'Block already registered'
                }, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=current_user)
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'user does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            admin = staffAdmin.objects.filter(email=current_user)
            if not admin.exists():
                return Response({
                    'status': False,
                    'message': 'admin does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            block_landlord = BlockLandlord.objects.filter(email = block_landlord_email)

            if not block_landlord.exists():
                return Response({
                    'status': False,
                    'message': 'landlord chosen does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            block_landlord = block_landlord.first()
            new_property = Property.objects.create(block_number=block_number, location=location)

            block_landlord.property.add(new_property)
            
            return Response({
                'status': False,
                'message': 'Property registered successfully'
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not add property'
            }, status=status.HTTP_400_BAD_REQUEST)
        
class AddBlockHousesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddBlockHousesSerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.user

            serializer =  self.serializer_class(data=data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            allowed_roles = ['landlord']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Operation not allowed check logged in user role'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            block = request.data.get('block')
            house_number = request.data.get('house_number')
            service_charge = request.data.get('service_charge')
            rent_charged = request.data.get('rent_charged')


            check_block_number = Property.objects.filter(block_number=block)
            if not check_block_number.exists():
                return Response({
                    'status': False,
                    'message': 'Block entered does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            check_block_number = check_block_number.first()

            user = User.objects.filter(email=current_user)
            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'user does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            admin = BlockLandlord.objects.filter(email=current_user)
            if not admin.exists():
                return Response({
                    'status': False,
                    'message': 'landlord does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            rent_due_date = date.today() + timedelta(days=30)
            PropertyBlock.objects.create(block=check_block_number, 
                                        house_number=house_number, 
                                        service_charge=service_charge,  
                                        annual_service_charge = service_charge *12,
                                        rent_charged=rent_charged, 
                                        rent_due_date=rent_due_date)

            
            return Response({
                'status': False,
                'message': 'House registered successfully'
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not add property'
            }, status=status.HTTP_400_BAD_REQUEST)
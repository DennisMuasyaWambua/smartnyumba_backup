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
                'status': True,
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
            annual_service_charge = float(service_charge) * 12  # Calculate annual from monthly
            PropertyBlock.objects.create(block=check_block_number,
                                        house_number=house_number,
                                        service_charge=service_charge,
                                        annual_service_charge=annual_service_charge,
                                        rent_charged=rent_charged,
                                        rent_due_date=rent_due_date,
                                        rent_charge_business_number=0)


            return Response({
                'status': True,
                'message': 'House registered successfully'
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not add property'
            }, status=status.HTTP_400_BAD_REQUEST)

class LandlordAddPropertyAPIView(APIView):
    """
    Landlords can create their own properties
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AddPropertySerializer

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

            # Only landlords can use this endpoint
            if current_user.role.short_name != 'landlord':
                return Response({
                    'status': False,
                    'message': 'Only landlords can add properties'
                }, status=status.HTTP_403_FORBIDDEN)

            block_number = request.data.get('block_number')
            location = request.data.get('location')

            # Check if block number already exists
            check_block_number = Property.objects.filter(block_number=block_number)
            if check_block_number.exists():
                return Response({
                    'status': False,
                    'message': 'Block number already exists'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get landlord profile
            block_landlord = BlockLandlord.objects.filter(user=current_user).first()
            if not block_landlord:
                return Response({
                    'status': False,
                    'message': 'Landlord profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Create property
            new_property = Property.objects.create(
                block_number=block_number,
                location=location,
                service_charge_business_number=0  # Default value
            )

            # Associate property with landlord
            block_landlord.property.add(new_property)

            return Response({
                'status': True,
                'message': 'Property added successfully',
                'property': {
                    'block_number': block_number,
                    'location': location
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not add property'
            }, status=status.HTTP_400_BAD_REQUEST)


class LandlordPropertiesListAPIView(APIView):
    """
    Get list of all properties owned by the logged-in landlord
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

            # Get all properties
            properties = block_landlord.property.all()

            properties_data = []
            for prop in properties:
                # Get houses in this property
                houses = PropertyBlock.objects.filter(block=prop)
                properties_data.append({
                    'id': prop.id,
                    'block_number': prop.block_number,
                    'location': prop.location,
                    'total_houses': houses.count(),
                    'houses': [
                        {
                            'id': house.id,
                            'house_number': house.house_number,
                            'service_charge': str(house.service_charge),
                            'rent_charged': str(house.rent_charged),
                            'rent_due_date': house.rent_due_date
                        }
                        for house in houses
                    ]
                })

            return Response({
                'status': True,
                'properties': properties_data,
                'total_properties': len(properties_data)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not retrieve properties'
            }, status=status.HTTP_400_BAD_REQUEST)


class GetAvailableHousesAPIView(APIView):
    """
    Get available (unoccupied) houses for a specific property block.
    Used when onboarding tenants to show only vacant houses.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user

            # Allow landlords and caretakers to access this
            allowed_roles = ['landlord', 'caretaker']
            if current_user.role.short_name not in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Only landlords and caretakers can access this resource'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get block_number from query params
            block_number = request.GET.get('block_number')
            if not block_number:
                return Response({
                    'status': False,
                    'message': 'block_number query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if block exists
            property_block = Property.objects.filter(block_number=block_number).first()
            if not property_block:
                return Response({
                    'status': False,
                    'message': f'Property block {block_number} not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # For landlords, verify they own this property
            if current_user.role.short_name == 'landlord':
                block_landlord = BlockLandlord.objects.filter(user=current_user).first()
                if not block_landlord:
                    return Response({
                        'status': False,
                        'message': 'Landlord profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)

                # Check if this property belongs to the landlord
                if property_block not in block_landlord.property.all():
                    return Response({
                        'status': False,
                        'message': 'You do not have access to this property'
                    }, status=status.HTTP_403_FORBIDDEN)

            # Get all houses in this property block
            all_houses = PropertyBlock.objects.filter(block=property_block)

            # Import Tenant model
            from authentication.models import Tenant

            # Get available houses (not occupied)
            available_houses = []
            for house in all_houses:
                # Check if house is occupied
                is_occupied = Tenant.objects.filter(PropertyBlock=house).exists()

                if not is_occupied:
                    available_houses.append({
                        'id': house.id,
                        'house_number': house.house_number,
                        'service_charge': str(house.service_charge) if house.service_charge else '0',
                        'rent_charged': str(house.rent_charged) if house.rent_charged else '0',
                        'rent_due_date': house.rent_due_date
                    })

            return Response({
                'status': True,
                'block_number': block_number,
                'available_houses': available_houses,
                'total_available': len(available_houses),
                'total_houses': all_houses.count()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(str(e))
            return Response({
                'status': False,
                'message': 'Could not retrieve available houses',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

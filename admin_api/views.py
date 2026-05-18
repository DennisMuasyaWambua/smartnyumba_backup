import random
import re
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from tenant_services.models import services, serviceTransactions, RentTransaction
from tenant_services.serializers import AllTRansactionsSerializer
from django.db.models import Sum


from django.contrib.auth import get_user_model

User = get_user_model()

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
            
            all_services = services.objects.filter(status=0).order_by('-id')

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


class PlatformEarningsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user
            allowed_roles = ['admin']

            if current_user.role.short_name not in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Admin access only'
                }, status=status.HTTP_403_FORBIDDEN)

            # Service charge commissions
            service_commission = serviceTransactions.objects.filter(
                isB2CCompleted=1
            ).aggregate(total=Sum('platform_earnings'))['total'] or 0

            # Rent commissions
            rent_commission = RentTransaction.objects.filter(
                isB2CCompleted=1
            ).aggregate(total=Sum('platform_earnings'))['total'] or 0

            # Total transactions count
            service_transaction_count = serviceTransactions.objects.filter(
                isB2CCompleted=1
            ).count()

            rent_transaction_count = RentTransaction.objects.filter(
                isB2CCompleted=1
            ).count()

            return Response({
                'status': True,
                'service_charge_commission': float(service_commission),
                'rent_commission': float(rent_commission),
                'total_commission': float(service_commission + rent_commission),
                'service_transactions_count': service_transaction_count,
                'rent_transactions_count': rent_transaction_count,
                'total_transactions_count': service_transaction_count + rent_transaction_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Platform earnings error: {str(e)}")
            return Response({
                'status': False,
                'message': 'Could not fetch platform earnings'
            }, status=status.HTTP_400_BAD_REQUEST)


class GetSystemConfigAPIView(APIView):
    """
    Get current system configuration settings.
    Admin only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user
            allowed_roles = ['admin']

            if current_user.role.short_name not in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Admin access only'
                }, status=status.HTTP_403_FORBIDDEN)

            from authentication.models import SystemConfiguration
            config = SystemConfiguration.get_config()

            return Response({
                'status': True,
                'landlord_activation_fee': float(config.landlord_activation_fee),
                'platform_commission_rate': float(config.platform_commission_rate),
                'last_updated': config.last_updated.isoformat() if config.last_updated else None,
                'updated_by': config.updated_by.email if config.updated_by else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Get config error: {str(e)}")
            return Response({
                'status': False,
                'message': 'Could not fetch system configuration'
            }, status=status.HTTP_400_BAD_REQUEST)


class UpdateSystemConfigAPIView(APIView):
    """
    Update system configuration settings.
    Admin only.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            current_user = request.user
            allowed_roles = ['admin']

            if current_user.role.short_name not in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Admin access only'
                }, status=status.HTTP_403_FORBIDDEN)

            from authentication.models import SystemConfiguration
            from decimal import Decimal

            config = SystemConfiguration.get_config()

            # Get values from request
            activation_fee = request.data.get('landlord_activation_fee')
            commission_rate = request.data.get('platform_commission_rate')

            updated_fields = []

            # Update activation fee if provided
            if activation_fee is not None:
                try:
                    activation_fee = Decimal(str(activation_fee))
                    if activation_fee < 0:
                        return Response({
                            'status': False,
                            'message': 'Activation fee cannot be negative'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    config.landlord_activation_fee = activation_fee
                    updated_fields.append(f"Activation fee: KES {activation_fee}")
                except (ValueError, TypeError):
                    return Response({
                        'status': False,
                        'message': 'Invalid activation fee format'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Update commission rate if provided
            if commission_rate is not None:
                try:
                    commission_rate = Decimal(str(commission_rate))
                    if not (0 <= commission_rate <= 1):
                        return Response({
                            'status': False,
                            'message': 'Commission rate must be between 0 and 1 (e.g., 0.05 for 5%)'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    config.platform_commission_rate = commission_rate
                    percentage = float(commission_rate) * 100
                    updated_fields.append(f"Commission rate: {percentage}%")
                except (ValueError, TypeError):
                    return Response({
                        'status': False,
                        'message': 'Invalid commission rate format'
                    }, status=status.HTTP_400_BAD_REQUEST)

            if not updated_fields:
                return Response({
                    'status': False,
                    'message': 'No fields to update'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save with current user as updater
            config.updated_by = current_user
            config.save()

            update_message = "System configuration updated: " + ", ".join(updated_fields)

            return Response({
                'status': True,
                'message': update_message,
                'landlord_activation_fee': float(config.landlord_activation_fee),
                'platform_commission_rate': float(config.platform_commission_rate),
                'updated_by': current_user.email
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Update config error: {str(e)}")
            return Response({
                'status': False,
                'message': 'Could not update system configuration'
            }, status=status.HTTP_400_BAD_REQUEST)


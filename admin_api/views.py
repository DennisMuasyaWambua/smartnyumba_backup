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


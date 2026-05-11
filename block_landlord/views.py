from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import datetime
import calendar

from .models import BlockLandlord
from tenant_services.models import RentTransaction, serviceTransactions, RentPayment, services
from properties.models import PropertyBlock
from authentication.models import Tenant


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

from decimal import Decimal
from django.conf import settings


def calculate_commission(amount):
    """
    Calculate platform commission and landlord payout.

    Args:
        amount (Decimal): Original payment amount

    Returns:
        dict: {
            'commission_amount': Decimal,
            'landlord_payout': Decimal,
            'platform_earnings': Decimal
        }
    """
    amount = Decimal(str(amount))
    commission_rate = Decimal(str(settings.PLATFORM_COMMISSION_RATE))

    commission_amount = amount * commission_rate
    landlord_payout = amount - commission_amount

    return {
        'commission_amount': commission_amount,
        'landlord_payout': landlord_payout,
        'platform_earnings': commission_amount
    }

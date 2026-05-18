from django.db import models
from django.contrib.auth.models import AbstractUser

from authentication.choices import ROLES
from properties.models import PropertyBlock

# Create your models here.


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    short_name = models.CharField(max_length=100, choices=ROLES, default='admin')
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    

    def __str__(self):
        return self.short_name

    class Meta:
        db_table = 'role'


class User(AbstractUser):
    email = models.EmailField()
    username = models.EmailField(unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    mobile_number = models.CharField(max_length=15)
    password = models.CharField(max_length=255)
    created_on = models.DateField(auto_created=True, null=True)
    status = models.IntegerField(default=0)

    class Meta:
        db_table = 'user'


class staffAdmin(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name='user')
    email = models.EmailField()
    name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15)
    id_number = models.CharField(max_length=9)
    is_active = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'admin'



class OtpVerificationCode(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=9)
    validated = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.email}-{self.otp}'

    class Meta:
        # managed=False
        db_table = 'otp_verification_code'

class Tenant(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name='tenant')
    email = models.EmailField()
    name = models.CharField(max_length=30)
    id_number = models.CharField(max_length=9)
    is_active = models.IntegerField(default=0)
    PropertyBlock = models.ForeignKey(PropertyBlock, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'tenant'
    
    def __str__(self) -> str:
        return f'{self.name} {self.PropertyBlock.block.block_number}'


class LoginOTP(models.Model):
    mobile_number = models.CharField(max_length=17)
    otp = models.CharField(max_length=9)
    validated = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.mobile_number}-{self.otp}'

    class Meta:
        #managed=False
        db_table = 'login_otp'


class SystemConfiguration(models.Model):
    """
    Stores system-wide configuration values that can be changed without code deployment.
    Singleton pattern - only one record should exist.
    """
    # Activation settings
    landlord_activation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=500.00,
        help_text="Amount in KES that landlords pay for account activation"
    )

    # Commission settings
    platform_commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.05,
        help_text="Platform commission rate (e.g., 0.05 for 5%)"
    )

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_updates'
    )

    class Meta:
        db_table = 'system_configuration'
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configuration'

    def save(self, *args, **kwargs):
        """Enforce singleton pattern"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton"""
        pass

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config

    def __str__(self):
        return f"System Config (Activation Fee: {self.landlord_activation_fee} KES)"


class ActivationPayment(models.Model):
    """
    Tracks landlord activation payment records.
    Similar to RentPayment model but for activation fees.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='activation_payment',
        help_text="Landlord user who is paying activation fee"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Activation fee amount"
    )

    payment_mode = models.CharField(
        default='mpesa',
        max_length=15,
        help_text="Payment method (mpesa, card, etc.)"
    )

    status = models.IntegerField(
        default=0,
        help_text="0=pending, 1=completed, 2=failed"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'activation_payments'
        verbose_name = 'Activation Payment'
        verbose_name_plural = 'Activation Payments'

    def __str__(self):
        return f'{self.user.email} - KES {self.amount} - Status: {self.status}'


class ActivationTransaction(models.Model):
    """
    Tracks M-Pesa transaction details for activation payments.
    Similar to RentTransaction but without B2C payout fields.
    """
    activation_payment = models.ForeignKey(
        ActivationPayment,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    status = models.IntegerField(
        default=0,
        help_text="0=pending, 1=completed, 2=failed"
    )

    # M-Pesa identifiers
    MerchantRequestID = models.CharField(max_length=50, null=True, blank=True)
    CheckoutRequestID = models.CharField(max_length=50, null=True, blank=True)
    MpesaReceiptNumber = models.CharField(max_length=50, null=True, blank=True)

    # Transaction details
    PhoneNumber = models.CharField(max_length=15, null=True, blank=True)
    TransactionDate = models.CharField(max_length=20, null=True, blank=True)

    # Platform earnings (100% - no commission deduction)
    platform_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Full activation fee goes to platform"
    )

    # Timestamps
    date_initiated = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True, blank=True)

    # Result details
    ResultCode = models.CharField(max_length=10, null=True, blank=True)
    ResultDesc = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'activation_transactions'
        verbose_name = 'Activation Transaction'
        verbose_name_plural = 'Activation Transactions'
        ordering = ['-date_initiated']

    def __str__(self):
        return f'{self.MerchantRequestID} - {self.status}'
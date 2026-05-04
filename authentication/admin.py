from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from . models import (
    Tenant, User, Role, staffAdmin,
    SystemConfiguration, ActivationPayment, ActivationTransaction
)
# Register your models here.

class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ('username', 'is_active', 'role', 'is_staff')
    list_filter = ('is_staff', 'is_active', 'role')
    fieldsets = (
        ('Personal info', 
                        {'fields': 
                                    ('username','first_name', 'email', 'mobile_number')
                        }
        ),
        ('Groups', 
                {'fields': 
                        ('groups',)
                }
        ),
        ('Permissions', 
                    {'fields': 
                            ('is_superuser', 'is_staff','is_active','role', 'status')
                    }
        ),
    )

    search_fields = ('email', 'username','mobile_number')

admin.site.register(User, UserAdmin)
admin.site.register(Role)
admin.site.register(staffAdmin)
admin.site.register(Tenant)


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for system configuration.
    Only one record can exist (singleton).
    """
    list_display = [
        'landlord_activation_fee',
        'platform_commission_rate',
        'last_updated',
        'updated_by'
    ]

    fieldsets = (
        ('Activation Settings', {
            'fields': ('landlord_activation_fee',)
        }),
        ('Commission Settings', {
            'fields': ('platform_commission_rate',)
        }),
        ('Metadata', {
            'fields': ('updated_by', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['last_updated']

    def has_add_permission(self, request):
        """Only allow one configuration record"""
        return not SystemConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of configuration"""
        return False


@admin.register(ActivationPayment)
class ActivationPaymentAdmin(admin.ModelAdmin):
    """Admin interface for activation payments"""
    list_display = [
        'user',
        'amount',
        'payment_mode',
        'status',
        'created_at',
        'completed_at'
    ]

    list_filter = ['status', 'payment_mode', 'created_at']
    search_fields = ['user__email', 'user__first_name']
    readonly_fields = ['created_at', 'completed_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Payment Details', {
            'fields': ('amount', 'payment_mode', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly if payment is completed"""
        if obj and obj.status == 1:
            return self.readonly_fields + ('amount', 'payment_mode', 'user')
        return self.readonly_fields


@admin.register(ActivationTransaction)
class ActivationTransactionAdmin(admin.ModelAdmin):
    """Admin interface for activation transactions"""
    list_display = [
        'MerchantRequestID',
        'activation_payment',
        'status',
        'MpesaReceiptNumber',
        'platform_earnings',
        'date_initiated',
        'date_completed'
    ]

    list_filter = ['status', 'date_initiated']
    search_fields = [
        'MerchantRequestID',
        'CheckoutRequestID',
        'MpesaReceiptNumber',
        'activation_payment__user__email'
    ]

    readonly_fields = [
        'date_initiated',
        'date_completed',
        'MerchantRequestID',
        'CheckoutRequestID',
        'MpesaReceiptNumber',
        'PhoneNumber',
        'TransactionDate',
        'ResultCode',
        'ResultDesc'
    ]

    fieldsets = (
        ('Payment Reference', {
            'fields': ('activation_payment',)
        }),
        ('M-Pesa Details', {
            'fields': (
                'MerchantRequestID',
                'CheckoutRequestID',
                'MpesaReceiptNumber',
                'PhoneNumber'
            )
        }),
        ('Transaction Status', {
            'fields': ('status', 'ResultCode', 'ResultDesc')
        }),
        ('Financial', {
            'fields': ('platform_earnings',)
        }),
        ('Timestamps', {
            'fields': ('date_initiated', 'date_completed'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Transactions are created programmatically"""
        return False
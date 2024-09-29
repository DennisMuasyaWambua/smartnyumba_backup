from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model

from properties.models import Property
from services.choices import PAYMENTS

user = get_user_model()

class services(models.Model):
    user = models.ForeignKey(user, on_delete=models.SET_NULL, null=True)
    block = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True)
    service_name = models.CharField(max_length=30, null=False)
    amount = models.DecimalField(max_digits=7, decimal_places=2, null=False)
    payment_mode = models.CharField(default='mpesa', max_length=15, choices=PAYMENTS)
    balance_service_charge = models.DecimalField(decimal_places=2, max_digits=7, default=1)

    class Meta:
        db_table = 'services'
        verbose_name_plural = 'services'

    def __str__(self):
        return f'{self.service_name}-{self.amount}'

    
class serviceTransactions(models.Model):
    service_instance = models.ForeignKey(services, on_delete=models.SET_NULL, null=True)
    status = models.IntegerField(default=0)
    date_paid = models.DateField(auto_now_add=True) 
    MerchantRequestID = models.CharField(max_length=50, null=True)
    CheckoutRequestID = models.CharField(max_length=50, null=True)
    isB2CCompleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'services_transactions'
        verbose_name_plural = 'services_transactions'

    def __str__(self):
        return self.MerchantRequestID
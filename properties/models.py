from django.db import models


# Create your models here.

class Property(models.Model):
    location = models.CharField(max_length=50, null=False)
    block_number = models.CharField(max_length=10)
    registration_date = models.DateField(auto_now_add=True)
    service_charge_business_number = models.IntegerField()

    class Meta:
        db_table = 'property_detail'
        verbose_name_plural = "Properties"

    def __str__(self):
        return self.block_number
    
class ServiceChargeCollection(models.Model):
    block = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True)
    tenant = models.EmailField(unique=True)
    total_amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    total_months_paid = models.IntegerField(null=True)
    total_months_unpaid = models.IntegerField(null=True)

class PropertyBlock(models.Model):
    block = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True)
    house_number = models.CharField(max_length=10, null=False)
    service_charge = models.DecimalField(decimal_places=2, max_digits=10)
    annual_service_charge = models.DecimalField(decimal_places=2, max_digits=10)
    rent_charged = models.DecimalField(decimal_places=2, max_digits=7)
    rent_due_date = models.DateField()
    rent_charge_business_number = models.IntegerField()

    class Meta:
        db_table = 'block_detail'
        verbose_name_plural = "PropertyBlocks"

    def __str__(self) -> str:
        return f'{self.block} {self.house_number}'




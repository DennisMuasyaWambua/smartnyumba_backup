from django.db import models

from django.contrib.auth import get_user_model

from properties.models import Property



User = get_user_model()

# Create your models here.

class BlockLandlord(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    id_number = models.CharField(max_length=9)
    is_active = models.IntegerField(default=0)
    approver = models.EmailField(null=False)
    property = models.ManyToManyField(Property, related_name='property')

    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'block_landlord'
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
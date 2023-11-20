from django.contrib import admin

from properties.models import Property, PropertyBlock

# Register your models here.

admin.site.register(Property)
admin.site.register(PropertyBlock)
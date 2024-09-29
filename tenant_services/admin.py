from django.contrib import admin

from properties.models import ServiceChargeCollection
from tenant_services.models import serviceTransactions, services


admin.site.register(services)
admin.site.register(ServiceChargeCollection)
admin.site.register(serviceTransactions)
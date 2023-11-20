from django.contrib import admin 
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from . models import Tenant, User, Role,staffAdmin
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
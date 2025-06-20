from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'is_approved', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'is_approved', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('額外資訊', {'fields': ('user_type', 'is_approved', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('額外資訊', {'fields': ('user_type', 'is_approved', 'phone')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)


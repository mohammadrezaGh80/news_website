from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm
from .forms import CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("phone_number", "age", )}),
    )
    fieldsets = UserAdmin.fieldsets + (
        ("More information", {"fields": ("phone_number", "age",)}),
    )
    list_display = ("username", "phone_number", "age", "email", "is_staff", )


admin.site.register(CustomUser, CustomUserAdmin)

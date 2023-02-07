from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm
from .forms import CustomUserChangeForm
from .models import CustomUser
from news.models import Comment


class CommentInline(admin.TabularInline):
    model = Comment
    fields = ("text", "report", "likes", "dislikes", )
    extra = 1


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
    list_display = ("username", "phone_number", "age", "email", )
    inlines = [
        CommentInline
    ]


admin.site.register(CustomUser, CustomUserAdmin)

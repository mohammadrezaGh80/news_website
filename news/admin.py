from django.contrib import admin

from .models import Report, Comment


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "datetime_created", "datetime_modified", )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "report", "datetime_created", )

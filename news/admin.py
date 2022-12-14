from django.contrib import admin

from .models import Report, Comment, CommentRelation


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "datetime_created", "datetime_modified",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "report", "datetime_created",)


@admin.register(CommentRelation)
class CommentRelationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_reply_user_name", "get_reply_to_user_name", "get_report", "get_datetime", )

    def get_reply_user_name(self, obj):
        return obj.reply.user
    get_reply_user_name.short_description = "reply's username"

    def get_reply_to_user_name(self, obj):
        return obj.reply_to.user
    get_reply_to_user_name.short_description = "reply's to username"

    def get_datetime(self, obj):
        return obj.reply.datetime_created
    get_datetime.short_description = "datetime_created"

    def get_report(self, obj):
        return obj.reply.report
    get_report.short_description = "report"

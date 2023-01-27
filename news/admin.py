from django.contrib import admin

from .models import Report, Comment, CommentRelation, UserLikeComment, UserDislikeComment


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "datetime_created", "datetime_modified",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "report", "likes", "dislikes", "datetime_created", "datetime_modified", )


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


@admin.register(UserLikeComment)
class UserLikeCommentAdmin(admin.ModelAdmin):
    list_display = ("get_user_username", "get_liked_comment", )

    def get_user_username(self, obj):
        return obj.user.username
    get_user_username.short_description = "like's username"

    def get_liked_comment(self, obj):
        return obj.comment.text
    get_liked_comment.short_description = "like's comment"


@admin.register(UserDislikeComment)
class UserLikeCommentAdmin(admin.ModelAdmin):
    list_display = ("get_user_username", "get_disliked_comment", )

    def get_user_username(self, obj):
        return obj.user.username
    get_user_username.short_description = "dislike's username"

    def get_disliked_comment(self, obj):
        return obj.comment.text
    get_disliked_comment.short_description = "dislike's comment"

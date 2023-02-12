from django.contrib import admin

from jalali_date import datetime2jalali

from .models import Report, Comment, CommentRelation, UserLikeComment, UserDislikeComment, Category, ReportCategory


class CommentInline(admin.TabularInline):
    model = Comment
    fields = ("user", "text", "likes", "dislikes", )
    extra = 1


class CommentRelationInline(admin.TabularInline):
    model = CommentRelation
    fields = ("reply", )
    fk_name = "reply_to"
    extra = 1


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status",
                    "get_report_datetime_created_jalali", "get_report_datetime_modified_jalali",)
    ordering = ("-datetime_modified",)
    inlines = [
        CommentInline,
    ]

    def get_report_datetime_created_jalali(self, obj):
        return datetime2jalali(obj.datetime_created).strftime('%Y/%m/%d - %H:%M:%S')
    get_report_datetime_created_jalali.short_description = "datetime_created"

    def get_report_datetime_modified_jalali(self, obj):
        return datetime2jalali(obj.datetime_modified).strftime('%Y/%m/%d - %H:%M:%S')
    get_report_datetime_modified_jalali.short_description = "datetime_modified"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "report", "likes", "dislikes",
                    "get_comment_datetime_created_jalali", "get_comment_datetime_modified_jalali", )
    inlines = [
        CommentRelationInline,
    ]

    def get_comment_datetime_created_jalali(self, obj):
        return datetime2jalali(obj.datetime_created).strftime('%Y/%m/%d - %H:%M:%S')
    get_comment_datetime_created_jalali.short_description = "datetime_created"

    def get_comment_datetime_modified_jalali(self, obj):
        return datetime2jalali(obj.datetime_modified).strftime('%Y/%m/%d - %H:%M:%S')
    get_comment_datetime_modified_jalali.short_description = "datetime_modified"


@admin.register(CommentRelation)
class CommentRelationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_reply_user_name", "get_reply_to_user_name",
                    "get_report", "get_comment_datetime_jalali", )

    def get_reply_user_name(self, obj):
        return obj.reply.user
    get_reply_user_name.short_description = "reply's username"

    def get_reply_to_user_name(self, obj):
        return obj.reply_to.user
    get_reply_to_user_name.short_description = "reply's to username"

    def get_comment_datetime_jalali(self, obj):
        return datetime2jalali(obj.reply.datetime_created).strftime('%Y/%m/%d - %H:%M:%S')
    get_comment_datetime_jalali.short_description = "datetime_created"

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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", )


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ("report_title", "category_name", )

    def report_title(self, obj):
        return obj.report.title
    report_title.short_description = "report's title"

    def category_name(self, obj):
        return obj.category.name
    category_name.short_description = "category's name"

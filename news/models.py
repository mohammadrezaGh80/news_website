from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date


class ReportPublishedManager(models.Manager):
    def get_queryset(self):
        return super(ReportPublishedManager, self).get_queryset().filter(status=Report.PUBLISHED)


class Report(models.Model):
    PENDING = "pending"
    PUBLISHED = "published"
    CANCELED = "canceled"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (PUBLISHED, "Published"),
        (CANCELED, "Canceled"),
    )

    title = models.CharField(max_length=250)
    description = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="reports")
    cover = models.ImageField(upload_to="covers/", blank=True)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default=PENDING)

    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    # Manager
    objects = models.Manager()
    report_published = ReportPublishedManager()

    def __str__(self):
        return self.title

    def calculate_days_diff_from_today(self):
        return abs((self.datetime_modified.date() - date.today()).days)

    def get_absolute_url(self):
        return reverse("report_detail", args=[self.id])


class Comment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="comments")
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)

    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField()

    def calculate_days_diff_from_today(self):
        return abs((self.datetime_modified.date() - date.today()).days)

    def get_all_id_of_children(self):
        all_id_list = []
        for comment_relation in self.replies.all():
            if comment_relation.reply.replies.count():
                all_id_list.extend(comment_relation.reply.get_all_id_of_children())
            all_id_list.append(comment_relation.reply.id)
        return all_id_list

    def get_all_replies(self):
        all_id_of_children = self.get_all_id_of_children()
        return CommentRelation.objects.filter(reply_id__in=all_id_of_children)

    def count_of_children(self):
        count_children = 0
        for comment_relation in self.replies.all():
            if comment_relation.reply.replies.count():
                count_children += comment_relation.reply.count_of_children()
            count_children += 1

        return count_children

    def has_parent(self):
        return self.to_comment.count()

    def get_root_comment(self):
        if self.has_parent():
            return self.to_comment.first().reply_to.get_root_comment()
        return self

    def __str__(self):
        return self.text


class CommentRelation(models.Model):
    reply = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="to_comment")
    reply_to = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="replies")

    def __str__(self):
        return f"{self.reply.text} to {self.reply_to.text}"


class UserLikeComment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="comments_like")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="users_like")

    def __str__(self):
        return f"{self.user.username} likes {self.comment.text}"


class UserDislikeComment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="comments_dislike")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="users_dislike")

    def __str__(self):
        return f"{self.user.username} dislikes {self.comment.text}"


class Category(models.Model):
    CATEGORY_NAME_CHOICES = (
        ("sport", "ورزش"),
        ("football", "فوتبال"),
        ("political", "سیاسی"),
        ("internal", "اخبار داخلی"),
        ("foreign", "اخبار خارجی"),
        ("exclusive", "اخبار اختصاصی"),
    )
    name = models.CharField(max_length=20, choices=CATEGORY_NAME_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class ReportCategory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="categories")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="reports")

    def __str__(self):
        return f"{self.category.name} for {self.report.title}"

    class Meta:
        verbose_name_plural = "Report Categories"

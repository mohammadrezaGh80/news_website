from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date


class Report(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="reports")
    cover = models.ImageField(upload_to="covers/", blank=True)

    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

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

    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

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

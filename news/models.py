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

    def get_absolute_url(self):
        return reverse("report_detail", args=[self.id])


class Comment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="comments")
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()

    datetime_created = models.DateTimeField(auto_now_add=True)

    def calculate_days_diff_from_today(self):
        return abs((self.datetime_created.date() - date.today()).days)

    def __str__(self):
        return self.text

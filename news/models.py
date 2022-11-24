from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model


class Report(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="reports")
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("report_detail", args=[self.id])

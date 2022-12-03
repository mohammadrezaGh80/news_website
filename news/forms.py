from django import forms

from .models import Report, Comment


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["title", "description", "cover", ]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text", ]

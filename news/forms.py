from django import forms
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox

from .models import Report, Comment


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["title", "description", "cover", ]


class CommentForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = Comment
        fields = ["text", ]

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    phone_number = models.CharField(
        validators=[RegexValidator(r"09[0-9]{9}", message="This phone number is incorrect!")],
        max_length=11
    )

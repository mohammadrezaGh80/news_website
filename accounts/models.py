from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    if len(value) == 11 and value.startswith("09"):
        return value
    else:
        return ValidationError("This phone number is incorrect!")


class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=11, validators=[validate_phone_number])

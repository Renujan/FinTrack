from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    currency = models.CharField(
        max_length=3,
        default="LKR",
        help_text="Primary currency ISO code (e.g. LKR, USD, EUR)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email if self.email else self.username

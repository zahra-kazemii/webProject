from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_librarian = models.BooleanField(default=False, verbose_name="آیا کتابدار است؟")

    def __str__(self):
        return f"{self.username} - {'کتابدار' if self.is_librarian else 'عضو'}"
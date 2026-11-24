from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^09\d{9}$',
    message='شماره موبایل باید 11 رقم باشد و با 09 شروع شود (مثال: 09123456789).'
)

class User(AbstractUser):
    is_librarian = models.BooleanField(default=False, verbose_name="آیا کتابدار است؟")
    phone = models.CharField(
        
        max_length=11,
        blank=True,
        validators=[phone_validator],
        verbose_name="شماره موبایل"
    )

    def __str__(self):
        return f"{self.username} - {'کتابدار' if self.is_librarian else 'عضو'}"
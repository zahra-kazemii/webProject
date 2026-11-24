from django.db import models
from django.conf import settings
from django.utils import timezone
from Books.models import Book

class Loan(models.Model):
    class Meta:
        verbose_name = 'امانت'
        verbose_name_plural = 'امانت‌ ها'
        ordering = ['-request_date']

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار تایید'),
        ('ACTIVE', 'فعال'),
        ('RETURNED', 'بازگردانده شده'),
        ('REJECTED', 'رد شده'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="عضو")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ درخواست")
    due_date = models.DateField(null=True, blank=True, verbose_name="تاریخ سررسید")
    return_date = models.DateField(null=True, blank=True, verbose_name="تاریخ بازگشت واقعی")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    renewal_count = models.IntegerField(default=0, verbose_name="تعداد تمدید شده")
    renewal_requested = models.BooleanField(default=False, verbose_name="درخواست تمدید دارد؟")
    fine_amount = models.IntegerField(default=0, verbose_name="مبلغ جریمه (تومان)")
    is_fine_paid = models.BooleanField(default=False, verbose_name="جریمه پرداخت شده؟")
    is_damaged = models.BooleanField(default=False, verbose_name="کتاب آسیب دیده؟")
    damage_notes = models.TextField(blank=True, null=True, verbose_name="توضیحات آسیب")
    rejection_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="دلیل رد درخواست")

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"
    
    @property
    def is_overdue(self):
        """آیا امانت فعال و از سررسید گذشته؟"""
        return (
            self.status == 'ACTIVE'
            and self.due_date is not None
            and timezone.localdate() > self.due_date
        )

    @property
    def late_days(self):
        if not self.due_date:
            return 0
        end = self.return_date or timezone.localdate()
        return max((end - self.due_date).days, 0)

    def calculate_fine(self):
        """مبلغ جریمه‌ی تأخیر بر اساس تعداد روز دیرکرد"""
        return self.late_days * settings.FINE_PER_DAY

    @property
    def can_renew(self):
        return (
            self.status == 'ACTIVE'
            and not self.is_overdue
            and not self.renewal_requested
            and self.renewal_count < settings.MAX_RENEWALS
        )


class Reservation(models.Model):
    class Meta:
        verbose_name = 'رزرو'
        verbose_name_plural = 'رزرو ها'
        ordering = ['reserved_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=models.Q(status__in=['ACTIVE', 'NOTIFIED']),
                name='unique_open_reservation',
            ),
        ]

    STATUS_CHOICES = (
        ('ACTIVE', 'فعال'),
        ('NOTIFIED', 'اطلاع‌رسانی شده'),
        ('FULFILLED', 'تبدیل به امانت شد'),
        ('CANCELLED', 'لغو شده'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="رزروکننده")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    reserved_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ رزرو")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="وضعیت رزرو")

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
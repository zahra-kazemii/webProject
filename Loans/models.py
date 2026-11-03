from django.db import models
from django.conf import settings
from Books.models import Book

class Loan(models.Model):
    class Meta:
        verbose_name = 'امانت'
        verbose_name_plural = 'امانت‌ ها'

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
    fine_amount = models.IntegerField(default=0, verbose_name="مبلغ جریمه (تومان)")
    is_fine_paid = models.BooleanField(default=False, verbose_name="جریمه پرداخت شده؟")
    is_damaged = models.BooleanField(default=False, verbose_name="کتاب آسیب دیده؟")
    damage_notes = models.TextField(blank=True, null=True, verbose_name="توضیحات آسیب")
    rejection_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="دلیل رد درخواست")

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"


class Reservation(models.Model):
    class Meta:
        verbose_name = 'رزرو'
        verbose_name_plural = 'رزرو ها'

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
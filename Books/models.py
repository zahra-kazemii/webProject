from django.db import models

class Book(models.Model):
    class Meta:
        verbose_name = 'کتاب'
        verbose_name_plural = 'کتاب ها'
        ordering = ['title']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock__lte=models.F('total_copies')),
                name='stock_lte_total_copies',
            ),
        ]

    CATEGORY_CHOICES = (
        ('fiction', 'رمان و داستان'),
        ('science', 'علمی و آموزشی'),
        ('history', 'تاریخی'),
        ('poetry', 'شعر و ادبیات'),
        ('children', 'کودک و نوجوان'),
        ('psychology', 'روانشناسی'),
        ('other', 'سایر'),
    )
    title = models.CharField(max_length=200, verbose_name="عنوان کتاب")
    author = models.CharField(max_length=150, verbose_name="نویسنده")
    publisher = models.CharField(max_length=150, verbose_name="ناشر")
    publish_year = models.IntegerField(verbose_name="سال انتشار")
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        verbose_name="دسته بندی",
        default='other'
    )
    stock = models.PositiveIntegerField(default=1, verbose_name="موجودی در انبار")
    total_copies = models.PositiveIntegerField(default=1, verbose_name="کل نسخه‌ها")

    def __str__(self):
        return self.title
from django import forms
from .models import Book
from Users.mixins import BootstrapFormMixin


class BookForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'publisher', 'publish_year', 'category', 'total_copies')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        self._borrowed = (inst.total_copies - inst.stock) if inst.pk else 0

    def clean_total_copies(self):
        total = self.cleaned_data['total_copies']
        if total < self._borrowed:
            raise forms.ValidationError(
                f'{self._borrowed} نسخه از این کتاب در حال حاضر امانت داده شده؛ '
                f'کل نسخه‌ها نمی‌تواند کمتر از این باشد.'
            )
        return total

    def save(self, commit=True):
        book = super().save(commit=False)
        book.stock = book.total_copies - self._borrowed
        if commit:
            book.save()
        return book


class BookFilterForm(BootstrapFormMixin, forms.Form):
    SORT_CHOICES = (
        ('title', 'عنوان (الف تا ی)'),
        ('-publish_year', 'جدیدترین'),
        ('publish_year', 'قدیمی‌ترین'),
    )

    q = forms.CharField(
        required=False, label='جستجو',
        widget=forms.TextInput(attrs={'placeholder': 'عنوان، نویسنده یا ناشر...'}),
    )
    category = forms.ChoiceField(
        required=False, label='موضوع',
        choices=[('', 'همه‌ی موضوعات')] + list(Book.CATEGORY_CHOICES),
    )
    publisher = forms.CharField(required=False, label='ناشر')
    year_from = forms.IntegerField(required=False, min_value=0, label='از سال')
    year_to = forms.IntegerField(required=False, min_value=0, label='تا سال')
    available = forms.BooleanField(required=False, label='فقط کتاب‌های موجود')
    sort = forms.ChoiceField(required=False, label='مرتب‌سازی', choices=SORT_CHOICES)

    def clean(self):
        data = super().clean()
        y1, y2 = data.get('year_from'), data.get('year_to')
        if y1 and y2 and y1 > y2:
            raise forms.ValidationError('«از سال» نمی‌تواند بزرگ‌تر از «تا سال» باشد.')
        return data
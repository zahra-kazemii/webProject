import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .mixins import BootstrapFormMixin


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, label='ایمیل')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone')
        labels = {
            'username': 'نام کاربری',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'phone': 'شماره موبایل',
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
        phone = phone.translate(digits)

        if not re.fullmatch('09\d{9}', phone):
            raise forms.ValidationError('شماره موبایل باید دقیقاً 11 رقم باشد و به فرم *********09 باشد.')
        return phone
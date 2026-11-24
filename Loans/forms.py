from django import forms
from Users.mixins import BootstrapFormMixin


class ReturnForm(BootstrapFormMixin, forms.Form):
    fine_amount = forms.IntegerField(
        min_value=0, label='مبلغ جریمه (تومان)',
        help_text='به‌صورت خودکار بر اساس روزهای تأخیر محاسبه شده؛ در صورت نیاز تغییر دهید.',
    )
    is_damaged = forms.BooleanField(required=False, label='کتاب آسیب دیده است')
    damage_notes = forms.CharField(
        required=False, label='توضیحات آسیب',
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    def clean(self):
        data = super().clean()
        if data.get('is_damaged') and not data.get('damage_notes', '').strip():
            self.add_error('damage_notes', 'برای کتاب آسیب‌دیده توضیحات را بنویسید.')
        return data


class RejectForm(forms.Form):
    reason = forms.CharField(max_length=255, label='دلیل رد درخواست')
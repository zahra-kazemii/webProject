from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class LibrarianRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """فقط کتابدار می‌تونه وارد این صفحه بشه."""

    def test_func(self):
        return self.request.user.is_librarian

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'شما به این بخش دسترسی ندارید.')
            return redirect('home')
        return super().handle_no_permission()


class MemberRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """فقط عضو عادی (نه کتابدار) می‌تونه وارد این صفحه بشه."""

    def test_func(self):
        return not self.request.user.is_librarian

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'این بخش مخصوص اعضای کتابخانه است.')
            return redirect('home')
        return super().handle_no_permission()


class BootstrapFormMixin:
    """به همه‌ی فیلدهای فرم کلاس Bootstrap اضافه می‌کنه تا ظاهرشون درست بشه."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(widget, forms.Select):
                css = 'form-select'
            else:
                css = 'form-control'
            widget.attrs['class'] = (widget.attrs.get('class', '') + ' ' + css).strip()
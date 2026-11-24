from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)
from Loans.models import Loan, Reservation
from Users.mixins import LibrarianRequiredMixin
from .forms import BookFilterForm, BookForm
from .models import Book


class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        qs = Book.objects.all()
        self.filter_form = BookFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            d = self.filter_form.cleaned_data

            if d['q']:
                qs = qs.filter(
                    Q(title__icontains=d['q'])
                    | Q(author__icontains=d['q'])
                    | Q(publisher__icontains=d['q'])
                )
            if d['category']:
                qs = qs.filter(category=d['category'])
            if d['publisher']:
                qs = qs.filter(publisher__icontains=d['publisher'])
            if d['year_from']:
                qs = qs.filter(publish_year__gte=d['year_from'])
            if d['year_to']:
                qs = qs.filter(publish_year__lte=d['year_to'])
            if d['available']:
                qs = qs.filter(stock__gt=0)
            if d['sort']:
                qs = qs.order_by(d['sort'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = self.filter_form
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['query_string'] = params.urlencode()
        ctx['total_count'] = len(ctx['books'])
        return ctx


class BookDetailView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_librarian:
            ctx['user_loan'] = Loan.objects.filter(
                user=user, book=self.object, status__in=['PENDING', 'ACTIVE']
            ).first()
            ctx['user_reservation'] = Reservation.objects.filter(
                user=user, book=self.object, status__in=['ACTIVE', 'NOTIFIED']
            ).first()
        return ctx


class BookCreateView(LibrarianRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('book_list')

    def form_valid(self, form):
        messages.success(self.request, 'کتاب با موفقیت ثبت شد.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'ثبت کتاب جدید'
        return ctx


class BookUpdateView(LibrarianRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'

    def get_success_url(self):
        return reverse_lazy('book_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'اطلاعات کتاب ویرایش شد.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'ویرایش کتاب'
        return ctx


class BookDeleteView(LibrarianRequiredMixin, DeleteView):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('book_list')

    def form_valid(self, form):
        if self.object.loan_set.filter(status__in=['PENDING', 'ACTIVE']).exists():
            messages.error(self.request, 'این کتاب امانت فعال یا درخواست در انتظار دارد و حذف نمی‌شود.')
            return redirect('book_detail', pk=self.object.pk)
        messages.success(self.request, 'کتاب حذف شد.')
        return super().form_valid(form)
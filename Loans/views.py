from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import FormView, ListView
from Books.models import Book
from Users.mixins import LibrarianRequiredMixin, MemberRequiredMixin
from . import services
from .forms import RejectForm, ReturnForm
from .models import Loan, Reservation
from .services import LoanError


def _back(request, default):
    nxt = request.POST.get('next', '')
    if nxt and url_has_allowed_host_and_scheme(
        nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(nxt)
    return redirect(default)


class MemberActionView(MemberRequiredMixin, View):
    http_method_names = ['post']
    default_redirect = 'my_loans'

    def post(self, request, pk):
        obj = self.get_object(pk)
        try:
            message = self.perform(request, obj)
            messages.success(request, message)
        except LoanError as e:
            messages.error(request, str(e))
        return _back(request, self.default_redirect)


class LibrarianActionView(LibrarianRequiredMixin, View):
    http_method_names = ['post']
    default_redirect = 'loan_manage_list'

    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        try:
            message = self.perform(request, loan)
            messages.success(request, message)
        except LoanError as e:
            messages.error(request, str(e))
        return _back(request, self.default_redirect)


class MyLoansView(MemberRequiredMixin, ListView):
    template_name = 'loans/my_loans.html'
    context_object_name = 'loans'

    def get_queryset(self):
        qs = Loan.objects.filter(user=self.request.user).select_related('book')
        status = self.request.GET.get('status', '')
        if status in dict(Loan.STATUS_CHOICES):
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['status'] = self.request.GET.get('status', '')
        ctx['status_choices'] = Loan.STATUS_CHOICES
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['query_string'] = params.urlencode()
        ctx['unpaid_fines'] = Loan.objects.filter(
            user=user, fine_amount__gt=0, is_fine_paid=False
        ).aggregate(total=Sum('fine_amount'))['total'] or 0
        return ctx


class LoanRequestView(MemberRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        try:
            services.request_loan(request.user, book)
            messages.success(request, f'درخواست امانت «{book.title}» ثبت شد و منتظر تایید کتابدار است.')
        except LoanError as e:
            messages.error(request, str(e))
        return _back(request, reverse('book_detail', args=[book.pk]))


class RenewRequestView(MemberActionView):
    def get_object(self, pk):
        return get_object_or_404(Loan, pk=pk, user=self.request.user)

    def perform(self, request, loan):
        services.request_renewal(request.user, loan)
        return 'درخواست تمدید ثبت شد و منتظر تایید کتابدار است.'


class MyReservationsView(MemberRequiredMixin, ListView):
    template_name = 'loans/my_reservations.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return (
            Reservation.objects.filter(user=self.request.user, status__in=services.OPEN_RES)
            .select_related('book')
            .order_by('-reserved_at')
        )


class ReserveBookView(MemberRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        try:
            services.reserve_book(request.user, book)
            messages.success(request, f'کتاب «{book.title}» رزرو شد. با موجود شدن به شما اطلاع می‌دهیم.')
        except LoanError as e:
            messages.error(request, str(e))
        return _back(request, reverse('book_detail', args=[book.pk]))


class CancelReservationView(MemberActionView):
    default_redirect = 'my_reservations'

    def get_object(self, pk):
        return get_object_or_404(Reservation, pk=pk, user=self.request.user)

    def perform(self, request, reservation):
        services.cancel_reservation(request.user, reservation)
        return 'رزرو لغو شد.'

class LoanManageListView(LibrarianRequiredMixin, ListView):
    template_name = 'loans/loan_manage_list.html'
    context_object_name = 'loans'

    def get_queryset(self):
        qs = Loan.objects.select_related('user', 'book')
        status = self.request.GET.get('status', '')
        today = timezone.localdate()

        if status == 'OVERDUE':
            qs = qs.filter(status='ACTIVE', due_date__lt=today)
        elif status == 'RENEWAL':
            qs = qs.filter(status='ACTIVE', renewal_requested=True)
        elif status in dict(Loan.STATUS_CHOICES):
            qs = qs.filter(status=status)

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(user__username__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(book__title__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        ctx['q'] = self.request.GET.get('q', '')
        ctx['status'] = self.request.GET.get('status', '')
        ctx['status_choices'] = Loan.STATUS_CHOICES
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['query_string'] = params.urlencode()
        ctx['reject_form'] = RejectForm()
        ctx['pending_count'] = Loan.objects.filter(status='PENDING').count()
        ctx['renewal_pending_count'] = Loan.objects.filter(status='ACTIVE', renewal_requested=True).count()
        ctx['overdue_count'] = Loan.objects.filter(status='ACTIVE', due_date__lt=today).count()
        return ctx


class LoanApproveView(LibrarianActionView):
    def perform(self, request, loan):
        services.approve_loan(loan)
        return 'درخواست امانت تایید شد.'


class LoanRejectView(LibrarianActionView):
    def perform(self, request, loan):
        form = RejectForm(request.POST)
        if not form.is_valid():
            raise LoanError('برای رد درخواست باید دلیل را بنویسید.')
        services.reject_loan(loan, form.cleaned_data['reason'])
        return 'درخواست رد شد.'


class RenewApproveView(LibrarianActionView):
    def perform(self, request, loan):
        services.approve_renewal(loan)
        return 'تمدید تایید شد.'


class RenewRejectView(LibrarianActionView):
    def perform(self, request, loan):
        services.reject_renewal(loan)
        return 'درخواست تمدید رد شد.'


class FinePaidView(LibrarianActionView):
    def perform(self, request, loan):
        services.mark_fine_paid(loan)
        return 'پرداخت جریمه ثبت شد.'


class LoanReturnView(LibrarianRequiredMixin, FormView):
    form_class = ReturnForm
    template_name = 'loans/loan_return.html'

    def get_loan(self):
        if not hasattr(self, '_loan'):
            self._loan = get_object_or_404(
                Loan.objects.select_related('user', 'book'), pk=self.kwargs['pk']
            )
        return self._loan

    def get(self, request, *args, **kwargs):
        if self.get_loan().status != 'ACTIVE':
            messages.error(request, 'این امانت فعال نیست و بازگشت ندارد.')
            return redirect('loan_manage_list')
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        return {'fine_amount': self.get_loan().calculate_fine()}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['loan'] = self.get_loan()
        return ctx

    def form_valid(self, form):
        loan = self.get_loan()
        d = form.cleaned_data
        try:
            services.return_loan(
                loan,
                fine_amount=d['fine_amount'],
                is_damaged=d['is_damaged'],
                damage_notes=d['damage_notes'],
            )
        except LoanError as e:
            messages.error(self.request, str(e))
            return redirect('loan_manage_list')

        msg = f'بازگشت «{loan.book.title}» ثبت شد.'
        if d['fine_amount']:
            msg += f' جریمه‌ی ثبت‌شده: {d["fine_amount"]:,} تومان.'
        messages.success(self.request, msg)
        return redirect('loan_manage_list')
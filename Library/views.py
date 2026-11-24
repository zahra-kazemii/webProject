from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView
from datetime import timedelta
from Books.models import Book
from Loans.models import Loan
from Users.models import User


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()

        if not user.is_authenticated:
            return ctx

        if user.is_librarian:
            ctx['pending_count'] = Loan.objects.filter(status='PENDING').count()
            ctx['overdue_count'] = Loan.objects.filter(status='ACTIVE', due_date__lt=today).count()
            ctx['renewal_count'] = Loan.objects.filter(status='ACTIVE', renewal_requested=True).count()
            ctx['book_count'] = Book.objects.count()
            ctx['member_count'] = User.objects.filter(is_librarian=False).count()
        else:
            active = Loan.objects.filter(user=user, status='ACTIVE').select_related('book')
            ctx['active_count'] = active.count()
            soon = today + timedelta(days=settings.REMINDER_DAYS_BEFORE)
            ctx['due_soon'] = active.filter(due_date__lte=soon).order_by('due_date')
            ctx['unpaid_fines'] = Loan.objects.filter(
                user=user, fine_amount__gt=0, is_fine_paid=False
            ).aggregate(total=Sum('fine_amount'))['total'] or 0
        return ctx
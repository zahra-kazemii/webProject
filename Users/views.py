from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from .forms import RegisterForm
from .mixins import LibrarianRequiredMixin
from .models import User


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'ثبت‌نام با موفقیت انجام شد. خوش آمدید!')
        return redirect(self.success_url)


class MemberListView(LibrarianRequiredMixin, ListView):
    template_name = 'users/member_list.html'
    context_object_name = 'members'

    def get_queryset(self):
        qs = (
            User.objects.filter(is_librarian=False)
            .annotate(
                active_loans=Count('loan', filter=Q(loan__status='ACTIVE'), distinct=True)
            )
            .order_by('username')
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['query_string'] = params.urlencode()
        return ctx
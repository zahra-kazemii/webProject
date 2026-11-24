from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from Books.models import Book
from .models import Loan, Reservation

OPEN_LOAN = ['PENDING', 'ACTIVE']
OPEN_RES = ['ACTIVE', 'NOTIFIED']     


class LoanError(Exception):
    """خطای قانون کتابخانه؛ متن آن مستقیم به کاربر نشان داده می‌شود."""


def request_loan(user, book):
    """ثبت درخواست امانت توسط عضو (بعد از تایید کتابدار فعال می‌شود)."""
    if book.stock <= 0:
        raise LoanError('این کتاب فعلاً موجود نیست. می‌توانید آن را رزرو کنید.')

    if Loan.objects.filter(user=user, book=book, status__in=OPEN_LOAN).exists():
        raise LoanError('برای این کتاب قبلاً درخواست امانت دارید یا آن را امانت گرفته‌اید.')

    today = timezone.localdate()
    if Loan.objects.filter(user=user, status='ACTIVE', due_date__lt=today).exists():
        raise LoanError('شما کتاب دیرکرده دارید. ابتدا آن را بازگردانید.')

    if Loan.objects.filter(
        user=user, status='RETURNED', fine_amount__gt=0, is_fine_paid=False
    ).exists():
        raise LoanError('شما جریمه‌ی پرداخت‌نشده دارید. ابتدا جریمه را تسویه کنید.')

    if Loan.objects.filter(user=user, status__in=OPEN_LOAN).count() >= settings.MAX_ACTIVE_LOANS:
        raise LoanError(f'حداکثر {settings.MAX_ACTIVE_LOANS} امانت هم‌زمان مجاز است.')

    return Loan.objects.create(user=user, book=book)


def request_renewal(user, loan):
    """ثبت درخواست تمدید توسط عضو."""
    if loan.user_id != user.id:
        raise LoanError('این امانت متعلق به شما نیست.')
    if loan.status != 'ACTIVE':
        raise LoanError('فقط امانت‌های فعال قابل تمدید هستند.')
    if loan.is_overdue:
        raise LoanError('امانت دیرکرده قابل تمدید نیست؛ کتاب را بازگردانید.')
    if loan.renewal_requested:
        raise LoanError('درخواست تمدید شما قبلاً ثبت شده و منتظر بررسی است.')
    if loan.renewal_count >= settings.MAX_RENEWALS:
        raise LoanError(f'حداکثر {settings.MAX_RENEWALS} بار می‌توان تمدید کرد.')
    loan.renewal_requested = True
    loan.save(update_fields=['renewal_requested'])

@transaction.atomic
def approve_loan(loan):
    """تایید درخواست: موجودی یکی کم می‌شود و سررسید تعیین می‌شود."""
    loan = Loan.objects.select_for_update().select_related('user', 'book').get(pk=loan.pk)
    if loan.status != 'PENDING':
        raise LoanError('این درخواست قبلاً بررسی شده است.')

    book = Book.objects.select_for_update().get(pk=loan.book_id)
    if book.stock <= 0:
        raise LoanError('موجودی این کتاب تمام شده و امکان تایید نیست.')

    book.stock -= 1
    book.save(update_fields=['stock'])

    loan.status = 'ACTIVE'
    loan.due_date = timezone.localdate() + timedelta(days=settings.LOAN_DAYS)
    loan.save(update_fields=['status', 'due_date'])
    Reservation.objects.filter(
        user=loan.user, book=book, status__in=OPEN_RES
    ).update(status='FULFILLED')
    return loan


def reject_loan(loan, reason):
    if loan.status != 'PENDING':
        raise LoanError('این درخواست قبلاً بررسی شده است.')
    loan.status = 'REJECTED'
    loan.rejection_reason = reason
    loan.save(update_fields=['status', 'rejection_reason'])


def approve_renewal(loan):
    if loan.status != 'ACTIVE' or not loan.renewal_requested:
        raise LoanError('درخواست تمدیدی برای تایید وجود ندارد.')
    if Reservation.objects.filter(book=loan.book, status__in=OPEN_RES).exists():
        raise LoanError('این کتاب رزرو شده و قابل تمدید نیست.')
    loan.due_date = loan.due_date + timedelta(days=settings.RENEW_DAYS)
    loan.renewal_count += 1
    loan.renewal_requested = False
    loan.save(update_fields=['due_date', 'renewal_count', 'renewal_requested'])


def reject_renewal(loan):
    if not loan.renewal_requested:
        raise LoanError('درخواست تمدیدی وجود ندارد.')
    loan.renewal_requested = False
    loan.save(update_fields=['renewal_requested'])


def return_loan(loan, fine_amount, is_damaged=False, damage_notes=''):
    """ثبت بازگشت کتاب: موجودی یکی زیاد می‌شود و جریمه ثبت می‌شود."""
    with transaction.atomic():
        loan = Loan.objects.select_for_update().get(pk=loan.pk)
        if loan.status != 'ACTIVE':
            raise LoanError('این امانت فعال نیست.')

        book = Book.objects.select_for_update().get(pk=loan.book_id)
        book.stock += 1
        book.save(update_fields=['stock'])

        loan.status = 'RETURNED'
        loan.return_date = timezone.localdate()
        loan.renewal_requested = False
        loan.fine_amount = fine_amount
        loan.is_fine_paid = (fine_amount == 0)
        loan.is_damaged = is_damaged
        loan.damage_notes = damage_notes
        loan.save()

    notify_next_reservations(loan.book)
    return loan


def mark_fine_paid(loan):
    if loan.fine_amount <= 0 or loan.is_fine_paid:
        raise LoanError('جریمه‌ی پرداخت‌نشده‌ای برای این امانت وجود ندارد.')
    loan.is_fine_paid = True
    loan.save(update_fields=['is_fine_paid'])

def reserve_book(user, book):
    if book.stock > 0:
        raise LoanError('این کتاب موجود است؛ مستقیماً درخواست امانت بدهید.')
    if Loan.objects.filter(user=user, book=book, status__in=OPEN_LOAN).exists():
        raise LoanError('این کتاب را در حال حاضر امانت دارید.')
    if Reservation.objects.filter(user=user, book=book, status__in=OPEN_RES).exists():
        raise LoanError('شما قبلاً این کتاب را رزرو کرده‌اید.')
    return Reservation.objects.create(user=user, book=book)


def cancel_reservation(user, reservation):
    if reservation.user_id != user.id:
        raise LoanError('این رزرو متعلق به شما نیست.')
    if reservation.status not in OPEN_RES:
        raise LoanError('این رزرو دیگر فعال نیست.')
    reservation.status = 'CANCELLED'
    reservation.save(update_fields=['status'])
    notify_next_reservations(reservation.book)


def notify_next_reservations(book):
    """
    به نفرات اول صف رزرو (به تعداد نسخه‌های آزاد) اطلاع می‌دهد که کتاب موجود شد.
    ایمیل در حالت توسعه داخل ترمینال چاپ می‌شود.
    """
    book.refresh_from_db()
    already_notified = Reservation.objects.filter(book=book, status='NOTIFIED').count()
    free = book.stock - already_notified
    if free <= 0:
        return

    queue = Reservation.objects.filter(book=book, status='ACTIVE').select_related('user')[:free]
    for res in queue:
        res.status = 'NOTIFIED'
        res.save(update_fields=['status'])
        if res.user.email:
            send_mail(
                subject='کتاب رزروشده‌ی شما موجود شد',
                message=(
                    f'سلام {res.user.get_full_name() or res.user.username}،\n'
                    f'کتاب «{book.title}» که رزرو کرده بودید اکنون موجود است. '
                    f'لطفاً هرچه زودتر درخواست امانت بدهید.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[res.user.email],
                fail_silently=True,
            )
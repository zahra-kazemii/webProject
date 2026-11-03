from django.contrib import admin
from .models import Loan, Reservation

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'due_date', 'return_date')
    list_filter = ('status',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'reserved_at')
    list_filter = ('status',)
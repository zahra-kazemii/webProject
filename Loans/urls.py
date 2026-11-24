from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.MyLoansView.as_view(), name='my_loans'),
    path('request/<int:pk>/', views.LoanRequestView.as_view(), name='loan_request'),      
    path('<int:pk>/renew/', views.RenewRequestView.as_view(), name='loan_renew_request'),  
    path('reservations/', views.MyReservationsView.as_view(), name='my_reservations'),
    path('reserve/<int:pk>/', views.ReserveBookView.as_view(), name='reserve_book'),      
    path('reservations/<int:pk>/cancel/', views.CancelReservationView.as_view(), name='reservation_cancel'),

    path('manage/', views.LoanManageListView.as_view(), name='loan_manage_list'),
    path('manage/<int:pk>/approve/', views.LoanApproveView.as_view(), name='loan_approve'),
    path('manage/<int:pk>/reject/', views.LoanRejectView.as_view(), name='loan_reject'),
    path('manage/<int:pk>/renew-approve/', views.RenewApproveView.as_view(), name='renew_approve'),
    path('manage/<int:pk>/renew-reject/', views.RenewRejectView.as_view(), name='renew_reject'),
    path('manage/<int:pk>/return/', views.LoanReturnView.as_view(), name='loan_return'),
    path('manage/<int:pk>/fine-paid/', views.FinePaidView.as_view(), name='fine_paid'),
]
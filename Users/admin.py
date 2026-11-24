from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
    ('اطلاعات کتابخانه', {'fields': ('is_librarian', 'phone')}),
)
    
    list_display = ('username', 'email', 'is_librarian', 'is_staff')
    list_filter = ('is_librarian', 'is_staff')
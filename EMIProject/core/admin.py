from django.contrib import admin
from .models import Loan

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('name', 'principal', 'rate', 'tenure_months', 'start_date')

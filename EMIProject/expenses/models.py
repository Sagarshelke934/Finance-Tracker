from django.db import models
from django.utils import timezone
from datetime import date

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('FOO', 'Food'),
        ('TRA', 'Transport'),
        ('ENT', 'Entertainment'),
        ('BIL', 'Bills'),
        ('EMI', 'EMI'),
        ('OTH', 'Other'),
    ]

    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=3, choices=CATEGORY_CHOICES, default='OTH')
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"

    class Meta:
        ordering = ['-date']

class RecurringExpense(models.Model):
    FREQUENCY_CHOICES = [
        ('MON', 'Monthly'),
        ('WEK', 'Weekly'),
    ]
    
    TYPE_CHOICES = [
        ('BILL', 'Bill/Subscription'),
        ('SIP', 'SIP / Investment'),
    ]

    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recurrence_type = models.CharField(max_length=4, choices=TYPE_CHOICES, default='BILL')
    category = models.CharField(max_length=3, choices=Expense.CATEGORY_CHOICES, null=True, blank=True)
    frequency = models.CharField(max_length=3, choices=FREQUENCY_CHOICES, default='MON')
    
    # New Field: Fixed Payment Date (1-31)
    payment_date = models.IntegerField(default=1, help_text="Day of the month (1-31) when this is due")
    
    start_date = models.DateField(default=date.today)
    last_processed_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.get_frequency_display()})"

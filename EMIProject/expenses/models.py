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
    
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=3, choices=Expense.CATEGORY_CHOICES, default='OTH')
    frequency = models.CharField(max_length=3, choices=FREQUENCY_CHOICES, default='MON')
    start_date = models.DateField(default=date.today)
    last_processed_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.get_frequency_display()})"

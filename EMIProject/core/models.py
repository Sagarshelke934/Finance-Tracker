from django.db import models
from datetime import date
from decimal import Decimal

class Loan(models.Model):
    BENCHMARK_CHOICES = [
        ('NONE', 'No Benchmark'),
        ('HOME', 'Home Loan Benchmark'),
        ('PERS', 'Personal Loan Benchmark'),
        ('CAR', 'Car Loan Benchmark'),
    ]
    name = models.CharField(max_length=100)
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual Interest Rate in %")
    tenure_months = models.IntegerField(help_text="Loan Tenure in Months")
    start_date = models.DateField()
    external_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="ID from external provider like Experian")
    benchmark_type = models.CharField(max_length=10, choices=BENCHMARK_CHOICES, default='NONE')


    def calculate_emi(self):
        # EMI = [P x R x (1+R)^N]/[(1+R)^N-1]
        # R is monthly rate (annual / 12 / 100)
        p = self.principal
        r = (self.rate / 12) / 100
        n = self.tenure_months
        
        if r == 0:
            return p / n
            
        emi = (p * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
        return round(emi, 2)

    def total_payable(self):
        return self.calculate_emi() * self.tenure_months

    def total_interest(self):
        return self.total_payable() - self.principal

    def __str__(self):
        return self.name

    @classmethod
    def get_total_emi(cls):
        loans = cls.objects.all()
        return sum(loan.calculate_emi() for loan in loans)

class Saving(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.amount}"

class Investment(models.Model):
    CATEGORY_CHOICES = [
        ('STK', 'Stocks'),
        ('MF', 'Mutual Funds'),
        ('GLD', 'Gold'),
        ('FD', 'Fixed Deposit'),
        ('RE', 'Real Estate'),
        ('CRY', 'Crypto'),
        ('OTH', 'Other'),
    ]
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Invested Amount")
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Current Market Value")
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1.0)
    category = models.CharField(max_length=3, choices=CATEGORY_CHOICES, default='OTH')
    date = models.DateField()
    external_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="ID from external broker")

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    @classmethod
    def get_total_invested(cls):
        from django.db.models import Sum
        return cls.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    @classmethod
    def get_total_current_value(cls):
        from django.db.models import Sum
        return cls.objects.aggregate(Sum('current_value'))['current_value__sum'] or 0

class RecurringWealth(models.Model):
    TYPE_CHOICES = [
        ('SAV', 'Saving'),
        ('INV', 'Investment'),
    ]
    FREQUENCY_CHOICES = [
        ('MON', 'Monthly'),
        ('WEK', 'Weekly'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=3, choices=FREQUENCY_CHOICES, default='MON')
    category = models.CharField(max_length=3, choices=Investment.CATEGORY_CHOICES, blank=True, null=True)
    last_processed_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(default=date.today)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

class Document(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='documents/')
    expiry_date = models.DateField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def filename(self):
        return self.file.name.split('/')[-1]

    @property
    def is_image(self):
        ext = self.file.name.split('.')[-1].lower()
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']

    @property
    def is_pdf(self):
        ext = self.file.name.split('.')[-1].lower()
        return ext == 'pdf'


class Policy(models.Model):
    TYPE_CHOICES = [
        ('TERM', 'Term Insurance'),
        ('HEALTH', 'Health Insurance'),
        ('VEHICLE', 'Vehicle Insurance'),
        ('OTHER', 'Other'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='TERM')
    sum_assured = models.DecimalField(max_digits=12, decimal_places=2)
    premium = models.DecimalField(max_digits=12, decimal_places=2)
    premium_date = models.DateField(help_text="Next Premium Due Date")

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    @classmethod
    def get_total_sum_assured(cls):
        from django.db.models import Sum
        return cls.objects.aggregate(Sum('sum_assured'))['sum_assured__sum'] or 0
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manual_investment_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manual_policy_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manual_emi_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vault_pin = models.CharField(max_length=4, blank=True, null=True, help_text="4-digit PIN for Document Vault")

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Expense
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'list': 'expense-titles', 'autocomplete': 'off', 'placeholder': 'e.g. Lunch, Uber, Rent', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Expense Name',
            'amount': 'Amount (₹)',
            'date': 'Date of Expense',
        }

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    ordering = ['-date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum
        from datetime import date
        import calendar
        
        today = date.today()
        first_day = today.replace(day=1)
        _, last_day = calendar.monthrange(today.year, today.month)
        
        # Monthly Outflow
        month_total = Expense.objects.filter(date__gte=first_day).aggregate(Sum('amount'))['amount__sum'] or 0
        context['month_total'] = float(month_total)
        context['month_count'] = Expense.objects.filter(date__gte=first_day).count()
        
        # Burn Rate (Daily Average)
        context['daily_burn'] = float(month_total) / today.day if today.day > 0 else 0
        
        # Projection (Burn Rate * Days in Month)
        context['projected_total'] = context['daily_burn'] * last_day
        
        # Budget context (using user income if available)
        try:
            profile = self.request.user.userprofile
            income = float(profile.monthly_income)
            context['budget_percent'] = (float(month_total) / income * 100) if income > 0 else 0
        except:
            context['budget_percent'] = 0
            
        return context

from core.services.whatsapp import WhatsAppService

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expense_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Check for High Value Expense (Alert Threshold: ₹5,000)
        if self.object.amount >= 5000:
            try:
                wa = WhatsAppService()
                # send_alert handles the message format and target
                wa.send_alert(self.request.user, self.object.title, self.object.amount)
            except Exception as e:
                print(f"Failed to send alert: {e}")
                
        return response

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill from GET params (e.g. from Scan & Pay)
        title = self.request.GET.get('title')
        amount = self.request.GET.get('amount')
        
        if title:
            initial['title'] = title
        if amount:
            initial['amount'] = amount
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get unique titles from past expenses
        existing_titles = list(Expense.objects.values_list('title', flat=True).distinct())
        # Common defaults
        defaults = ['Lunch', 'Dinner', 'Groceries', 'Uber', 'Fuel', 'Rent', 'Electricity', 'Internet', 'Movies', 'Coffee', 'Medicine']
        
        context['suggested_titles'] = sorted(list(set(existing_titles + defaults)))
        context['page_title'] = 'Add New Expense'
        context['button_text'] = 'Save Expense'
        return context

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expense_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Expense'
        context['button_text'] = 'Update Expense'
        return context

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expense_list')

from .models import RecurringExpense

class RecurringExpenseForm(forms.ModelForm):
    class Meta:
        model = RecurringExpense
        fields = ['title', 'amount', 'recurrence_type', 'category', 'payment_date', 'frequency', 'start_date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Netflix, Rent'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'recurrence_type': forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleCategory(this)'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31, 'placeholder': 'Day (1-31)'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'margin-left: 0;'})
        }

class RecurringExpenseListView(LoginRequiredMixin, ListView):
    model = RecurringExpense
    template_name = 'expenses/recurring_list.html'
    context_object_name = 'recurring_expenses'
    ordering = ['-start_date']

class RecurringExpenseCreateView(LoginRequiredMixin, CreateView):
    model = RecurringExpense
    form_class = RecurringExpenseForm
    template_name = 'expenses/recurring_form.html'
    success_url = reverse_lazy('recurring_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add Recurring Expense'
        context['button_text'] = 'Setup Automation'
        return context

class RecurringExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = RecurringExpense
    form_class = RecurringExpenseForm
    template_name = 'expenses/recurring_form.html'
    success_url = reverse_lazy('recurring_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Recurring Expense'
        context['button_text'] = 'Update Automation'
        return context

class RecurringExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = RecurringExpense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('recurring_list')

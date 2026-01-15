from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django import forms
from expenses.models import Expense, RecurringExpense
from django.db.models import Sum
from .services.experian import ExperianService
from .services.broker import BrokerService
from .services.market_rates import MarketRatesService
from datetime import date, timedelta
from .models import Loan, Saving, Investment, RecurringWealth, Document, UserProfile, Policy
from decimal import Decimal
from django.http import JsonResponse
import json
from .chatbot import ChatBotService

class ChatBotView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            if not message:
                return JsonResponse({'response': 'Please say something!'}, status=400)
            
            bot = ChatBotService()
            response_text = bot.process_message(request.user, message)
            
            return JsonResponse({'response': response_text})
        except Exception as e:
            return JsonResponse({'response': 'Error processing message.'}, status=500)

from .services.whatsapp import WhatsAppService
from django.contrib import messages

class WhatsAppReportView(LoginRequiredMixin, View):
    def get(self, request):
        if not hasattr(request.user, 'profile') or not request.user.profile.phone_number:
            messages.error(request, "Please add your phone number in Profile to receive WhatsApp reports.")
            return redirect('home')
            
        # Aggregate Data for Report
        user = request.user
        
        # 1. Net Worth
        total_invested = Investment.get_total_current_value()
        total_savings = Saving.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        net_worth = total_invested + total_savings
        
        # 2. Monthly Expenses
        today = date.today()
        current_month_expenses = Expense.objects.filter(
            date__year=today.year,
            date__month=today.month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # 3. Recent Transactions
        recents = Expense.objects.order_by('-date')[:5]
        
        # 4. Budget Status (Simple check)
        income = request.user.profile.monthly_income
        budget_status = 'SAFE'
        if income > 0 and current_month_expenses > (income * Decimal('0.8')): # 80% warning
            budget_status = 'DANGER'
            
        context = {
            'net_worth': net_worth,
            'expenses': current_month_expenses,
            'recent': recents,
            'budget_status': budget_status
        }
        
        # Send Message
        service = WhatsAppService()
        success, msg = service.send_message(
            request.user.profile.phone_number, 
            service.generate_report_message(user, context)
        )
        
        if success:
            messages.success(request, f"Report sent to {request.user.profile.phone_number} on WhatsApp!")
        else:
            messages.error(request, f"Failed to send WhatsApp: {msg}")
            
        return redirect('home')

class WhatsAppTestView(LoginRequiredMixin, View):
    def get(self, request):
        service = WhatsAppService()
        # Test message to specific number as requested
        target = "+919130044796"
        msg = "🔔 FinTrack Test Alert: This is a test message sent via pywhatkit!"
        
        success, response = service.send_message(target, msg)
        
        if success:
            messages.success(request, f"Test alert triggered for {target}! Check the server browser.")
        else:
            messages.error(request, f"Failed to send test alert: {response}")
            
        return redirect('home')

class UpdateProfileValueView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Fields that can be updated
        fields = {
            'monthly_income': 'Monthly income',
            'manual_investment_total': 'Investment total',
            'manual_policy_total': 'Policy sum assured',
            'manual_emi_total': 'Monthly EMI'
        }
        
        updated_something = False
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        for field, label in fields.items():
            value = request.POST.get(field)
            if value is not None:
                try:
                    val = Decimal(value)
                    if val < 0:
                        messages.error(request, f"{label} cannot be negative.")
                        continue
                    
                    setattr(profile, field, val)
                    updated_something = True
                    messages.success(request, f"{label} updated to ₹{val:,.2f}!")
                except (ValueError, ArithmeticError):
                    messages.error(request, f"Please enter a valid numeric value for {label}.")
        
        if updated_something:
            profile.save()
            
        return redirect('home')
        return redirect('home')
class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    fields = ['title', 'file', 'expiry_date']
    template_name = 'core/document_form.html'
    success_url = reverse_lazy('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Upload Document'
        context['button_text'] = 'Upload to Vault'
        return context

class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'core/search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        
        if query:
            from django.db.models import Q
            # Search Expenses
            context['expenses'] = Expense.objects.filter(
                Q(title__icontains=query) | 
                Q(category__icontains=query)
            ).order_by('-date')[:10]
            
            # Search Documents
            context['documents'] = Document.objects.filter(
                Q(title__icontains=query)
            ).order_by('-uploaded_at')[:10]
            
            context['query'] = query
        
        return context

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home_v2.html'


    def get_context_data(self, **kwargs):
        # --- Passive Automation: Sync data on load ---
        self._passive_sync()
        self._process_recurring_wealth()
        self._process_recurring_expenses()
        
        context = super().get_context_data(**kwargs)
        # Summary Stats
        total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        total_savings = Saving.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        total_investments = Investment.get_total_invested()
        total_policies = Policy.get_total_sum_assured()
        
        # Calculate real EMI from Loan objects
        real_emi_total = Loan.get_total_emi()
        
        # Get User Profile for manual overrides (if needed, or use as fallback)
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)

        context['total_income'] = profile.monthly_income
        context['raw_total_income'] = profile.monthly_income
        
        context['total_expenses'] = total_expenses
        context['raw_total_expenses'] = total_expenses
        
        context['total_savings'] = total_savings
        
        # Investments
        context['total_investments'] = total_investments
        
        # Policies
        context['total_policies'] = total_policies
        
        # EMI
        context['total_monthly_emi'] = real_emi_total
        context['raw_total_emi'] = context['total_monthly_emi']
        
        # User Profile settings (Manual Overrides)
        try:
            user_profile = UserProfile.objects.get(user=self.request.user)
            total_income = user_profile.monthly_income
            manual_investments = user_profile.manual_investment_total
            manual_policies = user_profile.manual_policy_total
            manual_emi = user_profile.manual_emi_total
        except UserProfile.DoesNotExist:
            total_income = 0
            user_profile = None # Ensure user_profile is defined even if not found
            manual_investments = 0
            manual_policies = 0
            manual_emi = 0

        active_loans = Loan.objects.count()
        
        # Calculate total EMI roughly (sum of all loan EMIs)
        loans = Loan.objects.all()
        total_monthly_emi = sum([loan.calculate_emi() for loan in loans])
        
        # Total income from profile
        total_income = user_profile.monthly_income if user_profile else 0
        
        # Calculate Ideal Coverage benchmark (Open Source actuarial data)
        rates_service = MarketRatesService()
        market_insurance = rates_service.get_insurance_benchmarks()
        
        if total_income > 0:
            benchmark = market_insurance['term_insurance']
            ideal_coverage = float(total_income) * 12 * benchmark['ideal_coverage_multiplier']
        else:
            ideal_coverage = 10000000 # 1 Cr default
            
        # Logic: Always show actual calculated values for consistency
        # User requested sync with respective sections
        display_investments = total_investments
        display_emi = total_monthly_emi
        
        # Auto-benchmark Policies if no manual override is provided
        display_policies = manual_policies if manual_policies > 0 else ideal_coverage
        
        context['total_expenses'] = total_expenses
        context['active_loans'] = active_loans
        context['total_monthly_emi'] = display_emi
        context['total_savings'] = total_savings
        context['total_investments'] = display_investments
        context['total_policies'] = display_policies
        context['total_income'] = total_income
        
        # Raw data for forms/charts
        context['raw_total_income'] = float(total_income)
        context['raw_manual_investments'] = float(manual_investments)
        context['raw_manual_policies'] = float(manual_policies)
        context['raw_manual_emi'] = float(manual_emi)
        context['ideal_insurance_coverage'] = ideal_coverage
        
        context['raw_total_expenses'] = float(total_expenses)
        context['raw_total_emi'] = float(display_emi)
        context['raw_total_savings'] = float(total_savings)
        context['raw_total_investments'] = float(display_investments)
        
        # Recent activity
        context['recent_expenses'] = Expense.objects.order_by('-date')[:5]
        
        # --- Market Insights (Open Source Data) ---
        context['market_loans'] = rates_service.get_loan_benchmarks()
        context['market_insurance'] = market_insurance
        
        context['recent_savings'] = Saving.objects.order_by('-date')[:3]
        context['recent_investments'] = Investment.objects.order_by('-date')[:3]
        
        # Recurring Expenses
        context['recurring_expenses'] = RecurringExpense.objects.filter(is_active=True).order_by('start_date')

        # Chart Data: Expenses by Category
        category_stats = Expense.objects.values('category').annotate(total=Sum('amount')).order_by('-total')
        
        # Helper to get display name from category code
        category_dict = dict(Expense.CATEGORY_CHOICES)
        
        chart_labels = []
        chart_data = []
        
        for stat in category_stats:
            cat_code = stat['category']
            chart_labels.append(category_dict.get(cat_code, cat_code))
            chart_data.append(float(stat['total']))
            
        context['chart_labels'] = chart_labels
        context['chart_data'] = chart_data
        
        # Chart Data: Portfolio (Savings vs Investments)
        portfolio_labels = ['Savings', 'Investments']
        portfolio_data = [float(total_savings), float(total_investments)]
        
        context['portfolio_labels'] = portfolio_labels
        context['portfolio_data'] = portfolio_data
        
        # --- Budget Alerts Logic ---
        budget_alerts = []
        
        # Calculate Category Totals for Alerts
        needs_total = 0
        wants_total = 0
        
        # Define categories mapping (Ensure these match your Expense model choices)
        NEEDS_CATEGORIES = ['RENT', 'EMI', 'BILLS', 'GROCERIES', 'FUEL', 'INSURANCE', 'HEALTH', 'EDUCATION']
        WANTS_CATEGORIES = ['FOOD', 'SHOPPING', 'TRAVEL', 'ENTERTAINMENT', 'SUBSCRIPTION', 'GIFT']
        
        for stat in category_stats:
            cat = stat['category']
            amt = float(stat['total'])
            if cat in NEEDS_CATEGORIES:
                needs_total += amt
            elif cat in WANTS_CATEGORIES:
                wants_total += amt
                
        # Thresholds
        income_float = float(total_income)
        needs_limit = income_float * 0.50
        wants_limit = income_float * 0.30
        
        if income_float > 0:
            if needs_total > needs_limit:
                excess = needs_total - needs_limit
                budget_alerts.append({
                    'type': 'critical',
                    'title': 'Needs Budget Exceeded',
                    'message': f'You have spent ₹{needs_total:,.0f} on Needs, exceeding the 50% limit (₹{needs_limit:,.0f}) by ₹{excess:,.0f}.'
                })
            
            if wants_total > wants_limit:
                excess = wants_total - wants_limit
                budget_alerts.append({
                    'type': 'warning',
                    'title': 'Wants Budget Exceeded',
                    'message': f'You have spent ₹{wants_total:,.0f} on Wants, exceeding the 30% limit (₹{wants_limit:,.0f}) by ₹{excess:,.0f}.'
                })
                
        context['budget_alerts'] = budget_alerts
        
        # JSON versions for lists
        context['recent_savings_json'] = [
            {'name': s.name, 'amount': str(s.amount)} 
            for s in context['recent_savings']
        ]
        context['recent_investments_json'] = [
            {'name': i.name, 'amount': str(i.amount), 'category_display': i.get_category_display()} 
            for i in context['recent_investments']
        ]
        context['recent_expenses_json'] = [
            {'title': e.title, 'amount': str(e.amount), 'category_display': e.get_category_display(), 'date': e.date.isoformat()} 
            for e in context['recent_expenses']
        ]

        # --- 50-30-20 Rule Calculation ---
        # --- 50-30-20 Rule Calculation ---
        # UserProfile is already imported from core.models
        from core.utils.budget_calculator import (
            calculate_ideal_budget,
            calculate_actual_spending,
            get_budget_alerts,
            calculate_budget_percentages
        )
        
        user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        monthly_income = float(user_profile.monthly_income) if user_profile else 0
        
        # Categorization mapping
        needs_cats = ['BIL', 'TRA', 'EMI', 'FOO']
        wants_cats = ['ENT', 'OTH']
        
        # Current month's data
        first_day = date.today().replace(day=1)
        
        # Calculate ideal and actual budgets
        ideal = calculate_ideal_budget(monthly_income)
        actual = calculate_actual_spending(
            Expense.objects,
            Saving.objects,
            Investment.objects,
            needs_cats,
            wants_cats,
            first_day
        )
        
        # Generate alerts
        alerts = get_budget_alerts(actual, ideal) if monthly_income > 0 else []
        
        # Calculate percentages
        percentages = calculate_budget_percentages(actual, monthly_income)

        context['budget_analysis'] = {
            'income': monthly_income,
            'needs': actual['needs'],
            'wants': actual['wants'],
            'savings': actual['savings'],
            'ideal': ideal,
            'percentages': percentages,
            'alerts': alerts
        }
        
        # --- Historical Trends (Last 6 Months) ---
        context['budget_trends'] = self._get_monthly_trends(monthly_income, needs_cats, wants_cats)
        
        # Groww-style Charts
        context['net_worth_trend'] = self._get_net_worth_trend()
        context['radar_chart'] = self._get_expense_radar()
        context['upcoming_reminders'] = self._get_upcoming_reminders()
        context['recent_documents'] = Document.objects.order_by('-uploaded_at')[:3]
        
        return context
    
    def _get_monthly_trends(self, monthly_income: float, needs_cats: list, wants_cats: list) -> dict:
        """Calculate budget performance for last 6 months"""
        from dateutil.relativedelta import relativedelta
        from core.utils.budget_calculator import calculate_actual_spending, calculate_ideal_budget
        
        trends = {
            'months': [],
            'needs': [],
            'wants': [],
            'savings': [],
            'ideal_needs': [],
            'ideal_wants': [],
            'ideal_savings': []
        }
        
        today = date.today()
        ideal = calculate_ideal_budget(monthly_income)
        
        for i in range(5, -1, -1):  # Last 6 months
            month_date = today - relativedelta(months=i)
            first_day = month_date.replace(day=1)
            
            # Calculate last day of month
            if month_date.month == 12:
                last_day = month_date.replace(day=31)
            else:
                next_month = month_date.replace(day=1) + relativedelta(months=1)
                last_day = next_month - relativedelta(days=1)
            
            # Get actual spending for this month
            actual = calculate_actual_spending(
                Expense.objects.filter(date__gte=first_day, date__lte=last_day),
                Saving.objects.filter(date__gte=first_day, date__lte=last_day),
                Investment.objects.filter(date__gte=first_day, date__lte=last_day),
                needs_cats,
                wants_cats,
                first_day
            )
            
            trends['months'].append(month_date.strftime('%b %Y'))
            trends['needs'].append(actual['needs'])
            trends['wants'].append(actual['wants'])
            trends['savings'].append(actual['savings'])
            trends['ideal_needs'].append(ideal['needs'])
            trends['ideal_wants'].append(ideal['wants'])
            trends['ideal_savings'].append(ideal['savings'])
        
        return trends

    def _passive_sync(self):
        """
        Silently syncs data from Experian and Broker to keep the dashboard automated.
        Also updates valuations based on live market prices.
        """
        mr_service = MarketRatesService()
        
        # 1. Sync Loans (Experian) & Update Market Benchmarks
        try:
            exp_service = ExperianService()
            loan_data = exp_service.fetch_user_trades()
            market_benchmarks = mr_service.get_loan_benchmarks()
            
            # Sync New Loans
            for trade in loan_data.get('trades', []):
                ext_id = trade.get('tradeId')
                if not Loan.objects.filter(external_id=ext_id).exists():
                    Loan.objects.create(
                        name=f"{trade.get('accountType')} ({trade.get('accountNumber')[-4:]})",
                        principal=trade.get('originalAmount'),
                        rate=trade.get('interestRate'),
                        tenure_months=trade.get('tenureMonths'),
                        start_date=trade.get('openDate'),
                        external_id=ext_id
                    )
            
            # Update Benchmark-linked Rates
            for loan in Loan.objects.exclude(benchmark_type='NONE'):
                if loan.benchmark_type == 'HOME' and 'home_loan' in market_benchmarks:
                    loan.rate = Decimal(str(market_benchmarks['home_loan']['rate']))
                    loan.save()
                elif loan.benchmark_type == 'PERS' and 'personal_loan' in market_benchmarks:
                    loan.rate = Decimal(str(market_benchmarks['personal_loan']['rate']))
                    loan.save()
        except Exception:
            pass 

        # 2. Sync Investments (Broker) & Update Valuations
        try:
            broker_service = BrokerService()
            inv_data = broker_service.fetch_portfolio()
            for holding in inv_data.get('holdings', []):
                sym = holding.get('symbol')
                ext_id = holding.get('isin') or sym
                
                # Check for existing investment
                existing = Investment.objects.filter(external_id=ext_id).first()
                if existing:
                    # Update valuation: current_value = Quantity * Current Price
                    curr_price = Decimal(str(holding.get('current_price', 0)))
                    existing.current_value = existing.quantity * curr_price
                    existing.save()
                else:
                    # Create new investment
                    # For new ones, we assume standard unit for simplicity unless broker data provides it
                    inv_amt = Decimal(str(holding.get('invested_amount')))
                    Investment.objects.create(
                        name=holding.get('name'),
                        amount=inv_amt,
                        current_value=inv_amt, # Initial value same as invested
                        quantity=Decimal(str(holding.get('quantity', 1))),
                        category=holding.get('type'),
                        date=holding.get('purchase_date'),
                        external_id=ext_id
                    )
        except Exception:
            pass

    def _process_recurring_expenses(self):
        """
        Checks for due Recurring Expenses/SIPs and creates them automatically.
        Uses 'payment_date' (1-31) to determine due day.
        """
        from expenses.models import RecurringExpense, Expense
        recurring_items = RecurringExpense.objects.filter(is_active=True)
        today = date.today()
        
        for item in recurring_items:
            # Check if processed this month
            if item.last_processed_date and item.last_processed_date.month == today.month and item.last_processed_date.year == today.year:
                continue

            # Check if today is the payment date (or past it if we missed it this month)
            # We simple check if today.day >= payment_date
            # Real logic might be more complex (handle Feb 30 etc), but simple >= implies we execute once per month
            
            should_run = False
            
            # Simple Logic: Run if we haven't run this month AND today >= payment_date
            if today.day >= item.payment_date:
                should_run = True
            
            if should_run:
                if item.recurrence_type == 'SIP':
                    # Create Investment
                    Investment.objects.create(
                        name=f"{item.title} (Auto SIP)",
                        amount=item.amount,
                        category='OTH', # Default or map if added to model
                        date=today,
                        external_id=f"SIP-{item.id}-{today.isoformat()}"
                    )
                else:
                    # Create Expense
                    Expense.objects.create(
                        title=f"{item.title} (Auto)",
                        amount=item.amount,
                        category=item.category or 'OTH',
                        date=today
                    )
                
                # Update last processed
                item.last_processed_date = today
                item.save()

    def _get_net_worth_trend(self):
        """
        Calculates Net Worth (Savings + Invest - Loans) for the last 6 months.
        Note: Simplification for demo. In a real app, we'd need historical snapshots.
        Here we simulate trend by random fluctuation around current value for demo purposes.
        """
        from datetime import timedelta
        import random
        
        current_savings = Saving.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        current_invest = Investment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        current_loans = Loan.objects.aggregate(Sum('principal'))['principal__sum'] or 0
        
        current_net_worth = float(current_savings + current_invest - current_loans)
        
        labels = []
        data = []
        today = date.today()
        
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=i*30)
            labels.append(month_date.strftime('%b'))
            
            # Simulate historical data (creating a realistic growth curve)
            # Factor: slightly less wealth in the past
            factor = 1.0 - (i * 0.05) + (random.uniform(-0.02, 0.02))
            value = max(0, current_net_worth * factor)
            data.append(round(value, 2))
            
        return {'labels': labels, 'data': data}

    def _get_expense_radar(self):
        """
        Prepares data for Polar Area chart (Spending Radar).
        """
        category_stats = Expense.objects.values('category').annotate(total=Sum('amount')).order_by('-total')
        category_dict = dict(Expense.CATEGORY_CHOICES)
        
        labels = []
        data = []
        
        # Limit to top 5 categories for Radar readability
        for stat in category_stats[:5]:
            labels.append(category_dict.get(stat['category']))
            data.append(float(stat['total']))
            
        return {'labels': labels, 'data': data}

    def _get_upcoming_reminders(self):
        """
        Fetches upcoming payments from Loans and Recurring Expenses.
        Returns a sorted list of dicts: {title, amount, date, type, days_left}
        """
        reminders = []
        today = date.today()
        
        # 1. Loans (Assume EMI due on 5th of every month for simple demo, or use a field)
        # For this demo, let's assume EMI is due 30 days from last payment or creation.
        # We'll just generate a dummy "Next Date" based on today for active loans to show logic.
        active_loans = Loan.objects.all() # In real app, filter active=True
        for loan in active_loans:
            # Logic: Due date is assumed to be 1st of next month for simplicity
            next_month = today.replace(day=1) + timedelta(days=32)
            due_date = next_month.replace(day=5) # Bills usually due on 5th
            
            days_left = (due_date - today).days
            if 0 <= days_left <= 30:
                reminders.append({
                    'title': f"{loan.name} EMI",
                    'amount': loan.calculate_emi(),
                    'date': due_date,
                    'type': 'loan',
                    'days_left': days_left
                })

        # 2. Recurring Expenses
        from expenses.models import RecurringExpense
        recurring = RecurringExpense.objects.filter(is_active=True)
        for item in recurring:
            last_date = item.last_processed_date or item.start_date
            # Simple frequency logic
            delta = timedelta(days=30) if item.frequency == 'MON' else timedelta(days=7)
            next_due = last_date + delta
            
            # If next_due is in past (missed), move it to today or future
            if next_due < today:
                next_due = today 
            
            days_left = (next_due - today).days
            
            if 0 <= days_left <= 30:
                reminders.append({
                    'title': item.title,
                    'amount': item.amount,
                    'date': next_due,
                    'type': 'expense',
                    'days_left': days_left
                })
        
        # Sort by nearest date
        reminders.sort(key=lambda x: x['days_left'])
        return reminders[:5] # Top 5

    def _process_recurring_wealth(self):
        """
        Checks for due SIPs/Recurring Savings and creates items automatically.
        """
        recurring_items = RecurringWealth.objects.filter(active=True)
        today = date.today()
        
        for item in recurring_items:
            # Determine reference date
            ref_date = item.last_processed_date or item.start_date
            
            # Simple frequency logic: Monthly (30 days) or Weekly (7 days)
            days_diff = (today - ref_date).days
            due = False
            
            if item.frequency == 'MON' and days_diff >= 30:
                due = True
            elif item.frequency == 'WEK' and days_diff >= 7:
                due = True
            
            if due:
                # Create the entry
                if item.type == 'SAV':
                    Saving.objects.create(
                        name=f"{item.name} (Auto)",
                        amount=item.amount,
                        date=today
                    )
                else:
                    Investment.objects.create(
                        name=f"{item.name} (Auto SIP)",
                        amount=item.amount,
                        category=item.category or 'OTH',
                        date=today,
                        external_id=f"RECUR-{item.id}-{today.isoformat()}"
                    )
                
                # Update last processed
                item.last_processed_date = today
                item.save()

class EMICalculatorView(TemplateView):
    template_name = 'core/emi_calculator_v2.html'

    def post(self, request):
        context = {}
        try:
            principal = float(request.POST.get('principal', 0))
            rate = float(request.POST.get('rate', 0))
            tenure = int(request.POST.get('tenure', 0))
            
            if principal and rate and tenure:
                r = (rate / 12) / 100
                n = tenure * 12 # Convert Years to Months
                
                emi = (principal * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
                
                context['emi'] = round(emi, 2)
                context['total_payment'] = round(emi * n, 2)
                context['total_interest'] = round((emi * n) - principal, 2)
                context['principal'] = principal
                context['rate'] = rate
                context['tenure'] = tenure
        except ValueError:
            context['error'] = "Invalid input. Please check your numbers."
            
        return render(request, self.template_name, context)

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django import forms

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['name', 'principal', 'rate', 'tenure_months', 'start_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'principal': forms.NumberInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'tenure_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'name': 'Loan Name (e.g. Home Loan)',
            'principal': 'Principal Amount (₹)',
            'rate': 'Interest Rate (% p.a)',
            'tenure_months': 'Tenure (Months)',
            'start_date': 'Start Date',
        }

class LoanCreateView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanForm
    template_name = 'core/loan_form.html'
    success_url = reverse_lazy('loan_list')

class LoanUpdateView(LoginRequiredMixin, UpdateView):
    model = Loan
    form_class = LoanForm
    template_name = 'core/loan_form.html'
    success_url = reverse_lazy('loan_list')

class LoanDeleteView(LoginRequiredMixin, DeleteView):
    model = Loan
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('loan_list')

class SavingForm(forms.ModelForm):
    class Meta:
        model = Saving
        fields = ['name', 'amount', 'date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'name': 'Saving Name (e.g. Emergency Fund)',
            'amount': 'Amount (₹)',
            'date': 'Date Saved',
        }

class SavingCreateView(LoginRequiredMixin, CreateView):
    model = Saving
    form_class = SavingForm
    template_name = 'core/saving_form.html'
    success_url = reverse_lazy('saving_list')

class SavingUpdateView(LoginRequiredMixin, UpdateView):
    model = Saving
    form_class = SavingForm
    template_name = 'core/saving_form.html'
    success_url = reverse_lazy('saving_list')

class SavingDeleteView(LoginRequiredMixin, DeleteView):
    model = Saving
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('saving_list')

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['name', 'amount', 'category', 'quantity', 'date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'name': 'Investment Name',
            'amount': 'Invested Amount (₹)',
            'category': 'Asset Class',
            'quantity': 'Units / Quantity',
            'date': 'Investment Date',
        }

class InvestmentCreateView(LoginRequiredMixin, CreateView):
    model = Investment
    form_class = InvestmentForm
    template_name = 'core/investment_form.html'
    success_url = reverse_lazy('investment_list')

class InvestmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Investment
    form_class = InvestmentForm
    template_name = 'core/investment_form.html'
    success_url = reverse_lazy('investment_list')

class InvestmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Investment
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('investment_list')

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = ['name', 'type', 'sum_assured', 'premium', 'premium_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'sum_assured': forms.NumberInput(attrs={'class': 'form-control'}),
            'premium': forms.NumberInput(attrs={'class': 'form-control'}),
            'premium_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'name': 'Policy Name',
            'type': 'Insurance Type',
            'sum_assured': 'Sum Assured (₹)',
            'premium': 'Premium Amount (₹)',
            'premium_date': 'Next Due Date',
        }


class InvestmentSyncView(LoginRequiredMixin, View):
    def get(self, request):
        service = BrokerService()
        try:
            data = service.fetch_portfolio()
            holdings = data.get('holdings', [])
            
            # CLEAR OLD DATA to ensure clean state and correct totals
            Investment.objects.all().delete()
            
            count = 0
            updated = 0
            
            for holding in holdings:
                # Use ISIN or Symbol as external ID
                external_id = holding.get('isin') or holding.get('symbol')
                
                # Check for existing investment
                existing = Investment.objects.filter(external_id=external_id).first()
                
                if existing:
                    # Update valuation AND invested amount (to correct old data)
                    curr_price = Decimal(str(holding.get('current_price', 0)))
                    existing.current_value = existing.quantity * curr_price
                    
                    # Update amount if provided in sync data to ensure "positive" resets
                    if holding.get('invested_amount'):
                        existing.amount = Decimal(str(holding.get('invested_amount')))
                        
                    existing.save()
                    updated += 1
                else:
                    inv_amt = Decimal(str(holding.get('invested_amount')))
                    curr_price = Decimal(str(holding.get('current_price', 0))) # Ensure we get current price
                    quantity = Decimal(str(holding.get('quantity', 1)))
                    
                    Investment.objects.create(
                        name=holding.get('name'),
                        amount=inv_amt,
                        current_value=quantity * curr_price, # Set initial current value
                        quantity=quantity,
                        category=holding.get('type'),
                        date=holding.get('purchase_date'),
                        external_id=external_id
                    )
                    count += 1
            
            if count > 0 or updated > 0:
                messages.success(request, f"Synced: {count} new, {updated} updated.")
            else:
                messages.info(request, "Portfolio is up to date.")
                
        except Exception as e:
            messages.error(request, f"Failed to sync with Broker: {str(e)}")
            
        return redirect('investment_list')

class ExperianSyncView(LoginRequiredMixin, View):
    def post(self, request):
        service = ExperianService()
        try:
            # In a real app, you might pass user-specific data here
            data = service.fetch_user_trades()
            
            trades = data.get('trades', [])
            count = 0
            
            for trade in trades:
                # Check if loan already exists
                external_id = trade.get('tradeId')
                if not Loan.objects.filter(external_id=external_id).exists():
                    Loan.objects.create(
                        name=f"{trade.get('accountType')} ({trade.get('accountNumber')[-4:]})",
                        principal=trade.get('originalAmount'),
                        rate=trade.get('interestRate'),
                        tenure_months=trade.get('tenureMonths'),
                        start_date=trade.get('openDate'),
                        external_id=external_id
                    )
                    count += 1
            
            if count > 0:
                messages.success(request, f"Successfully synced {count} loans from Experian.")
            else:
                messages.info(request, "No new loans found from Experian.")
                
        except Exception as e:
            messages.error(request, f"Failed to sync with Experian: {str(e)}")
            
        return redirect('home')
class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum
        from datetime import date, timedelta
        import calendar
        from dateutil.relativedelta import relativedelta
        
        # --- 1. Expense Breakdown (Pie/Doughnut) ---
        expenses = Expense.objects.all()
        category_data = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        context['pie_chart'] = {
            'labels': [dict(Expense.CATEGORY_CHOICES).get(item['category'], item['category']) for item in category_data],
            'data': [float(item['total']) for item in category_data]
        }

        # --- 2. Monthly Trends (Bar Chart) ---
        # Last 6 months
        today = date.today()
        labels = []
        income_data = []
        expense_data = []
        
        user_profile = self.request.user.userprofile
        # Fallback income if 0
        monthly_income = float(user_profile.monthly_income) if user_profile.monthly_income > 0 else 50000 

        for i in range(5, -1, -1):
            date_cursor = today - relativedelta(months=i)
            month_start = date_cursor.replace(day=1)
            # End of month
            _, last_day = calendar.monthrange(month_start.year, month_start.month)
            month_end = month_start.replace(day=last_day)
            
            labels.append(month_start.strftime('%b'))
            
            # Sum expenses for this month
            month_exp = Expense.objects.filter(date__gte=month_start, date__lte=month_end).aggregate(Sum('amount'))['amount__sum'] or 0
            expense_data.append(float(month_exp))
            income_data.append(monthly_income) # Using fixed income for now

        context['bar_chart'] = {
            'labels': labels,
            'income': income_data,
            'expenses': expense_data
        }

        # --- 3. EMI/Loan Distribution (Doughnut) ---
        loans = Loan.objects.all()
        context['emi_chart'] = {
            'labels': [l.name for l in loans],
            'data': [float(l.principal) for l in loans]
        }

        # --- 4. Portfolio Growth (Line Chart) ---
        # Cumulative invested amount over last 6 months
        stock_labels = []
        stock_data = []
        
        # Determine total invested BEFORE the 6 month window
        start_of_window = (today - relativedelta(months=5)).replace(day=1)
        base_invested = Investment.objects.filter(date__lt=start_of_window).aggregate(Sum('amount'))['amount__sum'] or 0
        running_total = float(base_invested)

        for i in range(5, -1, -1):
            date_cursor = today - relativedelta(months=i)
            month_start = date_cursor.replace(day=1)
            _, last_day = calendar.monthrange(month_start.year, month_start.month)
            month_end = month_start.replace(day=last_day)
            
            stock_labels.append(month_start.strftime('%b'))
            
            # Add investments made IN this month to running total
            month_inv = Investment.objects.filter(date__gte=month_start, date__lte=month_end).aggregate(Sum('amount'))['amount__sum'] or 0
            running_total += float(month_inv)
            stock_data.append(running_total)

        context['stock_chart'] = {
            'labels': stock_labels,
            'data': stock_data, 
            'label': 'Invested Capital'
        }

        return context

class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'core/loan_list.html'
    context_object_name = 'loans'
    ordering = ['-start_date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loans = context['loans']
        context['total_principal'] = sum(loan.principal for loan in loans)
        context['total_monthly_emi'] = Loan.get_total_emi()
        return context

class SavingListView(LoginRequiredMixin, ListView):
    model = Saving
    template_name = 'core/saving_list.html'
    context_object_name = 'savings'
    ordering = ['-date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        savings = context['savings']
        context['total_savings'] = sum(saving.amount for saving in savings)
        return context

class InvestmentListView(LoginRequiredMixin, ListView):
    model = Investment
    template_name = 'core/investment_list.html'
    context_object_name = 'investments'
    ordering = ['-date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        investments = context['investments']
        total_invested = Investment.get_total_invested()
        current_val = Investment.get_total_current_value()
        
        context['total_invested'] = total_invested
        context['current_value'] = current_val
        
        if total_invested > 0:
            context['returns_pct'] = ((current_val - total_invested) / total_invested) * 100
        else:
            context['returns_pct'] = 0
        return context

class PolicyListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = 'core/policy_list.html'
    context_object_name = 'policies'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        
        # Calculate totals from real Policy objects
        # Calculate totals from real Policy objects
        context['policy_total'] = Policy.get_total_sum_assured()
        
        # Benchmarking data
        rates_service = MarketRatesService()
        context['market_insurance'] = rates_service.get_insurance_benchmarks()
        
        if profile.monthly_income > 0:
            benchmark = context['market_insurance']['term_insurance']
            context['ideal_coverage'] = float(profile.monthly_income) * 12 * benchmark['ideal_coverage_multiplier']
        else:
            context['ideal_coverage'] = 10000000
            
        return context

class PolicyCreateView(LoginRequiredMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'core/policy_form.html'
    success_url = reverse_lazy('policy_list')

class PolicyUpdateView(LoginRequiredMixin, UpdateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'core/policy_form.html'
    success_url = reverse_lazy('policy_list')

class PolicyDeleteView(LoginRequiredMixin, DeleteView):
    model = Policy
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('policy_list')

# --- Document Vault Security ---
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin

class VaultAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        # 1. Setup PIN if not exists
        if not profile.vault_pin:
            return redirect('vault_setup')
            
        # 2. Check Session Lock
        if not request.session.get('vault_unlocked', False):
            return redirect('vault_unlock')
            
        return super().dispatch(request, *args, **kwargs)

class VaultUnlockView(LoginRequiredMixin, FormView):
    template_name = 'core/vault_unlock.html'
    success_url = reverse_lazy('document_list')
    
    class UnlockForm(forms.Form):
        pin = forms.CharField(max_length=4, widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter 4-digit PIN',
            'pattern': '[0-9]*', 
            'inputmode': 'numeric',
            'maxlength': '4',
            'style': 'text-align: center; letter-spacing: 12px; font-size: 1.5rem;'
        }))

    form_class = UnlockForm

    def form_valid(self, form):
        pin = form.cleaned_data['pin']
        profile = self.request.user.userprofile
        if pin == profile.vault_pin:
            self.request.session['vault_unlocked'] = True
            return super().form_valid(form)
        else:
            form.add_error('pin', 'Incorrect PIN')
            return self.form_invalid(form)

class VaultSetupView(LoginRequiredMixin, FormView):
    template_name = 'core/vault_setup.html'
    success_url = reverse_lazy('document_list')
    
    class SetupForm(forms.Form):
        pin = forms.CharField(max_length=4, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create 4-digit PIN', 'pattern': '[0-9]*', 'inputmode': 'numeric', 'maxlength': '4', 'style': 'text-align: center; letter-spacing: 8px; font-size: 1.2rem;'}))
        confirm_pin = forms.CharField(max_length=4, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm PIN', 'pattern': '[0-9]*', 'inputmode': 'numeric', 'maxlength': '4','style': 'text-align: center; letter-spacing: 8px; font-size: 1.2rem;'}))
        
        def clean(self):
            cleaned_data = super().clean()
            pin = cleaned_data.get("pin")
            confirm_pin = cleaned_data.get("confirm_pin")

            if pin and confirm_pin and pin != confirm_pin:
                self.add_error('confirm_pin', "PINs do not match")

    form_class = SetupForm

    def form_valid(self, form):
        pin = form.cleaned_data['pin']
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        profile.vault_pin = pin
        profile.save()
        self.request.session['vault_unlocked'] = True
        return super().form_valid(form)

class DocumentListView(VaultAccessMixin, ListView):
    model = Document
    template_name = 'core/document_list.html'
    context_object_name = 'documents'
    ordering = ['-uploaded_at']

class DocumentDetailView(VaultAccessMixin, DetailView):
    model = Document
    template_name = 'core/document_detail.html'
    context_object_name = 'doc'

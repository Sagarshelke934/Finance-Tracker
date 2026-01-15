"""
Unit tests for budget calculator utility
"""
from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal
from core.utils.budget_calculator import (
    calculate_ideal_budget,
    calculate_actual_spending,
    get_budget_alerts,
    calculate_budget_percentages
)
from expenses.models import Expense
from core.models import Saving, Investment


class BudgetCalculatorTests(TestCase):
    """Test suite for budget calculation functions"""
    
    def test_calculate_ideal_budget_standard(self):
        """Test ideal budget calculation with standard income"""
        income = 100000
        ideal = calculate_ideal_budget(income)
        
        self.assertEqual(ideal['needs'], 50000)
        self.assertEqual(ideal['wants'], 30000)
        self.assertEqual(ideal['savings'], 20000)
    
    def test_calculate_ideal_budget_zero_income(self):
        """Test ideal budget calculation with zero income"""
        income = 0
        ideal = calculate_ideal_budget(income)
        
        self.assertEqual(ideal['needs'], 0)
        self.assertEqual(ideal['wants'], 0)
        self.assertEqual(ideal['savings'], 0)
    
    def test_calculate_ideal_budget_decimal(self):
        """Test ideal budget calculation with decimal income"""
        income = 75500.50
        ideal = calculate_ideal_budget(income)
        
        self.assertAlmostEqual(ideal['needs'], 37750.25, places=2)
        self.assertAlmostEqual(ideal['wants'], 22650.15, places=2)
        self.assertAlmostEqual(ideal['savings'], 15100.10, places=2)
    
    def test_calculate_actual_spending_with_data(self):
        """Test actual spending calculation with sample data"""
        # Create test data
        today = date.today()
        first_day = today.replace(day=1)
        
        Expense.objects.create(title='Rent', amount=20000, category='BIL', date=today)
        Expense.objects.create(title='Groceries', amount=5000, category='FOO', date=today)
        Expense.objects.create(title='Movies', amount=1000, category='ENT', date=today)
        Saving.objects.create(name='Emergency Fund', amount=10000, date=today)
        Investment.objects.create(name='Stocks', amount=5000, category='STK', date=today)
        
        needs_cats = ['BIL', 'TRA', 'EMI', 'FOO']
        wants_cats = ['ENT', 'OTH']
        
        actual = calculate_actual_spending(
            Expense.objects.all(),
            Saving.objects.all(),
            Investment.objects.all(),
            needs_cats,
            wants_cats,
            first_day
        )
        
        self.assertEqual(actual['needs'], 25000)  # Rent + Groceries
        self.assertEqual(actual['wants'], 1000)   # Movies
        self.assertEqual(actual['savings'], 15000) # Saving + Investment
    
    def test_calculate_actual_spending_empty(self):
        """Test actual spending calculation with no data"""
        today = date.today()
        first_day = today.replace(day=1)
        
        needs_cats = ['BIL', 'TRA', 'EMI', 'FOO']
        wants_cats = ['ENT', 'OTH']
        
        actual = calculate_actual_spending(
            Expense.objects.all(),
            Saving.objects.all(),
            Investment.objects.all(),
            needs_cats,
            wants_cats,
            first_day
        )
        
        self.assertEqual(actual['needs'], 0)
        self.assertEqual(actual['wants'], 0)
        self.assertEqual(actual['savings'], 0)
    
    def test_get_budget_alerts_overspending(self):
        """Test alert generation for overspending"""
        actual = {'needs': 60000, 'wants': 35000, 'savings': 15000}
        ideal = {'needs': 50000, 'wants': 30000, 'savings': 20000}
        
        alerts = get_budget_alerts(actual, ideal)
        
        # Should have alerts for needs, wants, and savings shortfall
        self.assertEqual(len(alerts), 3)
        
        # Check needs alert
        needs_alert = next(a for a in alerts if a['category'] == 'Needs')
        self.assertIn('10,000', needs_alert['message'])
        
        # Check savings shortfall
        savings_alert = next(a for a in alerts if a['category'] == 'Savings')
        self.assertEqual(savings_alert['severity'], 'info')
    
    def test_get_budget_alerts_no_overspending(self):
        """Test alert generation when within budget"""
        actual = {'needs': 45000, 'wants': 25000, 'savings': 25000}
        ideal = {'needs': 50000, 'wants': 30000, 'savings': 20000}
        
        alerts = get_budget_alerts(actual, ideal)
        
        # Should have no overspending alerts, only savings info might appear
        overspend_alerts = [a for a in alerts if a['severity'] in ['warning', 'danger']]
        self.assertEqual(len(overspend_alerts), 0)
    
    def test_calculate_budget_percentages(self):
        """Test percentage calculation"""
        actual = {'needs': 50000, 'wants': 30000, 'savings': 20000}
        income = 100000
        
        percentages = calculate_budget_percentages(actual, income)
        
        self.assertEqual(percentages['needs'], 50.0)
        self.assertEqual(percentages['wants'], 30.0)
        self.assertEqual(percentages['savings'], 20.0)
    
    def test_calculate_budget_percentages_zero_income(self):
        """Test percentage calculation with zero income"""
        actual = {'needs': 1000, 'wants': 500, 'savings': 0}
        income = 0
        
        percentages = calculate_budget_percentages(actual, income)
        
        self.assertEqual(percentages['needs'], 0)
        self.assertEqual(percentages['wants'], 0)
        self.assertEqual(percentages['savings'], 0)

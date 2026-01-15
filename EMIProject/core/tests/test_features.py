from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from expenses.models import Expense
from datetime import date

class FeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
    def test_scan_pay_prefill(self):
        # Test that passing GET params to expense creation pre-fills the form
        url = reverse('expense_create')
        response = self.client.get(url, {'title': 'TestPayee', 'amount': '500.00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['title'], 'TestPayee')
        self.assertEqual(response.context['form'].initial['amount'], '500.00')

    def test_chart_data_context(self):
        # Create some expenses
        Expense.objects.create(title='Lunch', amount=100, category='FOO', date=date.today())
        Expense.objects.create(title='Dinner', amount=200, category='FOO', date=date.today())
        Expense.objects.create(title='Uber', amount=150, category='TRA', date=date.today())
        
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Check chart data in context
        labels = response.context['chart_labels']
        data = response.context['chart_data']
        
        self.assertIn('Food', labels)
        self.assertIn('Transport', labels)
        
        # Check totals (Food: 300, Transport: 150)
        # Order is by total desc
        self.assertEqual(data[0], 300.0) 
        self.assertEqual(data[1], 150.0)
        
        # Check Comparison Chart Data
        self.assertIn('raw_total_expenses', response.context)
        self.assertIn('raw_total_emi', response.context)
        self.assertIsInstance(response.context['raw_total_expenses'], float)

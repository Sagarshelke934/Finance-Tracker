from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Saving, Investment
from expenses.models import Expense
import datetime

class WealthFeatureTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        
    def test_create_saving(self):
        url = reverse('add_saving')
        data = {
            'name': 'Emergency Fund',
            'amount': 50000,
            'date': datetime.date.today()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) # Redirects to home
        self.assertEqual(Saving.objects.count(), 1)
        self.assertEqual(Saving.objects.first().name, 'Emergency Fund')
        
    def test_create_investment(self):
        url = reverse('add_investment')
        data = {
            'name': 'Reliance Stock',
            'amount': 20000,
            'category': 'STK',
            'date': datetime.date.today()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Investment.objects.count(), 1)
        self.assertEqual(Investment.objects.first().category, 'STK')
        
    def test_dashboard_context(self):
        # Create some data
        Saving.objects.create(name='Saving 1', amount=1000, date=datetime.date.today())
        Investment.objects.create(name='Invest 1', amount=2000, category='MF', date=datetime.date.today())
        Expense.objects.create(title='Food', amount=500, category='FOO', date=datetime.date.today())
        
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        # Check context has wealth data keys
        self.assertIn('total_savings', response.context)
        self.assertIn('total_investments', response.context)
        
        # Check raw context variables
        self.assertEqual(float(response.context['raw_total_savings']), 1000.0)
        # investments will be 2000 + sync data (96500)
        self.assertGreaterEqual(float(response.context['raw_total_investments']), 2000.0)

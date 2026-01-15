from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Investment
import datetime

class InvestmentAutomationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        
    def test_broker_sync(self):
        url = reverse('broker_sync')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302) # Redirects to home
        
        # Check that mock investments were created
        # Based on BrokerService.fetch_portfolio, there are 4 items
        self.assertEqual(Investment.objects.count(), 4)
        
        # Test Idempotency (running sync again shouldn't create duplicates)
        response = self.client.post(url)
        self.assertEqual(Investment.objects.count(), 4)
        
    def test_sync_data_fields(self):
        url = reverse('broker_sync')
        self.client.post(url)
        
        reliance = Investment.objects.get(external_id='INE002A01018')
        self.assertEqual(reliance.name, 'Reliance Industries')
        self.assertEqual(float(reliance.amount), 24000.0)
        self.assertEqual(reliance.category, 'STK')

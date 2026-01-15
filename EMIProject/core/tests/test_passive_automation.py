from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Investment, Saving, RecurringWealth, Loan
from datetime import date, timedelta

class PassiveAutomationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        
    def test_passive_sync_on_home_visit(self):
        # Before visit, no investments
        self.assertEqual(Investment.objects.count(), 0)
        
        # Visit Home page
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Passive sync should have triggered and created 4 items from Mock Broker
        self.assertEqual(Investment.objects.count(), 4)
        
    def test_recurring_processing_on_home_visit(self):
        # Setup a recurring saving that is "due" (started 31 days ago)
        start_date = date.today() - timedelta(days=31)
        item = RecurringWealth.objects.create(
            name='Monthly SIP',
            type='SAV',
            amount=1000,
            frequency='MON',
            start_date=start_date
        )
        
        self.assertEqual(Saving.objects.count(), 0)
        
        # Visit Home
        self.client.get(reverse('home'))
        
        # Should have created 1 Saving entry
        self.assertEqual(Saving.objects.count(), 1)
        # Check last processed date updated
        item.refresh_from_db()
        self.assertEqual(item.last_processed_date, date.today())

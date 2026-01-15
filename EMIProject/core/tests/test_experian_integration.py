from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from core.models import Loan
from core.views import ExperianSyncView
from core.services.experian import ExperianService

class ExperianIntegrationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
    def test_service_mock_data(self):
        service = ExperianService()
        data = service.fetch_user_trades()
        self.assertIn('trades', data)
        self.assertTrue(len(data['trades']) > 0)
        self.assertEqual(data['trades'][0]['accountType'], 'Personal Loan')

    def test_sync_view_creates_loans(self):
        # Ensure no loans initially
        Loan.objects.all().delete()
        
        request = self.factory.post(reverse('experian_sync'))
        
        # Add session and messages support to the request
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        # Mocking user authentication (LoginRequiredMixin)
        request.user = type('User', (object,), {'is_authenticated': True})
        
        view = ExperianSyncView.as_view()
        response = view(request)
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Check loans were created
        loans = Loan.objects.all()
        self.assertTrue(loans.count() >= 2) # Mock returns 2 loans
        
        loan1 = loans.filter(external_id='EXP_1001').first()
        self.assertIsNotNone(loan1)
        self.assertEqual(loan1.principal, 600000.00)
        
    def test_sync_view_idempotency(self):
        # Run sync twice
        request = self.factory.post(reverse('experian_sync'))
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request.user = type('User', (object,), {'is_authenticated': True})
        
        view = ExperianSyncView.as_view()
        view(request)
        
        initial_count = Loan.objects.count()
        
        # Run again
        view(request)
        
        # Count should be same (no duplicates)
        self.assertEqual(Loan.objects.count(), initial_count)

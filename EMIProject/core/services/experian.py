import requests
import os
import random
from datetime import date, timedelta

class ExperianService:
    def __init__(self):
        self.api_key = os.environ.get('EXPERIAN_API_KEY', 'mock-key')
        self.base_url = os.environ.get('EXPERIAN_BASE_URL', 'https://api.experian.com/v1')
        self.is_mock = self.api_key == 'mock-key'

    def fetch_user_trades(self, user_data=None):
        """
        Fetches active trades (loans) for the user.
        In a real scenario, user_data would contain PAN/SSN etc.
        """
        if self.is_mock:
            return self._mock_response()

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'pan': user_data.get('pan')
            }
            response = requests.post(
                f"{self.base_url}/credit-report",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            # Fallback to mock if API call fails
            return self._mock_response()

    def _mock_response(self):
        """
        Generates mock trade lines simulating an Experian credit report.
        """
        return {
            'creditScore': 750,
            'trades': [
                {
                    'tradeId': 'EXP_1001',
                    'accountType': 'Personal Loan',
                    'accountNumber': 'XXXX1234',
                    'currentBalance': 500000.00,
                    'interestRate': 12.5,
                    'originalAmount': 600000.00,
                    'openDate': (date.today() - timedelta(days=365)).isoformat(),
                    'tenureMonths': 36,
                    'status': 'Active'
                },
                {
                    'tradeId': 'EXP_1002',
                    'accountType': 'Car Loan',
                    'accountNumber': 'XXXX5678',
                    'currentBalance': 850000.00,
                    'interestRate': 9.25,
                    'originalAmount': 1000000.00,
                    'openDate': (date.today() - timedelta(days=180)).isoformat(),
                    'tenureMonths': 60,
                    'status': 'Active'
                }
            ]
        }

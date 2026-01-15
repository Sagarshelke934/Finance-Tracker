import random
import requests
from datetime import date

class BrokerService:
    """
    Service to fetch investment data from open sources (e.g., MFAPI.in).
    """
    
    def fetch_mf_nav(self, scheme_code):
        """
        Fetches the latest NAV for a mutual fund scheme from MFAPI.in.
        """
        try:
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and data.get('data'):
                latest = data['data'][0]
                return {
                    'name': data['meta']['scheme_name'],
                    'nav': float(latest['nav']),
                    'date': latest['date']
                }
        except Exception as e:
            print(f"Error fetching NAV for {scheme_code}: {e}")
        return None

    def fetch_portfolio(self):
        """
        Returns a list of investment holdings, including real mutual fund data.
        """
        # Common MF Scheme Codes (Open Source / Popular)
        mf_schemes = [
            '120503', # Axis Bluechip Fund 
            '118989', # HDFC Top 100 Fund
            '102030'  # ICICI Prudential Bluechip Fund
        ]
        
        holdings = []
        
        # 1. Fetch Real Mutual Fund Data
        for code in mf_schemes:
            mf_data = self.fetch_mf_nav(code)
            if mf_data:
                holdings.append({
                    'symbol': code,
                    'name': mf_data['name'],
                    'type': 'MF',
                    'quantity': 100,
                    'buy_price': mf_data['nav'] * 0.8, # 20% Profit margin mocked
                    'current_price': mf_data['nav'],
                    'invested_amount': (mf_data['nav'] * 0.8) * 100,
                    'purchase_date': '2023-01-01',
                    'isin': f'MF_{code}'
                })

        # 2. Add some Mock Stocks (Since yfinance is not installed, we use placeholders)
        holdings.extend([
            {
                'symbol': 'TATASTEEL',
                'name': 'Tata Steel',
                'type': 'STK',
                'quantity': 50,
                'buy_price': 100.0, # Lowered from 120 for more profit
                'current_price': 145.0, # Increased from 135
                'invested_amount': 5000.0,
                'purchase_date': '2023-05-10',
                'isin': 'INE081A01012'
            },
            {
                'symbol': 'SGB',
                'name': 'Sovereign Gold Bond',
                'type': 'GLD',
                'quantity': 10,
                'buy_price': 4500.0, # Lowered from 5200
                'current_price': 6200.0, # Increased from 6100
                'invested_amount': 45000.0,
                'purchase_date': '2022-10-15',
                'isin': 'IN0020190010'
            }
        ])
        
        return {
            'success': True,
            'holdings': holdings
        }

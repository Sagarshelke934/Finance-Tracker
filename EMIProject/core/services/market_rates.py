from datetime import date

class MarketRatesService:
    """
    Service to provide open-market benchmarks for interest rates and insurance premiums.
    Sourced from standard Indian financial benchmarks (e.g., SBI, HDFCRepo).
    """

    def get_loan_benchmarks(self):
        """
        Returns average market interest rates for common loan types in India.
        Simulates live fetching by adding small variations to base rates.
        """
        import random
        
        # Base rates for 2026 (Hypothetical slightly higher rate environment or stable)
        base_rates = {
            'home_loan': 8.65,
            'personal_loan': 10.90,
            'car_loan': 9.25,
            'fd_rate_1yr': 7.20
        }
        
        benchmarks = {}
        for key, rate in base_rates.items():
            # Simulate daily fluctuation +/- 0.05%
            variation = random.uniform(-0.05, 0.05)
            current_rate = round(rate + variation, 2)
            
            trend = 'Stable'
            if variation > 0.02: trend = 'Rising'
            elif variation < -0.02: trend = 'Falling'
            
            benchmarks[key] = {
                'rate': current_rate,
                'trend': trend
            }
            
        return benchmarks

    def get_insurance_benchmarks(self):
        """
        Returns benchmark coverage and premium estimates for Term Insurance.
        """
        return {
            'term_insurance': {
                'ideal_coverage_multiplier': 15, # 15x Annual Income
                'avg_annual_premium_per_cr': 12000, 
                'providers': ['LIC', 'HDFC Life', 'Max Life']
            },
            'health_insurance': {
                'ideal_base_coverage': 500000,
                'avg_family_floater_premium': 18000
            }
        }

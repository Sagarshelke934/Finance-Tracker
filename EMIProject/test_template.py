import os
import django
from django.conf import settings
from django.template import Template, Context, engines

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

engine = engines['django']
try:
    template = engine.get_template('core/home.html')
    context = {
        'total_savings': '1,234.56',
        'total_investments': '7,890.12',
        'total_expenses': '500.00',
        'total_monthly_emi': '100.00',
        'active_loans': 2,
        'recent_investments': [{'name': 'Test Inv', 'category': 'Equity', 'amount': 1000}],
        'recent_expenses': [{'title': 'Test Exp', 'category': 'Food', 'amount': 200, 'date': '2026-01-12'}],
        'chart_labels': [], 'chart_data': [], 'raw_total_expenses': 0, 'raw_total_emi': 0, 
        'portfolio_labels': [], 'portfolio_data': [],
    }
    rendered = template.render(context)
    print(f"Rendered length: {len(rendered)}")
    
    if 'Equity' in rendered:
        print("SUCCESS: item.category rendered correctly")
    else:
        print("FAILURE: item.category NOT rendered")
        idx = rendered.find('Investments')
        if idx != -1:
            print(rendered[idx:idx+500])
            
    if '200' in rendered:
        print("SUCCESS: item.amount rendered correctly")
    else:
        print("FAILURE: item.amount NOT rendered")
        idx = rendered.find('Recent Expenses')
        if idx != -1:
            print(rendered[idx:idx+1000])
            
except Exception as e:
    import traceback
    traceback.print_exc()

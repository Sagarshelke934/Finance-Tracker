
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from accounts.models import UserProfile

def reproduce():
    # Setup user
    username = 'testuser_repro'
    password = 'password123'
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()
    
    user = User.objects.create_user(username=username, password=password)
    # Ensure profile exists
    UserProfile.objects.get_or_create(user=user)
    
    c = Client()
    loggedIn = c.login(username=username, password=password)
    if not loggedIn:
        print("Login failed")
        return

    print(f"Initial Income: {user.profile.monthly_income}")

    # Try to update income
    # Use 127.0.0.1 which is likely in ALLOWED_HOSTS for dev
    response = c.post('/update-profile-value/', {
        'monthly_income': '50000.00'
    }, HTTP_HOST='127.0.0.1:8000')

    if response.status_code != 302:
        print(f"Failed to redirect. Status: {response.status_code}")
        content = response.content.decode('utf-8', errors='ignore')
        # Extract title or h1 from error page
        if '<title>' in content:
            start = content.find('<title>') + 7
            end = content.find('</title>')
            print(f"Page Title: {content[start:end]}")
        
    
    user.refresh_from_db()
    print(f"Updated Income: {user.profile.monthly_income}")
    
    if user.profile.monthly_income == Decimal('50000.00'):
        print("SUCCESS: Backend update works.")
    else:
        print("FAILURE: Backend update failed.")

if __name__ == '__main__':
    reproduce()

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Expense
from core.services.whatsapp import WhatsAppService
from django.contrib.auth import get_user_model
from django.conf import settings

# Threshold for High Value Alert (Could be moved to UserProfile)
HIGH_VALUE_THRESHOLD = 5000

@receiver(post_save, sender=Expense)
def alert_high_value_expense(sender, instance, created, **kwargs):
    if created and instance.amount > HIGH_VALUE_THRESHOLD:
        # We need the user to send the alert to. 
        # Since Expense model doesn't link to User directly in this snippet (simplified model?),
        # we might have to assume a single user or fetching logic.
        # However, typically Expense should have a 'user' field.
        # Looking at previous context, Expense model DOES NOT have a user field explicitly shown in models.py view, 
        # but typically it should. If it doesn't, we'll fetch the first superuser for now as a fallback
        # or assuming single-user app structure from `home_v2.html` context.
        
        # Checking models.py again in Step 5784...
        # Expense model has: title, amount, category, date, created_at. NO USER FIELD.
        # This implies it's a single user app or shared expenses. 
        # I will send to the first superuser found, effectively the main admin.
        
        User = get_user_model()
        # Find a user who has a profile with phone number
        target_user = User.objects.filter(profile__phone_number__isnull=False).first()
        
        if target_user:
            service = WhatsAppService()
            service.send_alert(target_user, instance.title, instance.amount)

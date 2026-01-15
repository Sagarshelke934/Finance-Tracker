from django.conf import settings
from twilio.rest import Client
import os
from datetime import datetime

class WhatsAppService:
    def __init__(self):
        # Fallbacks for dev environment (User must replace these)
        self.sid = os.environ.get('TWILIO_ACCOUNT_SID', 'AC_YOUR_SID_HERE') 
        self.token = os.environ.get('TWILIO_AUTH_TOKEN', 'YOUR_TOKEN_HERE')
        self.from_number = os.environ.get('TWILIO_FROM_NUMBER', 'whatsapp:+14155238886') # Twilio Sandbox Number
        
        try:
            self.client = Client(self.sid, self.token)
            self.enabled = True
        except:
            print("Twilio Client failed to initialize. Check credentials.")
            self.enabled = False

    def send_message(self, to_number, body):
        if not self.enabled:
            return False, "Service Disabled"
            
        # Ensure number has 'whatsapp:' prefix
        if not to_number.startswith('whatsapp:'):
            to_number = f"whatsapp:{to_number}"
            
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                body=body,
                to=to_number
            )
            return True, message.sid
        except Exception as e:
            return False, str(e)

    def send_alert(self, user, title, amount):
        """
        Sends an immediate alert for critical events
        """
        if not hasattr(user, 'profile') or not user.profile.phone_number:
            return False, "No phone number"

        msg = f"🚨 *High Value Transaction Alert*\n\n"
        msg += f"A new expense *'{title}'* of *₹{amount:,.2f}* was just recorded.\n"
        msg += f"Verify this transaction on your dashboard."
        
        return self.send_message(user.profile.phone_number, msg)

    def generate_report_message(self, user, context):
        """
        Generates a rich text report from context data
        context expected: {'net_worth': X, 'income': Y, 'expenses': Z, 'recent': [list]}
        """
        now = datetime.now().strftime("%d %b %Y, %I:%M %p")
        
        msg = f"📊 *FinTrack Daily Report*\n"
        msg += f"_{now}_\n\n"
        
        msg += f"💰 *Net Worth:* ₹{context.get('net_worth', 0):,}\n"
        msg += f"📉 *Monthly Expenses:* ₹{context.get('expenses', 0):,}\n"
        
        # Budget Alert
        if context.get('budget_status', '') == 'DANGER':
            msg += f"⚠️ *BUDGET ALERT:* You have exceeded your safe limit!\n"
        
        msg += f"\n📝 *Recent Transactions:*\n"
        recents = context.get('recent', [])
        if recents:
            for tx in recents[:5]: # Last 5
                msg += f"• ₹{tx.amount} - {tx.category} ({tx.date})\n"
        else:
            msg += "No recent transactions.\n"
            
        msg += f"\n_Reply 'MENU' for options_"
        return msg

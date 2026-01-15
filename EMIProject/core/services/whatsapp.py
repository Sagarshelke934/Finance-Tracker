from django.conf import settings
from datetime import datetime
import time

class WhatsAppService:
    def __init__(self):
        self.enabled = True
        self.default_number = "+919130044796" 

    def send_message(self, to_number, body):
        """
        Sends an instant WhatsApp message using pywhatkit.
        Opens a browser window to send the message.
        """
        if not self.enabled:
            return False, "Service Disabled"
            
        import pywhatkit as pwk

        # Use default number if explicit number not provided or for safety
        # The user requested alerts to specific number, so we prioritize that or fallback
        target = self.default_number
            
        try:
            # sendwhatmsg_instantly(phone_no, message, wait_time=15, tab_close=False, close_time=3)
            # wait_time: time to wait before sending (seconds) - keep it short but enough for load
            # close_time: time to wait after sending to close tab (if tab_close=True)
            print(f"Sending WhatsApp to {target}: {body}")
            pwk.sendwhatmsg_instantly(target, body, wait_time=10, tab_close=True, close_time=3)
            return True, "Message sent properly (Browser should open)"
        except Exception as e:
            print(f"WhatsApp Error: {e}")
            return False, str(e)

    def send_alert(self, user, title, amount):
        """
        Sends an immediate alert for critical events
        """
        # Ignoring user.profile.phone_number for now as per specific request to use 9130044796
        
        msg = f"🚨 *High Value Transaction Alert*\n"
        msg += f"A new expense *'{title}'* of *₹{amount:,.2f}* was just recorded.\n"
        msg += f"Verify this transaction on your dashboard."
        
        return self.send_message(self.default_number, msg)

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
            
        return msg

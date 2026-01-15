import re
import requests
import os
import json
from django.db.models import Sum
from expenses.models import Expense
from .models import Saving, Investment, Loan, Policy

class ChatBotService:
    def __init__(self):
        # Allow user to set key via env or hardcode it here for testing
        self.gemini_key = os.environ.get("GOOGLE_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        self.openai_url = "https://api.openai.com/v1/chat/completions"

    def get_context_data(self):
        """Gather financial context for the AI"""
        total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        total_savings = Saving.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        total_investments = Investment.get_total_invested()
        total_insurance = Policy.get_total_sum_assured()
        
        loans = Loan.objects.all()
        active_loans = loans.count()
        total_loan_principal = sum(l.principal for l in loans)
        total_monthly_emi = Loan.get_total_emi()

        return {
            "expenses": float(total_expenses),
            "savings": float(total_savings),
            "investments": float(total_investments),
            "insurance_coverage": float(total_insurance),
            "active_loans_count": active_loans,
            "total_debt_principal": float(total_loan_principal),
            "monthly_emi_outflow": float(total_monthly_emi),
            "currency": "INR",
            "net_worth": float(total_savings + total_investments)
        }

    def call_openai_api(self, user_message, context_data):
        if not self.openai_key:
            return None
            
        system_prompt = (
            f"You are FinBot, a helpful financial assistant. "
            f"Here is the user's current financial snapshot: {json.dumps(context_data)}. "
            f"Answer the user's question concisely based on this data."
        )
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 150
        }
        
        try:
            response = requests.post(self.openai_url, headers=headers, json=payload, timeout=8)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return None

    def call_gemini_api(self, user_message, context_data):
        if not self.gemini_key:
            return None
        
        system_prompt = (
            f"You are FinBot, a helpful financial assistant for a FinTech dashboard. "
            f"Here is the user's current financial snapshot: {json.dumps(context_data)}. "
            f"Answer the user's question concisely based on this data. "
            f"If the question is not about finances, politely steer them back."
        )

        payload = {
            "contents": [{
                "parts": [{"text": system_prompt + "\n\nUser: " + user_message}]
            }]
        }

        try:
            response = requests.post(self.gemini_url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return None

    def process_message(self, user, message):
        """
        Process the user's message. Tries OpenAI, then Gemini, then Rule-Based.
        """
        message_lower = message.lower().strip()
        context = self.get_context_data()

        # 1. Try OpenAI
        openai_response = self.call_openai_api(message, context)
        if openai_response:
            return openai_response

        # 2. Try Gemini
        gemini_response = self.call_gemini_api(message, context)
        if gemini_response:
            return gemini_response

        # 3. Fallback: Rule-Based Logic
        
        # Greetings
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return f"Hello {user.username.title()}! I am FinBot (Running in Local Mode). I can track your expenses, savings, and net worth."

        # Help
        if 'help' in message_lower or 'what can you do' in message_lower:
            return "I can track your finances. Try asking:\n- 'Total expenses'\n- 'How much have I saved?'\n- 'Show my investments'\n- 'What is my net worth?'"

        # Expenses
        if 'expense' in message_lower or 'spent' in message_lower or 'spending' in message_lower:
            return f"Your total recorded expenses amount to ₹{context['expenses']:,.2f}."

        # Savings
        if 'save' in message_lower or 'saving' in message_lower:
            return f"You have currently saved a total of ₹{context['savings']:,.2f}. Great job!"

        # Investments
        if 'invest' in message_lower:
            return f"Your total investment portfolio is valued at ₹{context['investments']:,.2f}."

        # Policies / Insurance
        if 'policy' in message_lower or 'insurance' in message_lower:
            return f"Your total insurance sum assured is ₹{context['insurance_coverage']:,.2f}."

        # Loans / EMI
        if 'loan' in message_lower or 'emi' in message_lower or 'debt' in message_lower:
            return f"You have {context['active_loans_count']} active loans. Your total monthly EMI obligation is ₹{context['monthly_emi_outflow']:,.2f}."

        # Net Worth
        if 'net worth' in message_lower or 'wealth' in message_lower:
            return f"Your approximate liquid net worth (Savings + Investments) is ₹{context['net_worth']:,.2f}."

        # Default fallback
        return "I'm running in local mode. Please configure OPENAI_API_KEY or GOOGLE_API_KEY for full AI capabilities."

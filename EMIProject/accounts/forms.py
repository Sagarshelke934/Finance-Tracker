from django import forms
from .models import UserProfile

class IncomeForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['monthly_income']
        widgets = {
            'monthly_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter monthly income',
                'step': '0.01'
            })
        }
        labels = {
            'monthly_income': 'Monthly Income (₹)'
        }

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Inform a valid email address.")
    phone_number = forms.CharField(max_length=15, required=False, help_text="Optional. Enter your mobile number.")

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Profile is automatically created by signal, so we just update it
            if hasattr(user, 'profile'):
                user.profile.phone_number = self.cleaned_data.get('phone_number', '')
                user.profile.save()
        return user

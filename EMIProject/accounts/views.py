from django.shortcuts import render, redirect
from django.views.generic import CreateView, View
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import IncomeForm, CustomUserCreationForm
from .models import UserProfile

class RegisterView(CreateView):
    template_name = 'registration/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

class UpdateIncomeView(LoginRequiredMixin, View):
    def post(self, request):
        # Ensure profile exists
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = IncomeForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Monthly income updated successfully!")
        else:
            messages.error(request, "Failed to update income. Please check the value.")
        return redirect('home')

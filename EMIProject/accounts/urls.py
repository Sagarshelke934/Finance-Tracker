from django.urls import path, include
from .views import RegisterView, UpdateIncomeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('income-update/', UpdateIncomeView.as_view(), name='income_update'),
    path('', include('django.contrib.auth.urls')),
]

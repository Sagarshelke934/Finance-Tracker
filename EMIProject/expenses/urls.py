from django.urls import path
from django.views.generic import TemplateView
from .views import (
    ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView,
    RecurringExpenseListView, RecurringExpenseCreateView, RecurringExpenseUpdateView, RecurringExpenseDeleteView
)

urlpatterns = [
    path('', ExpenseListView.as_view(), name='expense_list'),
    path('add/', ExpenseCreateView.as_view(), name='expense_create'),
    path('edit/<int:pk>/', ExpenseUpdateView.as_view(), name='expense_update'),
    path('delete/<int:pk>/', ExpenseDeleteView.as_view(), name='expense_delete'),
    path('scan/', TemplateView.as_view(template_name='expenses/scan.html'), name='scan_pay'),
    
    # Recurring Expenses
    path('recurring/', RecurringExpenseListView.as_view(), name='recurring_list'),
    path('recurring/add/', RecurringExpenseCreateView.as_view(), name='recurring_add'),
    path('recurring/edit/<int:pk>/', RecurringExpenseUpdateView.as_view(), name='recurring_edit'),
    path('recurring/delete/<int:pk>/', RecurringExpenseDeleteView.as_view(), name='recurring_delete'),
]

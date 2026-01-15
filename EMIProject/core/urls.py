from django.urls import path
from django.views.generic import TemplateView
from .views import (
    HomeView, EMICalculatorView, LoanCreateView, ExperianSyncView, 
    SavingCreateView, InvestmentCreateView, InvestmentSyncView, 
    DocumentCreateView, SearchView, AnalyticsView, UpdateProfileValueView,
    DocumentCreateView, SearchView, AnalyticsView, UpdateProfileValueView,
    LoanListView, SavingListView, InvestmentListView, PolicyListView, DocumentListView,
    DocumentDetailView, LoanUpdateView, LoanDeleteView, SavingUpdateView, SavingDeleteView,
    InvestmentUpdateView, InvestmentDeleteView, PolicyCreateView, PolicyUpdateView, PolicyDeleteView,
    ChatBotView, WhatsAppReportView
)

urlpatterns = [
    path('whatsapp/report/', WhatsAppReportView.as_view(), name='whatsapp_report'),
    path('chat/ask/', ChatBotView.as_view(), name='chatbot_ask'),
    path('', HomeView.as_view(), name='home'),
    path('update-profile-value/', UpdateProfileValueView.as_view(), name='update_profile_value'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('search/', SearchView.as_view(), name='search'),
    path('calculator/', EMICalculatorView.as_view(), name='emi_calculator'),
    path('loan/add/', LoanCreateView.as_view(), name='add_loan'),
    path('saving/add/', SavingCreateView.as_view(), name='add_saving'),
    path('investment/add/', InvestmentCreateView.as_view(), name='add_investment'),
    path('investment/sync/', InvestmentSyncView.as_view(), name='broker_sync'),
    path('experian/sync/', ExperianSyncView.as_view(), name='experian_sync'),
    path('receive-qr/', TemplateView.as_view(template_name='core/receive_qr.html'), name='receive_qr'),
    path('my-qr/', TemplateView.as_view(template_name='core/receive_qr.html'), name='my_qr'),
    path('scan-qr/', TemplateView.as_view(template_name='core/receive_qr.html'), name='scan_qr'),
    path('about/', TemplateView.as_view(template_name='core/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='core/contact.html'), name='contact'),
    path('documents/add/', DocumentCreateView.as_view(), name='add_document'),
    path('documents/', DocumentListView.as_view(), name='document_list'),
    path('documents/<int:pk>/', DocumentDetailView.as_view(), name='document_detail'),

    # Listing Pages
    path('loans/', LoanListView.as_view(), name='loan_list'),
    path('loan/edit/<int:pk>/', LoanUpdateView.as_view(), name='update_loan'),
    path('loan/delete/<int:pk>/', LoanDeleteView.as_view(), name='delete_loan'),
    
    path('savings/', SavingListView.as_view(), name='saving_list'),
    path('saving/edit/<int:pk>/', SavingUpdateView.as_view(), name='update_saving'),
    path('saving/delete/<int:pk>/', SavingDeleteView.as_view(), name='delete_saving'),
    
    path('investments/', InvestmentListView.as_view(), name='investment_list'),
    path('investment/edit/<int:pk>/', InvestmentUpdateView.as_view(), name='update_investment'),
    path('investment/delete/<int:pk>/', InvestmentDeleteView.as_view(), name='delete_investment'),

    path('policies/', PolicyListView.as_view(), name='policy_list'),
    path('policy/add/', PolicyCreateView.as_view(), name='add_policy'),
    path('policy/edit/<int:pk>/', PolicyUpdateView.as_view(), name='update_policy'),
    path('policy/delete/<int:pk>/', PolicyDeleteView.as_view(), name='delete_policy'),
]
# Force Reload

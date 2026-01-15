"""
Budget Calculator Utility

Provides reusable functions for calculating 50-30-20 budget allocations
and analyzing spending patterns.
"""
from decimal import Decimal
from typing import Dict, List, Tuple
from datetime import date
from django.db.models import Sum


def calculate_ideal_budget(monthly_income: float) -> Dict[str, float]:
    """
    Calculate ideal budget allocation based on 50-30-20 rule.
    
    Args:
        monthly_income: User's monthly income
        
    Returns:
        Dictionary with 'needs', 'wants', 'savings' ideal amounts
    """
    return {
        'needs': monthly_income * 0.5,
        'wants': monthly_income * 0.3,
        'savings': monthly_income * 0.2
    }


def calculate_actual_spending(expenses_qs, savings_qs, investments_qs, 
                              needs_categories: List[str], 
                              wants_categories: List[str],
                              start_date: date) -> Dict[str, float]:
    """
    Calculate actual spending in each budget category.
    
    Args:
        expenses_qs: QuerySet of Expense objects
        savings_qs: QuerySet of Saving objects
        investments_qs: QuerySet of Investment objects
        needs_categories: List of expense category codes for "needs"
        wants_categories: List of expense category codes for "wants"
        start_date: Start date for filtering (typically first day of month)
        
    Returns:
        Dictionary with 'needs', 'wants', 'savings' actual amounts
    """
    current_month_expenses = expenses_qs.filter(date__gte=start_date)
    
    actual_needs = float(
        current_month_expenses.filter(category__in=needs_categories)
        .aggregate(Sum('amount'))['amount__sum'] or 0
    )
    
    actual_wants = float(
        current_month_expenses.filter(category__in=wants_categories)
        .aggregate(Sum('amount'))['amount__sum'] or 0
    )
    
    actual_savings = float(
        savings_qs.filter(date__gte=start_date)
        .aggregate(Sum('amount'))['amount__sum'] or 0
    )
    
    actual_investments = float(
        investments_qs.filter(date__gte=start_date)
        .aggregate(Sum('amount'))['amount__sum'] or 0
    )
    
    return {
        'needs': actual_needs,
        'wants': actual_wants,
        'savings': actual_savings + actual_investments
    }


def get_budget_alerts(actual: Dict[str, float], ideal: Dict[str, float]) -> List[Dict[str, str]]:
    """
    Generate alerts when spending exceeds ideal percentages.
    
    Args:
        actual: Dictionary of actual spending amounts
        ideal: Dictionary of ideal spending amounts
        
    Returns:
        List of alert dictionaries with 'category', 'message', 'severity'
    """
    alerts = []
    
    for category in ['needs', 'wants', 'savings']:
        if actual[category] > ideal[category]:
            overspend_amount = actual[category] - ideal[category]
            overspend_percent = (overspend_amount / ideal[category] * 100) if ideal[category] > 0 else 0
            
            severity = 'warning' if overspend_percent < 20 else 'danger'
            
            alerts.append({
                'category': category.capitalize(),
                'message': f"You've exceeded your {category} budget by ₹{overspend_amount:,.2f} ({overspend_percent:.1f}%)",
                'severity': severity
            })
    
    # Check if savings is below ideal
    if actual['savings'] < ideal['savings']:
        shortfall = ideal['savings'] - actual['savings']
        alerts.append({
            'category': 'Savings',
            'message': f"You're ₹{shortfall:,.2f} short of your savings goal this month",
            'severity': 'info'
        })
    
    return alerts


def calculate_budget_percentages(actual: Dict[str, float], total_income: float) -> Dict[str, float]:
    """
    Calculate actual spending as percentage of income.
    
    Args:
        actual: Dictionary of actual spending amounts
        total_income: User's monthly income
        
    Returns:
        Dictionary with percentage values for each category
    """
    if total_income == 0:
        return {'needs': 0, 'wants': 0, 'savings': 0}
    
    return {
        'needs': (actual['needs'] / total_income) * 100,
        'wants': (actual['wants'] / total_income) * 100,
        'savings': (actual['savings'] / total_income) * 100
    }

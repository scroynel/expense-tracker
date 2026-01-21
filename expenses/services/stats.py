from django.db.models import Sum, Case, When, DecimalField, ExpressionWrapper, F
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractWeek

from expenses.models import Transaction



PERIOD_CONFIG = {
    'year': {
        'fields': {
            'year': ExtractYear('date')
        },
        'order_by': ['year']
    },
    'month': {
        'fields': {
            'year': ExtractYear('date'),
            'month': ExtractMonth('date')
        },
        'order_by': ['year', 'month']
    },
    'week': {
        'fields': {
            'year': ExtractYear('date'),
            'week': ExtractWeek('date')
        },
        'order_by': ['year', 'week']
    }
}


def get_time_stats(qs, period: str, category=None):
    config = PERIOD_CONFIG[period]
  
    if category:
        qs = qs.filter(category=category)

    result = list(qs.annotate(**config['fields']).values(*config['fields'].keys()).annotate(
        income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
        expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField())),
        net = ExpressionWrapper(F('income') - F('expense'), output_field=DecimalField())
    ).order_by(*config['order_by']))

    return result
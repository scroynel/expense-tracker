from django.db.models import Sum, F, Q
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractWeek, ExtractDay
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
    },
    'day': {
        'fields': {
            'year': ExtractYear('date'),
            'month': ExtractMonth('date'),
            'day': ExtractDay('date'),
        },
        'order_by': ['year', 'month', 'day']
    }
}


def get_time_stats(qs, period: str):
    config = PERIOD_CONFIG[period]
    
    result = list(qs.annotate(**config['fields']).values(*config['fields'].keys()).annotate(
        income = Sum('amount', filter=Q(type=Transaction.INCOME), default=0),
        expense = Sum('amount', filter=Q(type=Transaction.EXPENSE), default=0),
    ).annotate(
        net = F('income') - F('expense')
    ).order_by(*config['order_by']))

    return result


def get_categories_stats(qs, period: str):
    config = PERIOD_CONFIG[period]

    result = qs.annotate(**config['fields']).values('category__name', *config['fields'].keys()).annotate(
        income = Sum('amount', filter=Q(type=Transaction.INCOME), default=0),
        expense = Sum('amount', filter=Q(type=Transaction.EXPENSE), default=0)
    ).annotate(
        net = F('income') - F('expense')
    ).order_by('category__name', *config['order_by'])

    return result


def get_time_extreme_stats(qs, period: str):
    config = PERIOD_CONFIG[period]

    result = qs.annotate(**config['fields']).values(*config['fields'].keys()).annotate(total=Sum('amount')).order_by('total')

    return result
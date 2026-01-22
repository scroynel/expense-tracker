
from collections import defaultdict
import json

from django.db.models import Sum, Case, When, DecimalField, F, Value, Max, Min
from django.db.models.functions import TruncDate, Cast, ExtractWeek, ExtractMonth, ExtractYear
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Category, Transaction
from .serializer import CategorySerializer, TransactionSerializer
from .filters import TransactionFilter


from expenses.services.stats import get_time_stats


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)
    

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TransactionFilter
    ordering_fields = ['amount', 'date']
    ordering = ['-date']


    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)
    

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset()).filter(date__isnull=False)

        income = qs.filter(type=Transaction.INCOME)
        expense = qs.filter(type=Transaction.EXPENSE)

        income_total = income.aggregate(total=Sum('amount'))['total'] or 0
        expense_total = expense.aggregate(total=Sum('amount'))['total'] or 0

        # By categories stats
        by_category = defaultdict(list)

        for category in Category.objects.all().order_by('name'):
            if Transaction.objects.filter(category=category):
                by_category[category.name] = {
                    category.name: {
                        'yearly': get_time_stats(qs, 'year', category),
                        'monthly': get_time_stats(qs, 'month', category),
                        'weekly': get_time_stats(qs, 'week', category),
                    }
                }
                

        # Daily stats
        daily_qs = (
            qs.values('date').annotate(
                income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
                expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField()))
            ).order_by('date')
        )
        

        daily = [
            {
            'date': item['date'],
            'income': item['income'],
            'expense': item['expense'],
            'net': item['income'] - item['expense']
            }
            for item in daily_qs
        ]
        
        # Weekly stats
        weekly = get_time_stats(qs, 'week')

        # Monthly stats
        monthly = get_time_stats(qs, 'month')

        #yearly stats
        yearly = get_time_stats(qs, 'year')


        # All time stats
        all_time_income = qs.filter(type=Transaction.INCOME).aggregate(Sum('amount'))['amount__sum']
        all_time_expense = qs.filter(type=Transaction.EXPENSE).aggregate(Sum('amount'))['amount__sum']


        # The most expensive day
        cheapest_expensive_day = qs.filter(type=Transaction.EXPENSE).values('date').annotate(total=Sum('amount')).order_by('total')
        cheapest_day = cheapest_expensive_day.first()
        expensive_day = cheapest_expensive_day.order_by('-total').first()


        # Balance stats
        balance = all_time_income - all_time_expense
        

        data = {
            'transaction_count': qs.count(),
            'balance': balance,
            'total_income': all_time_income,
            'total_expense': all_time_expense,
            'cheapest_day': cheapest_day,
            'expensive_day': expensive_day,
            'by_category': list(by_category.values()),
            'daily': daily,
            'weekly': weekly,
            'monthly': monthly,
            'yearly': yearly
        }

        return Response(data)
        
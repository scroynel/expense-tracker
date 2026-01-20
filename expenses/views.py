
from collections import defaultdict
import json

from django.db.models import Sum, Case, When, DecimalField, F, Value
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


        # By category stats
        category_qs = (
            qs.values(category_name=F('category__name')).annotate(
                income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
                expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField()))
            )
        ).order_by('category')

        by_category = defaultdict(list)

        for category in Category.objects.all().order_by('name'):

            by_category[category.name] = {
                category.name: {
                    'yearly': get_time_stats(qs, 'year'),
                    'monthly': get_time_stats(qs, 'month'),
                    'weekly': get_time_stats(qs, 'week'),
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
        weekly_qs = (
            qs.annotate(year=ExtractYear('date'), week=ExtractWeek('date')).values('year', 'week').annotate(
                income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
                expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField()))
            )
        ).order_by('year', 'week')


        weekly = [
            {
            'year': item['year'],
            'week': item['week'],
            'income': item['income'],
            'expense': item['expense'],
            'net': item['income'] - item['expense']
            }
            for item in weekly_qs
        ]


        # Monthly stats
        monthly_qs = (
            qs.annotate(year=ExtractYear('date'), month=ExtractMonth('date')).values('year', 'month').annotate(
                income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
                expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField()))
            ).order_by('year', 'month')
        )


        monthly = [
            {
                'year': item['year'],
                'month': item['month'],
                'income': item['income'],
                'expense': item['expense'],
                'net': item['income'] - item['expense']
            }
            for item in monthly_qs
        ]


        # Yearly stats
        yearly_qs = (
            qs.annotate(year=ExtractYear('date')).values('year').annotate(
                income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
                expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField()))
            ).order_by('year')
        )


        yearly = [
            {
                'year': item['year'],
                'income': item['income'],
                'expense': item['expense'],
                'net': item['income'] - item['expense']
            }
            for item in yearly_qs
        ]


        data = {
            'transaction_count': qs.count(),
            'by_category': list(by_category.values()),
            'daily': daily,
            'weekly': weekly,
            'monthly': monthly,
            'yearly': yearly
        }

        return Response(data)
        
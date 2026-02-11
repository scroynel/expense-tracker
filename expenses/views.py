
from collections import defaultdict

from django.db.models import Sum, Case, When, DecimalField
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Category, Transaction
from .serializer import CategorySerializer, TransactionSerializer
from .filters import TransactionFilter

from .services.stats import get_time_stats, PERIOD_CONFIG, get_time_extreme_stats
from .permissions import IsOwner
from .paginations import CustomPagination10

from expenses.throttle import StatsThrottling


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwner]
    throttle_scope = 'category'

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)
    

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filterset_class = TransactionFilter
    pagination_class = CustomPagination10
    ordering_fields = ['amount', 'date']
    ordering = ['-date']


    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user).select_related('category')
    

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StatsViewSet(viewsets.GenericViewSet):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer


    @action(detail=False, methods=['get'], throttle_classes=[StatsThrottling,])
    def overview(self, request):
        qs = self.get_queryset().values('type').annotate(total=Sum('amount'))

        result = {item['type']: item['total'] for item in qs}

        # Balance stats
        balance = result['income'] - result['expense']

        data = {
            'transaction_count': self.queryset.count(),
            'balance': balance,
            'total_income': result['income'],
            'total_expense': result['expense']
        }

        return Response(data)
    

    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories = Category.objects.all().order_by('name')

        by_category = defaultdict(list)

        for category in categories:
            income = self.get_queryset().filter(category=category, type=Transaction.INCOME).aggregate(Sum('amount'))['amount__sum'] or 0
            expense = self.get_queryset().filter(category=category, type=Transaction.EXPENSE).aggregate(Sum('amount'))['amount__sum'] or 0

            if Transaction.objects.filter(category=category):
                by_category[category.name].append({
                    'income': income,
                    'expense': expense,
                    'net': income - expense,
                    'daily': get_time_stats(self.get_queryset(), 'day', category), 
                    'weekly': get_time_stats(self.get_queryset(), 'week', category), 
                    'monthly': get_time_stats(self.get_queryset(), 'month', category), 
                    'yearly': get_time_stats(self.get_queryset(), 'year', category) 
                })
        
        
        return Response(by_category)
    

    @action(detail=False, methods=['get'])
    def time(self, request):
        period = request.query_params.get('period')
        if period is not None:
            period = period.lower()

        if period not in PERIOD_CONFIG and period is None:
            return Response({"error": f"Invalid period: {period}"}, status=400)
        
        qs = self.get_queryset()
        time_stats = get_time_stats(qs, period)

        data = {
            period: time_stats
        }
        
        return Response(data)
    

    @action(detail=False, methods=['get'])
    def extreme_day(self, request):
        # period = request.query_params.get('period', 'day').lower()
        period = request.query_params.get('period')
        
        if period not in PERIOD_CONFIG and period is None:
            return Response({"error": f"Invalid period: {period}"}, status=400)

        qs = self.get_queryset().filter(type=Transaction.EXPENSE)
        data = get_time_extreme_stats(qs, period)

        cheapest = data.first()
        expensive = data.last()

        data = {
            period: {
                'cheapest': cheapest,
                'expensive': expensive
            }
        }

        return Response(data)
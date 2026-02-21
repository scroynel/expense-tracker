
from django.core.cache import cache
from decimal import Decimal

from django.db.models import Sum, Case, When, DecimalField, ExpressionWrapper, F, Max, Min
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Category, Transaction
from .serializer import CategorySerializer, TransactionSerializer
from .filters import TransactionFilter

from .services.period_stats import get_time_stats, PERIOD_CONFIG, get_time_extreme_stats, get_categories_stats
from .permissions import IsOwner
from .paginations import CustomPagination10

from .throttle import StatsThrottling
from .services.cache_helpers import make_float


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
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer


    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)


    @action(detail=False, methods=['get'], throttle_classes=[StatsThrottling,])
    def overview(self, request):
        cache_key = f'stats:user:{request.user.id}'
        user_stats = cache.get(cache_key) 

        if user_stats:
            return Response(user_stats)

        qs = self.get_queryset().values('type').annotate(
            total=Sum('amount'),
            max_amount=Max('amount'),
            min_amount=Min('amount')
        )

        res = {item['type']: item for item in qs}
     
        income = res.get('income')
        expense = res.get('expense')
        
        # Balance stats
        balance = income['total'] - expense['total']

        data = {
            'transaction_count': self.get_queryset().count(),
            'balance': balance,
            'total_income': income['total'],
            'max_income': income['max_amount'],
            'min_income': income['min_amount'],
            'total_expense': expense['total'],
            'max_expense': expense['max_amount'],
            'min_expense': expense['min_amount'],
        }

        converted_data = make_float(data)

        cache.set(cache_key, converted_data, timeout=300) # 5 minutes

        return Response(converted_data)
    

    @action(detail=False, methods=['get'])
    def categories(self, request):
        period = request.query_params.get('period')
        
        if period is not None:
            period = period.lower()
        
        if period not in PERIOD_CONFIG:
            return Response({'error': f'Invalid period {period}'}, status=400)
        
        tran = self.get_queryset().values('category__name').annotate(
            income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
            expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField())),
        )

        by_category = {}
    
        data = get_categories_stats(tran, period)
        
        period_keys = PERIOD_CONFIG[period]['order_by']

        for item in data:
            category = item['category__name']
            if category not in by_category:
                by_category[item['category__name']] = {period: []}

            period_data = {key: item[key] for key in period_keys}

            period_data.update({
                'income': item['income'],
                'expense': item['expense'],
                'net': item['net']
            })

            by_category[item['category__name']][period].append(period_data)
        
        return Response(by_category)
    

    @action(detail=False, methods=['get'])
    def time(self, request):
        period = request.query_params.get('period')
        if period is not None:
            period = period.lower()

        if period not in PERIOD_CONFIG:
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
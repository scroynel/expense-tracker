
from collections import defaultdict

from django.db.models import Sum, Case, When, DecimalField, ExpressionWrapper, F, Max, Min
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Category, Transaction
from .serializer import CategorySerializer, TransactionSerializer
from .filters import TransactionFilter

from .services.stats import get_time_stats, PERIOD_CONFIG, get_time_extreme_stats, get_categories_stats
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
        qs = self.get_queryset().values('type').annotate(total=Sum('amount'), max_amount=Max('amount'), min_amount=Min('amount'))
        print(qs)

        result = {item['type']: {'total': item['total'], 'max_amount': item['max_amount'], 'min_amount': item['min_amount']} for item in qs}
        print(result)
        # Balance stats
        balance = result['income']['total'] - result['expense']['total']

        data = {
            'transaction_count': self.queryset.count(),
            'balance': balance,
            'total_income': result['income']['total'],
            'max_income': result['income']['max_amount'],
            'min_income': result['income']['min_amount'],
            'total_expense': result['expense']['total'],
            'max_expense': result['expense']['max_amount'],
            'min_expense': result['expense']['min_amount'],
        }

        return Response(data)
    

    @action(detail=False, methods=['get'])
    def categories(self, request):
        period = request.query_params.get('period')
        
        if period is not None:
            period = period.lower()
        
        if period not in PERIOD_CONFIG:
            return Response({'error': f'Invalid period {period}'}, status=400)
        

        tran = self.queryset.values('category__name').annotate(
            income = Sum(Case(When(type=Transaction.INCOME, then='amount'), default=0, output_field=DecimalField())),
            expense = Sum(Case(When(type=Transaction.EXPENSE, then='amount'), default=0, output_field=DecimalField())),
        )

        # by_category = defaultdict(list)
        by_category = {}
    

        data = get_categories_stats(tran, period)
        
        period_keys = list(PERIOD_CONFIG[period]['fields'].keys())

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
            
        # for categ in tran:
        #     by_category[categ['category__name']].append({
        #         'income': categ['income'],
        #         'expense': categ['expense'],
                # period: get_categories_stats(tran, period, categ['category__name'])
                
            # })
        
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
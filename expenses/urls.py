from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet, StatsViewSet


router = DefaultRouter()
router.register(r'category', CategoryViewSet, basename='category')
router.register(r'transaction', TransactionViewSet, basename='transaction')
router.register(r'stats', StatsViewSet, basename='stats')


urlpatterns = router.urls
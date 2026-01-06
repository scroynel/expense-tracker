from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet


router = DefaultRouter()
router.register(r'category', CategoryViewSet, basename='category')
router.register(r'transaction', TransactionViewSet, basename='transaction')


urlpatterns = router.urls
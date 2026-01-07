from rest_framework.routers import DefaultRouter
from .views import VoucherViewSet, CreditViewSet


router = DefaultRouter()
router.register('vouchers', VoucherViewSet, basename='vouchers')
router.register('credit', CreditViewSet, basename='credit')


urlpatterns = router.urls

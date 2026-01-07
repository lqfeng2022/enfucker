from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from interact.utils.annotates import annotate_state_for_product
from store.serializers.product import ProductSerializer
from store.models import Product
import logging

logger = logging.getLogger(__name__)  # store.view


# '/store/product/'
class ProductViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['host', 'type']
    search_fields = ['expression__title', 'subtitle__content', 'video__title']
    ordering_fields = ['created_at', 'updated_at', 'views_count',
                       'likes_count']

    def get_queryset(self):
        user = self.request.user
        queryset = Product.objects. \
            select_related('host', 'video', 'subtitle', 'expression', 'video__genre'). \
            prefetch_related('subtitle__expressions')
        queryset = annotate_state_for_product(queryset, user)
        return queryset

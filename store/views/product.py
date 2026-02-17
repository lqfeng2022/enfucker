from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from django.db.models import Q, Case, When
from django_filters.rest_framework import DjangoFilterBackend
from interact.utils.recommendation import my_recommendation_engine
from interact.utils.annotates import annotate_state_for_product
from store.models import Product
from store.serializers.product import ProductSerializer
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


# '/store/feed/'
class FeedViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user if \
            self.request.user.is_authenticated else None
        recommended_ids = my_recommendation_engine(user)

        # Preserve the order from the recommendation engine
        preserved_order = Case(
            *[When(pk=pk, then=pos) for
              pos, pk in enumerate(recommended_ids)]
        )

        queryset = Product.objects. \
            filter(id__in=recommended_ids). \
            select_related('host', 'video', 'video__genre', 'subtitle', 'expression'). \
            prefetch_related('subtitle__expressions')
        queryset = annotate_state_for_product(queryset, user)
        return queryset.order_by(preserved_order)


# '/store/products/<pk>/relevants/'
class RelevantViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        source_id = self.kwargs.get('product_pk')
        product = self._base_qs().filter(id=source_id).first()
        if not product:
            return Product.objects.none()

        type_map = {
            Product.PRODUCT_VIDEO: self._for_video,
            Product.PRODUCT_SUBTITLE: self._for_subtitle,
            Product.PRODUCT_EXPRESSION: self._for_expression,
        }

        handler = type_map.get(product.type)
        qs = handler(product) if handler else Product.objects.none()

        # exclude the original product itself and annotate
        qs = qs.exclude(id=product.id)
        return annotate_state_for_product(qs, self.request.user)

    def _base_qs(self):
        return Product.objects.select_related(
            'video', 'subtitle', 'expression', 'host', 'parent'
        ).prefetch_related('subtitle__expressions')

    def _for_video(self, product):
        # children which are subtitle products of this video product
        return self._base_qs().filter(parent=product, type=Product.PRODUCT_SUBTITLE)

    def _for_subtitle(self, product):
        # parent (video product) + children (expression products)
        parent = product.parent
        children_q = self._base_qs().filter(
            parent=product, type=Product.PRODUCT_EXPRESSION)
        if parent:
            return self._base_qs().filter(Q(pk=parent.pk) |
                                          Q(pk__in=children_q.values_list('pk', flat=True)))
        return children_q

    def _for_expression(self, product):
        # return parent (subtitle product) and grandparent (video product) if exist
        parent = product.parent
        grandparent = parent.parent if parent is not None else None
        pks = [p.pk for p in (parent, grandparent) if p is not None]
        return self._base_qs().filter(pk__in=pks) if pks else Product.objects.none()

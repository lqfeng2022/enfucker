from django.db.models import Case, When
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from interact.utils.recommendation import my_recommendation_engine
from interact.utils.annotates import annotate_state_for_product
from store.models import Product
from store.serializers.product import ProductSerializer
import logging

logger = logging.getLogger(__name__)  # store.view


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

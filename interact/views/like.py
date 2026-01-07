from django.db.models import Max
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin)
from store.serializers.product import ProductSerializer
from interact.permissions import AdminDelete
from interact.utils.annotates import annotate_state_for_product
from interact.utils.getmodels import get_product_model
from interact.models import Like
from interact.serializers.like import LikeSerializer, LikeAddSerializer


# '/store/liked-products' (list/get)
class LikeProductViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        Product = get_product_model()

        # Fetch product IDs the user has liked
        product_ids = Like.objects.filter(user=user, visible=True). \
            values('product_id')

        # Query the real Product instances
        # Prefetch relations (important for performance)
        queryset = Product.objects.filter(id__in=product_ids). \
            select_related('host', 'expression', 'subtitle', 'video', 'video__genre'). \
            prefetch_related('subtitle__expressions'). \
            annotate(latest_liked=Max('likes__updated_at'))

        # Apply user interaction annotations
        queryset = annotate_state_for_product(queryset, user)

        return queryset.order_by('-latest_liked')


# '/interact/likes' (upldate/delete)
class LikeViewSet(ListModelMixin, RetrieveModelMixin, DestroyModelMixin,
                  GenericViewSet):
    permission_classes = [IsAuthenticated, AdminDelete]
    serializer_class = LikeSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = Like.objects.filter(user=user, visible=True). \
            select_related('product', 'product__host', 'product__expression',
                           'product__subtitle', 'product__video')
        return queryset


# '/store/product/<pk>/like' (create(update))
class LikeAddViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LikeAddSerializer

    def get_queryset(self):
        user = self.request.user
        prod = self.kwargs['product_pk']
        return Like.objects.filter(user_id=user.id, product_id=prod)

    def get_serializer_context(self):
        return {
            'user_id': self.request.user.id,
            'product_id': self.kwargs['product_pk']
        }

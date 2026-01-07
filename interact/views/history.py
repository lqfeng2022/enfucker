from django.db.models import Max
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin,
    UpdateModelMixin)
from store.serializers.product import ProductSerializer
from interact.permissions import AdminDelete
from interact.utils.annotates import annotate_state_for_product
from interact.utils.getmodels import get_product_model
from interact.models import UserView
from interact.serializers.history import (
    ViewAddSerializer, ViewUpdateSerializer, ViewSerializer)


# '/store/viewed-products' (list/get)
class UserViewProductViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        Product = get_product_model()

        # Fetch product IDs the user has viewed
        product_ids = UserView.objects.filter(user=user, visible=True). \
            values('product_id')

        # Query the real Product instances
        # Prefetch relations (important for performance)
        queryset = Product.objects.filter(id__in=product_ids). \
            select_related('host', 'expression', 'subtitle', 'video', 'video__genre'). \
            prefetch_related('subtitle__expressions'). \
            annotate(latest_viewed=Max('userviews__updated_at'))

        # Apply user interaction annotations
        queryset = annotate_state_for_product(queryset, user)
        return queryset.order_by('-latest_viewed')


# '/interact/views' (update/delete)
class UserViewViewSet(ListModelMixin, RetrieveModelMixin, DestroyModelMixin,
                      UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, AdminDelete]

    def get_serializer_class(self):
        if self.action == 'update':
            return ViewUpdateSerializer
        return ViewSerializer

    # any user can view their only histories
    def get_queryset(self):
        user = self.request.user
        queryset = UserView.objects.filter(user=user, visible=True). \
            select_related('product', 'product__host', 'product__expression',
                           'product__subtitle', 'product__video')
        return queryset


# '/store/product/<pk>/view' (create(update))
class UserViewAddViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    serializer_class = ViewAddSerializer

    def get_queryset(self):
        user = self.request.user.id
        prod = self.kwargs['product_pk']

        return UserView.objects.filter(user_id=user, product_id=prod)

    def get_serializer_context(self):
        # Ensure session key exists (important for anonymous users)
        if not self.request.session.session_key:
            self.request.session.save()

        return {
            'user_id': self.request.user.id,
            'product_id': self.kwargs['product_pk']
        }

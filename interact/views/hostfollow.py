from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin)
from store.serializers.product import ProductSerializer
from store.serializers.host import HostSerializer
from interact.utils.getmodels import get_product_model, get_host_model
from interact.utils.annotates import (
    annotate_state_for_product, annotate_counts_for_host, annotate_follow_for_host)
from interact.models import Follow
from interact.serializers.hostfollow import (
    HostFollowSerializer, HostFollowAddSerializer, HostFollowAddSerializer)


# '/store/hosts/<pk>/follow' (create(update))
class HostFollowAddViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = HostFollowAddSerializer

    def get_queryset(self):
        user = self.request.user
        host = self.kwargs['host_pk']
        return Follow.objects.filter(user_id=user.id, host_id=host)

    def get_serializer_context(self):
        return {
            'user_id': self.request.user.id,
            'host_id': self.kwargs['host_pk']
        }


# '/followed/<pk>/' (list/get/delete)
class HostFollowViewSet(ListModelMixin, RetrieveModelMixin, DestroyModelMixin,
                        GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = HostFollowSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Follow.objects.select_related('host'). \
            filter(user=user, visible=True). \
            order_by('-updated_at')
        return queryset

    def perform_destroy(self, instance):
        instance.visible = False
        instance.save(update_fields=['visible'])


# 'store/followed-hosts/<pk>/' (list/get)
class HostFollowedViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = HostSerializer

    def get_queryset(self):
        user = self.request.user
        Host = get_host_model()

        queryset = Host.objects. \
            filter(followers__user=user, followers__visible=True)
        queryset = annotate_counts_for_host(queryset)
        queryset = annotate_follow_for_host(queryset, user)
        return queryset.order_by('-updated_at')


# 'store/followed-products/'
class HostFollowedProductsViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        Product = get_product_model()

        # 1)all visible followed hosts
        followed_hosts = Follow.objects. \
            filter(user=user, visible=True).values('host_id')

        # 2)filter products by followed hosts
        queryset = Product.objects. \
            select_related('host', 'video', 'subtitle', 'expression', 'video__genre'). \
            prefetch_related('subtitle__expressions'). \
            filter(host_id__in=followed_hosts). \
            distinct()

        # 3)annotate like/bookmark state
        queryset = annotate_state_for_product(queryset, user)

        # 4)sort newest first
        return queryset.order_by('-updated_at')

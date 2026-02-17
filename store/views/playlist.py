from django.db.models import Max, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from store.models import Playlist, PlaylistItem, Product
from store.serializers.playlist import PlaylistSerializer, PlaylistItemListSerializer
from store.serializers.product import ProductSerializer
from interact.utils.annotates import annotate_state_for_product


class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PlaylistSerializer
    queryset = Playlist.objects.select_related('host'). \
        annotate(items_count=Count('playlist_items'))

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['host']

    lookup_field = 'short_uuid'  # safe public ID


class PlaylistItemViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PlaylistItemListSerializer

    def get_queryset(self):
        return PlaylistItem.objects. \
            filter(playlist__short_uuid=self.kwargs['playlist_short_uuid']). \
            select_related(
                'product__video',
                'product__expression',
                'product__subtitle'
            ). \
            prefetch_related('product__subtitle__expressions'). \
            order_by('order')


# '/store/playlist/<short_uuid>/products/<pk>'
class PlaylistProductViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        playlist_uuid = self.kwargs['playlist_short_uuid']
        user = self.request.user

        playlist_filter = Q(
            playlist_items__playlist__short_uuid=playlist_uuid
        )

        queryset = (
            Product.objects.filter(playlist_filter).
            select_related(
                'host',
                'expression',
                'subtitle',
                'video',
                'video__genre',
            ).
            annotate(latest_added=Max(
                'playlist_items__updated_at',
                filter=playlist_filter
            ))
        )
        queryset = annotate_state_for_product(queryset, user)

        return queryset.order_by('-latest_added').distinct()

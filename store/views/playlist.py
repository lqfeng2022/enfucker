from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from store.models import Playlist, PlaylistItem
from store.serializers.playlist import PlaylistSerializer, PlaylistItemListSerializer


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

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from store.models import Playlist
from store.serializers.playlist import PlaylistSerializer, PlaylistSimpleSerializer


class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return PlaylistSimpleSerializer
        return PlaylistSerializer

    # URL becomes /store/playlists/<short_uuid>/
    lookup_field = 'short_uuid'  # safe public ID

    queryset = Playlist.objects. \
        prefetch_related(
            'playlist_items__product__video',
            'playlist_items__product__expression',
            'playlist_items__product__subtitle__expressions',
        ).select_related('host')

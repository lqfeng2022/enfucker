from django.db.models import Count, Q, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from store.models import Playlist, PlaylistItem, Product, Course
from store.serializers.playlist import (
    PlaylistSerializer, PlaylistItemListSerializer, CourseListSerializer,
    CourseSerializer
)
from store.serializers.product import ProductSerializer
from interact.utils.annotates import annotate_state_for_product


class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PlaylistSerializer
    queryset = Playlist.objects.select_related('host'). \
        annotate(items_count=Count('playlist_items')). \
        order_by('-updated_at')

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
                'host', 'expression', 'subtitle', 'video', 'video__genre',
            ).
            annotate(playlist_order=F('playlist_items__order'))
        )

        queryset = annotate_state_for_product(queryset, user)

        return queryset.order_by('playlist_order')


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

    queryset = Course.objects.select_related('host'). \
        annotate(items_count=Count('playlists'))

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['host']

    lookup_field = 'slug'

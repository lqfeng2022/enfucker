from django.db.models import Max, Count, Prefetch
from rest_framework import status
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
)
from store.models import Playlist
from store.serializers.product import ProductSerializer
from interact.utils.decorators import RetryOnDeadlock
from interact.utils.annotates import annotate_state_for_product
from interact.utils.getmodels import get_product_model
from interact.models import Collection, CollectionItem, SavedPlaylist
from interact.serializers.collection import (
    CollectionSerializer, CollectionUpdateSerializer, CollectionItemSerializer,
    CollectionItemAddSerializer, SavedPlaylistSerializer, SavedPlaylistAddSerializer
)


# '/interact/collection/<pk>'
class CollectionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'update':
            return CollectionUpdateSerializer
        return CollectionSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Collection.objects.filter(user_id=user.id). \
            prefetch_related(
                'items__product',
                'items__product__host',
                'items__product__video',
                'items__product__expression',
                'items__product__subtitle',
                'items__product__subtitle__expressions'
        )
        return queryset

    def get_serializer_context(self):
        return {
            'user_id': self.request.user.id,
            'request': self.request
        }

    # custom url: 'interact/collections/slug/<slug>'
    @action(detail=False, url_path='slug/(?P<slug>[^/.]+)', methods=['get', 'put', 'delete'])
    def retrieve_by_slug(self, request, slug=None):
        list_obj = self.get_queryset().filter(slug=slug).first()

        if not list_obj:
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'GET':
            serializer = self.get_serializer(list_obj)
            return Response(serializer.data)

        if request.method == 'PUT':
            serializer = self.get_serializer(list_obj, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        if request.method == 'DELETE':
            list_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


# '/interact/collections/<pk>/items/<pk>'
class CollectionItemViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin,
                            DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CollectionItemAddSerializer
        return CollectionItemSerializer

    def get_queryset(self):
        user = self.request.user
        collection = self.kwargs.get('collection_pk')

        queryset = CollectionItem.objects. \
            filter(collection__user=user, collection_id=collection). \
            select_related(
                'product__host',
                'product__expression',
                'product__video',
                'product__subtitle'
            )
        return queryset

    def get_serializer_context(self):
        return {'collection_id': self.kwargs['collection_pk']}

    # Adjust the HTTP status code
    @RetryOnDeadlock(retries=3)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        if getattr(serializer, '_was_created', False):
            status_code = status.HTTP_201_CREATED
        else:
            status_code = status.HTTP_200_OK  # silent success

        return Response(CollectionItemSerializer(item).data, status=status_code)


# '/interact/collections/<pk>/products/<pk>'
class CollectionProductViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        collection = self.kwargs['collection_pk']
        Product = get_product_model()

        product_ids = CollectionItem.objects. \
            filter(collection__user=user, collection_id=collection, visible=True). \
            values('product_id')

        queryset = Product.objects. \
            filter(id__in=product_ids). \
            select_related('host', 'expression', 'subtitle', 'video'). \
            annotate(latest_added=Max('items__updated_at'))

        queryset = annotate_state_for_product(queryset, user)

        return queryset.order_by('-latest_added')


# '/store/bookmarked-products/'
class BookmarkedProductViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        Product = get_product_model()

        queryset = (
            Product.objects.
            select_related(
                'host', 'video', 'subtitle', 'expression', 'video__genre'
            ).
            prefetch_related('subtitle__expressions').
            filter(items__collection__user=user, items__visible=True).
            annotate(latest_bookmark=Max('items__updated_at'))
        )

        queryset = annotate_state_for_product(queryset, user)
        return queryset.order_by('-latest_bookmark')


class SavedPlaylistViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin,
                           DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SavedPlaylistAddSerializer
        return SavedPlaylistSerializer

    def get_queryset(self):
        annotated_playlists = Playlist.objects. \
            select_related('course'). \
            annotate(items_count=Count('playlist_items'))
        return SavedPlaylist.objects. \
            filter(user=self.request.user). \
            prefetch_related(
                Prefetch('playlist', queryset=annotated_playlists)
            )

    def perform_create(self, serializer):
        SavedPlaylist.objects.get_or_create(
            user=self.request.user,
            playlist=serializer.validated_data['playlist']
        )

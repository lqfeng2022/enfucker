from django.db.models import Max, Count, Prefetch
from rest_framework import status
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
)
from store.models import Playlist, Course
from store.serializers.product import ProductSerializer
from interact.utils.decorators import RetryOnDeadlock
from interact.utils.annotates import annotate_state_for_product
from interact.utils.getmodels import get_product_model
from interact.models import Collection, CollectionItem, SavedPlaylist, SavedCourse
from interact.serializers.collection import (
    CollectionSerializer, CollectionUpdateSerializer, CollectionItemSerializer,
    CollectionItemAddSerializer, SavedPlaylistSerializer, SavedPlaylistAddSerializer,
    SavedCourseAddSerializer, SavedCourseSerializer
)


# '/interact/collection/<pk>'
class CollectionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    # lookup_field = 'short_uuid'

    def get_serializer_class(self):
        if self.action == 'update':
            return CollectionUpdateSerializer
        return CollectionSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Collection.objects.filter(user_id=user.id). \
            annotate(items_count=Count('items'))
        return queryset

    def get_serializer_context(self):
        return {
            'user_id': self.request.user.id,
            'request': self.request
        }

    # custom url: retrieve collection by short_uuid
    # NOTE: lookup_field = 'short_uuid' works fine on parent urls, BUT not work on nested urls
    @action(detail=False, url_path='slug/(?P<short_uuid>[^/.]+)', methods=['get', 'put', 'delete'])
    def retrieve_by_short_uuid(self, request, short_uuid=None):
        obj = self.get_queryset().filter(short_uuid=short_uuid).first()
        if not obj:
            return Response({'detail': 'Not found.'}, status=404)
        if request.method == 'GET':
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        if request.method == 'PUT':
            serializer = self.get_serializer(obj, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        if request.method == 'DELETE':
            obj.delete()
            return Response(status=204)

    # custom url: get all product related collections
    @action(detail=False, methods=['get'], url_path='products/(?P<product_id>\d+)')
    def collections_for_product(self, request, product_id=None):
        collections = Collection.objects. \
            filter(user=request.user, items__product_id=product_id). \
            distinct()
        serializer = CollectionSerializer(
            collections, many=True, context={'request': request}
        )
        return Response(serializer.data)

    # custom url: delte all product related collections
    @action(detail=False, methods=['delete'], url_path='product')
    def remove_product_from_collections(self, request):
        product_id = request.data.get('product_id')
        list_ids = request.data.get('listIds', [])

        if not product_id or not list_ids:
            return Response(
                {'detail': 'product_id and listIds are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        CollectionItem.objects.filter(
            collection_id__in=list_ids,
            product_id=product_id,
            collection__user=request.user
        ).delete()

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
            filter(collection__user=user, collection_id=collection,
                   visible=True). \
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
                'host',
                'video',
                'subtitle',
                'expression',
                'video__genre'
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
            annotate(product_count=Count('playlist_items'))
        return SavedPlaylist.objects.filter(user=self.request.user). \
            prefetch_related(
                Prefetch('playlist', queryset=annotated_playlists)
        )

    def perform_create(self, serializer):
        SavedPlaylist.objects.get_or_create(
            user=self.request.user,
            playlist=serializer.validated_data['playlist']
        )


class SavedCourseViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin,
                         DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SavedCourseAddSerializer
        return SavedCourseSerializer

    def get_queryset(self):
        annotated_courses = Course.objects. \
            select_related('host'). \
            annotate(playlist_count=Count('playlists'))
        return SavedCourse.objects. \
            filter(user=self.request.user). \
            prefetch_related(
                Prefetch('course', queryset=annotated_courses)
            )

    def perform_create(self, serializer):
        SavedCourse.objects.get_or_create(
            user=self.request.user,
            course=serializer.validated_data['course']
        )

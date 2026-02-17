from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Count
from interact.utils.annotates import annotate_follow_for_host, annotate_counts_for_host
from store.models import Host, Genre, Alphabet
from store.serializers.host import HostSerializer, GenreSerializer, AlphabetSerializer
import logging

logger = logging.getLogger(__name__)  # store.view


# '/store/host/'
class HostViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = HostSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Host.objects.all()
        queryset = annotate_counts_for_host(queryset)
        queryset = annotate_follow_for_host(queryset, user)
        return queryset

    # custom url: '/host/slug/<slug>'
    @action(detail=False, url_path='slug/(?P<slug>[^/.]+)', methods=['get'])
    def retrieve_by_slug(self, request, slug=None):
        try:
            host = self.get_queryset().get(slug=slug)
            serializer = self.get_serializer(host)
            return Response(serializer.data)
        except Host.DoesNotExist:
            logger.warning('Host not found for slug: %s', slug)
            return Response(
                {'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND
            )


# '/store/genres'
class GenreViewSet(ReadOnlyModelViewSet):
    queryset = Genre.objects. \
        annotate(videos_count=Count('videos')).all()

    # serializer = GenreSerializer(queryset, many=True) # a list of genres
    # genre = get_object_or_404(Genre.objects.annotate(videos_count=Count('videos')), pk=id)
    # serializer = GenreSerializer(genre)
    serializer_class = GenreSerializer


# '/store/alphabets'
class AlphabetViewSet(ReadOnlyModelViewSet):
    queryset = Alphabet.objects. \
        annotate(expressions_count=Count('expressions')).all()

    serializer_class = AlphabetSerializer

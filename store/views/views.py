from django.db.models import Count
from rest_framework.viewsets import ReadOnlyModelViewSet
from store.models import Genre, Alphabet
from store.serializers.serializer import GenreSerializer, AlphabetSerializer
import logging

logger = logging.getLogger(__name__)  # store.view


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

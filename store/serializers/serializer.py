from rest_framework import serializers
from store.models import Video, Genre, Expression, Subtitle, Alphabet


class GenreSerializer(serializers.ModelSerializer):
    videos_count = serializers.IntegerField(read_only=True)
    # read_only=True: prevent update/create related objects from Host endpoint

    class Meta:
        model = Genre
        fields = ['id', 'title', 'videos_count', 'created_at', 'updated_at']


class AlphabetSerializer(serializers.ModelSerializer):
    expressions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Alphabet
        fields = ['id', 'title', 'slug', 'expressions_count']


class VideoSerializer(serializers.ModelSerializer):
    genre = serializers.StringRelatedField()

    class Meta:
        model = Video
        fields = ['id', 'genre', 'kind', 'title',
                  'slug', 'released_year', 'original', 'cover', 'file']


class ExpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expression
        fields = ['id', 'title', 'slug', 'image']


class SubtitleSerializer(serializers.ModelSerializer):
    expressions = ExpressionSerializer(many=True, read_only=True)

    class Meta:
        model = Subtitle
        fields = ['id', 'order', 'content', 'expressions']

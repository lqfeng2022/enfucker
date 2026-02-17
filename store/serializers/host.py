from rest_framework import serializers
from store.models import Host, Video, Genre, Expression, Subtitle, Alphabet


class HostSimpleSerializer(serializers.ModelSerializer):
    portrait = serializers.ImageField(read_only=True)
    cover = serializers.ImageField(read_only=True)

    class Meta:
        model = Host
        fields = ['id', 'name', 'slug', 'portrait', 'cover', 'description']


class HostSerializer(serializers.ModelSerializer):
    portrait = serializers.ImageField(read_only=True)
    cover = serializers.ImageField(read_only=True)
    audio_intro = serializers.FileField(read_only=True)

    videos_count = serializers.IntegerField(read_only=True)
    subtitles_count = serializers.IntegerField(read_only=True)
    expressions_count = serializers.IntegerField(read_only=True)

    total_content = serializers.SerializerMethodField()

    followed = serializers.SerializerMethodField()

    class Meta:
        model = Host
        fields = ['id', 'name', 'slug', 'portrait', 'cover', 'audio_intro',
                  'description', 'total_content', 'videos_count', 'subtitles_count',
                  'expressions_count', 'followed', 'created_at', 'updated_at']

    def get_total_content(self, obj):
        return (getattr(obj, 'videos_count', 0) +
                getattr(obj, 'subtitles_count', 0) +
                getattr(obj, 'expressions_count', 0))

    def get_followed(self, obj):
        return getattr(obj, '_is_followed', False)


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

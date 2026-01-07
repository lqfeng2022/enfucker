from rest_framework import serializers
from store.models import Host


class HostSimpleSerializer(serializers.ModelSerializer):
    portrait = serializers.ImageField(
        source='host_profile.portrait', read_only=True)
    cover = serializers.ImageField(
        source='host_profile.cover', read_only=True)

    class Meta:
        model = Host
        fields = ['id', 'name', 'slug', 'portrait', 'cover']


class HostSerializer(serializers.ModelSerializer):
    portrait = serializers.ImageField(
        source='host_profile.portrait', read_only=True)
    cover = serializers.ImageField(
        source='host_profile.cover', read_only=True)

    videos_count = serializers.IntegerField(read_only=True)
    subtitles_count = serializers.IntegerField(read_only=True)
    expressions_count = serializers.IntegerField(read_only=True)

    total_content = serializers.SerializerMethodField()

    followed = serializers.SerializerMethodField()

    class Meta:
        model = Host
        fields = ['id', 'name', 'slug', 'portrait', 'cover', 'total_content',
                  'videos_count', 'subtitles_count', 'expressions_count',
                  'followed', 'created_at', 'updated_at']

    def get_total_content(self, obj):
        return (getattr(obj, 'videos_count', 0) +
                getattr(obj, 'subtitles_count', 0) +
                getattr(obj, 'expressions_count', 0))

    def get_followed(self, obj):
        return getattr(obj, '_is_followed', False)

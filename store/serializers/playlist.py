from rest_framework import serializers
from store.models import Playlist, PlaylistItem, Course
from store.serializers.product import ProductListSerializer
from store.serializers.host import HostSimpleSerializer


class CourseListSerializer(serializers.ModelSerializer):
    host = HostSimpleSerializer(read_only=True)
    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ['title', 'slug', 'host', 'cover', 'items_count',
                  'created_at', 'updated_at']


class PlaylistItemListSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = PlaylistItem
        fields = ['id', 'product', 'created_at', 'updated_at']


class PlaylistSimpleSerializer(serializers.ModelSerializer):
    short_uuid = serializers.CharField(read_only=True)
    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Playlist
        fields = ['order', 'title', 'slug', 'short_uuid',
                  'items_count', 'cover', 'created_at', 'updated_at']


class PlaylistSerializer(serializers.ModelSerializer):
    short_uuid = serializers.CharField(read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = ['order', 'title', 'slug', 'short_uuid', 'course',
                  'items_count', 'cover', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    host = HostSimpleSerializer(read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    playlists = PlaylistSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'host', 'cover', 'playlists',
                  'items_count', 'created_at', 'updated_at']

from rest_framework import serializers
from store.models import Playlist, PlaylistItem
from store.serializers.product import ProductListSerializer


class PlaylistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = PlaylistItem
        fields = ['id', 'product', 'created_at', 'updated_at']

    def get_thumbnail(self, obj):
        return obj.product.get_thumbnail_url()


class PlaylistSerializer(serializers.ModelSerializer):
    short_uuid = serializers.CharField(read_only=True)
    host_name = serializers.CharField(source='host.name', read_only=True)
    items_count = serializers.SerializerMethodField(read_only=True)
    playlist_items = PlaylistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = ['short_uuid', 'title', 'slug', 'host_name', 'items_count',
                  'playlist_items']

    def get_items_count(self, obj):
        return obj.playlist_items.count()


class PlaylistSimpleSerializer(serializers.ModelSerializer):
    short_uuid = serializers.CharField(read_only=True)
    host_name = serializers.CharField(source='host.name', read_only=True)
    items_count = serializers.SerializerMethodField(read_only=True)
    first_thumbnail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Playlist
        fields = ['short_uuid', 'title', 'slug', 'host_name', 'items_count',
                  'first_thumbnail', 'created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.playlist_items.count()

    def get_first_thumbnail(self, obj):
        # Use the model method for the first product thumbnail
        return obj.get_first_product_thumbnail()

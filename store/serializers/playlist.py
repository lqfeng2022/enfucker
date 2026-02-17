from rest_framework import serializers
from store.models import Playlist, PlaylistItem
from store.serializers.product import ProductListSerializer
from store.serializers.host import HostSimpleSerializer


class PlaylistItemListSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = PlaylistItem
        fields = ['id', 'product', 'created_at', 'updated_at']


class PlaylistSerializer(serializers.ModelSerializer):
    short_uuid = serializers.CharField(read_only=True)

    items_count = serializers.IntegerField(read_only=True)

    first_thumbnail = serializers.SerializerMethodField(read_only=True)

    host = HostSimpleSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = ['short_uuid', 'title', 'slug', 'host', 'items_count',
                  'first_thumbnail', 'created_at', 'updated_at']

    def get_first_thumbnail(self, obj):
        request = self.context.get('request')
        relative_url = obj.get_first_product_thumbnail()

        if relative_url and request:
            return request.build_absolute_uri(relative_url)

        return relative_url

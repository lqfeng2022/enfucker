from rest_framework import serializers
from store.models import Product
from store.serializers.host import HostSimpleSerializer
from store.mixins.product_content import ProductContentMixin


class ProductSimpleSerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'type', 'host']


class ProductChatSerializer(ProductContentMixin, serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'type', 'content']


class ProductListSerializer(ProductContentMixin, serializers.ModelSerializer):
    host = HostSimpleSerializer(read_only=True)
    content = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'type', 'host', 'content']


class ProductSerializer(ProductContentMixin, serializers.ModelSerializer):
    host = HostSimpleSerializer(read_only=True)
    content = serializers.SerializerMethodField()

    like_state = serializers.SerializerMethodField()
    bookmark_state = serializers.SerializerMethodField()
    chat_state = serializers.SerializerMethodField()
    followed = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'type', 'host', 'content', 'views_count', 'likes_count',
                  'like_state', 'bookmarks_count', 'bookmark_state',
                  'chat_state', 'followed', 'created_at', 'updated_at']

    def get_like_state(self, obj):
        return getattr(obj, '_is_liked', False)

    def get_bookmark_state(self, obj):
        return getattr(obj, '_is_bookmarked', False)

    def get_followed(self, obj):
        return getattr(obj, '_is_followed', False)

    def get_chat_state(self, obj):
        return getattr(obj, '_is_chatted', False)

from django.utils import text
from rest_framework import serializers
from store.serializers.product import ProductListSerializer
from store.serializers.playlist import PlaylistSerializer, CourseSerializer
from store.models import Playlist, Course
from interact.models import Collection, CollectionItem, SavedPlaylist, SavedCourse
from interact.utils.getmodels import get_product_model


class CollectionItemAddSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CollectionItem
        fields = ['id', 'product_id']

    def validate_product_id(self, value):
        Product = get_product_model()
        # Validate the product exists
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                'No product with the given ID was found.'
            )
        return value

    def create(self, validated_data):
        collection_id = self.context['collection_id']
        product_id = validated_data['product_id']

        item, created = CollectionItem.objects.get_or_create(
            collection_id=collection_id,
            product_id=product_id
        )

        # Inform the ViewSet whether this is a new or duplicate record
        self._was_created = created

        return item


class CollectionItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = CollectionItem
        fields = ['id', 'visible', 'product', 'created_at', 'updated_at']


class CollectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['title']

    # update an existing collection
    def update(self, instance, validated_data):
        # If title is updated, regenerate the slug only
        if 'title' in validated_data:
            validated_data['slug'] = text.slugify(validated_data['title'])
        return super().update(instance, validated_data)


class CollectionSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(read_only=True)
    short_uuid = serializers.CharField(read_only=True)

    items_count = serializers.IntegerField(read_only=True)

    first_thumbnail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'title', 'slug', 'short_uuid', 'items_count',
                  'first_thumbnail', 'created_at', 'updated_at']

    def get_first_thumbnail(self, obj):
        request = self.context.get('request')
        relative_url = obj.get_first_product_thumbnail()

        if relative_url and request:
            return request.build_absolute_uri(relative_url)

        return relative_url

    # create a new collection
    def create(self, validated_data):
        user = self.context['user_id']
        title = validated_data['title']
        validated_data['slug'] = text.slugify(title)

        return Collection.objects.create(user_id=user, **validated_data)


class SavedPlaylistAddSerializer(serializers.ModelSerializer):
    # accept playlist `short_uuid` from user
    playlist = serializers.SlugRelatedField(
        slug_field='short_uuid',
        queryset=Playlist.objects.all()
    )

    class Meta:
        model = SavedPlaylist
        fields = ['playlist']


class SavedPlaylistSerializer(serializers.ModelSerializer):
    playlist = PlaylistSerializer(read_only=True)

    class Meta:
        model = SavedPlaylist
        fields = ['id', 'playlist', 'saved_at']


class SavedCourseAddSerializer(serializers.ModelSerializer):
    course = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Course.objects.all()
    )

    class Meta:
        model = SavedCourse
        fields = ['course']


class SavedCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)

    class Meta:
        model = SavedPlaylist
        fields = ['id', 'course', 'saved_at']

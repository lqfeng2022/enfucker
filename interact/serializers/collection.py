from django.utils import text
from rest_framework import serializers
from store.serializers.product import ProductListSerializer
from interact.models import Collection, CollectionItem
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
        # If title is updated, regenerate the slug
        if 'title' in validated_data:
            validated_data['slug'] = text.slugify(validated_data['title'])
        return super().update(instance, validated_data)


class CollectionSerializer(serializers.ModelSerializer):
    slug = serializers.StringRelatedField(read_only=True)
    items = CollectionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'title', 'slug', 'items', 'created_at', 'updated_at']

    # create a new collection
    def create(self, validated_data):
        user = self.context['user_id']
        title = validated_data['title']
        validated_data['slug'] = text.slugify(title)

        return Collection.objects.create(user_id=user, **validated_data)

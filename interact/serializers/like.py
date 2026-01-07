from rest_framework import serializers
from store.serializers.product import ProductSimpleSerializer
from interact.models import Like


class LikeSerializer(serializers.ModelSerializer):
    product = ProductSimpleSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'visible', 'product', 'created_at', 'updated_at']


class LikeAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'product_id', 'visible', 'created_at', 'updated_at']

    # update the existing one or create a new one
    def create(self, validated_data):
        user = self.context['user_id']
        prod = self.context['product_id']
        visible = validated_data.get('visible', True)

        like, _ = Like.objects.update_or_create(
            user_id=user, product_id=prod,
            defaults={'visible': visible}
        )
        return like

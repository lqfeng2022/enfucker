from rest_framework import serializers
from store.serializers.product import ProductSimpleSerializer
from interact.models import UserView


class ViewAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserView
        fields = ['id']

    # update the existing one or create a new one
    def create(self, validated_data):
        user = self.context['user_id']
        prod = self.context['product_id']

        obj, created = UserView.objects.get_or_create(
            user_id=user, product_id=prod,
            defaults={'visible': True, 'count': 1}
        )

        if not created:
            obj.visible = True
            obj.count += 1
            obj.save()
        return obj


class ViewSerializer(serializers.ModelSerializer):
    product = ProductSimpleSerializer(read_only=True)

    class Meta:
        model = UserView
        fields = ['id', 'product', 'visible', 'created_at', 'updated_at']


class ViewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserView
        fields = ['visible']

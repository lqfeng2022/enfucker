from store.models import Product


class ProductContentMixin:
    """
    Provides a reusable get_content for product serializers.
    Uses lazy imports to avoid circular dependencies.
    """

    def get_content(self, obj):
        if obj.type == Product.PRODUCT_VIDEO and obj.video:
            from store.serializers.serializer import VideoSerializer
            return VideoSerializer(obj.video, context=self.context).data

        if obj.type == Product.PRODUCT_EXPRESSION and obj.expression:
            from store.serializers.serializer import ExpressionSerializer
            return ExpressionSerializer(obj.expression, context=self.context).data

        if obj.type == Product.PRODUCT_SUBTITLE and obj.subtitle:
            from store.serializers.serializer import SubtitleSerializer
            return SubtitleSerializer(obj.subtitle, context=self.context).data

        return None

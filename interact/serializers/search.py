from rest_framework import serializers
from interact.utils.cleancontent import clean_content
from interact.models import Search


class SearchUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = ['visible']


class SearchSerializer(serializers.ModelSerializer):
    visible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Search
        fields = ['id', 'content', 'visible', 'created_at']

    # update the existing one or create a new one
    def create(self, validated_data):
        user = self.context['user_id']
        content = clean_content(validated_data['content'])

        search, _ = Search.objects.update_or_create(
            user_id=user, content=content,
            defaults={'visible': True}
        )
        return search

from rest_framework import serializers
from store.serializers.host import HostSimpleSerializer
from interact.models import Follow


class HostFollowAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'host_id', 'visible', 'created_at', 'updated_at']

    # update the existing one or create a new one
    def create(self, validated_data):
        user = self.context['user_id']
        host = self.context['host_id']
        visible = validated_data.get('visible', True)

        hostFollow, _ = Follow.objects.update_or_create(
            user_id=user, host_id=host,
            defaults={'visible': visible}
        )
        return hostFollow


class HostFollowSerializer(serializers.ModelSerializer):
    host = HostSimpleSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'host', 'created_at', 'updated_at']

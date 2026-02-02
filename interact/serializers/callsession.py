from rest_framework import serializers
from interact.models import CallSession
from interact.serializers.chatsession import ChatMessageSerializer


class CallSessionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallSession
        fields = ['id', 'uuid', 'state', 'started_at', 'ended_at',
                  'duration_seconds', 'cost']


class CallSessionAddSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    state = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CallSession
        fields = ['id', 'uuid', 'state']


class CallSessionSerializer(serializers.ModelSerializer):
    transcripts = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = CallSession
        fields = ['id', 'uuid', 'state', 'started_at', 'ended_at', 'duration_seconds',
                  'cost', 'summary', 'transcripts']

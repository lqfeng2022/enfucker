from rest_framework import serializers
from store.serializers.product import ProductChatSerializer
from store.serializers.host import HostSimpleSerializer
from interact.models import ChatMessage, ChatSession
from interact.usecases.stt import create_user_message
from interact.usecases.chat import get_assistant_message
from interact.usecases.enhancement import assistant_tts_enhancement
from interact.usecases.tts import assistant_tts_audio
from interact.validators import validate_text_audio_input


# ChatMessage serializers
class ChatMessageAddSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True)
    content = serializers.CharField(max_length=2000, required=False,
                                    allow_blank=False)
    audio = serializers.FileField(required=False)
    is_voice = serializers.BooleanField(default=False)

    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'audio', 'content', 'is_voice', 'is_enhancement',
                  'created_at']

    def validate(self, attrs):
        try:
            validated = validate_text_audio_input(
                content=attrs.get('content'),
                audio=attrs.get('audio'),
            )
        except ValueError as e:
            raise serializers.ValidationError(str(e))

        # Replace attrs with normalized values
        attrs.update(validated)
        return attrs

    def create(self, validated_data):
        session = self.context['session']
        content = validated_data.get('content', '')
        audio = validated_data.pop('audio', None)

        is_voice = validated_data.pop('is_voice', False)
        enhancement = validated_data.pop('is_enhancement', False)

        # 1)Create USER message
        user_msg = create_user_message(
            session=session, content=content, audio=audio
        )

        # 2)LLM assistant message
        assistant_msg = get_assistant_message(
            session=session, user_msg=user_msg
        )

        # STT failed or empty input
        if assistant_msg is None:
            return user_msg

        # 3)Optional enhancement
        if is_voice and enhancement:
            assistant_tts_enhancement(
                message=assistant_msg, is_enhancement=enhancement
            )

        # 4)Optional TTS
        if is_voice:
            assistant_tts_audio(message=assistant_msg, is_voice=is_voice)

        session.save()  # update session timestamp
        return assistant_msg


class ChatMessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['visible']


class ChatMessageSerializer(serializers.ModelSerializer):
    audio = serializers.FileField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'audio', 'created_at']


# ChatSession serializers
class ChatSessionAddSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'visible', 'user_id', 'product_id', 'messages',
                  'created_at']

    def create(self, validated_data):
        user = self.context['user']
        product = self.context.get('product')
        visible = validated_data.get('visible', True)

        session, _ = ChatSession.objects.update_or_create(
            user=user, host=product.host, product=product, defaults={'visible': visible})

        if validated_data.get('visible') is False:
            session.messages.update(visible=False)

        return session


class ChatSessionListSerializer(serializers.ModelSerializer):
    host = HostSimpleSerializer(read_only=True)
    product = ProductChatSerializer(read_only=True)

    # read from annotation, not SerializerMethodField
    messages_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'messages_count', 'host', 'product', 'summary',
                  'latest_chat', 'created_at', 'updated_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    host = HostSimpleSerializer(read_only=True)
    product = ProductChatSerializer(read_only=True)
    host_id = serializers.IntegerField(write_only=True, required=False)  # NEW

    # messages = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'visible', 'created_at', 'updated_at', 'host', 'product',
                  'host_id']  # include host_id in fields

    # def get_messages(self, session):
    #     qs = session.messages.filter(visible=True).order_by('created_at')
    #     # ADD `context=self.context`,
    #     # pass this serializer the context, so it contains request from viewset
    #     return ChatMessageSerializer(qs, many=True, context=self.context).data

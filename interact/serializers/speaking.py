from django.db.models import Max
from rest_framework import serializers
from interact.models import (
    MockTest, SpeakingAnswer, SpeakingAttempt, SpeakingRewrite, SpeakingEvaluation)


# List Mock Tests
class MockTestSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = MockTest
        fields = ['id', 'title', 'total_questions', 'created_at']

    def get_total_questions(self, obj):
        return obj.playlist.products.count()


# Start Attempt
class SpeakingAttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingAttempt
        fields = ['id', 'started_at']

    def create(self, validated_data):
        user = self.context['user']
        mock_test = self.context.get('mock_test')

        existing = SpeakingAttempt.objects.filter(
            user=user,
            mock_test=mock_test,
            status='in_progress'
        ).first()

        if existing:
            return existing

        return SpeakingAttempt.objects.create(
            user=user,
            mock_test=mock_test
        )


# Submit Answer
class SpeakingAnswerCreateSerializer(serializers.ModelSerializer):
    audio = serializers.FileField(required=False)

    class Meta:
        model = SpeakingAnswer
        fields = ['id', 'audio']

    def validate(self, attrs):
        attempt = self.context['attempt']

        if attempt.status != 'in_progress':
            raise serializers.ValidationError("Attempt already completed.")

        return attrs

    def create(self, validated_data):
        attempt = self.context['attempt']
        audio = validated_data['audio']

        # Get next order safely
        last_order = attempt.answers.aggregate(Max('order'))['order__max'] or 0
        next_order = last_order + 1

        # Get corresponding product (question)
        playlist = attempt.mock_test.playlist

        try:
            product = playlist.products.all().order_by('id')[next_order - 1]
        except IndexError:
            raise serializers.ValidationError("No more questions.")

        # Prevent duplicate (extra safety)
        if SpeakingAnswer.objects.filter(
            attempt=attempt,
            product=product
        ).exists():
            raise serializers.ValidationError("Answer already exists.")

        answer = SpeakingAnswer.objects.create(
            attempt=attempt,
            product=product,
            order=next_order,
            audio=audio,
            status='pending'
        )

        # trigger async (later)
        # process_answer.delay(answer.id)

        return answer


class SpeakingEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingEvaluation
        fields = ['overall_score', 'scores', 'feedback']


class SpeakingRewriteSerializer(serializers.ModelSerializer):
    content = serializers.CharField(read_only=True)

    class Meta:
        model = SpeakingRewrite
        fields = ['content']


class SpeakingAnswerSerializer(serializers.ModelSerializer):
    evaluation = SpeakingEvaluationSerializer(read_only=True)
    rewrite = SpeakingRewriteSerializer(read_only=True)

    class Meta:
        model = SpeakingAnswer
        fields = ['id', 'order', 'audio', 'audio_seconds', 'transcript',
                  'status', 'evaluation', 'rewrite', 'created_at']


# Get Attempt
class SpeakingAttemptSerializer(serializers.ModelSerializer):
    answers = SpeakingAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = SpeakingAttempt
        fields = ['id', 'status', 'overall_score', 'started_at',
                  'completed_at', 'answers']

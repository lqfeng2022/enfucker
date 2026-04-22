from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin
from interact.models import SpeakingAttempt, SpeakingAnswer, MockTest
from interact.serializers.speaking import (
    SpeakingAttemptCreateSerializer, SpeakingAttemptSerializer, SpeakingAnswerSerializer,
    SpeakingAnswerCreateSerializer, MockTestSerializer)


# [ CONTENT LAYER ]
# GET /mock-tests/<id>
class MockTestViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MockTestSerializer

    def get_queryset(self):
        return MockTest.objects.select_related('playlist').all()


# [ ACTION LAYER ]
# POST /mock-tests/<id>/attempts/
class MockTestAttemptViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SpeakingAttemptCreateSerializer

    def get_queryset(self):
        return SpeakingAttempt.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        mock_test_id = self.kwargs[mock_test_id]
        mock_test = get_object_or_404(MockTest, pk=mock_test_id)
        return {
            'request': self.request,
            'mock_test': mock_test
        }


# [ DATA LAYER ]
# GET /attempts/<id>/
class SpeakingAttemptViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SpeakingAttemptSerializer

    def get_queryset(self):
        return (
            SpeakingAttempt.objects.
            filter(user=self.request.user).
            prefetch_related('answers__evaluation', 'answers__rewrite')
        )


# POST /attempts/<id>/answers/
class SpeakingAnswerViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        attempt_id = self.kwargs['attempt_id']
        user = self.request.user
        return (
            SpeakingAnswer.objects.
            filter(attempt_id=attempt_id, attempt__user=user).
            select_related('evaluation', 'rewrite')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return SpeakingAnswerCreateSerializer
        return SpeakingAnswerSerializer

    def get_serializer_context(self):
        attempt_id = self.kwargs['attempt_id']
        user = self.request.user
        attempt = get_object_or_404(SpeakingAttempt, pk=attempt_id, user=user)
        return {
            'request': self.request,
            'attempt': attempt
        }

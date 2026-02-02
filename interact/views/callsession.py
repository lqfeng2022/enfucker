from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin
from interact.models import CallSession, ChatSession
from interact.serializers.callsession import (
    CallSessionListSerializer, CallSessionAddSerializer, CallSessionSerializer)


class CallSessionViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin,
                         GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CallSessionListSerializer
        if self.action == 'create':
            return CallSessionAddSerializer
        return CallSessionSerializer

    def get_chat_session(self):
        chat_id = self.kwargs['session_pk']
        return get_object_or_404(ChatSession, id=chat_id, user=self.request.user,
                                 visible=True)

    def get_queryset(self):
        chat = self.get_chat_session()
        return CallSession.objects.filter(session=chat). \
            prefetch_related('transcripts').order_by('-started_at')

    def perform_create(self, serializer):
        chat = self.get_chat_session()
        # Create and save CallSession using serializer.save()
        serializer.save(session=chat, state=CallSession.ACTIVE)

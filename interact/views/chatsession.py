from django.db.models import Count, Q
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, UpdateModelMixin, CreateModelMixin,
    DestroyModelMixin)
from interact.permissions import AdminDelete
from interact.models import ChatSession, ChatMessage
from interact.serializers.chatsession import (
    ChatSessionAddSerializer, ChatSessionListSerializer, ChatSessionSerializer,
    ChatMessageAddSerializer, ChatMessageUpdateSerializer, ChatMessageSerializer)
from interact.utils.getmodels import get_product_model, get_default_host


# '/store/product/<pk>/chatsession/'
class ChatSessionAddViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatSessionAddSerializer
        return ChatSessionListSerializer

    def get_queryset(self):
        user = self.request.user
        prod = self.kwargs['product_pk']
        return ChatSession.objects. \
            filter(user_id=user.id, product_id=prod, visible=True)

    # pass extra info, like user_id from the URL
    def get_serializer_context(self):
        Product = get_product_model()
        product_obj = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        return {'user': self.request.user, 'product': product_obj}


# '/interact/chatsessions/<pk>/'
class ChatSessionViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin,
                         DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer

    def get_queryset(self):
        user = self.request.user
        return ChatSession.objects.filter(user=user, visible=True). \
            select_related('user', 'host', 'product', 'product__host', 'product__video',
                           'product__video__genre', 'product__expression', 'product__subtitle'). \
            prefetch_related('product__subtitle__expressions'). \
            annotate(messages_count=Count('messages', filter=Q(messages__visible=True))). \
            order_by('-updated_at')

    def perform_create(self, serializer):
        # serializer.save(user=self.request.user, host=get_default_host())
        user = self.request.user
        host = get_default_host()

        try:
            with transaction.atomic():
                session, _ = ChatSession.objects.get_or_create(
                    user=user, host=host, product_key=0,  # NULL product chat
                    defaults={'product': None, 'visible': True},
                )
        except IntegrityError:
            # Race-condition fallback
            session = ChatSession.objects. \
                get(user=user, host=host, product_key=0)

        # Revive soft-deleted session if needed
        if not session.visible:
            session.visible = True
            session.save(update_fields=['visible'])

        serializer.instance = session

    def perform_destroy(self, instance):
        # Soft delete the session
        instance.visible = False
        instance.save(update_fields=['visible'])
        # Soft delete all its messages
        instance.messages.update(visible=False)


# '/interact/chatsessions/<pk>/messages/<pk>'
class ChatMessageViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin,
                         UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, AdminDelete]

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatMessageAddSerializer
        elif self.action == 'update':
            return ChatMessageUpdateSerializer
        return ChatMessageSerializer

    def get_queryset(self):
        user = self.request.user
        session = self.kwargs['session_pk']
        queryset = ChatMessage.objects. \
            filter(session_id=session, session__user=user, visible=True)
        return queryset

    def get_serializer_context(self):
        user = self.request.user
        context = super().get_serializer_context()
        context['session'] = get_object_or_404(
            ChatSession, pk=self.kwargs['session_pk'], user=user.id
        )
        return context

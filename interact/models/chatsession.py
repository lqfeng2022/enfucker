import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from interact.utils.mediauploadto import chat_audio_upload_to


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# interact_chatsession
class ChatSession(AbstractCommon):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("ja", "Japanese"),
        ("zh", "Chinese"),
        ("fr", "French"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='chat_sessions')
    host = models.ForeignKey(settings.STORE_HOST_MODEL, on_delete=models.CASCADE,
                             related_name='chat_sessions')

    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)

    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='chat_sessions')
    product_key = models.IntegerField(editable=False)
    visible = models.BooleanField(default=True)

    latest_chat = models.TextField(max_length=255, blank=True)

    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0,
                               help_text="Cached sum of ModelUsage costs (derived)")

    # financial projection
    credits_used = models.PositiveIntegerField(default=0)

    # usage projection
    user_audio_seconds = models.PositiveIntegerField(default=0)
    assistant_audio_seconds = models.PositiveIntegerField(default=0)
    call_audio_seconds = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"Chat Session - {self.id}"

    def save(self, *args, **kwargs):
        self.product_key = self.product_id or 0

        # Set language from host (only if not already set)
        if not self.language and self.host_id:
            # Avoid extra query if possible
            if hasattr(self.host, "language") and self.host.language:
                self.language = self.host.language.code

        super().save(*args, **kwargs)

    class Meta:
        unique_together = [('user', 'host', 'product_key')]
        verbose_name_plural = 'Chat Sessions'
        ordering = ['-updated_at']


# interact_callsession
class CallSession(models.Model):
    ACTIVE = 'active'
    ENDED = 'ended'
    TERMINATED = 'terminated'

    STATE_CHOICES = [(ACTIVE, 'Active'), (ENDED, 'Ended'),
                     (TERMINATED, 'Terminated'),]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE,
                                related_name='calls')

    # Public identifier (used by frontend & websocket)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False,
                            db_index=True)
    state = models.CharField(max_length=12, choices=STATE_CHOICES,
                             default=ACTIVE)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    duration_seconds = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    summary = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'CallSession({self.id})'

    def end(self):
        if self.state != self.ACTIVE:
            return
        self.ended_at = timezone.now()
        self.duration_seconds = int(
            (self.ended_at - self.started_at).total_seconds()
        )
        self.state = self.ENDED
        self.save(update_fields=['ended_at', 'duration_seconds', 'state'])

    class Meta:
        verbose_name_plural = 'Chat Call Sessions'
        ordering = ['-started_at']


# interact_chatmessage
class ChatMessage(models.Model):
    USER, ASSISTANT = 'user', 'assistant'

    ROLE_CHOICES = [(USER, 'User'), (ASSISTANT, 'Assistant')]

    TYPE_CHOICES = [('text', 'Text'), ('audio', 'Audio'), ('call', 'Call')]

    created_at = models.DateTimeField(auto_now_add=True)

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE,
                                related_name='messages')
    call_session = models.ForeignKey(CallSession, on_delete=models.PROTECT, null=True,
                                     blank=True, related_name='messages', editable=False)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()

    type = models.CharField(max_length=10, choices=TYPE_CHOICES,
                            default='text')

    is_enhancement = models.BooleanField(default=False)
    enhanced_content = models.TextField(blank=True)

    is_voice = models.BooleanField(default=False)
    audio = models.FileField(upload_to=chat_audio_upload_to, null=True,
                             blank=True)
    audio_seconds = models.IntegerField(blank=True, default=0)

    visible = models.BooleanField(default=True)

    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    event = models.ForeignKey('SessionEvent', null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='messages')

    def save(self, *args, **kwargs):
        if self.call_session_id:
            self.type = 'call'
        elif self.is_voice:
            self.type = 'audio'
        else:
            self.type = 'text'
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.id}'

    class Meta:
        verbose_name_plural = 'Chat Session Messages'
        ordering = ['created_at']

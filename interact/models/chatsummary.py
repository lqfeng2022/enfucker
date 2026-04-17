from django.db import models
from .chatsession import ChatSession


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# interact_sessionevent
# event-specific, daily event memory capture
class SessionEvent(AbstractCommon):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE,
                                related_name='events')

    title = models.CharField(max_length=255)
    content = models.TextField()
    topics = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.title} - {self.id}"

    class Meta:
        verbose_name_plural = 'Chat Session Events'


# interact_sessionsummary
# session-wide memory, user profile, agent adaptation
class SessionSummary(AbstractCommon):
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE,
                                   related_name='sessionsummary')

    content = models.TextField()  # core summary content
    topics = models.JSONField(default=list, blank=True)

    current = models.TextField(blank=True)  # temporary current memory

    def __str__(self):
        return f"SessionSummary - {self.session_id}"

    class Meta:
        verbose_name_plural = 'Chat Session Summary'

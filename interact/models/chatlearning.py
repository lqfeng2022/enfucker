from django.db import models
from .chatsession import ChatMessage


# interact_messagerewrite
# learning-specific, content rewrite & vocab/phrase capture
class MessageRewrite(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    message = models.OneToOneField(ChatMessage, on_delete=models.CASCADE,
                                   related_name='learning')

    content = models.TextField()  # call LLM rewrite user message

    vocabulary = models.JSONField(default=list, blank=True)
    phrase = models.JSONField(default=list, blank=True)
    note = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"MessageRewrite - {self.id}"

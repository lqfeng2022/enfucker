from django.conf import settings
from django.db import models
from .chatsession import ChatSession, ChatMessage, CallSession


# interact_modelusage
class ModelUsage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name='usage_costs', editable=False)
    message = models.ForeignKey(ChatMessage, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='usage_costs', editable=False)
    session = models.ForeignKey(ChatSession, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='usage_costs', editable=False)

    call_session = models.ForeignKey(CallSession, null=True, blank=True,  on_delete=models.SET_NULL,
                                     related_name='usage_costs', editable=False)

    chat_model = models.ForeignKey(settings.AI_MODELPROVIDER_MODEL, on_delete=models.CASCADE,
                                   related_name='usage_costs')

    # Immutable snapshot copied from ModelProvider at creation
    step = models.CharField(max_length=30, db_index=True, editable=False)
    unit_price = models.DecimalField(max_digits=12, decimal_places=6,
                                     editable=False)
    units = models.DecimalField(max_digits=12, decimal_places=3,
                                help_text='1K-tokens, seconds, characters')
    cost = models.DecimalField(max_digits=12, decimal_places=6)

    def __str__(self) -> str:
        return f'{self.units}'

    class Meta:
        verbose_name_plural = 'Chat Model Usages'
        ordering = ['id']
        indexes = [models.Index(fields=['step']),
                   models.Index(fields=['created_at'])]


# interact_debitledger
class DebitLedger(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='credit_ledgers')

    usage = models.OneToOneField(ModelUsage, on_delete=models.PROTECT)

    amount = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f'{self.amount} credits'

    class Meta:
        verbose_name_plural = 'User Debit Ledgers'
        ordering = ['created_at']

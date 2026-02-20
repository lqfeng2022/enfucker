import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from store.utils import short_uuid
from .utils.mediauploadto import chat_audio_upload_to


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# interact_follow
class Follow(AbstractCommon):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='followings')
    host = models.ForeignKey(settings.STORE_HOST_MODEL, on_delete=models.CASCADE,
                             related_name='followers')

    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.host.slug}[{self.user.username}]'

    class Meta:
        unique_together = ('user', 'host')  # prevent duplicates
        verbose_name_plural = 'Followings'
        ordering = ['id']


# interact_search
class Search(AbstractCommon):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='searches')

    content = models.CharField(max_length=255)
    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'Search No. {self.pk}'

    class Meta:
        unique_together = ('user', 'content')
        verbose_name_plural = 'Searches'
        ordering = ['-created_at']


# interact_userview
class UserView(AbstractCommon):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='userviews')
    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.CASCADE,
                                related_name='userviews')

    visible = models.BooleanField(default=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'view No. {self.pk}'

    class Meta:
        unique_together = [('user', 'product')]
        verbose_name_plural = 'Histories'
        ordering = ['-updated_at']


# interact_like
class Like(AbstractCommon):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='likes')
    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.CASCADE,
                                related_name='likes')

    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        unique_together = [('user', 'product')]
        ordering = ['-created_at']


# interact_collection
class Collection(AbstractCommon):
    short_uuid = models.CharField(max_length=22, unique=True, editable=False,
                                  default=short_uuid)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='collections')
    products = models.ManyToManyField(settings.STORE_PRODUCT_MODEL, through='CollectionItem',
                                      related_name='collections')

    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)  # optional

    def __str__(self) -> str:
        return f'{self.title}'

    def get_first_product_thumbnail(self):
        """
        Return the thumbnail URL of the first product in this collection.
        If no products exist, returns None.
        """
        first_item = self.items.filter(visible=True). \
            select_related('product__video', 'product__expression',
                           'product__subtitle'). \
            prefetch_related('product__subtitle__expressions') \
            .first()

        if first_item and first_item.product:
            return first_item.product.get_thumbnail_url()

        return None

    class Meta:
        unique_together = [('user', 'title')]
        ordering = ['-created_at']


# interact_collectionitem
class CollectionItem(AbstractCommon):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='items')
    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL,
                                on_delete=models.CASCADE, related_name='items')

    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.product}'

    class Meta:
        unique_together = [('collection', 'product')]
        ordering = ['-created_at']


# interact_savedplaylist
class SavedPlaylist(models.Model):
    saved_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='saved_playlists')
    playlist = models.ForeignKey('store.Playlist', on_delete=models.CASCADE,
                                 related_name='saved_playlists')

    class Meta:
        unique_together = [('user', 'playlist')]
        ordering = ['-saved_at']


# interact_savedcourse
class SavedCourse(models.Model):
    saved_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='saved_courses')
    course = models.ForeignKey('store.Course', on_delete=models.CASCADE,
                               related_name='saved_courses')

    class Meta:
        unique_together = [('user', 'course')]
        ordering = ['-saved_at']


# interact_chatsession
class ChatSession(AbstractCommon):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='chat_sessions')
    host = models.ForeignKey(settings.STORE_HOST_MODEL, on_delete=models.CASCADE,
                             related_name='chat_sessions')

    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='chat_sessions')
    product_key = models.IntegerField(editable=False)
    visible = models.BooleanField(default=True)

    summary = models.TextField(blank=True)
    # marks the last message already summarized
    summary_upto_message = models.ForeignKey('ChatMessage', null=True, blank=True,
                                             on_delete=models.SET_NULL, related_name='chat_sessions')

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
        return f'{self.id}'

    def save(self, *args, **kwargs):
        self.product_key = self.product_id or 0
        super().save(*args, **kwargs)

    class Meta:
        unique_together = [('user', 'host', 'product_key')]
        ordering = ['-updated_at']


# interact_callsession
class CallSession(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE,
                                related_name='calls')

    # Public identifier (used by frontend & websocket)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False,
                            db_index=True)
    ACTIVE = 'active'
    ENDED = 'ended'
    TERMINATED = 'terminated'
    STATE_CHOICES = [(ACTIVE, 'Active'), (ENDED, 'Ended'),
                     (TERMINATED, 'Terminated'),]
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
        verbose_name_plural = 'Call Sessions'
        ordering = ['-started_at']


# interact_chatmessage
class ChatMessage(models.Model):
    USER = 'user'
    ASSISTANT = 'assistant'
    ROLE_CHOICES = [(USER, 'User'), (ASSISTANT, 'Assistant')]

    created_at = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE,
                                related_name='messages')
    call_session = models.ForeignKey(CallSession, on_delete=models.PROTECT, null=True,
                                     blank=True, related_name='messages', editable=False)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()

    is_enhancement = models.BooleanField(default=False)
    enhanced_content = models.TextField(blank=True)

    is_voice = models.BooleanField(default=False)
    audio = models.FileField(upload_to=chat_audio_upload_to, null=True,
                             blank=True)
    audio_seconds = models.IntegerField(blank=True, default=0)

    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0,
                               help_text="Cached sum of ModelUsage costs (derived)")

    def __str__(self) -> str:
        return f'{self.id}'

    class Meta:
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']


# interact_modelusage
class ModelUsage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name='usage_costs', editable=False)
    message = models.ForeignKey(ChatMessage, null=True, blank=True, on_delete=models.CASCADE,
                                related_name='usage_costs', editable=False)
    session = models.ForeignKey(ChatSession, null=True, blank=True, on_delete=models.PROTECT,
                                related_name='usage_costs', editable=False)

    call_session = models.ForeignKey(CallSession, null=True, blank=True,  on_delete=models.PROTECT,
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
        verbose_name_plural = 'Model Usages'
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
        ordering = ['created_at']

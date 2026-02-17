from django.contrib import admin
from interact.mixins.admin import (
    ChatMessageCountMinxin, ChatSessionLinkMixin, CollectionItemCountMinxin,
    CollectionLinkMixin, is_english_like_prefix)
from store.mixins.admin import (
    FormattedCreateDateMixin, FormattedUpdateDateMixin, FormattedSavedDateMixin,
    PlaylistLinkMixin)
from .mixins.admin import AudioThumbnailMixin
from . import models


# 1)Search admin
@admin.register(models.Search)
class SearchAdmin(FormattedCreateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'user', 'content', 'visible', 'formatted_created_at']
    list_per_page = 15
    list_select_related = ['user']
    list_editable = ['visible']
    list_filter = ['created_at']

    search_fields = ['user__first_name__istartswith',
                     'user__last_name__istartswith']


# 2)Views admin
@admin.register(models.UserView)
class UserViewsAdmin(FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'user__username', 'product__id',
                    'product', 'visible', 'count', 'formatted_updated_at']
    list_per_page = 15
    list_editable = ['visible']
    list_select_related = ['user', 'product']
    list_filter = ['product__type', 'updated_at']

    search_fields = ['user__first_name__istartswith',
                     'user__last_name__istartswith']


# 3)Like admin
@admin.register(models.Like)
class LikeAdmin(FormattedCreateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'user__username', 'product__id',
                    'product', 'visible', 'formatted_created_at']
    list_per_page = 15
    list_editable = ['visible']
    list_filter = ['product__type', 'created_at']


# 4)Collection, CollectionItem admins
# A)Collection admin
class CollectionItemInline(admin.StackedInline):
    model = models.CollectionItem

    autocomplete_fields = ['product']

    extra = 0
    min_num = 0
    max_num = 10


@admin.register(models.Collection)
class CollectionAdmin(CollectionItemCountMinxin, FormattedCreateDateMixin,
                      admin.ModelAdmin):
    inlines = [CollectionItemInline]

    list_display = ['id', 'user__username', 'title',
                    'slug', 'items_count', 'formatted_created_at']
    list_per_page = 15
    list_filter = ['created_at']

    prepopulated_fields = {'slug': ['title']}
    related_field = 'collection_id'


# B)CollectionItem admin
@admin.register(models.CollectionItem)
class CollectionItemAdmin(CollectionLinkMixin, FormattedCreateDateMixin,
                          admin.ModelAdmin):
    list_display = ['id', 'product', 'collection_link', 'formatted_created_at']
    list_per_page = 15
    list_filter = ['product__type', 'created_at']

    autocomplete_fields = ['product']


# 6)SavedPlaylist Admin
@admin.register(models.SavedPlaylist)
class SavedPlaylistAdmin(PlaylistLinkMixin, FormattedSavedDateMixin, admin.ModelAdmin):
    list_display = ['id', 'user', 'playlist_link', 'formatted_saved_at']
    list_per_page = 15
    list_filter = ['saved_at']


# 5)ChatSession, Chatmessage admins
# A)ChatMessage admin
class ChatMessageInline(AudioThumbnailMixin, admin.StackedInline):
    model = models.ChatMessage

    fields = ['role', 'content', 'thumbnail']
    readonly_fields = ['role', 'content', 'thumbnail']

    extra = 0
    min_num = 0
    max_num = 1000


@admin.register(models.ChatSession)
class ChatSessionAdmin(ChatMessageCountMinxin, FormattedUpdateDateMixin,
                       admin.ModelAdmin):
    inlines = [ChatMessageInline]

    list_display = ['id', 'user', 'host', 'product__type', 'product', 'messages_count',
                    'visible', 'cost', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['product__type', 'created_at', 'host', 'user']

    search_fields = ['user__username']
    autocomplete_fields = ['product']
    related_field = 'session_id'
    readonly_fields = ['host', 'user', 'product', 'summary']

    ordering = ['-updated_at']


# B)ChatMessage admin
@admin.register(models.ChatMessage)
class ChatMessageAdmin(AudioThumbnailMixin, ChatSessionLinkMixin, FormattedCreateDateMixin,
                       admin.ModelAdmin):
    list_display = ['id', 'role', 'display_content', 'audio_seconds', 'session_link',
                    'cost', 'formatted_created_at']
    list_per_page = 13
    list_filter = ['role', 'is_voice', 'created_at']

    # list_editable = ['is_voice']
    search_fields = ['session__id']
    readonly_fields = ['cost', 'session', 'role', 'audio_seconds', 'content',
                       'audio', 'is_voice', 'thumbnail']

    def display_content(self, obj):
        if not obj.content:
            return ''

        is_english = is_english_like_prefix(obj.content)
        limit = 30 if is_english else 20

        truncated = obj.content[:limit]
        suffix = '' if len(obj.content) <= limit else '...'
        return f'{truncated}{suffix}'

    display_content.short_description = 'Content'


# D)UsageCost admin
@admin.register(models.ModelUsage)
class UsageCostAdmin(FormattedCreateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'chat_model', 'step', 'unit_price', 'units', 'cost',
                    'message', 'session', 'formatted_created_at']
    list_per_page = 15
    list_filter = ['chat_model', 'step', 'created_at']


@admin.register(models.DebitLedger)
class DebitLedgerAdmin(FormattedCreateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'usage', 'note',
                    'formatted_created_at']
    list_per_page = 15
    list_filter = ['created_at']

    search_fields = ['user__username']

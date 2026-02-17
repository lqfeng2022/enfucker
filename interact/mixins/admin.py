from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, urlencode


class CollectionLinkMixin:
    @admin.display(description='Collection')
    def collection_link(self, obj):
        url = (reverse('admin:interact_collection_changelist') + '?'
               + urlencode({'id': obj.collection_id}))
        return format_html("<a href='{}'>{}</a>", url, obj.collection.title)


class CollectionItemCountMinxin:
    @admin.display(ordering='items_count', description='CollectionItems')
    def items_count(self, obj):
        url = (reverse('admin:interact_collectionitem_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html("<a href='{}'>{}</a>", url, obj.items_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            items_count=Count('items', distinct=True))


class ChatMessageCountMinxin:
    @admin.display(ordering='messages_count', description='ChatMessages')
    def messages_count(self, obj):
        url = (reverse('admin:interact_chatmessage_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html("<a href='{}'>{}</a>", url, obj.messages_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            messages_count=Count('messages', distinct=True))


class ChatSessionLinkMixin:
    @admin.display(description='ChatSession')
    def session_link(self, obj):
        url = (reverse('admin:interact_chatsession_changelist') + '?'
               + urlencode({'id': obj.session_id}))
        return format_html("<a href='{}'>{}</a>", url, obj.session)


def is_english_like_prefix(text: str, sample_size=10) -> bool:
    if not text:
        return True

    sample = text[:sample_size]
    ascii_count = sum(1 for ch in sample if ch.isascii())
    return ascii_count >= len(sample) * 0.8  # 80% ASCII


class AudioThumbnailMixin:
    def thumbnail(self, instance):
        if instance.audio:
            return format_html("<audio controls src='{}'/>",
                               instance.audio.url)
        return '-'
    thumbnail.short_description = 'Audio Thumbnail'


class HostLinkMixin:
    @admin.display(description='Host')
    def host_link(self, obj):
        url = (reverse('admin:store_host_changelist') + '?'
               + urlencode({'id': obj.host_id}))
        content = obj.host.name if obj.host else ''
        return format_html("<a href='{}'>{}</a>", url, content)
    host_link.short_description = 'host'


class PlaylistLinkMixin:
    @admin.display(description='Playlist')
    def playlist_link(self, obj):
        url = (reverse('admin:store_playlist_changelist') + '?'
               + urlencode({'id': obj.playlist_id}))
        return format_html("<a href='{}'>{}</a>", url, obj.playlist.title)

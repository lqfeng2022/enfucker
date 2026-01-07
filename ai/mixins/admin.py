from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, urlencode, mark_safe


# Custom this ThumbnailMixin to display images
class ThumbnailMixin:
    readonly_fields = ['thumbnail']

    def thumbnail(self, instance):
        thumbnails = []
        for field in ['portrait', 'cover']:
            file = getattr(instance, field, None)
            url = getattr(file, 'url', file) if file else ''
            html_image = format_html(
                '<img src="{}" class="thumbnail" alt="{}"/>',
                url, field)
            url and thumbnails.append(html_image)
        return mark_safe(' '.join(thumbnails)) if thumbnails else ''

    class Media:
        css = {'all': ['ai/styles.css']}


class HostCountMixin:
    @admin.display(ordering='host_count', description='Hosts')
    def host_count(self, obj):
        url = (reverse('admin:ai_hostprofile_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html("<a href='{}'>{}</a>", url, obj.host_count)

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .annotate(host_count=Count('host_profiles', distinct=True))

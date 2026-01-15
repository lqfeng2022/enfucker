from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, urlencode


class HostCountMixin:
    @admin.display(ordering='host_count', description='Hosts')
    def host_count(self, obj):
        url = (reverse('admin:ai_hostprofile_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html("<a href='{}'>{}</a>", url, obj.host_count)

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .annotate(host_count=Count('host_profiles', distinct=True))

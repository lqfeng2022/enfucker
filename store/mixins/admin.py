from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, urlencode, mark_safe
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from store.models import Product


# Custom this ThumbnailMixin to display images
class ThumbnailMixin:
    # Tell django display thumbnail field and make it read_only
    readonly_fields = ['thumbnail']

    # Define thumbnail() to render the html <img> tag showing cover iamge
    def thumbnail(self, instance):
        thumbnails = []
        for field in ['portrait', 'cover', 'image']:
            # getattr() equal to `instance.field` which means file is gonna be instance.image or instance.cover
            # ->handle FileField and raw URLField/CharField cases
            file = getattr(instance, field, None)
            url = getattr(file, 'url', file) if file else ''
            html_image = format_html(
                '<img src="{}" class="thumbnail" alt="{}"/>', url, field)
            url and thumbnails.append(html_image)
        return mark_safe(' '.join(thumbnails)) if thumbnails else ''

    # Specify the static assets
    class Media:
        css = {'all': ['store/styles.css']}


class VideoCountMixin:
    """Mixin to add a video_count column with a link to the Video changelist page."""
    @admin.display(ordering='video_count', description='Videos')
    def video_count(self, obj):
        # Generate a link to the Video changelist page filtered by this tag
        # 1)reverse('admin:store_model_page): this f generate the url for the model page
        # 2)'changelist' is a default name for model list page in Django
        # 3)Filter by `related_field`
        url = (reverse('admin:store_video_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html('<a href="{}">{}</a>', url, obj.video_count)

    def get_queryset(self, request):
        # Annotate the queryset with the count of related videos
        return super().get_queryset(request) \
            .annotate(video_count=Count('videos', distinct=True))


class SubtitleCountMinxin:
    """ADD `distinct=True` -> FIX bug
      - When you have multiple annotate() calls in different mixins,
        and each annotate() is doing a `.annotate(Count(...))` on a related field,
        Django will produce multiple joins in the same query.
      - If both subtitles and expressions are related to Video,
        those joins can multiply rows in the SQL result, so your counts end up inflated.
    """
    @admin.display(ordering='subtitle_count', description='Subtitles')
    def subtitle_count(self, obj):
        url = (reverse('admin:store_subtitle_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html("<a href='{}'>{}</a>", url, obj.subtitle_count)

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .annotate(subtitle_count=Count('subtitles', distinct=True))


class ExpressionCountMixin:
    @admin.display(ordering='expression_count', description='Expressions')
    def expression_count(self, obj):
        url = (reverse('admin:store_expression_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html("<a href='{}'>{}</a>", url, obj.expression_count)

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .annotate(expression_count=Count('expressions', distinct=True))


class VideoLinkMixin:
    """Mixin to add a video_link column with a link to the Video changelist page."""
    @admin.display(description='Video')  # Set the column header to 'Video'
    def video_link(self, obj):
        # Generate a link to the Video changelist page filtered by video_id
        url = (reverse('admin:store_video_changelist') + '?'
               + urlencode({'id': obj.video_id}))
        return format_html("<a href='{}'>{}</a>", url, obj.video.title)


class SubtitleLinkMixin:
    """Mixin to add a subtitle_link column with a link to the Subtitle changelist page."""
    @admin.display(description='Subtitle')
    def subtitle_link(self, obj):
        url = (reverse('admin:store_subtitle_changelist') + '?'
               + urlencode({'id': obj.subtitle_id}))
        return format_html("<a href='{}'>{}</a>", url, obj.subtitle)


class FormattedCreateDateMixin:
    date_field = 'created_at'  # default field name
    date_format = '%b %d, %Y'  # default formatting

    def formatted_created_at(self, obj):
        value = getattr(obj, self.date_field, None)
        return '_' if not value else value.strftime(self.date_format)
    formatted_created_at.short_description = 'Created At'


class FormattedUpdateDateMixin:
    date_field = 'updated_at'  # default field name
    date_format = '%b %d, %Y'  # default formatting

    def formatted_updated_at(self, obj):
        value = getattr(obj, self.date_field, None)
        return '_' if not value else value.strftime(self.date_format)

    formatted_updated_at.short_description = 'Updated At'


# Custom product type filter
class ProductTypeFilter(admin.SimpleListFilter):
    # `gettext_lazy as _`: Lazy Translation
    # - The translation is deferred until the string is actually used.
    # - The string is marked for translation, but the actual translation does not happen until the string is accessed,
    #   such as in template rendering or form field definitions.
    title = _('Product Type')
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return Product.PRODUCT_TYPE_CHOICES

    def queryset(self, request, queryset):
        value = self.value()
        return queryset if value is None else queryset.filter(type=value)


# Add Product content and link to the original one
class ContentLinkMixin:
    def content_link(self, obj):
        if obj.video_id:
            url = reverse('admin:store_video_change',
                          args=(obj.video_id,))  # make sure args is a tuple
            return format_html('<a href="{}">{}</a>', url, obj.video.title)
        elif obj.subtitle_id:
            url = reverse('admin:store_subtitle_change',
                          args=(obj.subtitle_id,))
            return format_html('<a href="{}">{}</a>', url, f'{obj.subtitle.content[:30]}...')
        elif obj.expression_id:
            url = reverse('admin:store_expression_change',
                          args=(obj.expression_id,))
            return format_html('<a href="{}">{}</a>', url, obj.expression.title)
        return '-'

    content_link.short_description = 'Content'


class ProductCountMixin:
    @admin.display(ordering='product_count', description='Products')
    def product_count(self, obj):
        url = (reverse('admin:store_product_changelist') + '?'
               + urlencode({self.related_field: str(obj.id)}))
        return format_html("<a href='{}'>{}</a>", url, obj.product_count)

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .annotate(product_count=Count('products', distinct=True))

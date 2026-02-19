from django.contrib import admin
from .models import (
    Country, City, Language, Genre, Alphabet, Video, Subtitle, Expression,
    Product, Host, Playlist, PlaylistItem, Course)
from .mixins.admin import (
    ThumbnailMixin, VideoCountMixin, VideoLinkMixin, SubtitleCountMinxin,
    SubtitleLinkMixin, ExpressionCountMixin, FormattedUpdateDateMixin,
    FormattedCreateDateMixin, ProductTypeFilter, ContentLinkMixin,
    ProductCountMixin, PlaylistItemCountMinxin, PlaylistLinkMixin,
    ProductThumbnailAdminMixin, PlaylistCountMinxin
)
from store.services.product_sync import sync_products_host_for_video


# 0)Language admin
@admin.register(Language)
class LanguageAdmin(FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'slug', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    prepopulated_fields = {'slug': ['title']}
    search_fields = ['title']
    related_field = 'language_id'  # Field used to filter videos by genre


@admin.register(Country)
class CountryAdmin(FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'slug', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    prepopulated_fields = {'slug': ['title']}
    search_fields = ['title']
    related_field = 'country_id'


@admin.register(City)
class CityAdmin(FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'slug', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    prepopulated_fields = {'slug': ['title']}
    search_fields = ['title']
    related_field = 'city_id'
    autocomplete_fields = ['country']


# 1)Genre admin
@admin.register(Genre)
class GenreAdmin(VideoCountMixin, FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'slug',
                    'video_count', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    prepopulated_fields = {'slug': ['title']}
    search_fields = ['title']
    related_field = 'genre_id'  # Field used to filter videos by genre


# 2)Alphabet admin
@admin.register(Alphabet)
class AlphabetAdmin(ExpressionCountMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'slug',
                    'expression_count', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    prepopulated_fields = {'slug': ['title']}
    related_field = 'alphabet_id'  # filter words by alphabet

    def formatted_updated_at(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    formatted_updated_at.short_description = 'Last Update'


# 3)Host admin
@admin.register(Host)
class HostAdmin(ThumbnailMixin, ProductCountMixin, FormattedUpdateDateMixin,
                admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'product_count',
                    'formatted_updated_at']
    list_per_page = 12
    list_filter = ['updated_at']

    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name']
    related_field = 'host_id'


# 4)Video admin
class SubtitleInline(admin.StackedInline):
    model = Subtitle

    fields = ['order', 'title', 'content']

    classes = ['collapse']

    extra = 0
    min_num = 0
    max_num = 100


@admin.register(Video)
class VideoAdmin(SubtitleCountMinxin, ThumbnailMixin, FormattedUpdateDateMixin,
                 admin.ModelAdmin):
    inlines = [SubtitleInline]

    list_display = ['id', 'title', 'kind', 'genre_title', 'host__name',
                    'subtitle_count', 'formatted_updated_at']
    list_per_page = 15
    list_select_related = ['genre']
    list_filter = ['kind', 'genre', 'host__name', 'updated_at']

    prepopulated_fields = {'slug': ['title']}
    # useful to fields that have tons of items
    autocomplete_fields = ['genre']
    search_fields = ['title']
    related_field = 'video_id'  # set the CountMixin field here

    def genre_title(self, obj):
        return obj.genre.title
    genre_title.short_description = 'Genre'

    # update video host here
    def save_model(self, request, obj, form, change):
        # Detect host change BEFORE save
        host_changed = change and 'host' in form.changed_data
        # Let admin do its normal save
        super().save_model(request, obj, form, change)
        # Sync AFTER save
        if host_changed:
            sync_products_host_for_video(obj)


# 5)Subtitle admin
class ExpressionInline(ThumbnailMixin, admin.StackedInline):
    model = Expression

    prepopulated_fields = {'slug': ['title']}

    extra = 0
    min_num = 0
    max_num = 200


@admin.register(Subtitle)
class SubtitleAdmin(ExpressionCountMixin, VideoLinkMixin,
                    FormattedUpdateDateMixin, admin.ModelAdmin):
    inlines = [ExpressionInline]

    list_display = ['id', 'order', 'title', 'expression_count', 'video_link',
                    'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    autocomplete_fields = ['video']
    search_fields = ['content']
    related_field = 'subtitle_id'


# 6)Expression admin
@admin.register(Expression)
class ExpressionAdmin(ThumbnailMixin, SubtitleLinkMixin,
                      FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'subtitle_link', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    autocomplete_fields = ['subtitle']
    prepopulated_fields = {'slug': ['title']}
    search_fields = ['title']


# 7)Product Admin
@admin.register(Product)
class ProductAdmin(FormattedUpdateDateMixin, ContentLinkMixin, admin.ModelAdmin):
    list_display = ('id', 'type', 'content_link', 'views_count', 'likes_count',
                    'bookmarks_count', 'formatted_updated_at')
    list_per_page = 16
    list_filter = [ProductTypeFilter, 'updated_at']

    search_fields = ['id', 'video__title', 'subtitle__content',
                     'expression__title']
    autocomplete_fields = ['video', 'subtitle', 'expression']

    ordering = ['id']


# 9)Course admin
class PlaylistInline(ThumbnailMixin, admin.StackedInline):
    model = Playlist

    readonly_fields = ['thumbnail']
    prepopulated_fields = {'slug': ['title']}

    classes = ['collapse']

    ordering = ['order']
    extra = 0
    min_num = 0
    max_num = 100


@admin.register(Course)
class CourseAdmin(ThumbnailMixin, PlaylistCountMinxin, FormattedCreateDateMixin,
                  FormattedUpdateDateMixin, admin.ModelAdmin):
    inlines = [PlaylistInline]

    list_display = ['id', 'title', 'host__name', 'playlist_count',
                    'formatted_created_at', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['created_at']

    prepopulated_fields = {'slug': ['title']}
    related_field = 'course_id'
    search_fields = ['title']

    ordering = ['id']


# 8)Playlist, PlaylistItem admins
class PlaylistItemInline(ProductThumbnailAdminMixin, admin.StackedInline):
    model = PlaylistItem

    readonly_fields = ['product_thumbnail']
    autocomplete_fields = ['product']

    classes = ['collapse']

    ordering = ['order']

    extra = 0
    min_num = 0
    max_num = 1000

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        queryset = qs.select_related(
            'product',
            'product__video',
            'product__expression',
            'product__subtitle',
        ).prefetch_related('product__subtitle__expressions')

        return queryset


@admin.register(Playlist)
class PlaylistAdmin(ThumbnailMixin, PlaylistItemCountMinxin, FormattedCreateDateMixin,
                    FormattedUpdateDateMixin, admin.ModelAdmin):
    inlines = [PlaylistItemInline]

    list_display = ['id', 'order', 'title', 'host__name', 'course__title',
                    'items_count', 'formatted_created_at', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['created_at']

    prepopulated_fields = {'slug': ['title']}
    related_field = 'playlist_id'
    autocomplete_fields = ['course', 'host']

    ordering = ['id']


@admin.register(PlaylistItem)
class PlaylistItemAdmin(PlaylistLinkMixin, FormattedCreateDateMixin,
                        admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'playlist_link',
                    'formatted_created_at']
    list_per_page = 15
    list_filter = ['product__type', 'created_at']

    autocomplete_fields = ['product']

    ordering = ['id']

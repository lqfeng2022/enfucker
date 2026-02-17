from django.db import models
from django.core.validators import MinValueValidator
from .utils import expression_image_upload_to, video_upload_to


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# store_language
class Language(AbstractCommon):
    title = models.CharField(max_length=255)
    slug = models.SlugField()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['id']


# store_country
class Country(AbstractCommon):
    title = models.CharField(max_length=255)
    slug = models.SlugField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ['id']


# store_city
class City(AbstractCommon):
    title = models.CharField(max_length=255)
    slug = models.SlugField()

    country = models.ForeignKey(Country, on_delete=models.CASCADE,
                                related_name='cities')

    def __str__(self):
        return f'{self.title}, {self.country.title}'

    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ['id']


# store_genre
class Genre(AbstractCommon):
    title = models.CharField(max_length=255)
    slug = models.SlugField()

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['id']


# store_alphabet
class Alphabet(AbstractCommon):
    title = models.CharField(max_length=255)
    slug = models.SlugField()

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['id']


# store_host
class Host(AbstractCommon):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    portrait = models.ImageField(upload_to='store/image/host-avatar',
                                 blank=True, null=True)
    cover = models.ImageField(upload_to='store/image/host-back',
                              blank=True, null=True)
    audio_intro = models.FileField(upload_to='store/audio/host-intro',
                                   blank=True, null=True)

    description = models.CharField(max_length=255, null=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ['id']


# store_video
class Video(AbstractCommon):
    REGULAR = 'REGULAR'
    SHORT = 'SHORT'
    VIDEO_CHOICES = [(REGULAR, 'Regular'), (SHORT, 'Short')]

    kind = models.CharField(max_length=10, choices=VIDEO_CHOICES,
                            default='REGULAR')

    host = models.ForeignKey(Host, on_delete=models.PROTECT,
                             related_name='videos')
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT,
                              related_name='videos')

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    released_year = models.IntegerField(validators=[MinValueValidator(1888)],
                                        blank=True)
    original = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)

    cover = models.ImageField(upload_to='store/image/clip-cover', blank=True)
    file = models.FileField(upload_to=video_upload_to, blank=True)
    context = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.slug

    class Meta:
        ordering = ['id']


# store_subtitle
class Subtitle(AbstractCommon):
    video = models.ForeignKey(Video, on_delete=models.CASCADE,
                              related_name='subtitles')

    order = models.PositiveSmallIntegerField()
    content = models.TextField()

    def __str__(self) -> str:
        return f'{self.content[:40]}...'

    class Meta:
        ordering = ['id']


# store_expression
class Expression(AbstractCommon):
    subtitle = models.ForeignKey(Subtitle, on_delete=models.CASCADE,
                                 related_name='expressions')

    alphabet = models.ForeignKey(Alphabet, on_delete=models.PROTECT,
                                 related_name='expressions')

    title = models.CharField(max_length=255)
    slug = models.SlugField()

    image = models.ImageField(upload_to=expression_image_upload_to, blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['id']


# store_product
class Product(AbstractCommon):
    PRODUCT_VIDEO = 'video'
    PRODUCT_EXPRESSION = 'expression'
    PRODUCT_SUBTITLE = 'subtitle'
    PRODUCT_TYPE_CHOICES = [(PRODUCT_VIDEO, 'Video'), (PRODUCT_EXPRESSION, 'Expression'),
                            (PRODUCT_SUBTITLE, 'Subtitle'),]

    type = models.CharField(max_length=16, choices=PRODUCT_TYPE_CHOICES)

    host = models.ForeignKey(Host, on_delete=models.PROTECT,
                             related_name='products')

    video = models.OneToOneField(Video, null=True, blank=True,
                                 on_delete=models.CASCADE)
    subtitle = models.OneToOneField(Subtitle, null=True, blank=True,
                                    on_delete=models.CASCADE)
    expression = models.OneToOneField(Expression, null=True, blank=True,
                                      on_delete=models.CASCADE)

    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children', on_delete=models.SET_NULL)

    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        if self.type == self.PRODUCT_VIDEO and self.video:
            return self.video.title
        elif self.type == self.PRODUCT_EXPRESSION and self.expression:
            return self.expression.title
        elif self.type == self.PRODUCT_SUBTITLE and self.subtitle:
            # Show first 30 chars to avoid huge strings
            preview = (self.subtitle.content[:30] + '...') if \
                len(self.subtitle.content) > 30 else self.subtitle.content
            return preview
        # fallback — should never happen if your data is clean
        return f'Product {self.pk}'

    def get_thumbnail_url(self):
        if self.type == self.PRODUCT_VIDEO and self.video and self.video.cover:
            return self.video.cover.url

        if self.type == self.PRODUCT_EXPRESSION and self.expression and self.expression.image:
            return self.expression.image.url

        if self.type == self.PRODUCT_SUBTITLE and self.subtitle:
            # first expression image
            first_expression = self.subtitle.expressions.first()
            if first_expression and first_expression.image:
                return first_expression.image.url

        return None

    class Meta:
        ordering = ['-updated_at']


# store_playlist
class Playlist(AbstractCommon):
    host = models.ForeignKey(Host, on_delete=models.CASCADE,
                             related_name='playlists')

    title = models.CharField(max_length=255)
    slug = models.SlugField(db_index=True)  # important for API lookup

    products = models.ManyToManyField(Product, through='PlaylistItem',
                                      related_name='playlists')

    def __str__(self) -> str:
        return f'{self.title}'

    class Meta:
        unique_together = [('host', 'slug')]
        ordering = ['-created_at']


# store_playlistitem
class PlaylistItem(AbstractCommon):
    order = models.PositiveIntegerField(default=0, db_index=True)

    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE,
                                 related_name='playlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='playlist_items')

    def __str__(self) -> str:
        return f'{self.product}'

    class Meta:
        unique_together = [('playlist', 'product'), ('playlist', 'order')]
        ordering = ['order']

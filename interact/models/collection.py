from django.conf import settings
from django.db import models
from store.utils import short_uuid


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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
        first_item = (
            self.items.filter(visible=True).
            select_related('product__video', 'product__expression', 'product__subtitle').
            prefetch_related('product__subtitle__expressions').
            first()
        )

        if first_item and first_item.product:
            return first_item.product.get_thumbnail_url()

        return None

    class Meta:
        unique_together = [('user', 'title')]
        verbose_name_plural = 'User Collections'
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
        verbose_name_plural = 'User Collection Items'
        ordering = ['-created_at']

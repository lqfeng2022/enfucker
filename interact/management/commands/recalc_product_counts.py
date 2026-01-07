from django.core.management.base import BaseCommand
from django.conf import settings
from interact.models import Like, UserView, CollectionItem


class Command(BaseCommand):
    help = 'Recalculate likes, views, bookmarks counts for all products'

    def handle(self, *args, **kwargs):
        products = settings.STORE_PRODUCT_MODEL.objects.all()

        for product in products:
            likes = Like.objects.filter(product=product, visible=True).count()
            views = UserView.objects.filter(
                product=product, visible=True).count()
            bookmarks = CollectionItem.objects.filter(product=product). \
                values('collection__user').distinct().count()

            settings.STORE_PRODUCT_MODEL.objects.filter(id=product.id).update(
                likes_count=likes,
                views_count=views,
                bookmarks_count=bookmarks
            )
            self.stdout.write(
                f'Updated Product {product.id}: likes={likes}, \
                  views={views}, bookmarks={bookmarks}'
            )

        self.stdout.write(self.style.SUCCESS('All products recalculated!'))

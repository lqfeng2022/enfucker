from django.db import transaction
from django.core.management.base import BaseCommand
from store.models import Video, Subtitle, Expression, Product


class Command(BaseCommand):
    help = 'Backfill Product tree for Video / Subtitle / Expression'

    def handle(self, *args, **options):
        created_count = 0

        # --------------------------------------------------
        # 1)VIDEO products (root)
        # --------------------------------------------------
        video_products = {}

        for video in Video.objects.select_related('host').iterator():
            with transaction.atomic():
                product, created = Product.objects.get_or_create(
                    type=Product.PRODUCT_VIDEO,
                    video=video,
                    defaults={'host': video.host, 'parent': None},
                )

                # Why we assign immediately after creation
                # 1)Parent availability for children
                # 2)Identity stability (important but subtle)
                video_products[video.id] = product

                if created:
                    created_count += 1

        # --------------------------------------------------
        # 2. SUBTITLE products (child of video)
        # --------------------------------------------------
        subtitle_products = {}

        for subtitle in Subtitle.objects.select_related('video__host').iterator():
            parent = video_products.get(subtitle.video_id)
            if not parent:
                continue  # defensive

            with transaction.atomic():
                product, created = Product.objects.get_or_create(
                    type=Product.PRODUCT_SUBTITLE,
                    subtitle=subtitle,
                    defaults={'host': subtitle.video.host, 'parent': parent},
                )

                # fix parent drift
                if product.parent_id != parent.id:
                    product.parent = parent
                    product.save(update_fields=['parent'])

                subtitle_products[subtitle.id] = product

                if created:
                    created_count += 1

        # --------------------------------------------------
        # 3. EXPRESSION products (child of subtitle)
        # --------------------------------------------------
        for expression in Expression.objects. \
                select_related('subtitle__video__host').iterator():
            parent = subtitle_products.get(expression.subtitle_id)
            if not parent:
                continue

            with transaction.atomic():
                product, created = Product.objects.get_or_create(
                    type=Product.PRODUCT_EXPRESSION,
                    expression=expression,
                    defaults={'host': expression.subtitle.video.host,
                              'parent': parent},
                )

                # fix parent drift
                if product.parent_id != parent.id:
                    product.parent = parent
                    product.save(update_fields=['parent'])

                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Backfill complete. Total rows created: {created_count}'
            )
        )

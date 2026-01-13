from django.db import transaction
from store.models import Product, Video


def sync_products_host_for_video(video: Video):
    """Ensure all products under a video have the same host as the video.
    Safe for admin, API, commands, and bulk jobs.
    """
    new_host = video.host

    with transaction.atomic():
        Product.objects.filter(video=video).update(host=new_host)
        Product.objects.filter(subtitle__video=video).update(host=new_host)
        Product.objects.filter(
            expression__subtitle__video=video
        ).update(host=new_host)

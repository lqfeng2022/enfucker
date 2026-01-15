import os
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import Video, Subtitle, Expression, Product, Host


# 1)CREATE/DELETE products
def _get_or_create_video_product(video):
    return Product.objects.get_or_create(
        type=Product.PRODUCT_VIDEO,
        video=video,
        defaults={'host': video.host, 'parent': None}
    )


def _get_or_create_subtitle_product(subtitle, parent_product):
    return Product.objects.get_or_create(
        type=Product.PRODUCT_SUBTITLE,
        subtitle=subtitle,
        defaults={'host': subtitle.video.host, 'parent': parent_product}
    )


def _get_or_create_expression_product(expression, parent_product):
    return Product.objects.get_or_create(
        type=Product.PRODUCT_EXPRESSION,
        expression=expression,
        defaults={'host': expression.subtitle.video.host,
                  'parent': parent_product}
    )


# 1.1)CREATE Product on new content
@receiver(post_save, sender=Video)
def create_product_for_video(sender, instance, created, **kwargs):
    if created:
        _get_or_create_video_product(instance)


@receiver(post_save, sender=Subtitle)
def create_product_for_subtitle(sender, instance, created, **kwargs):
    if not created:
        return

    with transaction.atomic():
        parent_product, _ = _get_or_create_video_product(instance.video)
        _get_or_create_subtitle_product(instance, parent_product)


@receiver(post_save, sender=Expression)
def create_product_for_expression(sender, instance, created, **kwargs):
    if not created:
        return

    with transaction.atomic():
        # ensure the video-level parent exists
        video_parent, _ = _get_or_create_video_product(instance.subtitle.video)
        # ensure the subtitle-level parent exists and is linked to the video parent
        subtitle_parent, _ = _get_or_create_subtitle_product(
            instance.subtitle, video_parent)
        # finally create/get the expression product using the subtitle parent
        _get_or_create_expression_product(instance, subtitle_parent)


# 1.2)DELETE Product when original content deleted
# (CASCADE already covers this, but added for safety)
@receiver(post_delete, sender=Video)
def delete_product_for_video(sender, instance, **kwargs):
    Product.objects.filter(video=instance).delete()


@receiver(post_delete, sender=Subtitle)
def delete_product_for_subtitle(sender, instance, **kwargs):
    Product.objects.filter(subtitle=instance).delete()


@receiver(post_delete, sender=Expression)
def delete_product_for_expression(sender, instance, **kwargs):
    Product.objects.filter(expression=instance).delete()


# 2)Clean unused video files via signals
def delete_file_if_changed(old_file_field, new_file_field):
    if not (old_file_field or old_file_field.name):
        return
    elif old_file_field.name != new_file_field.name:
        if os.path.isfile(old_file_field.path):
            os.remove(old_file_field.path)


# 2.1)DELETE files on delete
@receiver(post_delete, sender=Video)
def cleanup_video_files_on_delete(sender, instance, **kwargs):
    if not instance.pk:
        return  # New object, no old file

    try:
        old_file = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    delete_file_if_changed(old_file.cover, instance.cover)
    delete_file_if_changed(old_file.file, instance.file)
    delete_file_if_changed(old_file.text, instance.text)


# 2.2)REPLACE files
@receiver(pre_save, sender=Video)
def cleanup_video_files_on_replace(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = Video.objects.get(pk=instance.pk)
    except Video.DoesNotExist:
        return

    if old_file.cover != instance.cover:
        delete_file_if_changed(old_file.cover, instance.cover)

    if old_file.file != instance.file:
        delete_file_if_changed(old_file.file, instance.file)


# 3)Clean unused exp image via signals
@receiver(post_delete, sender=Expression)
def cleanup_expimage_on_delete(sender, instance, **kwargs):
    if not instance.pk:
        return  # New object, no old file

    try:
        old_file = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    delete_file_if_changed(old_file.image, instance.image)


@receiver(pre_save, sender=Expression)
def cleanup_expimage_on_replace(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = Expression.objects.get(pk=instance.pk)
    except Expression.DoesNotExist:
        return

    if old_file.image != instance.image:
        delete_file_if_changed(old_file.image, instance.image)


# 4)Clean unused host images, audios via signals
@receiver(post_delete, sender=Host)
def cleanup_expfile_on_delete(sender, instance, **kwargs):
    if not instance.pk:
        return  # New object, no old file

    try:
        old_file = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    delete_file_if_changed(old_file.portrait, instance.portrait)
    delete_file_if_changed(old_file.cover, instance.cover)
    delete_file_if_changed(old_file.audio_intro, instance.audio_intro)


@receiver(pre_save, sender=Host)
def cleanup_expfile_on_replace(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = Host.objects.get(pk=instance.pk)
    except Host.DoesNotExist:
        return

    if old_file.portrait != instance.portrait:
        delete_file_if_changed(old_file.portrait, instance.portrait)

    if old_file.cover != instance.cover:
        delete_file_if_changed(old_file.cover, instance.cover)

    if old_file.audio_intro != instance.audio_intro:
        delete_file_if_changed(old_file.audio_intro, instance.audio_intro)

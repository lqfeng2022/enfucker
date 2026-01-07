from django.db.models import F
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from interact.utils.getmodels import get_product_model
from .models import Like, UserView, CollectionItem, ChatMessage


# UPDATE `latest_chat` when we create new message
@receiver(post_save, sender=ChatMessage)
def update_latest_chat(sender, instance, **kwargs):
    session = instance.session
    content = f' {'[voice]' if instance.is_voice else ''}{instance.content}'

    session.latest_chat = content
    session.save(update_fields=['latest_chat'])


# view signal
@receiver(post_save, sender=UserView)
def view_saved(sender, instance, created, **kwargs):
    Product = get_product_model()  # resolve at runtime

    Product.objects.filter(pk=instance.product_id). \
        update(views_count=F('views_count') + 1)


# Like signals
@receiver(post_save, sender=Like)
def like_created(sender, instance, created, **kwargs):
    Product = get_product_model()  # resolve at runtime

    if created and instance.visible:
        Product.objects.filter(pk=instance.product_id). \
            update(likes_count=F('likes_count') + 1)


@receiver(pre_save, sender=Like)
def like_visibility_change(sender, instance, **kwargs):
    Product = get_product_model()  # resolve at runtime

    if not instance.pk:
        return
    old = Like.objects.get(pk=instance.pk)

    if old.visible != instance.visible:
        delta = 1 if instance.visible else -1
        Product.objects.filter(pk=instance.product_id). \
            update(likes_count=F('likes_count') + delta)


# CollectionItem signals
@receiver(post_save, sender=CollectionItem)
def collectionitem_created(sender, instance, created, **kwargs):
    Product = get_product_model()  # resolve at runtime

    if created and instance.visible:
        Product.objects.filter(pk=instance.product_id). \
            update(bookmarks_count=F('bookmarks_count') + 1)


@receiver(post_delete, sender=CollectionItem)
def collectionitem_deleted(sender, instance, **kwargs):
    Product = get_product_model()  # resolve at runtime

    if instance.visible:
        Product.objects.filter(pk=instance.product_id). \
            update(bookmarks_count=F('bookmarks_count') - 1)


# 'post_save': a Django signal that gets triggered after a model’s save() method completes.
# 'sender': the model class
# 'created': a boolean — True if a new object was created, False if it was just updated
# 'instance': the model instance that was just saved
# **kwargs: extra context (e.g., update_fields, raw)

from django.conf import settings
from django.db import models


# interact_like
class Like(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='likes')
    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.CASCADE,
                                related_name='likes')

    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        unique_together = [('user', 'product')]
        verbose_name_plural = 'User Likes'
        ordering = ['-created_at']

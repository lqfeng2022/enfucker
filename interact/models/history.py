from django.conf import settings
from django.db import models


# interact_userview
class UserView(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='userviews')
    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.CASCADE,
                                related_name='userviews')

    visible = models.BooleanField(default=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'view No. {self.pk}'

    class Meta:
        unique_together = [('user', 'product')]
        verbose_name_plural = 'User Histories'
        ordering = ['-updated_at']

from django.conf import settings
from django.db import models


# interact_search
class Search(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='searches')

    content = models.CharField(max_length=255)
    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'Search No. {self.pk}'

    class Meta:
        unique_together = ('user', 'content')
        verbose_name_plural = 'User Searches'
        ordering = ['-created_at']

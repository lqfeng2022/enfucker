from django.conf import settings
from django.db import models


# interact_follow
class Follow(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='followings')
    host = models.ForeignKey(settings.STORE_HOST_MODEL, on_delete=models.CASCADE,
                             related_name='followers')

    visible = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.host.slug}[{self.user.username}]'

    class Meta:
        unique_together = ('user', 'host')  # prevent duplicates
        verbose_name_plural = 'User Followings'
        ordering = ['id']


# interact_savedplaylist
class SavedPlaylist(models.Model):
    saved_at = models.DateTimeField(auto_now_add=True)

    playlist = models.ForeignKey('store.Playlist', on_delete=models.CASCADE,
                                 related_name='saved_playlists')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='saved_playlists')

    class Meta:
        unique_together = [('user', 'playlist')]
        verbose_name_plural = 'User Saved Playlist'
        ordering = ['-saved_at']


# interact_savedcourse
class SavedCourse(models.Model):
    saved_at = models.DateTimeField(auto_now_add=True)

    course = models.ForeignKey('store.Course', on_delete=models.CASCADE,
                               related_name='saved_courses')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='saved_courses')

    class Meta:
        unique_together = [('user', 'course')]
        verbose_name_plural = 'User Saved Course'
        ordering = ['-saved_at']

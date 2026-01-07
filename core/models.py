from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# core_user
class User(AbstractUser):
    # override email field to make it be unique
    email = models.EmailField(unique=True)


# core_profile
class Profile(AbstractCommon):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    city = models.ForeignKey(settings.STORE_CITY_MODEL, on_delete=models.PROTECT,
                             null=True, blank=True, related_name='user_profiles')

    phone = models.CharField(max_length=255, blank=True)  # optional field
    # null=True (db level behavior), blank=True, both needed
    birth_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    bro = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        verbose_name_plural = 'User Profiles'
        ordering = ['user__first_name', 'user__last_name']


# core_userlog
class UserLog(AbstractCommon):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    ip = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    sessid = models.CharField(max_length=255, blank=True, db_index=True)

    device = models.CharField(max_length=50, blank=True)

    os = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)

    browser = models.CharField(max_length=50, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        verbose_name_plural = 'User Logs'

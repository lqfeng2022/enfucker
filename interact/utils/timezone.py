import pytz
from django.utils import timezone


def local_time_for_user(dt, user):
    tz = pytz.timezone(user.timezone)
    return timezone.localtime(dt, tz)

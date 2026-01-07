from user_agents import parse
from django.utils.timezone import now
from .models import UserLog


def save_user_agent_info(request, user):
    """# https://pypi.org/project/user-agents/
    Model.objects.update_or_create(
        defaults={...},  # fields to update or set on creation
        **lookup_fields   # required fields to search for existing instance
    )
    If all the lookup fields match exactly one row:
        Django updates that row using values from defaults.
    If no match is found with the lookup fields:
        Django creates a new row, combining lookup fields and defaults.
    Extract and save user agent & IP info for a user.
    Ensures uniqueness per (user, user_agent).
    """
    if not request.session.session_key:
        request.session.create()  # Ensure session exists, don't use save()

    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = forwarded.split(',')[0] if forwarded \
        else request.META.get('REMOTE_ADDR')

    ua_string = request.META.get('HTTP_USER_AGENT', '')
    ua = parse(ua_string)
    ua_pretty = str(ua)

    sessid = request.session.session_key

    UserLog.objects.update_or_create(
        user=user,
        user_agent=ua_pretty,
        sessid=sessid,
        defaults={
            'ip': ip,
            'device': ua.device.family,
            'os': ua.os.family,
            'os_version': ua.os.version_string,
            'browser': ua.browser.family,
            'browser_version': ua.browser.version_string,
            'updated_at': now(),  # optional if you wanna override created_at
        }
    )

# interact/services/auth.py
from channels.db import database_sync_to_async


# AUTH HELPERS (async-safe)
@database_sync_to_async
def get_user_from_jwt(token_str):
    """
    Never import ORM-touching stuff at module level in ASGI / Channels code
    """
    # Lazy imports
    from rest_framework_simplejwt.tokens import AccessToken, TokenError
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.auth import get_user_model

    User = get_user_model()

    if not token_str:
        return AnonymousUser()

    try:
        token = AccessToken(token_str)
        user_id = token['user_id']
        return User.objects.get(id=user_id)  # ORM, async-safe
    except (TokenError, KeyError, User.DoesNotExist):
        return AnonymousUser()  # safe, direct

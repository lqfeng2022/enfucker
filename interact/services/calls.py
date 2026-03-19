# interact/services/calls.py
from channels.db import database_sync_to_async
from django.apps import apps


# DB HELPERS (async-safe)
@database_sync_to_async
def get_call_session(call_uuid):
    # lazy import
    CallSession = apps.get_model('interact', 'CallSession')

    return (
        CallSession.objects
        .select_related('session', 'session__user')
        .get(uuid=call_uuid)
    )

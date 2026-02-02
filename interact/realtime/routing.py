# interact/usecases/reouting.py
from django.urls import path
from interact.realtime.websocket import CallConsumer


websocket_urlpatterns = [
    path('ws/call/<uuid:call_id>/', CallConsumer.as_asgi()),
]

# `<uuid:call_id>`:
#  <uuid:call_id> means: uuid → converter (UUID type) call_id → key in kwargs
#  Django needs a named path converter to populate kwargs.

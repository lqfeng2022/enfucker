# interact/realtime/websocket.py
import asyncio
from asgiref.sync import sync_to_async
from django.apps import apps
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from interact.realtime.protocol import ClientEvent, ServerEvent
from interact.text_tools import delta_length_ok, get_new_sentences, sanitize_stt_text

STABLE_REPEAT_THRESHOLD = 2
HARD_SILENCE_MS = 5000  # ms, server-side decision window


class CallConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        from interact.usecases.voiceagent import VoiceAgent  # lazy load

        # UUID object (from <uuid:call_id>)
        self.call_id = self.scope['url_route']['kwargs']['call_id']

        # auth check
        token = self.scope['cookies'].get('access_token')
        self.user = await get_user_from_jwt(token)

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # load call (DB lookup)
        try:
            self.call = await get_call_session(self.call_id)
        except Exception:
            await self.close(code=4004)  # call not found
            return

        # permission check
        if self.call.session.user_id != self.user.id:
            await self.close(code=4003)
            return

        await self.accept()
        print('🔥 WS connected:', self.call_id, 'user:', self.user.id)

        # per-call runtime state (IMPORTANT)
        self.last_text = ""
        self.committed_prefix = ""
        self.stable_count = 0
        self.last_update_ts = None
        self.silence_task = None
        self.is_committing = False

        # create per-call agent
        self.voice_agent = VoiceAgent(
            call_session=self.call,
            send_event=self._send_agent_event
        )

        # notify client
        await self.send_json({
            'type': ServerEvent.AGENT_STATE,
            'data': {'state': 'idle'}
        })

    async def _send_agent_event(self, event_type, data):
        await self.send_json({
            'type': event_type,
            'data': data
        })

    async def receive_json(self, payload, **kwargs):
        event_type = payload.get('type')
        print('🔥 CALL WS receive:', payload)

        if event_type == ClientEvent.TEXT_PARTIAL:
            await self.handle_text_partial(payload)

        elif event_type == ClientEvent.TEXT_FINAL:
            await self.handle_text_final(payload)

        elif event_type == ClientEvent.CALL_END:
            await self.handle_call_end()

    async def handle_text_final(self, payload):
        data = payload.get('data') or {}

        text = (data.get('text') or "").strip()
        text = sanitize_stt_text(text)

        if not text:
            return

        # Cancel any pending silence watcher
        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()
            self.silence_task = None

        # commit only if delta is enough
        if delta_length_ok(text, self.committed_prefix):
            # Update last_text and commit immediately
            self.last_text = text
            self.stable_count = STABLE_REPEAT_THRESHOLD  # force commit
            self.last_update_ts = None
            await self.commit_final_text()

        # reset prefix for next user turn
        self.committed_prefix = ""

    async def handle_text_partial(self, payload):
        data = payload.get('data') or {}

        text = (data.get('text') or "").strip()
        text = sanitize_stt_text(text)
        ts = data.get('ts')

        # return if text/ts is missing
        if not text or ts is None:
            return

        # ignore very short deltas
        if not delta_length_ok(text, self.committed_prefix):
            return

        # stability detection
        if text == self.last_text:
            self.stable_count += 1
        else:
            self.last_text = text
            self.stable_count = 1

        self.last_update_ts = ts

        # cancel any pending silence detection
        if self.silence_task and not self.silence_task.done():
            # cancel() tells the asyncio task: "please stop ASAP."
            self.silence_task.cancel()
            # clear reference → avoids accidental reuse
            self.silence_task = None

        # primary commit path: stabilized text
        if self.stable_count >= STABLE_REPEAT_THRESHOLD:
            await self.commit_final_text()
            return

        # failsafe: hard silence
        self.silence_task = asyncio.create_task(
            self._hard_silence_commit(ts)
        )

    async def _hard_silence_commit(self, ts_snapshot):
        try:
            await asyncio.sleep(HARD_SILENCE_MS / 1000)
            if self.last_update_ts == ts_snapshot:
                await self.commit_final_text()

        except asyncio.CancelledError:
            # new partial arrived
            pass

    # INTENT COMMIT → LLM → AGENT RESPONSE
    async def commit_final_text(self):
        # commit lock
        if getattr(self, 'is_committing', False):
            return

        self.is_committing = True
        try:
            # cancel any pending silence watcher
            if self.silence_task and not self.silence_task.done():
                self.silence_task.cancel()
                self.silence_task = None

            full_text = self.last_text.strip()
            if not full_text:
                return

            # compute delta VS already committed text
            new_text = get_new_sentences(full_text, self.committed_prefix)
            if not new_text:
                # nothing new was spoken since last commit
                return

            print('🧠 COMMIT USER INTENT:', new_text)

            # mark utterance as consumed
            self.committed_prefix = full_text

            # clear partial state for next turn
            self.last_text = ""
            self.stable_count = 0
            self.last_update_ts = None

            # 🔥 HAND OFF TO AGENT
            await self.voice_agent.on_user_text(new_text)

        finally:
            self.is_committing = False

    async def handle_call_end(self):
        # lazy load
        from interact.usecases.call_end import end_call_and_record_usage

        # Cancel silence watcher
        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()
            self.silence_task = None

        # 🔥 END + BILL (sync boundary)
        await sync_to_async(end_call_and_record_usage)(self.call)

        await self.send_json({
            'type': ServerEvent.AGENT_STATE,
            'data': {'state': 'idle'}
        })

        await self.close(code=1000)

    async def disconnect(self, close_code):
        # Ensure no background tasks leak
        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()
            self.silence_task = None

        print('🔥 CALL WS disconnect', close_code)


# DB / AUTH HELPERS (async-safe)
@database_sync_to_async
def get_user_from_jwt(token_str):
    """
    Never import ORM-touching stuff at module level in ASGI / Channels code
    """
    # Lazy import ()
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


@database_sync_to_async
def get_call_session(call_uuid):
    # lazy import
    CallSession = apps.get_model('interact', 'CallSession')

    return CallSession.objects. \
        select_related('session', 'session__user'). \
        get(uuid=call_uuid)

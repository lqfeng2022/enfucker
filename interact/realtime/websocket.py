# interact/realtime/websocket.py
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from interact.realtime.protocol import ClientEvent, ServerEvent
from interact.realtime.session import RealtimeSession
from interact.services.auth import get_user_from_jwt
from interact.services.calls import get_call_session


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

        print('🔥 WS connected:', self.call_id)

        # create per-call agent
        self.voice_agent = VoiceAgent(
            call_session=self.call,
            send_event=self._send_agent_event
        )

        # create per-call session
        self.session = RealtimeSession(
            voice_agent=self.voice_agent,
            send_event=self._send_agent_event
        )

        # notify client
        await self._send_agent_event(
            ServerEvent.AGENT_STATE,
            {'state': 'idle'}
        )

    async def receive_json(self, payload, **kwargs):
        event_type = payload.get('type')
        data = payload.get('data') or {}

        print('🔥 CALL WS receive:', payload)

        if event_type == ClientEvent.TEXT_PARTIAL:
            await self.session.on_partial(
                text=data.get('text'),
                ts=data.get('ts')
            )

        elif event_type == ClientEvent.TEXT_FINAL:
            await self.session.on_final(
                text=data.get('text')
            )

        elif event_type == ClientEvent.CALL_END:
            await self.handle_call_end()

    async def handle_call_end(self):
        # lazy load
        from interact.usecases.call_end import end_call_and_record_usage

        # Cancel silence watcher
        await self.session.on_call_end()

        # END + BILL (sync boundary)
        await sync_to_async(end_call_and_record_usage)(self.call)

        await self._send_agent_event(
            ServerEvent.AGENT_STATE,
            {'state': 'idle'}
        )

        await self.close(code=1000)

    async def disconnect(self, close_code):
        # Ensure no background tasks leak
        await self.session.on_call_end()
        print('🔥 CALL WS disconnect', close_code)

    async def _send_agent_event(self, event_type, data):
        await self.send_json({
            'type': event_type,
            'data': data
        })

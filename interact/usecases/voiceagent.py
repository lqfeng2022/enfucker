# interact/usecases/voiceagent.py
from decimal import Decimal
from asgiref.sync import sync_to_async
from ai.services.get_modelprovider import get_tts_stream_model_provider
from ai.services.get_aimodel import resolve_model
from ai.contracts import STREAM
from interact.models import ChatMessage, CallSession
from interact.realtime.protocol import ServerEvent
from interact.text_tools import format_for_tts
from interact.utils.recorder import record_usage
from .chat import get_assistant_message


class VoiceAgent:
    """
    Call-scoped conversational agent.
    Consumes finalized user text and emits assistant actions.
    """

    def __init__(self, call_session, send_event):
        self.call_session = call_session
        self.session = call_session.session
        self.send_event = send_event
        self.is_processing = False

    async def on_user_text(self, text: str):
        """
        Handle finalized user text (TEXT_FINAL).
        """
        if not text.strip():
            return

        if self.is_processing:
            # Drop or queue — policy decision
            return

        if self.call_session.state != CallSession.ACTIVE:
            return

        self.is_processing = True

        try:
            # Agent thinking
            await self.send_event(ServerEvent.AGENT_STATE, {
                'state': 'thinking'
            })

            # Persist USER message (belongs to call)
            user_msg = await sync_to_async(ChatMessage.objects.create)(
                session=self.session,
                call_session=self.call_session,
                role=ChatMessage.USER,
                content=text,
                is_voice=True,
            )

            # LLM call (text only)
            assistant_msg = await sync_to_async(get_assistant_message)(
                session=self.session, user_msg=user_msg
            )

            if not assistant_msg:
                await self.send_event(ServerEvent.ERROR, {
                    'message': 'Assistant failed to generate reply'
                })
                return

            # Attach to call
            assistant_msg.call_session = self.call_session
            await sync_to_async(assistant_msg.save)(
                update_fields=['call_session']
            )

            # Agent speaking (before text)
            await self.send_event(ServerEvent.AGENT_STATE, {
                'state': 'speaking'
            })

            # Emit assistant text
            clean_text = format_for_tts(assistant_msg.content)
            await self.send_event(ServerEvent.AGENT_TEXT, {
                'text': clean_text
            })
            print('🧠 AGENT REPLY:', clean_text)  # debug

            # Record streaming TTS usage
            stream_model = await sync_to_async(resolve_model)(
                profile=self.session.host.host_profile, usecase=STREAM
            )
            stream_model_provider = await sync_to_async(get_tts_stream_model_provider)(
                model=stream_model
            )
            await sync_to_async(record_usage)(
                message=assistant_msg,  # message is obj not str
                call_session=self.call_session,
                model=stream_model_provider,
                units=Decimal(len(clean_text)),  # char-based billing
            )

        finally:
            self.is_processing = False

            # Back to idle
            await self.send_event(ServerEvent.AGENT_STATE, {
                'state': 'idle'
            })

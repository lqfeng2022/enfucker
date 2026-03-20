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
    def __init__(self, call_session, send_event):
        self.call_session = call_session
        self.session = call_session.session
        self.send_event = send_event
        self.is_processing = False

    async def on_user_text(self, text: str):
        if not text.strip():
            return

        # Drop or queue — policy decision
        if self.is_processing:
            return
        if self.call_session.state != CallSession.ACTIVE:
            return
        self.is_processing = True

        try:
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
                    "message": "Assistant failed to generate reply"
                })
                return

            # Attach to call
            assistant_msg.call_session = self.call_session
            await sync_to_async(assistant_msg.save)(
                update_fields=['call_session']
            )

            # Emit assistant text
            clean_text = format_for_tts(assistant_msg.content)
            print("##### AGENT REPLY:", clean_text)  # debug

            # return FIRST (for state timing)
            await self.send_event(ServerEvent.AGENT_TEXT, {
                "text": clean_text
            })

            # Record streaming TTS usage
            stream_model = await sync_to_async(resolve_model)(
                profile=self.session.host.host_profile,
                usecase=STREAM
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

            return clean_text

        finally:
            self.is_processing = False

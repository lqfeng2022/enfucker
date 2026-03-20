# interact/realtime/session.py
import asyncio
from interact.realtime.protocol import ServerEvent
from interact.text_tools import (
    delta_length_ok, get_new_sentences, sanitize_stt_text
)

STABLE_REPEAT_THRESHOLD = 2
HARD_SILENCE_MS = 5000  # ms, server-side decision window


class RealtimeSession:
    def __init__(self, voice_agent, send_event):
        # create voice_agent and send_event
        self.voice_agent = voice_agent
        self.send_event = send_event

        # add state field
        self.state = "IDLE"

        # runtime variables (IMPORTANT)
        self.last_text = ""
        self.committed_prefix = ""
        self.stable_count = 0
        self.last_update_ts = None
        self.silence_task = None
        self.is_committing = False

    # PUBLIC APIs
    async def on_partial(self, text: str, ts: int):
        text = sanitize_stt_text(text)
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

        # cancel silence watcher
        self._cancel_silence_task()

        # primary commit: stable
        if self.stable_count >= STABLE_REPEAT_THRESHOLD:
            await self._commit()
            return

        # fallback: silence
        self.silence_task = asyncio.create_task(
            self._hard_silence_commit(ts)
        )

    async def on_final(self, text: str):
        text = sanitize_stt_text(text)
        if not text:
            return

        # cancel silence watcher
        self._cancel_silence_task()

        # commit only if delta is enough
        if delta_length_ok(text, self.committed_prefix):
            self.last_text = text
            self.stable_count = STABLE_REPEAT_THRESHOLD
            self.last_update_ts = None
            await self._commit()

        # reset prefix for next user turn
        self.committed_prefix = ""

    async def on_call_end(self):
        self._cancel_silence_task()

    # INTERNAL LOGICs
    async def _hard_silence_commit(self, ts_snapshot):
        try:
            await asyncio.sleep(HARD_SILENCE_MS / 1000)

            if self.last_update_ts == ts_snapshot:
                await self._commit()

        except asyncio.CancelledError:
            # new partial arrived
            pass

    # INTENT COMMIT → LLM → AGENT RESPONSE
    async def _commit(self):
        if self.is_committing:
            return
        self.is_committing = True

        try:
            # cancel any pending silence watcher
            self._cancel_silence_task()

            full_text = self.last_text.strip()
            if not full_text:
                return

            # compute delta VS already committed text
            new_text = get_new_sentences(full_text, self.committed_prefix)
            if not new_text:
                # nothing new was spoken since last commit
                return
            print("##### COMMIT USER INTENT:", new_text)

            # mark consumed
            self.committed_prefix = full_text

            # reset partial state
            self.last_text = ""
            self.stable_count = 0
            self.last_update_ts = None

            # HANDOFF TO AGENT
            await self._set_state("THINKING")

            response_text = await self.voice_agent.on_user_text(new_text)

            if response_text:
                await self._set_state("RESPONDED")

        finally:
            self.is_committing = False

    # Cancel any pending silence watcher
    def _cancel_silence_task(self):
        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()
        self.silence_task = None

    # Centralized setter
    async def _set_state(self, new_state: str):
        if self.state == new_state:
            return
        self.state = new_state

        await self.send_event(ServerEvent.AGENT_STATE, {
            "state": new_state.lower()
        })

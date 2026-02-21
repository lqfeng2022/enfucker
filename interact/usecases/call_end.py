# interact/usecases/call_end.py
from decimal import Decimal
from ai.contracts import REALTIME
from ai.services.get_aimodel import resolve_model
from ai.services.get_modelprovider import get_stt_realtime_model_provider
from interact.utils.recorder import record_usage


def end_call_and_record_usage(call_session):
    """
    Finalize call lifecycle and record realtime STT usage.
    Safe to call once.
    """

    # 1) End call (idempotent)
    if call_session.state == call_session.ACTIVE:
        call_session.end()

    # 2) Guard: no duration → no billing
    duration = call_session.duration_seconds
    if not duration or duration <= 0:
        return

    # 3) Guard: avoid double billing
    if call_session.usage_costs.filter(chat_model__usecase=REALTIME).exists():
        return

    # 4) Resolve STT realtime model provider
    realtime_model = resolve_model(
        profile=call_session.session.host.host_profile,
        usecase=REALTIME,
    )
    model_provider = get_stt_realtime_model_provider(model=realtime_model)

    # 5) Record usage (time-based)
    record_usage(
        session=call_session.session,
        call_session=call_session,
        model=model_provider,
        units=Decimal(duration),  # seconds
    )

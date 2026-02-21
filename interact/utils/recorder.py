from decimal import Decimal
from django.db.models import Sum, F
from interact.services.ledger import debit_for_usage
from interact.models import ModelUsage, ChatSession
import logging

logger = logging.getLogger(__name__)


def record_usage(*, session=None, message=None, call_session=None, model=None, units):
    """Record a usage instance, update costs and session projections."""
    if not message and not session:
        raise ValueError('Either message or session is required')
    if not model:
        raise ValueError('ModelProvider is required')

    # Resolve session and call_session
    if not session and message:
        session = message.session
    elif not session and call_session:
        session = call_session.session

    if not call_session and message:
        call_session = message.call_session

    # Resolve user
    user = None
    if session:
        user = session.user
    elif message:
        user = message.session.user
    elif call_session:
        user = call_session.session.user

    # Create usage record
    usage = ModelUsage.objects.create(
        user=user,
        session=session,            # ALWAYS SET
        message=message,            # optional
        call_session=call_session,  # optional
        units=Decimal(units),
        chat_model=model,
        step=f'{model.usecase}-{model.step}',  # snapshot
        unit_price=model.unit_price,  # snapshot
        cost=Decimal(units) * model.unit_price,
    )

    # Update aggregated costs
    update_costs(message=message, session=session, call_session=call_session)

    # Update session projections: credits_used & audio seconds
    update_session_projections(
        usage=usage,
        message=message,
        session=session,
        call_session=call_session
    )

    return usage


def update_costs(*, message=None, session=None, call_session=None):
    """Update aggregated cost fields for message, session, call_session."""
    # Update message cost
    if message:
        message.cost = message.usage_costs.aggregate(
            total=Sum('cost'))['total'] or Decimal('0')
        message.save(update_fields=['cost'])

    # Update session cost
    if session:
        session.cost = session.usage_costs.aggregate(
            total=Sum('cost'))['total'] or Decimal('0')
        session.save(update_fields=['cost'])

    # Update call_session cost
    if call_session:
        call_session.cost = call_session.usage_costs.aggregate(total=Sum('cost'))[
            'total'] or Decimal('0')
        call_session.save(update_fields=['cost'])


def update_session_projections(*, usage, message=None, session=None, call_session=None):
    """Update credits_used and audio seconds projections on ChatSession."""
    # Credits used
    try:
        ledger = debit_for_usage(usage=usage)
        ledger_amount = ledger.amount if ledger else 0
    except ValueError as e:
        logger.info(f"Debit skipped for usage {usage.id}: {e}")
        ledger_amount = 0

    if session:
        session.credits_used = (session.credits_used or 0) + ledger_amount
        session.save(update_fields=['credits_used'])

    # Audio seconds (ISSUE)
    if message and message.audio_seconds:
        seconds = int(message.audio_seconds)
        if message.role == message.USER:
            ChatSession.objects.filter(id=session.id).update(
                user_audio_seconds=F('user_audio_seconds') + seconds
            )
            # Also update the in-memory object
            session.user_audio_seconds = (
                session.user_audio_seconds or 0) + seconds
        else:
            ChatSession.objects.filter(id=session.id).update(
                assistant_audio_seconds=F('assistant_audio_seconds') + seconds
            )
            # Also update the in-memory object
            session.assistant_audio_seconds = (
                session.assistant_audio_seconds or 0) + seconds

    if call_session and call_session.duration_seconds:
        seconds = int(call_session.duration_seconds)
        ChatSession.objects.filter(id=call_session.session_id).update(
            call_audio_seconds=F('call_audio_seconds') + seconds
        )

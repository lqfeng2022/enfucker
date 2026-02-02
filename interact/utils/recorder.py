from decimal import Decimal
from django.db.models import Sum
from interact.services.ledger import debit_for_usage
from interact.models import ModelUsage
import logging

logger = logging.getLogger(__name__)


def record_usage(*, session=None, message=None, call_session=None, model=None, units):
    if not message and not session:
        raise ValueError('Either message or session is required')
    if not model:
        raise ValueError('ModelProvider is required')

    # Resolve session for cost aggregation
    if not session and message:
        session = message.session
    elif not session and call_session:
        session = call_session.session

    # Resolve call_session
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

    # Update message cost
    if message:
        message.cost = (
            message.usage_costs.aggregate(total=Sum('cost'))['total']
            or Decimal('0')
        )
        message.save(update_fields=['cost'])

    # Update session cost
    if session:
        session.cost = (
            session.usage_costs.aggregate(total=Sum('cost'))['total']
            or Decimal('0')
        )
        session.save(update_fields=['cost'])

    # Update call_session cost
    if call_session:
        call_session.cost = (
            call_session.usage_costs.aggregate(total=Sum('cost'))['total']
            or Decimal('0')
        )
        call_session.save(update_fields=['cost'])

    # Billing hook
    try:
        debit_for_usage(usage=usage)
    except ValueError as e:
        logger.info(f'Debit skipped for usage {usage.id}: {e}')

    return usage

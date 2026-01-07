from decimal import Decimal
from django.db.models import Sum
from interact.services.ledger import debit_for_usage
from interact.models import ModelUsage
import logging

logger = logging.getLogger(__name__)


def record_usage(*, session=None, message=None, model=None, units):
    if not message and not session:
        raise ValueError('Either message or session is required')
    if not model:
        raise ValueError('ModelProvider is required')

    # Resolve session
    if not session and message:
        session = message.session

    user = session.user  # 🔑 SINGLE SOURCE

    usage = ModelUsage.objects.create(
        user=user,
        session=session,  # ALWAYS SET
        message=message,  # optional
        units=Decimal(units),
        chat_model=model,
        step=f'{model.usecase}-{model.step}',  # snapshot
        unit_price=model.unit_price,  # snapshot
        cost=Decimal(units) * model.unit_price,
    )

    # Update message cash
    if message:
        message.cost = (
            message.usage_costs.aggregate(total=Sum('cost'))['total']
            or Decimal('0')
        )
        message.save(update_fields=['cost'])

    # Update session cash
    if session:
        session.cost = (
            session.usage_costs.aggregate(total=Sum('cost'))['total']
            or Decimal('0')
        )
        session.save(update_fields=['cost'])

    # BILLING HOOK
    try:
        debit_for_usage(usage=usage)
    except ValueError as e:
        # Only log at a general level if needed
        logger.info(f"Debit skipped for usage {usage.id}: {e}")

    return usage

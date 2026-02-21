from django.db import transaction
from django.db.models import F
from interact.utils.getmodels import get_credit_account_model
from interact.services.pricing import cost_to_credits
from interact.models import DebitLedger, ChatSession
import logging

logger = logging.getLogger(__name__)


@transaction.atomic
def debit_for_usage(*, usage):
    print("💰 [DEBIT_FOR_USAGE START]")
    print(
        f"usage.id: {usage.id}, session_id: {usage.session_id}, usage.cost: {usage.cost}")

    CreditAccount = get_credit_account_model()

    credits = cost_to_credits(usage.cost)
    print(f"💰 credits calculated: {credits}")

    if credits <= 0:
        print("💰 credits <= 0, skipping debit")
        return None

    # Lock credit account row
    account, _ = CreditAccount.objects. \
        select_for_update().get_or_create(user=usage.user)

    if account.balance < credits:
        logger.warning(
            f"Credit debit skipped: insufficient balance | "
            f"user_id={usage.user.id} "
            f"usage_id={usage.id} credits_required={credits} "
            f"balance={account.balance}"
        )
        raise ValueError("Insufficient credits")

    # Ledger entry (single source of truth)
    ledger = DebitLedger.objects.create(
        user=usage.user,
        amount=credits,
        usage=usage,
        note=f'Usage: {usage.step}',
    )

    # Account snapshot update
    account.balance -= credits
    account.lifetime_debits += credits
    account.save(update_fields=['balance', 'lifetime_debits'])
    print(
        f"💰 Account updated: balance={account.balance}, lifetime_debits={account.lifetime_debits}")

    # Session projection update (if usage tied to session)
    if usage.session_id:
        print(
            f"💰 About to update ChatSession credits_used for session_id={usage.session_id}")
        rows = ChatSession.objects.filter(id=usage.session_id).update(
            credits_used=F('credits_used') + credits
        )
        print(f"💰 Rows updated: {rows}")
        session = ChatSession.objects.get(id=usage.session_id)
        print(f"💰 New credits_used value: {session.credits_used}")

    print("💰 [DEBIT_FOR_USAGE END]")
    return ledger

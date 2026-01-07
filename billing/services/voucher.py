from django.db import transaction
from django.utils import timezone
from billing.models import CreditAccount


def redeem_voucher(*, voucher, user):
    with transaction.atomic():
        # Lock voucher row (prevents double redeem)
        voucher = voucher.__class__.objects.select_for_update().get(pk=voucher.pk)

        if voucher.redeemed:
            raise ValueError("Voucher already redeemed.")

        # Get or create credit account
        account, _ = CreditAccount.objects. \
            select_for_update().get_or_create(user=user)

        credits = voucher.credits

        # Update account
        account.balance += credits
        account.lifetime_credits += credits
        account.save(update_fields=['balance', 'lifetime_credits'])

        # Update voucher
        voucher.redeemed = True
        voucher.redeemed_by = user
        voucher.redeemed_at = timezone.now()
        voucher.save(update_fields=['redeemed', 'redeemed_by', 'redeemed_at'])

        return {"credits_added": credits, "balance": account.balance}

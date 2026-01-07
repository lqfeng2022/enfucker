from decimal import Decimal, ROUND_CEILING


CREDITS_PER_USD = Decimal('1000')
MIN_CREDITS = 1


def cost_to_credits(cost_usd: Decimal) -> int:
    if cost_usd <= 0:
        return 0
    credits = (cost_usd * CREDITS_PER_USD).to_integral_value(
        rounding=ROUND_CEILING
    )
    return max(MIN_CREDITS, int(credits))

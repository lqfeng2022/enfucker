import logging

logger = logging.getLogger(__name__)


def require_credits(min_credits):
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = resolve_user(*args, **kwargs)
            check_user_credits(user, min_credits)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def resolve_user(*args, **kwargs):
    if 'user' in kwargs:
        return kwargs['user']

    if 'session' in kwargs:
        return kwargs['session'].user

    if 'message' in kwargs:
        return kwargs['message'].session.user

    if 'assistant_msg' in kwargs:
        return kwargs['assistant_msg'].session.user

    for arg in args:
        if hasattr(arg, 'session'):
            return arg.session.user

    raise ValueError("Cannot resolve user for credit check")


def check_user_credits(user, required_credits: int):
    account = getattr(user, 'credit_account', None)

    if not account:
        logger.info(
            f"Credit check failed: User {user.id} has no credit account"
        )
        raise InsufficientCredits(
            f"User {user.id} has no credit account"
        )

    if account.balance < required_credits:
        logger.info(
            f"Credit check failed: insufficient balance"
            f"({account.balance if account else 0}, required {required_credits})"
        )
        raise InsufficientCredits(
            f"User {user.id} has insufficient credits"
        )

    return account


class InsufficientCredits(Exception):
    pass

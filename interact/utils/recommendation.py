import random
from .getmodels import get_product_model


def my_recommendation_engine(user=None, limit=50):
    Product = get_product_model()
    """Simple recommendation engine."""
    qs = Product.objects.all().order_by('-created_at')
    products = list(qs[:200])  # take a recent slice (for performance)

    # (Optional) later: bias based on user history
    if user and user.is_authenticated:
        # Placeholder: you can mix in liked/bookmarked data
        random.shuffle(products)
    else:
        # Anonymous user: just randomize
        random.shuffle(products)

    return [p.id for p in products[:limit]]

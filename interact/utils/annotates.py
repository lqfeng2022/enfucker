from django.db.models import BooleanField, Value, Exists, OuterRef, Count, Q
from interact.models import Like, CollectionItem, Follow, ChatSession
from .getmodels import get_product_model


def annotate_state_for_product(queryset, user):
    """Annotate the given queryset of Products with per-user
    like, bookmark and follow state.
    """
    if not user or not user.is_authenticated:
        return queryset.annotate(
            _is_liked=Value(False, output_field=BooleanField()),
            _is_bookmarked=Value(False, output_field=BooleanField()),
            _is_followed=Value(False, output_field=BooleanField()),
        )

    return queryset.annotate(
        _is_liked=Exists(
            Like.objects.filter(
                user=user, product_id=OuterRef('pk'), visible=True
            )
        ),
        _is_bookmarked=Exists(
            CollectionItem.objects.filter(
                collection__user=user, product_id=OuterRef('pk'), visible=True
            )
        ),
        _is_followed=Exists(
            Follow.objects.filter(
                user=user, host_id=OuterRef('host_id'), visible=True
            )
        ),
        _is_chatted=Exists(
            ChatSession.objects.filter(
                user=user, product_id=OuterRef('pk'), visible=True
            )
        ),
    )


def annotate_follow_for_host(queryset, user):
    """Annotate the given queryset of Products with per-user follow state."""
    if not user or not user.is_authenticated:
        return queryset.annotate(
            _is_followed=Value(False, output_field=BooleanField()),
        )

    return queryset.annotate(
        _is_followed=Exists(
            Follow.objects.filter(
                user=user, host_id=OuterRef('pk'), visible=True
            )
        ),
    )


def annotate_counts_for_host(queryset):
    Product = get_product_model()

    return queryset.annotate(
        videos_count=Count(
            'products',
            filter=Q(products__type=Product.PRODUCT_VIDEO),
            distinct=True,
        ),
        subtitles_count=Count(
            'products',
            filter=Q(products__type=Product.PRODUCT_SUBTITLE),
            distinct=True,
        ),
        expressions_count=Count(
            'products',
            filter=Q(products__type=Product.PRODUCT_EXPRESSION),
            distinct=True,
        ),
    )

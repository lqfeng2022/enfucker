from rest_framework_nested import routers
from interact.views.history import UserViewAddViewSet, UserViewProductViewSet
from interact.views.like import LikeAddViewSet, LikeProductViewSet
from interact.views.chatsession import ChatSessionAddViewSet
from interact.views.hostfollow import HostFollowAddViewSet, HostFollowedViewSet, HostFollowedProductsViewSet
from interact.views.collection import BookmarkedProductViewSet
from .views import feed, host, product, relevant, views, playlist


# Create parent routers, like 'store/videos/'...
router = routers.DefaultRouter()

router.register('alphabets', views.AlphabetViewSet)
router.register('genres', views.GenreViewSet)

router.register('hosts', host.HostViewSet, basename='host')
router.register('followed-hosts', HostFollowedViewSet,
                basename='followed-hosts')

router.register('feed', feed.FeedViewSet, basename='feed')

router.register('playlists', playlist.PlaylistViewSet, basename='playlist')

router.register('products', product.ProductViewSet, basename='product')

router.register('viewed-products', UserViewProductViewSet,
                basename='viewed-products')
router.register('liked-products', LikeProductViewSet,
                basename='liked-products')
router.register('bookmarked-products', BookmarkedProductViewSet,
                basename='bookmarked-products')
router.register('followed-products', HostFollowedProductsViewSet,
                basename='followed-products')


# store/products/<product_pk>/like/
product_router = routers.NestedDefaultRouter(router, 'products',
                                             lookup='product')
product_router.register('view', UserViewAddViewSet, basename='product-view')
product_router.register('like', LikeAddViewSet, basename='product-like')
product_router.register('chatsession', ChatSessionAddViewSet,
                        basename='product-chatsessions')
product_router.register('relevants', relevant.RelevantViewSet,
                        basename='product-relevants')


# store/playlists/<short_uuid>/items/
playlist_router = routers.NestedDefaultRouter(router, 'playlists',
                                              lookup='playlist')
playlist_router.register('items', playlist.PlaylistItemViewSet,
                         basename='playlist-items')


host_router = routers.NestedDefaultRouter(router, 'hosts', lookup='host')
host_router.register('follow', HostFollowAddViewSet, basename='host-follow')


urlpatterns = (
    router.urls +
    product_router.urls +
    host_router.urls +
    playlist_router.urls
)


# NOTE:
# NestedDefaultRouter(parent router, parent prefix, lookup)
# `lookup='product`: means we're gonna have a parameter called 'product_pk'

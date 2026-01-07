from rest_framework_nested import routers
from .views.search import SearchViewSet
from .views.history import UserViewViewSet
from .views.like import LikeViewSet
from .views.hostfollow import HostFollowViewSet
from .views.collection import (
    CollectionViewSet, CollectionItemViewSet, CollectionProductViewSet)
from .views.chatsession import ChatSessionViewSet, ChatMessageViewSet


router = routers.DefaultRouter()

# 1)Base routers
router.register('searches', SearchViewSet, basename='searches')
router.register('views', UserViewViewSet, basename='views')
router.register('likes', LikeViewSet, basename='likes')
router.register('follows', HostFollowViewSet, basename='follows')
router.register('collections', CollectionViewSet, basename='collections')
router.register('chatsessions', ChatSessionViewSet, basename='chatsessions')


# 2)Nested routers
# a)'collections/<pk>/items/<item_pk>'
collection_router = routers.NestedDefaultRouter(router, 'collections',
                                                lookup='collection')
collection_router.register('items', CollectionItemViewSet,
                           basename='collection-items')
# b)'collections/<pk>/items/<product_pk>'
collection_router.register('products', CollectionProductViewSet,
                           basename='collection-products')

# c)'chatsessions/<pk>/messages/<message_pk>'
chatsession_router = routers.NestedDefaultRouter(router, 'chatsessions',
                                                 lookup='session')
chatsession_router.register('messages', ChatMessageViewSet,
                            basename='chatsession-messages')


urlpatterns = router.urls + collection_router.urls + chatsession_router.urls

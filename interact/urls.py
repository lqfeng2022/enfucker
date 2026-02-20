from rest_framework_nested import routers
from .views.search import SearchViewSet
from .views.history import UserViewViewSet
from .views.like import LikeViewSet
from .views.hostfollow import HostFollowViewSet
from .views.collection import (
    CollectionViewSet, CollectionItemViewSet, CollectionProductViewSet,
    SavedPlaylistViewSet, SavedCourseViewSet
)
from .views.chatsession import ChatSessionViewSet, ChatMessageViewSet
from .views.callsession import CallSessionViewSet


router = routers.DefaultRouter()

# Base routers
router.register('searches', SearchViewSet, basename='searches')
router.register('views', UserViewViewSet, basename='views')
router.register('likes', LikeViewSet, basename='likes')
router.register('follows', HostFollowViewSet, basename='follows')
router.register('collections', CollectionViewSet, basename='collections')
router.register('chatsessions', ChatSessionViewSet, basename='chatsessions')

router.register('saved-playlists', SavedPlaylistViewSet,
                basename='savedplaylists')
router.register('saved-courses', SavedCourseViewSet,
                basename='savedcourses')

# Nested routers
collection_router = routers.NestedDefaultRouter(router, 'collections',
                                                lookup='collection')
# collections/<pk>/items/<item_pk>
collection_router.register('items', CollectionItemViewSet,
                           basename='collection-items')
# collections/<pk>/products/<product_pk>
collection_router.register('products', CollectionProductViewSet,
                           basename='collection-products')

chatsession_router = routers.NestedDefaultRouter(router, 'chatsessions',
                                                 lookup='session')
# chatsessions/<pk>/messages/<message_pk>
chatsession_router.register('messages', ChatMessageViewSet,
                            basename='chatsession-messages')
# chatsessions/<pk>/calls/<call_pk>
chatsession_router.register('calls', CallSessionViewSet,
                            basename='chatsession-calls')


urlpatterns = (
    router.urls +
    collection_router.urls +
    chatsession_router.urls
)

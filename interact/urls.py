from rest_framework_nested import routers
from .views.search import SearchViewSet
from .views.history import UserViewViewSet
from .views.like import LikeViewSet
from .views.hostfollow import HostFollowViewSet
from .views.collection import (
    CollectionViewSet, CollectionItemViewSet, CollectionProductViewSet,
    SavedPlaylistViewSet, SavedCourseViewSet)
from .views.chatsession import ChatSessionViewSet, ChatMessageViewSet
from .views.callsession import CallSessionViewSet
from .views.speaking import (
    MockTestViewSet, SpeakingAttemptViewSet, MockTestAttemptViewSet,
    SpeakingAnswerViewSet)


router = routers.DefaultRouter()

# Base routers
router.register('searches', SearchViewSet, basename='searches')
router.register('views', UserViewViewSet, basename='views')
router.register('likes', LikeViewSet, basename='likes')
router.register('follows', HostFollowViewSet, basename='follows')

router.register('collections', CollectionViewSet, basename='collections')
router.register('chatsessions', ChatSessionViewSet, basename='chatsessions')

router.register('saved-playlists', SavedPlaylistViewSet,
                basename='saved-playlists')
router.register('saved-courses', SavedCourseViewSet,
                basename='saved-courses')

# Nested routers

# COLLECTION
# collections/<pk>/items/<item_pk>
# collections/<pk>/products/<product_pk>
collection_router = routers.NestedDefaultRouter(
    router,
    'collections',
    lookup='collection'
)
collection_router.register(
    'items',
    CollectionItemViewSet,
    basename='collection-items'
)
collection_router.register(
    'products',
    CollectionProductViewSet,
    basename='collection-products'
)


# CHAT
# chatsessions/<pk>/messages/<message_pk>
# chatsessions/<pk>/calls/<call_pk>
chatsession_router = routers.NestedDefaultRouter(
    router,
    'chatsessions',
    lookup='session'
)
chatsession_router.register(
    'messages',
    ChatMessageViewSet,
    basename='chatsession-messages'
)
chatsession_router.register(
    'calls',
    CallSessionViewSet,
    basename='chatsession-calls'
)


# MOCK TESTS
# GET /mock-tests/
# GET /mock-tests/{id}/
# POST /mock-tests/{id}/attempts/
router.register('mock-tests', MockTestViewSet, basename='mock-tests')
mocktest_router = routers.NestedDefaultRouter(
    router,
    'mock-tests',
    lookup='mock_test'
)
mocktest_router.register(
    'attempts',
    MockTestAttemptViewSet,
    basename='mock-tests-attempts'
)

# GET /attempts/
# GET /attempts/{id}/
# POST /attempts/{id}/answers/
# GET /attempts/{id}/answers/
router.register('attempts', SpeakingAttemptViewSet, basename='attempts')
attempts_router = routers.NestedDefaultRouter(
    router,
    'attempts',
    lookup='attempt'
)
attempts_router.register(
    'answers',
    SpeakingAnswerViewSet,
    basename='attempts-answers'
)


urlpatterns = (
    router.urls +
    collection_router.urls +
    chatsession_router.urls +
    mocktest_router.urls +
    attempts_router.urls
)

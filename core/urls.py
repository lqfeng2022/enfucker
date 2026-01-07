from django.views.generic import TemplateView
from django.urls import path, include
from .views import CookieLoginView, CookieLogoutView, ProfileViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', TemplateView.as_view(template_name='core/index.html')),
    path('login/', CookieLoginView.as_view()),
    path('logout/', CookieLogoutView.as_view()),
    path('', include(router.urls)),
]

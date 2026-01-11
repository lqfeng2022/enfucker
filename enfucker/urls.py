from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static


admin.site.site_header = 'en-fucker Admin'
admin.site.index_title = 'Admin'

urlpatterns = [
    path('', include('core.urls')),
    path('admin-9fge0-2fe3/', admin.site.urls),
    path('store/', include('store.urls')),
    path('interact/', include('interact.urls')),
    path('billing/', include('billing.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('__debug__/', include('debug_toolbar.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

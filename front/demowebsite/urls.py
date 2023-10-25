from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('shared.urls')),
    path('dti/', include('dticlustering.urls')),

    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve media files in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
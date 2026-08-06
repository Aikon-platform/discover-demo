from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path("", include("shared.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    # TODO make the following apps optional (set in .env)
    path("dti/", include("dticlustering.urls")),
    path("similarity/", include("similarity.urls")),
    path("regions/", include("regions.urls")),
    path("search/", include("search.urls")),
    path("watermarks/", include("watermarks.urls")),
    path("datasets/", include("datasets.urls")),
    # path("watermarks/", include("pipelines.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

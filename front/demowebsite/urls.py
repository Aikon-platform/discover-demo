from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('shared.urls')),
    path('dti/', include('dticlustering.urls')),

    path('admin/', admin.site.urls),
]

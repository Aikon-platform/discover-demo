from django.contrib import admin

from .models import DTIClustering, SavedClustering

admin.site.register(DTIClustering)
admin.site.register(SavedClustering)
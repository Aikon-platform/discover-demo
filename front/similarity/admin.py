from django.contrib import admin

from .models import Similarity, SavedSimilarity

admin.site.register(Similarity)
admin.site.register(SavedSimilarity)

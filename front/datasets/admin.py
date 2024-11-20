from django.contrib import admin

from .models import *

admin.site.register(ZippedDataset)


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "created_on")
    ordering = ("-created_on",)

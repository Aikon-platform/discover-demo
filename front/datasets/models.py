from django.db import models
import uuid
import os

from .utils import PathAndRename

path_datasets = PathAndRename("datasets/")

# MODELS

class ZippedDataset(models.Model):
    """
    This class is used to store simple datasets made of a single uploaded .zip file
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, default="dataset", blank=True, 
                            verbose_name="Dataset name", help_text="An optional name to identify this dataset")
    
    zip_file = models.FileField(upload_to=path_datasets, max_length=500)
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
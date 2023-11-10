from django.db import models
from django.utils.deconstruct import deconstructible
import uuid
import os

# UTILS

@deconstructible
class PathAndRename(object):
    """
    This class is used to rename the uploaded files
    """
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        return os.path.join(self.path, filename)

path_datasets = PathAndRename("datasets/")

# MODELS

class ZippedDataset(models.Model):
    """
    This class is used to store simple datasets made of a single uploaded .zip file
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    zip_file = models.FileField(upload_to=path_datasets, max_length=500)
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
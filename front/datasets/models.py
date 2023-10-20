from django.db import models
from django.utils.deconstruct import deconstructible
import uuid
import os


@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        return os.path.join(self.path, filename)

path_datasets = PathAndRename("datasets/")


# A simple model for a dataset made of a single .zip file
class ZippedDataset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    zip_file = models.FileField(upload_to=path_datasets, max_length=500)
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
from django.utils.deconstruct import deconstructible
import os
import uuid


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

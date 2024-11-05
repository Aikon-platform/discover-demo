from django.utils.deconstruct import deconstructible
import os
import uuid


IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".tiff"}


@deconstructible
class PathAndRename(object):
    """
    This class is used to rename the uploaded files
    """

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        # Generate UUID if not already set (should be rare since UUID is default)
        filename = f"{instance.id or uuid.uuid4()}.{ext}"
        return os.path.join(self.path, filename)

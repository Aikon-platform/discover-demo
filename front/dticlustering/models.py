from django.conf import settings
from django.db import models
from pathlib import Path

from ..datasets.models import ZippedDataset

# A simple model for a clustering query and result
class DTIClustering(models.Model):
    id = models.UUIDField(primary_key=True)

    notify_email = models.EmailField(
        verbose_name="Email address to notify",
        help_text="Email address to notify you about the clustering progress")

    status = models.CharField(max_length=20, default='PENDING', editable=False)
    is_finished = models.BooleanField(default=False, editable=False)
    requested_on = models.DateTimeField(auto_now_add=True, editable=False)

    # The clustering tracking id
    api_tracking_id = models.UUIDField(null=True, editable=False)

    # The clustering parameters
    dataset = models.ForeignKey(ZippedDataset, null=True, on_delete=models.SET_NULL)
    parameters = models.JSONField(null=True)

    class Meta:
        ordering = ['-requested_on']

    @property
    def result_media_path(self):
        return f"dticlustering/{self.id}/result"
    
    @property
    def result_media_url(self):
        return f"{settings.MEDIA_URL}{self.result_media_path}"
    
    @property
    def result_full_path(self):
        return Path(settings.MEDIA_ROOT) / self.result_media_path

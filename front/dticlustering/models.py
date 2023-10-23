from django.conf import settings
from django.db import models
from pathlib import Path
from django.urls import reverse
import requests
import uuid

from datasets.models import ZippedDataset

DTI_API_URL = getattr(settings, 'DTI_API_URL', 'http://localhost:5000')
BASE_URL = getattr(settings, 'BASE_URL', 'http://localhost:8000')

# A simple model for a clustering query and result
class DTIClustering(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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
    def result_media_path(self) -> str:
        return f"dticlustering/{self.id}/result"
    
    @property
    def result_media_url(self) -> str:
        return f"{settings.MEDIA_URL}{self.result_media_path}"
    
    @property
    def result_full_path(self) -> Path:
        return Path(settings.MEDIA_ROOT) / self.result_media_path
    
    @property
    def log_file_path(self) -> Path:
        return self.result_full_path / "log.txt"
    
    def get_full_log(self):
        if not self.log_file_path.exists():
            return "No log"
        with open(self.log_file_path, "r") as f:
            return f.read()
    
    def write_log(self, text: str):
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file_path, "a") as f:
            f.write(text)

    def get_absolute_url(self):
        return reverse("dticlustering:status", kwargs={"pk": self.pk})

    def start_clustering(self):
        """
        Queries the API to start the task
        """
        api_query = requests.post(
            f"{DTI_API_URL}/clustering/start",
            data={
                "dataset_url": f"{settings.BASE_URL}{self.dataset.zip_file.url}",
                "dataset_id": str(self.dataset.id),
                "clustering_id": str(self.id),
                "callback_url": f"{settings.BASE_URL}{reverse('dticlustering:callback', kwargs={'pk': self.pk})}"
            }
        )
        try:
            api_result = api_query.json()
            self.api_tracking_id = api_result["tracking_id"]
        except:
            self.write_log(f"Error starting clustering: {api_query.text}")
            self.status = "ERROR"
            self.is_finished = True

        self.save()

    def cancel_clustering(self):
        """
        Queries the API to cancel the task
        """
        api_query = requests.post(
            f"{DTI_API_URL}/clustering/{self.api_tracking_id}/cancel",
        )
        try:
            print(api_query.text)
        except:
            self.write_log(f"Error cancelling clustering: {api_query.text}")
            self.status = "ERROR"
            self.is_finished = True

    def terminate_clustering(self, data: dict):
        """
        Called by the API when the task is finished
        """
        self.status = "FINISHED"
        self.is_finished = True
        self.write_log(f"Clustering finished: {data}")
        self.save()

    def get_progress(self):
        """
        Queries the API to get the task progress
        """
        api_query = requests.get(
            f"{DTI_API_URL}/clustering/{self.api_tracking_id}/status",
        )
        try:
            return api_query.json()
        except:
            self.write_log(f"Error getting clustering progress: {api_query.text}")
            return {
                "status": "UNKNOWN",
            }
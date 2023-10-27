from django.conf import settings
from django.db import models
from pathlib import Path
from django.urls import reverse
import requests
import uuid
import json
from django.utils.functional import cached_property

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
    
    @property
    def result_zip_url(self) -> str:
        return f"{self.result_media_url}/results.zip"
    
    @property
    def result_zip_exists(self) -> bool:
        return (self.result_full_path / "results.zip").exists()
    
    @cached_property
    def expanded_results(self) -> "ResultStruct":
        return ResultStruct(self.result_full_path, self.result_media_url)
    
    def get_token(self):
        return uuid.uuid5(uuid.NAMESPACE_URL, settings.SECRET_KEY + str(self.id)).hex

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
                "parameters": json.dumps(self.parameters),
                "notify_url": f"{settings.BASE_URL}{reverse('dticlustering:notify', kwargs={'pk': self.pk})}?token={self.get_token()}"
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
            self.status = "CANCELLED"
            self.is_finished = True
        except:
            self.write_log(f"Error cancelling clustering: {api_query.text}")
            self.status = "ERROR"
            self.is_finished = True
        self.save()

    def receive_notification(self, data: dict):
        """
        Called by the API when tasks events happen
        """
        event = data["event"]
        if event == "STARTED":
            self.status = "PROGRESS"
            self.save()
            return
        elif event == "SUCCESS":
            self.status = "FETCHING RESULTS"
            self.save()
            # start collecting results
            from .tasks import collect_results
            collect_results.send(str(self.pk), data["output"]["result_url"])
        elif event == "ERROR":
            self.finish_clustering("ERROR", data["error"])

    def finish_clustering(self, status="SUCCESS", error=None):
        """
        Called when the task is finished
        """
        self.status = status
        if error:
            self.write_log(error)
        self.is_finished = True
        self.save()

    def get_progress(self):
        """
        Queries the API to get the task progress
        """
        api_query = requests.get(
            f"{DTI_API_URL}/clustering/{self.api_tracking_id}/status",
        )
        try:
            return {
                "status": self.status,
                **api_query.json()
            }
        except:
            self.write_log(f"Error getting clustering progress: {api_query.text}")
            return {
                "status": "UNKNOWN",
            }
        

class ResultStruct:
    """
    A class to browse the result of a clustering
    """
    def __init__(self, path: Path, media_url: str):
        clusters_path = path / "clusters"
        prototypes_path = path / "prototypes"
        backgrounds_path = path / "backgrounds"

        # Cluster_by_path csv
        cluster_by_path_file = path / "cluster_by_path.csv"
        if cluster_by_path_file.exists():
            self.cluster_by_path = f"{media_url}/cluster_by_path.csv"

        # no proto
        if not prototypes_path.exists():
            self.clusters = []
            return

        # List prototypes
        prototypes = {
            int(c.name[len("prototype"):-4])
            for c in prototypes_path.glob("prototype*")
            if c.suffix in [".jpg", ".png"]
        }
        self.clusters = []
        
        # List backgrounds
        self.backgrounds = [
            f"{media_url}/backgrounds/{b.name}"
            for b in backgrounds_path.glob("background*")
            if b.suffix in [".jpg", ".png"]
        ]

        def try_and_get_url(*try_names):
            """
            For each name in try_names, returns (as a URL) the first one
            that exists (as a file), or None
            """
            for try_name in try_names:
                if (path / try_name).exists():
                    return f"{media_url}/{try_name}"

        # Iter clusters
        for p in sorted(prototypes):
            # test if masked version exists
            proto_url = try_and_get_url(
                f"masked_prototypes/prototype{p}.png",
                f"masked_prototypes/prototype{p}.jpg",
                f"prototypes/prototype{p}.png",
                f"prototypes/prototype{p}.jpg",
            )

            cluster = {"prototype": proto_url, "id": p, "imgs": []}

            # add mask
            cluster["mask"] = try_and_get_url(
                f"masks/mask{p}.png",
                f"masks/mask{p}.jpg",
            )

            cluster_dir = clusters_path / f"cluster{p}"
            if not cluster_dir.exists():
                continue

            for img in cluster_dir.glob("*_raw.*"):
                if not img.suffix in [".jpg", ".png"]:
                    continue
                cluster["imgs"].append({
                    "raw": f"{media_url}/clusters/cluster{p}/{img.name}",
                    "tsf": f"{media_url}/clusters/cluster{p}/{img.name[:-8]}_tsf{img.suffix}",
                })
            
            self.clusters.append(cluster)

from django.conf import settings
from django.db import models
from pathlib import Path
from django.urls import reverse
import requests
import uuid
import json
import csv
import io
from django.utils.functional import cached_property

from datasets.models import ZippedDataset

DTI_API_URL = getattr(settings, 'DTI_API_URL', 'http://localhost:5000')
BASE_URL = getattr(settings, 'BASE_URL', 'http://localhost:8000')

class DTIClustering(models.Model):
    """
    Main model for a clustering query and result
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, default="dti", blank=True, 
                            verbose_name="Clustering name", help_text="An optional name to identify this clustering")

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

    def get_absolute_url(self):
        return reverse("dticlustering:status", kwargs={"pk": self.pk})

    # Util URLs and Paths
    @property
    def result_media_path(self) -> str:
        """
        Path to the result folder, relative to MEDIA_ROOT
        """
        return f"dticlustering/{self.id}/result"
    
    @property
    def result_full_path(self) -> Path:
        """
        Full path to the result folder
        """
        return Path(settings.MEDIA_ROOT) / self.result_media_path
    
    @property
    def log_file_path(self) -> Path:
        """
        Full path to the log file
        """
        return self.result_full_path / "log.txt"
    
    @property
    def result_media_url(self) -> str:
        """
        URL to the result folder, including MEDIA_URL
        """
        return f"{settings.MEDIA_URL}{self.result_media_path}"
    
    @property
    def result_zip_url(self) -> str:
        """
        URL to the result zip file
        """
        return f"{self.result_media_url}/results.zip"
    
    @property
    def result_zip_exists(self) -> bool:
        """
        True if the result zip file exists
        """
        return (self.result_full_path / "results.zip").exists()
    
    @cached_property
    def full_log(self):
        """
        Returns the full log file content
        """
        if not self.log_file_path.exists():
            return None
        with open(self.log_file_path, "r") as f:
            return f.read()
    
    def write_log(self, text: str):
        """
        Writes text to the log file
        """
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file_path, "a") as f:
            f.write(text)

    def get_token(self):
        """
        Returns a unique token to secure in the notification callback URL
        """
        return uuid.uuid5(uuid.NAMESPACE_URL, settings.SECRET_KEY[:10] + str(self.id)).hex

    def start_clustering(self):
        """
        Queries the API to start the task
        """
        try:
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
        except ConnectionError:
            self.write_log("Connection error when starting task")
            self.status = "ERROR"
            self.is_finished = True
            self.save()
            return

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
        try:
            api_query = requests.post(
                f"{DTI_API_URL}/clustering/{self.api_tracking_id}/cancel",
            )
        except ConnectionError:
            self.write_log("Connection error when cancelling task")
            self.save()
            return

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
        try:
            api_query = requests.get(
                f"{DTI_API_URL}/clustering/{self.api_tracking_id}/status",
            )
        except ConnectionError:
            return {
                "status": "UNKNOWN",
                "error": "Connection error when getting task progress from the worker"
            }

        try:
            return {
                "status": self.status,
                **api_query.json()
            }
        except:
            self.write_log(f"Error when reading clustering progress: {api_query.text}")
            return {
                "status": "UNKNOWN",
            }
    
    @cached_property
    def expanded_results(self):
        """
        Returns a dict with all the result data
        """

        path = self.result_full_path
        result_dict = {}

        clusters_path = path / "clusters"
        prototypes_path = path / "prototypes"
        backgrounds_path = path / "backgrounds"

        # Cluster_by_path csv
        cluster_by_path_file = path / "cluster_by_path.csv"
        if cluster_by_path_file.exists():
            result_dict["csv_export_file"] = "cluster_by_path.csv"

        # Image data json
        image_data_file = path / "cluster_by_path.json"
        image_data = {}
        if image_data_file.exists():
            with open(image_data_file, "r") as f:
                image_data = json.load(f)

        # no proto
        if not prototypes_path.exists():
            result_dict["clusters"] = []
            return result_dict

        # List prototypes
        prototypes = {
            int(c.name[len("prototype"):-4])
            for c in prototypes_path.glob("prototype*")
            if c.suffix in [".jpg", ".png"]
        }

        clusters = {}
        result_dict["clusters"] = clusters

        # List backgrounds
        result_dict["background_urls"] = [
            "backgrounds/{b.name}"
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
                    return f"{try_name}"

        # Iter clusters
        for p in sorted(prototypes):
            # Display the masked prototype if it exists, otherwise the original
            proto_url = try_and_get_url(
                f"masked_prototypes/prototype{p}.png",
                f"masked_prototypes/prototype{p}.jpg",
                f"prototypes/prototype{p}.png",
                f"prototypes/prototype{p}.jpg",
            )

            cluster = {
                "proto_url": proto_url, 
                "id": p, 
                "name": f"Cluster {p}", 
                "images": []
            }
            clusters[p] = cluster

            # add mask
            cluster["mask_url"] = try_and_get_url(
                f"masks/mask{p}.png",
                f"masks/mask{p}.jpg",
            )

            cluster_dir = clusters_path / f"cluster{p}"
            if not cluster_dir.exists():
                continue

            for img in cluster_dir.glob("*_raw.*"):
                if not img.suffix in [".jpg", ".png"]:
                    continue
                img_id = int(img.stem[: -len("_raw")])
                img_data = {
                    "raw_url": f"clusters/cluster{p}/{img.name}",
                    "tsf_url": f"clusters/cluster{p}/{img_id}_tsf{img.suffix}",
                    "path": None,
                    "distance": 100.,
                    "id": img_id,
                }
                if str(img_id) in image_data:
                    img_ext_data = image_data[str(img_id)]
                    assert img_ext_data["cluster_id"] == p
                    img_data["path"] = img_ext_data["path"]
                    img_data["distance"] = img_ext_data["distance"]
                
                cluster["images"].append(img_data)

        return result_dict


class SavedClustering(models.Model):
    """
    Model for saving clustering modifications made by user
    """
    from_dti = models.ForeignKey(DTIClustering, on_delete=models.CASCADE, related_name="saved_clustering")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, default="dti", blank=True, 
                            verbose_name="Clustering name", help_text="An optional name to identify this clustering")

    date = models.DateTimeField(auto_now=True, editable=False)

    clustering_data = models.JSONField(null=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Manual clustering"

    def get_absolute_url(self) -> str:
        return reverse("dticlustering:saved", kwargs={"pk": self.pk, "from_pk": self.from_dti_id})
    
    def format_as_csv(self) -> str:
        """
        Returns a CSV string with the clustering data
        """
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["image_id", "image_path", "cluster_id", "cluster_name"])

        for cluster_id, cluster in self.clustering_data["clusters"].items():
            for img in cluster["images"]:
                writer.writerow([img["id"], img["path"], cluster_id, cluster["name"]])

        return output.getvalue()
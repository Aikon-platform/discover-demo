from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.functional import cached_property
from django.core.mail import send_mail, mail_admins
from django.utils import timezone
from django.urls import reverse
from pathlib import Path
import requests
import uuid
import json
import csv
import io
import traceback
import shutil

from typing import Dict, Any

from datasets.models import ZippedDataset
from requests import RequestException

User = get_user_model()

DTI_API_URL = getattr(settings, "DTI_API_URL", "http://localhost:5000")
BASE_URL = getattr(settings, "BASE_URL", "http://localhost:8000")


class DTIClustering(models.Model):
    """
    Main model for a clustering query and result
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=64,
        default="dti",
        blank=True,
        verbose_name="Experiment name",
        help_text="Optional name to identify this clustering experiment",
    )

    notify_email = models.BooleanField(
        default=True,
        verbose_name="Notify by email",
        blank=True,
        help_text="Send an email when the clustering is finished",
    )

    status = models.CharField(max_length=20, default="PENDING", editable=False)
    is_finished = models.BooleanField(default=False, editable=False)
    requested_on = models.DateTimeField(auto_now_add=True, editable=False)
    requested_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, editable=False
    )

    # The clustering tracking id
    api_tracking_id = models.UUIDField(null=True, editable=False)

    # The clustering parameters
    dataset = models.ForeignKey(ZippedDataset, null=True, on_delete=models.SET_NULL)
    parameters = models.JSONField(null=True)

    class Meta:
        ordering = ["-requested_on"]
        permissions = [
            ("monitor_dticlustering", "Can monitor DTI Clustering"),
        ]

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

    @property
    def result_summary_url(self) -> str:
        """
        URL to the result summary file
        """
        return f"{self.result_media_url}/summary.zip"

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
        return uuid.uuid5(
            uuid.NAMESPACE_URL, settings.SECRET_KEY[:10] + str(self.id)
        ).hex

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
                    "notify_url": f"{settings.BASE_URL}{reverse('dticlustering:notify', kwargs={'pk': self.pk})}?token={self.get_token()}",
                },
            )
        except (ConnectionError, RequestException):
            self.write_log("Connection error when starting task")
            self.status = "ERROR"
            self.is_finished = True
            self.save()
            # Send error email to website admins
            mail_admins(
                f"[discover-demo] Offline API",
                f"Error starting DTI Clustering task {self.name}. The API server is offline.",
                fail_silently=True,
            )
            return

        print(
            f"Request for clustering failed with {api_query.status_code}: {api_query.text}"
        )

        try:
            api_result = api_query.json()
            self.api_tracking_id = api_result["tracking_id"]
        except Exception as e:
            exc = f"\n[{e.__class__.__name__}] {e}\nStack Trace:\n{traceback.format_exc()}\n"
            self.write_log(
                f"Request for clustering failed with {api_query.status_code}: {api_query.text}\n{exc}"
            )
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
        except (ConnectionError, RequestException):
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

    def finish_clustering(self, status="SUCCESS", error=None, notify=True):
        """
        Called when the task is finished
        """
        self.status = status
        if error:
            self.write_log(error)
        self.is_finished = True
        self.save()

        if notify and self.notify_email:
            try:
                send_mail(
                    f"[discover-demo] DTI Clustering {self.status}",
                    f"Your DTI Clustering task {self.name} has finished with status {self.status}.\n\nYou can access the results at : {BASE_URL}{self.get_absolute_url()}",
                    settings.DEFAULT_FROM_EMAIL,
                    [self.requested_by.email],
                    fail_silently=False,
                )
            except:
                self.write_log(f"Error sending email: {traceback.format_exc()}")

    def get_progress(self):
        """
        Queries the API to get the task progress
        """
        try:
            api_query = requests.get(
                f"{DTI_API_URL}/clustering/{self.api_tracking_id}/status",
            )
        except (ConnectionError, RequestException):
            return {
                "status": "UNKNOWN",
                "error": "Connection error when getting task progress from the worker",
            }

        try:
            return {"status": self.status, **api_query.json()}
        except:
            self.write_log(f"Error when reading clustering progress: {api_query.text}")
            return {
                "status": "UNKNOWN",
            }

    @staticmethod
    def get_api_monitoring():
        """
        Returns a dict with the monitoring data
        """
        try:
            api_query = requests.get(
                f"{DTI_API_URL}/clustering/monitor",
            )
        except (ConnectionError, RequestException):
            return {
                "error": "Connection error when getting monitoring data from the worker"
            }

        try:
            return api_query.json()
        except:
            return {"error": "Error when reading monitoring data"}

    @staticmethod
    def get_frontend_monitoring():
        """
        Returns a dict with the monitoring data
        """
        total_size = 0
        for f in Path(settings.MEDIA_ROOT).glob("**/*"):
            if f.is_file():
                total_size += f.stat().st_size
        n_datasets = ZippedDataset.objects.count()
        n_clusterings = DTIClustering.objects.count()

        return {
            "total_size": total_size,
            "n_datasets": n_datasets,
            "n_clusterings": n_clusterings,
        }

    @staticmethod
    def clear_old_clusterings(days_before: int = 30) -> Dict[str, int]:
        """
        Clears all clusterings older than days_before days
        """
        old_clusterings = DTIClustering.objects.filter(
            requested_on__lte=timezone.now() - timezone.timedelta(days=days_before)
        )

        # remove results
        for c in old_clusterings:
            shutil.rmtree(c.result_full_path, ignore_errors=True)

        # remove all datasets except those who have a clustering younger than days_before days
        old_datasets = ZippedDataset.objects.exclude(
            dticlustering__requested_on__gt=timezone.now()
            - timezone.timedelta(days=days_before)
        )
        for d in old_datasets:
            d.zip_file.delete()

        cleared_data = {
            "cleared_clusterings": len(old_clusterings),
            "cleared_datasets": len(old_datasets),
        }

        # remove records
        old_clusterings.delete()
        old_datasets.delete()

        return cleared_data

    @staticmethod
    def clear_api_old_clusterings(days_before: int = 30) -> Dict[str, Any]:
        """
        Clears all clusterings older than days_before days from the API server
        """
        try:
            api_query = requests.post(
                f"{DTI_API_URL}/clustering/monitor/clear",
                data={
                    "days_before": days_before,
                },
            )
        except (ConnectionError, RequestException):
            return {
                "error": "Connection error when clearing old clusterings from the worker"
            }

        try:
            return api_query.json()
        except:
            return {
                "error": "Error when output from API server",
                "output": api_query.text,
            }

    @cached_property
    def expanded_results(self):
        """
        Returns a dict with all the result data
        """

        path = self.result_full_path
        if not path.exists():
            return {}

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
            int(c.name[len("prototype") : -4])
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
                "images": [],
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
                    "distance": 100.0,
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

    from_dti = models.ForeignKey(
        DTIClustering, on_delete=models.CASCADE, related_name="saved_clustering"
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=64,
        default="dti",
        blank=True,
        verbose_name="Clustering name",
        help_text="An optional name to identify this clustering",
    )

    date = models.DateTimeField(auto_now=True, editable=False)

    clustering_data = models.JSONField(null=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Manual clustering"

    def get_absolute_url(self) -> str:
        return reverse(
            "dticlustering:saved",
            kwargs={"pk": self.pk, "from_pk": self.from_pk},  # self.from_dti_id}
        )

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

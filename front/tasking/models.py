import shutil
import uuid
import requests
from requests.exceptions import RequestException
import traceback
from typing import Dict, Any
from pathlib import Path

from django.db import models
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, mail_admins
from django.utils.functional import cached_property
from django.utils import timezone
from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.conf import settings

from datasets.models import Dataset

"""
MODELS: AbstractAPITask
        → AbstractAPITaskOnDataset (w/ Dataset PK)
        → AbstractAPITaskOnCrops
        → Similarity
FORMS:  AbstractTaskForm + DatasetForm
        → AbstractTaskOnDatasetForm (combines both)
        → AbstractTaskOnCropsForm
        → SimilarityForm
"""

User = get_user_model()

API_URL = getattr(settings, "API_URL", "http://localhost:5000")
BASE_URL = getattr(settings, "BASE_URL", "http://localhost:8000")


def AbstractTask(task_prefix: str):
    class AbstractTask(models.Model):
        """
        Abstract model for tasks that are sent to the API
        """

        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        name = models.CharField(
            max_length=64,
            blank=True,
            verbose_name="Experiment name",
            help_text=f"Optional name to identify this {task_prefix} experiment",
        )

        notify_email = models.BooleanField(
            default=True,
            verbose_name="Notify by email",
            blank=True,
            help_text=f"Send an email when the {task_prefix} task is finished",
        )

        status = models.CharField(max_length=20, default="PENDING", editable=False)
        is_finished = models.BooleanField(default=False, editable=False)
        requested_on = models.DateTimeField(auto_now_add=True, editable=False)
        requested_by = models.ForeignKey(
            User, null=True, on_delete=models.SET_NULL, editable=False
        )

        django_app_name = task_prefix

        parameters = models.JSONField(null=True)

        pipeline = models.ForeignKey(
            "pipelines.Pipeline",
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name=f"{task_prefix}_tasks",
        )

        class Meta:
            abstract = True
            ordering = ["-requested_on"]
            permissions = [
                (f"monitor_{task_prefix}", f"Can monitor {task_prefix} task"),
            ]

        def __str__(self):
            if self.name:
                return f"{self.name}"
            return f"{self.__class__.__name__} task"

        # Util URLs and Paths
        def get_absolute_url(self):
            return reverse(f"{self.django_app_name}:status", kwargs={"pk": self.pk})

        @property
        def task_media_path(self) -> str:
            """
            Full path to the result folder
            """
            return f"{self.django_app_name}/{self.id}"

        @property
        def result_media_path(self) -> str:
            """
            Path to the result folder, relative to MEDIA_ROOT
            """
            return f"{self.task_media_path}/result"

        @property
        def task_full_path(self) -> Path:
            """
            Full path to the result folder
            """
            return Path(settings.MEDIA_ROOT) / self.task_media_path

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

        @cached_property
        def full_log(self):
            """
            Returns the full log file content
            TODO keep log content before final error
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

        def get_notify_url(self):
            """
            Returns the URL to notify the front-end
            """
            return f"{BASE_URL}{reverse(f'{self.django_app_name}:notify', kwargs={'pk': self.pk})}?token={self.get_token()}"

        def get_task_kwargs(self):
            return {"parameters": self.parameters}

        def get_task_files(self):
            return None

        def start_task(self, endpoint: str = "start"):
            """
            Start the task
            """
            raise NotImplementedError()

        def cancel_task(self, endpoint: str = "cancel"):
            """
            Cancel the task
            """
            raise NotImplementedError()

        def on_task_success(self, data):
            """
            Handle the end of the task
            """
            self.terminate_task("SUCCESS")

        def on_task_error(self, data):
            """
            Handle the end of the task
            """
            self.terminate_task("ERROR", data.get("error", "Unknown error"))

        def terminate_task(self, status="SUCCESS", error=None, notify=True):
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
                        f"[discover-demo] Task {self.status}",
                        f"Your task {self} on discover-demo has finished with status {self.status}.\n\nYou can access the results at: {BASE_URL}{self.get_absolute_url()}",
                        settings.DEFAULT_FROM_EMAIL,
                        [self.requested_by.email],
                        fail_silently=False,
                    )
                except:
                    self.write_log(f"Error sending email: {traceback.format_exc()}")

            if self.pipeline:
                self.pipeline.on_task_finished(self)

        def receive_notification(self, data: dict):
            """
            Called by the API when tasks events happen (@notifying)
            """
            event = data["event"]
            if event == "STARTED":
                self.status = "PROGRESS"
                self.save()
                return
            elif event == "SUCCESS":
                self.on_task_success(data)
            elif event == "ERROR":
                self.on_task_error(data)

        def get_progress(self):
            """
            Queries the API to get the task progress
            """
            raise NotImplementedError()

        @classmethod
        def get_frontend_monitoring(cls):
            """
            Returns a dict with the monitoring data
            """
            total_size = 0
            for f in Path(settings.MEDIA_ROOT).glob("**/*"):
                if f.is_file():
                    total_size += f.stat().st_size
            n_datasets = (
                Dataset.objects.count()
            )  # TODO filter to keep only Datasets used by tasks
            n_experiments = cls.objects.count()

            return {
                "total_size": total_size,
                "n_datasets": n_datasets,
                "n_experiments": n_experiments,
            }

        @classmethod
        def clear_old_tasks(cls, days_before: int = 30) -> Dict[str, int]:
            """
            Clears all tasks older than days_before days
            """
            # TODO Needs to be adapted to the new Dataset model
            # remove all tasks and datasets except those younger than days_before days
            from_date = timezone.now() - timezone.timedelta(days=days_before)

            cleared_data = {
                "cleared_experiments": 0,
                "cleared_datasets": 0,
            }

            try:
                old_exp = cls.objects.filter(requested_on__lte=from_date)

                for exp in old_exp:
                    shutil.rmtree(exp.result_full_path, ignore_errors=True)
                    cleared_data["cleared_experiments"] += 1

                # TODO change that to fit to new Dataset / delete even crops of the dataset
                # old_datasets = Dataset.objects.exclude(
                #     dticlustering__requested_on__gt=from_date
                # )
                old_datasets = []
                for d in old_datasets:
                    try:
                        d.delete()
                        cleared_data["cleared_datasets"] += 1
                    except Exception as e:
                        cleared_data["error"] = f"Error when clearing old datasets: {e}"

                # remove records
                old_exp.delete()
            except Exception as e:
                cleared_data["error"] = f"Error when clearing old tasks: {e}"

            return cleared_data

        def clear_task(self) -> Dict[str, int]:
            """
            Clears the files of a given task
            """
            try:
                shutil.rmtree(self.task_full_path, ignore_errors=True)
                # TODO do not work with Vectorisation
                cleared = 1
            except Exception:
                cleared = 0

            return {
                "cleared_files": cleared,
            }

        @classmethod
        def get_available_models(cls):
            try:
                response = requests.get(f"{cls.api_endpoint_prefix}/models")
                response.raise_for_status()
                models = response.json()
            except Exception as e:
                return [("", f"Unable to fetch available models: {e}")]
            if not models:
                return [("", "No available models")]

            # models = { "ref": { "name": "Display Name", "model": "filename", "desc": "Description" }, ... }
            return [
                (info["model"], f"{info['name']} ({info['desc']})")
                for info in models.values()
            ]

    @receiver(pre_delete, sender=AbstractTask)
    def pre_delete_task(sender, instance: AbstractTask, **kwargs):
        # Clear files on the API server
        instance.clear_task()
        return

    return AbstractTask


def AbstractTaskOnDataset(task_prefix: str):
    class AbstractTaskOnDataset(AbstractTask(task_prefix)):
        """
        Abstract model for tasks on dataset of images that are sent to the API
        """

        dataset = models.ForeignKey(
            Dataset,
            verbose_name="Use existing dataset...",
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name=f"{task_prefix}_tasks",
        )
        # parameters = models.JSONField(null=True)

        class Meta:
            abstract = True
            ordering = ["-requested_on"]

        def get_dataset_id(self):
            return self.dataset.id
            # return self.zip_dataset.id

        def get_task_kwargs(self):
            kwargs = super().get_task_kwargs()
            kwargs.update(
                {
                    "documents": self.dataset.documents_for_api(),
                    # "parameters": self.parameters,
                }
            )
            return kwargs

    return AbstractTaskOnDataset


def AbstractAPITaskOnDataset(task_prefix: str):
    class AbstractAPITaskOnDataset(AbstractTaskOnDataset(task_prefix)):
        """
        Abstract model for tasks that are sent to the API
        """

        api_tracking_id = models.UUIDField(null=True, editable=False)
        api_endpoint_prefix = f"{API_URL}/{task_prefix}"

        class Meta:
            abstract = True
            ordering = ["-requested_on"]

        def start_task(self, endpoint: str = "start"):
            """
            Start the task
            """
            data = {
                "experiment_id": str(self.id),
                "notify_url": self.get_notify_url(),
                **self.get_task_kwargs(),
            }
            try:
                api_query = requests.post(
                    f"{self.api_endpoint_prefix}/{endpoint}",
                    json=data,
                    files=self.get_task_files(),
                )
            except (ConnectionError, RequestException):
                self.write_log("Connection error when starting task")
                self.status = "ERROR"
                self.is_finished = True
                self.save()
                # Send error email to website admins
                mail_admins(
                    f"[discover-demo] Offline API",
                    f"Error starting task {self}. The API server is offline.",
                    fail_silently=True,
                )
                return

            print(
                f"Request for task returned {api_query.status_code}: {api_query.text}"
            )

            try:
                api_result = api_query.json()
                self.api_tracking_id = api_result["tracking_id"]
            except Exception as e:
                exc = f"\n[{e.__class__.__name__}] {e}\nStack Trace:\n{traceback.format_exc()}\n"
                self.write_log(
                    f"Request for task failed with {api_query.status_code}: {api_query.text}\n{exc}"
                )
                self.status = "ERROR"
                self.is_finished = True

            self.save()

        def cancel_task(self, endpoint: str = "cancel"):
            """
            Cancel the task
            """
            try:
                api_query = requests.post(
                    f"{self.api_endpoint_prefix}/{self.api_tracking_id}/{endpoint}",
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
                self.write_log(f"Error cancelling task: {api_query.text}")
                self.status = "ERROR"
                self.is_finished = True
            self.save()

        def get_progress(self):
            """
            Queries the API to get the task progress
            """
            try:
                api_res = requests.get(
                    f"{self.api_endpoint_prefix}/{self.api_tracking_id}/status",
                )
            except (ConnectionError, RequestException):
                return {
                    "status": "UNKNOWN",
                    "error": "Connection error when getting task progress from the worker",
                }

            try:
                return {"status": self.status, **api_res.json()}
            except:
                self.write_log(f"Error when reading task progress: {api_res.text}")
                return {
                    "status": "UNKNOWN",
                }

        @classmethod
        def get_api_monitoring(cls):
            """
            Returns a dict with the monitoring data
            """
            try:
                api_query = requests.get(
                    f"{cls.api_endpoint_prefix}/monitor",
                )
            except (ConnectionError, RequestException):
                return {
                    "error": "Connection error when getting monitoring data from the worker"
                }

            try:
                return api_query.json()
            except:
                return {"error": "Error when reading monitoring data"}

        @classmethod
        def clear_api_old_tasks(cls, days_before: int = 30) -> Dict[str, Any]:
            """
            Clears all tasks older than days_before days from the API server
            """
            try:
                api_query = requests.post(
                    f"{cls.api_endpoint_prefix}/monitor/clear",
                    data={
                        "days_before": days_before,
                    },
                )
            except (ConnectionError, RequestException):
                return {
                    "error": "Connection error when clearing old tasks from the worker"
                }

            try:
                return api_query.json()
            except:
                return {
                    "error": "Error when retrieving output from API server",
                    "output": api_query.text,
                }

        @classmethod
        def clear_api_task(cls, tracking_id: str) -> Dict[str, Any]:
            """
            Clears the files generated during this task on the API server
            """
            try:
                api_query = requests.post(
                    f"{cls.api_endpoint_prefix}/monitor/clear/{tracking_id}",
                )
            except (ConnectionError, RequestException):
                return {"error": "Connection error when clearing task from the worker"}

            try:
                return api_query.json()
            except Exception as e:
                return {
                    "error": f"Error when clearing task from the worker: {e}",
                    "output": api_query.text,
                }

    @receiver(pre_delete, sender=AbstractAPITaskOnDataset)
    def pre_delete_task(sender, instance: AbstractAPITaskOnDataset, **kwargs):
        # Clear files on the API server
        sender.clear_api_task(instance.api_tracking_id)
        instance.clear_task()
        return

    return AbstractAPITaskOnDataset

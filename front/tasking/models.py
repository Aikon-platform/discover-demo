from django.db import models
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, mail_admins
from django.utils.functional import cached_property
import uuid
import requests
from requests.exceptions import RequestException
import traceback
from typing import Dict, Any
from pathlib import Path

from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver

from django.urls import reverse
from django.conf import settings

User = get_user_model()

API_URL = getattr(settings, "API_URL", "http://localhost:5000")
BASE_URL = getattr(settings, "BASE_URL", "http://localhost:8000")


def AbstractAPITask(task_prefix: str):
    class AbstractAPITask(models.Model):
        """
        Abstract model for tasks that are sent to the API
        """

        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        name = models.CharField(
            max_length=64,
            # default=task_prefix,
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

        api_tracking_id = models.UUIDField(null=True, editable=False)

        api_endpoint_prefix = task_prefix
        django_app_name = task_prefix

        class Meta:
            abstract = True
            ordering = ["-requested_on"]

        # Util URLs and Paths
        @property
        def result_media_path(self) -> str:
            """
            Path to the result folder, relative to MEDIA_ROOT
            """
            return f"{self.api_endpoint_prefix}/{self.id}/result"

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
            return {}

        def get_task_files(self):
            return None

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
                    f"{API_URL}/{self.api_endpoint_prefix}/{endpoint}",
                    data=data,
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
                    f"{API_URL}/{self.api_endpoint_prefix}/{self.api_tracking_id}/{endpoint}",
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
                self.on_task_success(data)
            elif event == "ERROR":
                self.on_task_error(data)

        def get_progress(self):
            """
            Queries the API to get the task progress
            """
            try:
                api_query = requests.get(
                    f"{API_URL}/{self.api_endpoint_prefix}/{self.api_tracking_id}/status",
                )
            except (ConnectionError, RequestException):
                return {
                    "status": "UNKNOWN",
                    "error": "Connection error when getting task progress from the worker",
                }

            try:
                return {"status": self.status, **api_query.json()}
            except:
                self.write_log(
                    f"Error when reading clustering progress: {api_query.text}"
                )
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
                    f"{API_URL}/{cls.api_endpoint_prefix}/monitor",
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
        def get_frontend_monitoring(cls):
            """
            Returns a dict with the monitoring data
            """
            raise NotImplementedError()

        @classmethod
        def clear_old_tasks(cls, days_before: int = 30) -> Dict[str, int]:
            """
            Clears all tasks older than days_before days
            """
            raise NotImplementedError()

        @classmethod
        def clear_api_old_tasks(cls, days_before: int = 30) -> Dict[str, Any]:
            """
            Clears all tasks older than days_before days from the API server
            """
            try:
                api_query = requests.post(
                    f"{API_URL}/{cls.api_endpoint_prefix}/monitor/clear",
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
                    "error": "Error when output from API server",
                    "output": api_query.text,
                }

        @classmethod
        def clear_task(cls, task_id: str) -> Dict[str, int]:
            """
            Clears the files of a given task
            """
            raise NotImplementedError()

        @classmethod
        def clear_api_task(cls, tracking_id: str) -> Dict[str, Any]:
            """
            Clears the files generated during this task on the API server
            """
            try:
                api_query = requests.post(
                    f"{API_URL}/{cls.api_endpoint_prefix}/monitor/clear/{tracking_id}",
                )
            except (ConnectionError, RequestException):
                return {"error": "Connection error when clearing task from the worker"}

            try:
                return api_query.json()
            except:
                return {
                    "error": "Error when clearing task from the worker",
                    "output": api_query.text,
                }

    @receiver(pre_delete, sender=AbstractAPITask)
    def pre_delete_task(sender, instance: AbstractAPITask, **kwargs):
        # Clear files on the API server
        sender.clear_api_task(instance.api_tracking_id)
        sender.clear_task(instance.id)
        return

    return AbstractAPITask

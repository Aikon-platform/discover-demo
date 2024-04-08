from flask import request, send_from_directory, Blueprint
from slugify import slugify
import uuid
from dramatiq_abort import abort
from dramatiq.results import ResultMissing, ResultFailure
import json
import shutil
from datetime import datetime

from .. import config

from ..main import app
from .tasks import train_dti
from ..shared.utils.fileutils import xaccel_send_from_directory, clear_dir
from ..shared import routes as shared_routes
from .const import (
    DTI_RESULTS_PATH,
    DATASETS_PATH,
    RUNS_PATH,
    DTI_DATA_FOLDER,
    DTI_XACCEL_PREFIX,
)

blueprint = Blueprint("clustering", __name__, url_prefix="/clustering")


@blueprint.route("start", methods=["POST"])
def start_clustering():
    """
    Start a new DTI clustering task

    Accepts the following POST parameters:
    - dataset_url [required]: the URL of the zipped dataset to be used
    - experiment_id [optional]: a unique identifier for this clustering task
    - dataset_id [optional]: a unique identifier for the dataset to be used
    - notify_url [optional]: the URL to be called when the task is finished
    - parameters [optional]: a JSON object containing the parameters to be used

    The callback_url will be called with a JSON object containing the following keys:
    - tracking_id: the task ID
    - result_url: the URL from which to fetch the results
    """

    # Extract experiment_id, dataset_id, dataset_url from POST parameters
    dataset_url = request.form["dataset_url"]  # Throw 400 if not exists

    experiment_id = slugify(request.form.get("experiment_id", str(uuid.uuid4())))
    dataset_id = slugify(request.form.get("dataset_id", str(uuid.uuid4())))
    notify_url = request.form.get("notify_url", None)
    parameters = json.loads(request.form.get("parameters", "{}"))

    # task = train_dti.send(
    #     experiment_id=experiment_id,
    #     dataset_id=dataset_id,
    #     dataset_url=dataset_url,
    #     parameters=parameters,
    #     notify_url=notify_url,
    # )
    #
    # return {
    #     "tracking_id": task.message_id,
    #     "experiment_id": experiment_id,
    #     "dataset_id": dataset_id,
    # }
    return shared_routes.start_task(
        train_dti,
        experiment_id,
        {
            "dataset_id": dataset_id,
            "dataset_url": dataset_url,
            "parameters": parameters,
            "notify_url": notify_url,
        },
    )


@blueprint.route("<tracking_id>/cancel", methods=["POST"])
def cancel_clustering(tracking_id: str):
    # """
    # Cancel a DTI clustering task
    # """
    # abort(tracking_id)
    #
    # return {"tracking_id": tracking_id}
    return shared_routes.cancel_task(tracking_id)


@blueprint.route("<tracking_id>/status", methods=["GET"])
def status_clustering(tracking_id: str):
    # """
    # Get the status of a DTI clustering task
    # """
    # try:
    #     log = train_dti.message().copy(message_id=tracking_id).get_result()
    # except ResultMissing:
    #     log = None
    # except ResultFailure as e:
    #     log = {
    #         "status": "ERROR",
    #         "infos": [f"Error: Actor raised {e.orig_exc_type} ({e.orig_exc_msg})"],
    #     }
    #
    # return {
    #     "tracking_id": tracking_id,
    #     "log": log,
    # }
    return shared_routes.status(tracking_id, train_dti)


@blueprint.route("<tracking_id>/result", methods=["GET"])
def result_clustering(tracking_id: str):
    # """
    # Get the result of a DTI clustering task
    # """
    # if not config.USE_NGINX_XACCEL:
    #     return send_from_directory(DTI_RESULTS_PATH, f"{slugify(tracking_id)}.zip")
    #
    # return xaccel_send_from_directory(
    #     DTI_RESULTS_PATH, DTI_XACCEL_PREFIX, f"{slugify(tracking_id)}.zip"
    # )
    return shared_routes.result(
        DTI_RESULTS_PATH, DTI_XACCEL_PREFIX, f"{slugify(tracking_id)}.zip"
    )


@blueprint.route("qsizes", methods=["GET"])
def qsizes_clustering():
    # """
    # List the queues of the broker and the number of tasks in each queue
    # """
    # try:
    #     return {
    #         "queues": {
    #             q: {"name": q, "size": train_dti.broker.do_qsize(q)}
    #             for q in train_dti.broker.get_declared_queues()
    #         }
    #     }
    # except AttributeError:
    #     return {"error": "Cannot get queue sizes from broker"}
    return shared_routes.qsizes(train_dti.broker)


@blueprint.route("monitor", methods=["GET"])
def monitor_clustering():
    # """
    # Get the status of the clustering service
    # """
    # # Get total size of the results directory
    # total_size = 0
    # for path in DTI_DATA_FOLDER.glob("**/*"):
    #     total_size += path.stat().st_size
    #
    # return {"total_size": total_size, **qsizes_clustering()}
    return shared_routes.monitor(DTI_DATA_FOLDER, train_dti.broker)


@blueprint.route("monitor/clear", methods=["POST"])
def clear_clustering():
    # """
    # Clear the results directory
    # """
    #
    # output = {
    #     "cleared_runs": 0,
    #     "cleared_results": 0,
    #     "cleared_datasets": 0,
    # }
    #
    # for path in RUNS_PATH.glob("*"):
    #     logfile = path / "trainer.log"
    #     # if logfile is older than 30 days, delete the run
    #     if (
    #         not logfile.exists()
    #         or (datetime.now() - datetime.fromtimestamp(logfile.stat().st_mtime)).days
    #         > 30
    #     ):
    #         shutil.rmtree(path)
    #         output["cleared_runs"] += 1
    #
    # for path in DATASETS_PATH.glob("*"):
    #     metafile = path / "ready.meta"
    #     # if metafile is older than 30 days, delete the dataset
    #     if (
    #         not metafile.exists()
    #         or (datetime.now() - datetime.fromtimestamp(metafile.stat().st_mtime)).days
    #         > 30
    #     ):
    #         shutil.rmtree(path)
    #         output["cleared_datasets"] += 1
    #
    # for path in DTI_RESULTS_PATH.glob("*.zip"):
    #     # if path is older than 30 days, delete the result
    #     if (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).days > 30:
    #         path.unlink()
    #         output["cleared_results"] += 1
    #
    # return output
    return {
        "cleared_runs": clear_dir(RUNS_PATH, file_to_check="trainer.log"),
        "cleared_datasets": clear_dir(DATASETS_PATH, file_to_check="ready.meta"),
        "cleared_results": clear_dir(DTI_RESULTS_PATH, path_to_clear="*.zip"),
    }

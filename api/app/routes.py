from flask import request, send_from_directory
from slugify import slugify
import uuid
from dramatiq_abort import abort
from dramatiq.results import ResultMissing, ResultFailure
import json

from . import config

from .main import app
from .tasks import train_dti
from .utils.fileutils import xaccel_send_from_directory

@app.route("/clustering/start", methods=["POST"])
def start_clustering():
    """
    Start a new DTI clustering task

    Accepts the following POST parameters:
    - dataset_url [required]: the URL of the zipped dataset to be used
    - clustering_id [optional]: a unique identifier for this clustering task
    - dataset_id [optional]: a unique identifier for the dataset to be used
    - notify_url [optional]: the URL to be called when the task is finished
    - parameters [optional]: a JSON object containing the parameters to be used

    The callback_url will be called with a JSON object containing the following keys:
    - tracking_id: the task ID
    - result_url: the URL from which to fetch the results
    """

    # Extract clustering_id, dataset_id, dataset_url from POST parameters
    dataset_url = request.form["dataset_url"] # Throw 400 if not exists

    clustering_id = slugify(request.form.get("clustering_id", str(uuid.uuid4())))
    dataset_id = slugify(request.form.get("dataset_id", str(uuid.uuid4())))
    notify_url = request.form.get("notify_url", None)
    parameters = json.loads(request.form.get("parameters", "{}"))

    task = train_dti.send(
        clustering_id=clustering_id, 
        dataset_id=dataset_id, 
        dataset_url=dataset_url, 
        parameters=parameters, 
        notify_url=notify_url
    )

    return {
        "tracking_id": task.message_id,
        "clustering_id": clustering_id,
        "dataset_id": dataset_id
    }

@app.route("/clustering/<tracking_id>/cancel", methods=["POST"])
def cancel_clustering(tracking_id:str):
    """
    Cancel a DTI clustering task
    """
    abort(tracking_id)

    return {
        "tracking_id": tracking_id
    }

@app.route("/clustering/<tracking_id>/status", methods=["GET"])
def status(tracking_id:str):
    """
    Get the status of a DTI clustering task
    """
    try:
        log = train_dti.message().copy(message_id=tracking_id).get_result()
    except ResultMissing:
        log = None
    except ResultFailure as e:
        log = {"status": "ERROR", "infos": [f"Error: Actor raised {e.orig_exc_type} ({e.orig_exc_msg})"]}


    return {
        "tracking_id": tracking_id,
        "log": log,
    }

@app.route("/clustering/<tracking_id>/result", methods=["GET"])
def result(tracking_id:str):
    """
    Get the result of a DTI clustering task
    """
    if not config.USE_NGINX_XACCEL:
        return send_from_directory(config.DTI_RESULTS_PATH, f"{slugify(tracking_id)}.zip")
    
    return xaccel_send_from_directory(config.DTI_RESULTS_PATH, config.DTI_XACCEL_PREFIX, f"{slugify(tracking_id)}.zip")
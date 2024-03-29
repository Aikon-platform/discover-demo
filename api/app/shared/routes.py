from flask import request, send_from_directory
from slugify import slugify
import uuid
from dramatiq_abort import abort
from dramatiq.results import ResultMissing, ResultFailure
import json
import shutil

from .. import config

from .utils.fileutils import xaccel_send_from_directory, is_too_old


def start_task(request, task_fct):
    """
    Start a new task
    """
    dataset_url = request.form["dataset_url"]  # Throw 400 if not exists
    experiment_id = slugify(request.form.get("experiment_id", str(uuid.uuid4())))
    dataset_id = slugify(request.form.get("dataset_id", str(uuid.uuid4())))
    notify_url = request.form.get("notify_url", None)
    parameters = json.loads(request.form.get("parameters", "{}"))

    task = task_fct.send(
        clustering_id=experiment_id,
        dataset_id=dataset_id,
        dataset_url=dataset_url,
        parameters=parameters,
        notify_url=notify_url,
    )

    return {
        "tracking_id": task.message_id,
        "experiment_id": experiment_id,
        "dataset_id": dataset_id,
    }


def cancel_task(tracking_id: str):
    """
    Cancel a task
    """
    abort(tracking_id)

    return {"tracking_id": tracking_id}


def status(tracking_id: str, task_fct):
    """
    Get the status of a task
    """
    try:
        log = task_fct.message().copy(message_id=tracking_id).get_result()
    except ResultMissing:
        log = None
    except ResultFailure as e:
        log = {
            "status": "ERROR",
            "infos": [f"Error: Actor raised {e.orig_exc_type} ({e.orig_exc_msg})"],
        }

    return {
        "tracking_id": tracking_id,
        "log": log,
    }


def result(tracking_id: str, results_dir, xaccel_prefix):
    """
    Get the result of a task
    """
    if not config.USE_NGINX_XACCEL:
        return send_from_directory(results_dir, f"{slugify(tracking_id)}.zip")

    return xaccel_send_from_directory(
        results_dir, xaccel_prefix, f"{slugify(tracking_id)}.zip"
    )


def qsizes(broker):
    """
    List the queues of the broker and the number of tasks in each queue
    """
    try:
        return {
            "queues": {
                q: {"name": q, "size": broker.do_qsize(q)}
                for q in broker.get_declared_queues()
            }
        }
    except AttributeError:
        return {"error": "Cannot get queue sizes from broker"}


def monitor(results_dir):
    # Get total size of the results directory
    total_size = 0
    for path in results_dir.glob("**/*"):
        total_size += path.stat().st_size

    return {"total_size": total_size, **qsizes()}


def clear(run_dir=None, data_dir=None, results_dir=None):
    """
    Clear the results directory
    """
    output = {
        "cleared_runs": 0,
        "cleared_results": 0,
        "cleared_datasets": 0,
    }

    if run_dir is not None:
        for path in run_dir.glob("*"):
            # TODO factorize this for all directories
            if is_too_old(path / "trainer.log"):
                shutil.rmtree(path)
                output["cleared_runs"] += 1

    if data_dir is not None:
        for path in data_dir.glob("*"):
            if is_too_old(path / "ready.meta"):
                shutil.rmtree(path)
                output["cleared_datasets"] += 1

    if results_dir is not None:
        for path in results_dir.glob("*.zip"):
            if is_too_old(path):
                path.unlink()
                output["cleared_results"] += 1

    return output

import os
import time

from flask import request, jsonify, Blueprint
from slugify import slugify
import uuid

from ..main import app
from .tasks import extract_objects, extract_all
from ..shared import routes as shared_routes
from .const import EXT_RESULTS_PATH, MAN_PATH, MODEL_PATH, IMG_PATH
from ..shared.utils.fileutils import delete_path, sanitize_str

blueprint = Blueprint("extraction", __name__, url_prefix="/extraction")


@blueprint.route("start", methods=["POST"])
@shared_routes.get_client_id
@shared_routes.error_wrapper
def start_extraction(client_id):
    experiment_id = slugify(request.form.get("experiment_id", str(uuid.uuid4())))
    manifest_url = request.form['manifest_url']
    model = request.form.get('model')
    notify_url = request.form.get('callback')

    task = extract_objects.send(
        experiment_id=experiment_id,
        manifest_url=manifest_url,
        model=model,
        notify_url=notify_url,
    )

    return {
        "message": f"Extraction task triggered for {manifest_url}!",
        "tracking_id": task.message_id,
        "experiment_id": experiment_id,
    }


@blueprint.route("start_all", methods=["POST"])
@shared_routes.get_client_id
@shared_routes.error_wrapper
def start_extract_all(client_id):
    experiment_id = slugify(request.form.get("experiment_id", str(uuid.uuid4())))
    url_file = request.files['url_file']
    model = request.form.get('model')
    notify_url = request.form.get('callback')

    url_file.save(f'{MAN_PATH}/{url_file.filename}')

    with open(f'{MAN_PATH}/{url_file.filename}', mode='r') as f:
        url_list = f.read().splitlines()
    url_list = list(filter(None, url_list))

    task = extract_all.send(
        experiment_id=experiment_id,
        manifest_list=url_list,
        model=model,
        notify_url=notify_url,
    )

    return {
        "message": f"Extraction task triggered for {url_file.filename}!",
        "tracking_id": task.message_id,
        "experiment_id": experiment_id,
    }


@blueprint.route("<tracking_id>/cancel", methods=["POST"])
def cancel_extraction(tracking_id: str):
    return shared_routes.cancel_task(tracking_id)


@blueprint.route("<tracking_id>/status", methods=["GET"])
def status_extraction(tracking_id: str):
    return shared_routes.status(tracking_id, extract_objects)


@blueprint.route("qsizes", methods=["GET"])
def qsizes_extraction():
    """
    List the queues of the broker and the number of tasks in each queue
    """
    return shared_routes.qsizes(extract_objects.broker)


@blueprint.route("monitor", methods=["GET"])
def monitor_extraction():
    return shared_routes.monitor(EXT_RESULTS_PATH, extract_objects.broker)


@blueprint.route("models", methods=['GET'])
def get_models():
    models_info = {}

    try:
        for filename in os.listdir(MODEL_PATH):
            if filename.endswith(".pt"):
                full_path = os.path.join(MODEL_PATH, filename)
                modification_date = os.path.getmtime(full_path)
                models_info[filename] = time.ctime(modification_date)

        return jsonify(models_info)

    except Exception:
        return jsonify("No models.")


@blueprint.route("clear", methods=["POST"])
def clear_images():
    manifest_url = request.form['manifest_url']
    dir_path = os.path.join(IMG_PATH, sanitize_str(manifest_url).replace("manifest", "").replace("json", ""))

    return {
        "cleared_img_dir": 1 if delete_path(IMG_PATH / dir_path) else 0,
    }

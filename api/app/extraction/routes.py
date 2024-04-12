import os
import time

from flask import request, jsonify
from slugify import slugify
import uuid

from ..main import app
from ..shared import routes
from .tasks import extract_objects, extract_all
from ..shared.routes import get_client_id
from .const import EXT_RESULTS_PATH, MAN_PATH, MODEL_PATH


@app.route("/run_extraction", methods=["POST"])
@get_client_id
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


@app.route("/extract_all", methods=["POST"])
@get_client_id
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


@app.route("/extraction/<tracking_id>/cancel", methods=["POST"])
def cancel_extraction(tracking_id: str):
    return routes.cancel_task(tracking_id)


@app.route("/extraction/<tracking_id>/status", methods=["GET"])
def status_extraction(tracking_id: str):
    return routes.status(tracking_id, extract_objects)


@app.route("/extraction/qsizes", methods=["GET"])
def qsizes_extraction():
    """
    List the queues of the broker and the number of tasks in each queue
    """
    return routes.qsizes(extract_objects.broker)


@app.route("/extraction/monitor", methods=["GET"])
def monitor_extraction():
    return routes.monitor(EXT_RESULTS_PATH, extract_objects.broker)


@app.route('/extraction/models', methods=['GET'])
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
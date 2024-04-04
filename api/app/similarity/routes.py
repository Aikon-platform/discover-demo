from .const import FEAT_NET
from ..shared.routes import get_client_id

from flask import request, send_from_directory
from slugify import slugify
import uuid

from ..main import app
from .tasks import compute_similarity
from ..shared import routes
from ..shared.utils.fileutils import delete_path
from .const import (
    IMG_PATH,
    FEATS_PATH,
    SIM_RESULTS_PATH,
    SIM_XACCEL_PREFIX,
)


@app.route("/run_similarity", methods=["POST"])
@get_client_id
def start_similarity(client_id):
    """
    documents = {
        "wit3_man186_anno181": "https://eida.obspm.fr/eida/wit3_man186_anno181/list/",
        "wit87_img87_anno87": "https://eida.obspm.fr/eida/wit87_img87_anno87/list/",
        "wit2_img2_anno2": "https://eida.obspm.fr/eida/wit2_img2_anno2/list/"
    }
    Compute similarity for images from a list of URLs.
    Each URL corresponds to a document and contains a list of images to download:
    {
        "img_name": "https://domain-name.com/image_name.jpg",
        "img_name": "https://other-domain.com/image_name.jpg",
        "img_name": "https://iiif-server.com/.../coordinates/size/rotation/default.jpg",
        "img_name": "..."
    }
    Each document is compared to itself and other documents resulting in a list a comparison pairs
    """

    if not request.is_json:
        return "Similarity task aborted!"

    experiment_id = slugify(request.form.get("experiment_id", str(uuid.uuid4())))
    # dict of document ids with a URL containing a list of images
    dataset = request.get_json().get("documents", {})
    parameters = {
        # which feature extraction backbone to use
        "model": request.get_json().get("model", FEAT_NET),
        "client_id": client_id,
    }
    # which url to send back the similarity results and updates on the task
    notify_url = request.get_json().get("callback", None)

    task = compute_similarity.send(
        experiment_id=experiment_id,
        dataset=dataset,
        parameters=parameters,
        notify_url=notify_url,
    )

    return {
        "message": f"Similarity task triggered for {list(dataset.keys())}!",
        "tracking_id": task.message_id,
        "experiment_id": experiment_id,
    }


@app.route("/similarity/<tracking_id>/cancel", methods=["POST"])
def cancel_similarity(tracking_id: str):
    return routes.cancel_task(tracking_id)


@app.route("/similarity/<tracking_id>/status", methods=["GET"])
def status_similarity(tracking_id: str):
    return routes.status(tracking_id, compute_similarity)


@app.route("/similarity/<doc_pair>/result", methods=["GET"])
def result_similarity(doc_pair: str):
    """
    Sends the similarity results file for a given document pair
    """
    return routes.result(
        SIM_RESULTS_PATH, SIM_XACCEL_PREFIX, f"{slugify(doc_pair)}.npy"
    )


@app.route("/similarity/qsizes", methods=["GET"])
def qsizes_similarity():
    """
    List the queues of the broker and the number of tasks in each queue
    """
    return routes.qsizes(compute_similarity.broker)


@app.route("/similarity/monitor", methods=["GET"])
def monitor_similarity():
    return routes.monitor(SIM_RESULTS_PATH, compute_similarity.broker)


@app.route("/similarity/monitor/clear/<doc_id>/", methods=["POST"])
def clear_doc(doc_id: str):
    """
    Clear all images, features and scores related to a given document
    doc_id = "{app_name}_{doc_id}"
    """

    output = {
        "cleared_img_dir": 1 if delete_path(IMG_PATH / doc_id) else 0,
        "cleared features": 1 if delete_path(FEATS_PATH / f"{doc_id}.pt") else 0,
        "cleared_results": 0,  # TODO clear all pair score files for a given doc_id
    }
    return output

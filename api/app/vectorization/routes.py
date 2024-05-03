from flask import request, send_from_directory, Blueprint
from slugify import slugify
import uuid

from ..main import app
from .tasks import compute_vectorization
from ..shared import routes as shared_routes
from ..shared.utils.fileutils import delete_path, clear_dir
from .const import (
    IMG_PATH

)

from ..shared.utils.logging import console

blueprint = Blueprint("vectorization", __name__, url_prefix="/vectorization")


@blueprint.route("start", methods=["POST"])
@shared_routes.get_client_id
@shared_routes.error_wrapper
def start_similarity(client_id):
    """
    {"images":
    {
        "img_name": "https://domain-name.com/image_name.jpg",
        "img_name": "https://other-domain.com/image_name.jpg",
        "img_name": "https://iiif-server.com/.../coordinates/size/rotation/default.jpg",
        "img_name": "..."
    }
    }
    A list of images to download
    """

    if not request.is_json:
        return "No JSON in request: Vectorization task aborted!"

    data = request.get_json()
    console(data, color="cyan")

    experiment_id = slugify(request.form.get("experiment_id", str(uuid.uuid4())))
    # dict of document ids with a URL containing a list of images
    dataset = data.get("images", {})
    # which url to send back the similarity results and updates on the task
    notify_url = data.get("callback", None)
    doc_id = data.get("doc_id", None)



    return shared_routes.start_task(
        compute_vectorization,
        experiment_id,
        {
            "dataset": dataset,
            "notify_url": notify_url,
            "doc_id": doc_id
        },
    )

'''
@blueprint.route("<tracking_id>/cancel", methods=["POST"])
def cancel_vectorization(tracking_id: str):
    return shared_routes.cancel_task(tracking_id)


@blueprint.route("<tracking_id>/status", methods=["GET"])
def status_vectorization(tracking_id: str):
    return shared_routes.status(tracking_id, compute_vectorization)


@blueprint.route("task/<doc_pair>/result", methods=["GET"])
def result_vectorization(doc_pair: str):
    """
    Sends the vecto results file for a given document pair
    """
    return shared_routes.result(
        SIM_RESULTS_PATH, SIM_XACCEL_PREFIX, f"{slugify(doc_pair)}.npy"
    )


@blueprint.route("qsizes", methods=["GET"])
def qsizes_vectorization():
    """
    List the queues of the broker and the number of tasks in each queue
    """
    return shared_routes.qsizes(compute_vectorization.broker)


@blueprint.route("monitor", methods=["GET"])
def monitor_similarity():
    return shared_routes.monitor(SIM_RESULTS_PATH, compute_similarity.broker)


@blueprint.route("monitor/clear/", methods=["POST"])
def clear_old_similarity():
    return {
        "cleared_img_dir": clear_dir(IMG_PATH),
        "cleared features": clear_dir(FEATS_PATH, path_to_clear="*.pt"),
        "cleared_results": clear_dir(SIM_RESULTS_PATH, path_to_clear="*.npy"),
    }


@blueprint.route("monitor/clear/<doc_id>/", methods=["POST"])
def clear_doc(doc_id: str):
    """
    Clear all images, features and scores related to a given document
    doc_id = "{app_name}_{doc_id}"
    TODO: re-united doc_id / tracking_id
    """

    return {
        "cleared_img_dir": clear_dir(
            IMG_PATH, path_to_clear=f"*_{doc_id}", condition=True
        ),
        "cleared features": clear_dir(
            FEATS_PATH, path_to_clear=f"*_{doc_id}.pt", condition=True
        ),
        "cleared_results": clear_dir(
            SIM_RESULTS_PATH, path_to_clear=f"*{doc_id}*.npy", condition=True
        ),
    }
    '''
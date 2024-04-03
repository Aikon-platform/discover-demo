from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    url_for,
    jsonify,
    Blueprint,
)
from slugify import slugify
from pathlib import Path
from PIL import Image, ImageOps
from torchvision import transforms
import torch
import traceback
from typing import List
from functools import wraps
import json
import uuid

from ..shared.utils.fileutils import xaccel_send_from_directory
from ..shared import routes as shared_routes
from ..main import app
from .. import config
from .const import WATERMARKS_SOURCES_FOLDER, WATERMARKS_XACCEL_PREFIX, WATERMARKS_DATA_FOLDER
from .tasks import pipeline
from .sources import WatermarkSource

MODELS = {}
DEVICE = "cpu"

blueprint = Blueprint("watermarks", __name__, url_prefix="/watermarks")

def error_wrapper(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e), "traceback": traceback.format_exc()})
    return wrapped


@blueprint.route("sources", methods=["GET"])
def sources():
    return jsonify(WatermarkSource.list_available())

@blueprint.route("sources/<source>/images.zip", methods=["GET"])
def images(source):
    source = WatermarkSource(source)

    if not source.data_folder.exists():
        r = jsonify({"error": f"Source {source.uid} not found"})
        r.status_code = 404
        return r
    
    f = (source.data_folder / "images.zip")
    if not f.exists():
        r = jsonify({"error": f"Source {source.uid} images not found"})
        r.status_code = 404
        return r
    
    f = f.relative_to(WATERMARKS_SOURCES_FOLDER)

    if not config.USE_NGINX_XACCEL:
        return send_from_directory(WATERMARKS_SOURCES_FOLDER, str(f))

    return xaccel_send_from_directory(
        WATERMARKS_SOURCES_FOLDER, WATERMARKS_XACCEL_PREFIX, str(f)
    )


@blueprint.route("detect", methods=["POST"])
@blueprint.route("sources/<source>/compare", methods=["POST"])
@error_wrapper
def start_task(source=None):

    detect = request.args.get("detect", "true").lower() == "true"
    experiment_id = slugify(request.form.get("experiment_id", str(uuid.uuid4())))
    notify_url = request.form.get("notify_url", None)

    if source is not None:
        source = WatermarkSource(source)

        if not source.data_folder.exists():
            r = jsonify({"error": f"Source {source.uid} not found"})
            r.status_code = 404
            return r

    im = Image.open(request.files["image"])
    sv_dir = WATERMARKS_DATA_FOLDER / "tmp_queries"
    sv_dir.mkdir(parents=True, exist_ok=True)
    im_file = sv_dir / f"{experiment_id}.jpg"
    im.save(im_file)

    return shared_routes.start_task(pipeline, experiment_id, {"image_path": str(im_file), "detect": detect, "compare_to": source, "notify_url": notify_url})


@blueprint.route("task/<tracking_id>", methods=["GET"])
def task_status(tracking_id):
    return shared_routes.status(tracking_id, pipeline)


@blueprint.route("task/<tracking_id>/cancel", methods=["POST"])
def task_cancel(tracking_id):
    return shared_routes.cancel_task(tracking_id)


@blueprint.route("task/<tracking_id>/result", methods=["GET"])
def task_result(tracking_id):
    out_file = WATERMARKS_DATA_FOLDER / "results" / f"{tracking_id}.json"
    if not out_file.exists():
        r = jsonify({"error": f"Result {tracking_id} not found"})
        r.status_code = 404
        return r
    
    with open(out_file, "r") as f:
        return jsonify(json.load(f))

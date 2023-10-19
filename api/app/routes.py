from flask import request
from slugify import slugify
import uuid

from .app import app
from .tasks import train_dti

@app.route("/start_clustering", methods=["POST"])
def start_clustering():
    """
    Start a new DTI clustering task
    """
    # Extract clustering_id, dataset_id, dataset_url from POST parameters
    clustering_id = slugify(request.form.get("clustering_id", str(uuid.uuid4())))
    dataset_id = slugify(request.form.get("dataset_id", str(uuid.uuid4())))

    dataset_url = request.form["dataset_url"] # Throw 400 if not exists

    task = train_dti.delay(clustering_id=clustering_id, dataset_id=dataset_id, dataset_url=dataset_url, parameters={})

    return {
        "tracking_id": task.id,
        "clustering_id": clustering_id,
        "dataset_id": dataset_id
    }


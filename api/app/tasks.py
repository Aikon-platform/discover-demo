import dramatiq
from dramatiq.middleware import CurrentMessage
from typing import Optional
import requests
from zipfile import ZipFile
from PIL import Image

from . import config
from .training import DATASETS_PATH, run_kmeans_training, run_sprites_training
from .utils.logging import notifying, TLogger, LoggerHelper

@dramatiq.actor(time_limit=1000*60*60, max_retries=0, store_results=True)
@notifying
def train_dti(
    clustering_id: str, 
    dataset_id: str, 
    dataset_url: str, 
    parameters: Optional[dict]=None, 
    logger: TLogger=LoggerHelper):
    """
    Train a DTI model

    Parameters:
    - clustering_id: the ID of the clustering task
    - dataset_id: the ID of the dataset
    - dataset_url: the URL of the zipped dataset to be downloaded
    - parameters: a JSON object containing the training parameters
    - logger: a logger object
    """

    current_task = CurrentMessage.get_current_message()
    current_task_id = current_task.message_id

    result_file = config.DTI_RESULTS_PATH / f"{current_task_id}.zip"
    result_file.parent.mkdir(parents=True, exist_ok=True)

    # Download and extract dataset to local storage
    dataset_path = DATASETS_PATH / "generic" / dataset_id
    dataset_ready_file = dataset_path / "ready.meta"

    if not dataset_ready_file.exists():
        dataset_path.mkdir(parents=True, exist_ok=True)
        dataset_zip_path = dataset_path / "dataset.zip"

        with requests.get(dataset_url, stream=True) as r:
            r.raise_for_status()
            with open(dataset_zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Unzip dataset
        with ZipFile(dataset_zip_path, "r") as zipObj:
            zipObj.extractall(dataset_path / "train")

        dataset_zip_path.unlink()

        # Create ready file
        dataset_ready_file.touch()
    else:
        print("Dataset already ready")
        dataset_ready_file.touch()

    # Start training
    use_sprites = parameters.get("use_sprites", False)
    if use_sprites:
        output_path = run_sprites_training(clustering_id, dataset_id, parameters, logger)
    else:
        output_path = run_kmeans_training(clustering_id, dataset_id, parameters, logger)

    # zip results to config.DTI_RESULTS_PATH
    with ZipFile(result_file, "w") as zipObj:
        for file in output_path.glob("**/*"):
            if file.suffix == ".pkl": # Don't include the model
                continue

            if file.suffix == ".png": # Convert to jpg if not transparent
                img = Image.open(file)
                if img.mode != "RGBA":
                    nfile = file.with_suffix(".jpg")
                    img.save(nfile)
                    file.unlink()

            zipObj.write(file, file.relative_to(output_path))

    return {"result_url": f"{config.BASE_URL}/clustering/{current_task_id}/result"}
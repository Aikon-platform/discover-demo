import dramatiq
from dramatiq.middleware import CurrentMessage
from typing import Optional
import requests
from zipfile import ZipFile
import traceback

from . import config
from .training import run_training, DATASETS_PATH

def result_key_for_tracking_id(tracking_id: str):
    return f"result:{tracking_id}"

@dramatiq.actor
def train_dti(
    clustering_id: str, 
    dataset_id: str, 
    dataset_url: str, 
    parameters: Optional[dict]=None, 
    callback_url: Optional[str]=None):

    try:
        current_task = CurrentMessage.get_current_message()
        logging_key = result_key_for_tracking_id(current_task.message_id)
        print(logging_key)

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

        # Start training
        run_training(clustering_id, dataset_id, parameters, logging_key)

        # Upload results
        if callback_url:
            print(requests.post(
                callback_url,
                data={
                    "tracking_id": clustering_id,
                    "success": True,
                    "result_url": f"{config.BASE_URL}/{clustering_id}/result"
                }
            ).text)
    except Exception as e:
        try:
            if callback_url:
                print(requests.post(
                    callback_url,
                    data={
                        "tracking_id": clustering_id,
                        "success": False,
                        "error": traceback.format_exc()
                    }
                ).text)
        except Exception as e:
            print(e)


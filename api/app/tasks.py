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
        current_task_id = current_task.message_id
        logging_key = result_key_for_tracking_id(current_task_id)
        result_file = config.DTI_RESULTS_PATH / f"{current_task_id}.zip"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        print(logging_key, result_file)

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

        # Start training
        output_path = run_training(clustering_id, dataset_id, parameters, logging_key)

        # zip results to config.DTI_RESULTS_PATH
        with ZipFile(result_file, "w") as zipObj:
            for file in output_path.glob("**/*"):
                zipObj.write(file, file.relative_to(output_path))

        # Upload results
        if callback_url:
            requests.post(
                callback_url,
                data={
                    "tracking_id": current_task_id,
                    "success": True,
                    "result_url": f"{config.BASE_URL}/clustering/{current_task_id}/result"
                }
            )
    except Exception as e:
        try:
            if callback_url:
                requests.post(
                    callback_url,
                    data={
                        "tracking_id": clustering_id,
                        "success": False,
                        "error": traceback.format_exc()
                    }
                )
            traceback.print_exc()
        except Exception as e:
            traceback.print_exc()


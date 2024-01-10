from ..training import DATASETS_PATH
import requests
from zipfile import ZipFile


def download_zip(zip_url, save_path):
    try:
        with requests.get(zip_url, stream=True) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as e:
        print(e)
        return False
    return True


def unzip(zip_path, extract_path):
    try:
        with ZipFile(zip_path, "r") as zipObj:
            zipObj.extractall(extract_path)
    except Exception as e:
        print(e)
        return False
    return True


def save_dataset(dataset_url, dataset_id):
    # Download and extract dataset to local storage
    dataset_path = DATASETS_PATH / "generic" / dataset_id
    dataset_ready_file = dataset_path / "ready.meta"

    if not dataset_ready_file.exists():
        dataset_path.mkdir(parents=True, exist_ok=True)
        dataset_zip_path = dataset_path / "dataset.zip"

        if download_zip(dataset_url, dataset_zip_path):
            if unzip(dataset_zip_path, dataset_path / "train"):
                dataset_zip_path.unlink()
                dataset_ready_file.touch()
                return True
        return False

    print("Dataset already ready")
    dataset_ready_file.touch()
    return True

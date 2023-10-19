from .app import celery
from yaml import load, Loader, dump, Dumper
import requests
from zipfile import ZipFile
from pathlib import Path

from . import config # overrides dti_source config

from .dti.src.kmeans_trainer import Trainer
from .dti.src.utils.path import RUNS_PATH, DATASETS_PATH, CONFIGS_PATH

def _run_training(clustering_id: str, dataset_id: str, parameters: dict):
    train_config = load(open(Path(__file__).parent / "dti_template.yml"), Loader=Loader)

    train_config["dataset"]["tag"] = dataset_id
    run_dir = RUNS_PATH / clustering_id

    # TODO update train_config with parameters

    config_file = CONFIGS_PATH / f"{clustering_id}.yml"
    dump(train_config, open(config_file, "w"), Dumper=Dumper)

    trainer = Trainer(config_file, run_dir, seed=train_config["training"]["seed"])
    trainer.run(seed=train_config["training"]["seed"])

@celery.task
def train_dti(clustering_id: str, dataset_id: str, dataset_url: str, parameters: dict):

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

        # Create ready file
        dataset_ready_file.touch()

    # Start training
    _run_training(clustering_id, dataset_id, parameters)

    # Upload results
    pass
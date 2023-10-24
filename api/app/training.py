
from yaml import load, Loader, dump, Dumper
from pathlib import Path

from . import config # overrides dti_source config

from .dti.src.kmeans_trainer import Trainer
from .dti.src.utils.path import RUNS_PATH, DATASETS_PATH, CONFIGS_PATH

from dramatiq import get_broker

class AdaptedTrainer(Trainer):
    def __init__(self, logging_key: str, *args, **kwargs):
        self.logging_key = logging_key
        self.log_history = []
        super().__init__(*args, **kwargs)

    def print_and_log_info(self, string):
        self.log_history.append(string)
        self.log_history = self.log_history[-10:]
        get_broker().client.set(self.logging_key, "\n".join(self.log_history), ex=60*60*24)

def run_training(clustering_id: str, dataset_id: str, parameters: dict, logging_key: str) -> Path:
    train_config = load(open(Path(__file__).parent / "dti_template.yml"), Loader=Loader)

    train_config["dataset"]["tag"] = dataset_id
    run_dir = RUNS_PATH / clustering_id

    # TODO update train_config with parameters

    config_file = CONFIGS_PATH / f"{clustering_id}.yml"
    CONFIGS_PATH.mkdir(parents=True, exist_ok=True)
    dump(train_config, open(config_file, "w"), Dumper=Dumper)

    trainer = AdaptedTrainer(logging_key, config_file, run_dir, seed=train_config["training"]["seed"])
    trainer.run(seed=train_config["training"]["seed"])

    return run_dir
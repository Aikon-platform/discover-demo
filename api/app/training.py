from typing import Any, Optional

from yaml import load, Loader, dump, Dumper
from pathlib import Path

from . import config # overrides dti_source config

from .dti.src.kmeans_trainer import Trainer as KMeansTrainer
from .dti.src.sprites_trainer import Trainer as SpritesTrainer
from .dti.src.utils.path import RUNS_PATH, DATASETS_PATH, CONFIGS_PATH

from .utils.logging import TLogger, LoggerHelper

class LoggingTrainerMixin:
    """
    A mixin with hooks to track training progress
    """
    def __init__(self, logger: TLogger, *args, **kwargs):
        self.jlogger = logger
        super().__init__(*args, **kwargs)

        class DataLoadWrapper:
            def __init__(self, loader):
                self.loader = loader

            def __iter__(self):
                return iter(logger.iterate(self.loader, title="Training step"))
            
            def __getattribute__(self, __name: str) -> Any:
                if __name == "loader":
                    return super().__getattribute__("loader")

                return getattr(self.loader, __name)

        self.train_loader = DataLoadWrapper(self.train_loader)

    def print_and_log_info(self, string):
        self.jlogger.info(string)
        self.logger.info(string)

    def run(self, *args, **kwargs):
        self.jlogger.progress(self.start_epoch-1, self.n_epoches, title="Training epoch")
        return super().run(*args, **kwargs)

    def update_scheduler(self, epoch, batch):
        self.jlogger.progress(epoch-1, self.n_epoches, title="Training epoch")
        return super().update_scheduler(epoch, batch)
    
    def save_training_metrics(self):
        self.jlogger.progress(self.n_epoches, self.n_epoches, title="Training epoch", end=True)
        self.jlogger.info("Training over, running evaluation")
        return super().save_training_metrics()

class LoggedKMeansTrainer(LoggingTrainerMixin, KMeansTrainer):
    pass

class LoggedSpritesTrainer(LoggingTrainerMixin, SpritesTrainer):
    pass

def run_kmeans_training(clustering_id: str, dataset_id: str, parameters: dict, logger: TLogger=LoggerHelper) -> Path:
    train_config = load(open(Path(__file__).parent / "dti-configs" / "kmeans-template.yml"), Loader=Loader)

    train_config["dataset"]["tag"] = dataset_id
    run_dir = RUNS_PATH / clustering_id

    if "n_prototypes" in parameters:
        train_config["model"]["n_prototypes"] = parameters["n_prototypes"]

    if "transformation_sequence" in parameters:
        train_config["model"]["transformation_sequence"] = parameters["transformation_sequence"]

    config_file = CONFIGS_PATH / f"{clustering_id}.yml"
    CONFIGS_PATH.mkdir(parents=True, exist_ok=True)
    dump(train_config, open(config_file, "w"), Dumper=Dumper)

    trainer = LoggedKMeansTrainer(logger, config_file, run_dir, seed=train_config["training"]["seed"])
    trainer.run(seed=train_config["training"]["seed"])

    return run_dir

def run_sprites_training(clustering_id: str, dataset_id: str, parameters: dict, logger: TLogger=LoggerHelper) -> Path:
    train_config = load(open(Path(__file__).parent / "dti-configs" / "sprites-template.yml"), Loader=Loader)

    train_config["dataset"]["tag"] = dataset_id
    run_dir = RUNS_PATH / clustering_id

    if "n_prototypes" in parameters:
        train_config["model"]["n_sprites"] = parameters["n_prototypes"]

    if "transformation_sequence" in parameters:
        train_config["model"]["transformation_sequence"] = parameters["transformation_sequence"]
        train_config["model"]["transformation_sequence_bkg"] = parameters["transformation_sequence"]

    config_file = CONFIGS_PATH / f"{clustering_id}.yml"
    CONFIGS_PATH.mkdir(parents=True, exist_ok=True)
    dump(train_config, open(config_file, "w"), Dumper=Dumper)

    trainer = LoggedSpritesTrainer(logger, config_file, run_dir, seed=train_config["training"]["seed"])
    trainer.run(seed=train_config["training"]["seed"])

    return run_dir
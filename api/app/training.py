from typing import Any, Optional

from yaml import load, Loader, dump, Dumper
from pathlib import Path
import os, torch
import numpy as np
import copy
from torch.utils.data import DataLoader
import pandas as pd

from . import config # overrides dti_source config

from .dti.src.kmeans_trainer import Trainer as KMeansTrainer
from .dti.src.sprites_trainer import Trainer as SpritesTrainer
from .dti.src.utils.path import RUNS_PATH, DATASETS_PATH, CONFIGS_PATH
from .dti.src.utils.image import convert_to_img

from .utils.logging import TLogger, LoggerHelper

class LoggingTrainerMixin:
    """
    A mixin with hooks to track training progress
    """
    def __init__(self, logger: TLogger, *args, **kwargs):
        self.jlogger = logger
        super().__init__(*args, **kwargs)

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

    @torch.no_grad()
    def qualitative_eval(self):
        """Routine to save qualitative results"""
        cluster_path = Path(self.run_dir / "clusters")
        cluster_path.mkdir(parents=True, exist_ok=True)
        dataset = self.train_loader.dataset
        train_loader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            num_workers=self.n_workers,
            shuffle=False,
        )
        cluster_by_path = []
        count_per_cluster = np.zeros(self.n_prototypes, dtype=np.int32)

        for k in range(self.n_prototypes):
            path = (cluster_path / f"cluster{k}")
            path.mkdir(parents=True, exist_ok=True)

        for images, labels, path in train_loader:
            images = images.to(self.device)
            argmin_idx = self._get_cluster_argmin_idx(images) # depends on the method
            transformed_images = self.model.transform(images)
            argmin_idx = argmin_idx.astype(np.int32)
            cluster_by_path += [
                (os.path.relpath(p, train_loader.dataset.data_path), argmin_idx[i]) 
                for i, p in enumerate(path)]

            for img, idx, p, tsf_imgs in zip(images, argmin_idx, path, transformed_images):
                convert_to_img(img).save(
                    cluster_path / f"cluster{idx}" / f"{count_per_cluster[idx]}_raw.png"
                )
                convert_to_img(tsf_imgs[idx]).save(
                    cluster_path / f"cluster{idx}" / f"{count_per_cluster[idx]}_tsf.png"
                )
                count_per_cluster[idx] += 1

        cluster_by_path = pd.DataFrame(
            cluster_by_path, columns=["path", "cluster_id"]
        ).set_index("path")
        cluster_by_path.to_csv(self.run_dir / "cluster_by_path.csv")

        return [np.array([]) for k in range(self.n_prototypes)]

    @torch.no_grad()
    def _get_cluster_argmin_idx(self, images):
        raise NotImplementedError()

class LoggedKMeansTrainer(LoggingTrainerMixin, KMeansTrainer):
    @torch.no_grad()
    def _get_cluster_argmin_idx(self, images):
        out = self.model(images)[1:]
        dist_min_by_sample, argmin_idx = map(lambda t: t.cpu().numpy(), out)
        return argmin_idx

class LoggedSpritesTrainer(LoggingTrainerMixin, SpritesTrainer):
    @torch.no_grad()
    def _get_cluster_argmin_idx(self, images):
        dist = self.model(images)[1]
        if self.n_backgrounds > 1:
            dist = dist.view(
                images.size(0), self.n_prototypes, self.n_backgrounds
            ).min(2)[0]
        dist_min_by_sample, argmin_idx = map(lambda t: t.cpu().numpy(), dist.min(1))
        return argmin_idx

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
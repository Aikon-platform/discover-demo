import os, sys
from pathlib import Path
from typing import Optional
import requests
import numpy as np
import torch, json
import cv2
from PIL import Image
from torchvision import transforms
from torch.utils.data import DataLoader


from .HDV.src.main import build_model_main
from .HDV.src.util.slconfig import SLConfig
from .HDV.src.util import box_ops
from .HDV.src.datasets.transforms import arc_cxcywh2_to_xy3, arc_xy3_to_cxcywh2
import matplotlib.pyplot as plt
from pathlib import Path
from torch import nn
import matplotlib.pyplot as plt
#import datasets.transforms as T
import glob

from ..const import IMG_PATH, MODEL_PATH, VEC_RESULTS_PATH

from ...shared.utils.logging import LoggingTaskMixin, console

from ..lib.utils import is_downloaded, download_img


class ComputeVectorization:
    def __init__(
        self,
        dataset: dict,
        doc_id: str,
        notify_url: Optional[str] = None,
    ):
        self.dataset = dataset
        self.notify_url = notify_url
        self.client_id = "default"
        self.doc_id = doc_id
        self.imgs = []

    def run_task(self):
        pass

    def check_dataset(self):
        # TODO add more checks
        if len(list(self.dataset.keys())) == 0:
            return False
        return True


class LoggedComputeVectorization(LoggingTaskMixin, ComputeVectorization):
    def run_task(self):
        if not self.check_dataset():
            self.print_and_log_warning(f"[task.vectorization] No documents to download")
            return

        self.print_and_log(
            f"[task.vectorization] Vectorization task triggered for {list(self.dataset.keys())} !"
        )

        self.download_dataset()
        self.compute_vectorization()

        return True

    def download_dataset(self):
        for image_id, url in self.dataset.items():
            self.print_and_log(
                f"[task.vectorization] Dowloading images...", color="blue"
            )
            try:
                if not is_downloaded(self.doc_id, image_id):
                    self.print_and_log(
                        f"[task.vectorization] Downloading {image_id} images..."
                    )
                    download_img(url, self.doc_id, image_id)

            except Exception as e:
                self.print_and_log(
                    f"[task.vectorization] Unable to download images for {image_id}", e
                )
    
    def compute_vectorization(self):
        model_folder = Path({MODEL_PATH}) # change the path of the model folder
        model_config_path = f"{model_folder}/config_cfg.py" # change the path of the model config file
        epoch = '0036'
        model_checkpoint_path = f"{model_folder}/checkpoint{epoch}.pth"
        args = SLConfig.fromfile(model_config_path) 
        args.device = 'cuda' 
        #args.device = 'cpu' 
        args.num_select = 200

        corpus_folder = Path({IMG_PATH}) # TODO: change this to the input folder of images you want to consider
        image_paths = glob.glob(str(corpus_folder/ {self.doc_id}) + "/*.jpg") # TODO: if your images are png change to /*.png 
        npz_dir = {VEC_RESULTS_PATH} / {self.doc_id} # Currently naming the folder as pred_npz_{threshold}
        #os.makedirs(npz_dir) 
        os.makedirs(npz_dir, exist_ok=True)

        print(image_paths.absolute())
        print(corpus_folder.absolute())
        print(model_checkpoint_path.absolute())

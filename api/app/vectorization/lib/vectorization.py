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
from .HDV.src.util.visualizer import COCOVisualizer
from .HDV.src.util import box_ops
from .HDV.src.datasets.transforms import arc_cxcywh2_to_xy3, arc_xy3_to_cxcywh2
from .utils import *
import matplotlib.pyplot as plt
from pathlib import Path
from torch import nn
import matplotlib.pyplot as plt
from .HDV.src.datasets import transforms as T
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
        model_folder = Path(MODEL_PATH) # changer le chemin du dossier du modèle
        model_config_path = f"{model_folder}/config_cfg.py" # changer le chemin du fichier de configuration du modèle
        epoch = '0044'
        model_checkpoint_path = f"{model_folder}/checkpoint{epoch}.pth"
        args = SLConfig.fromfile(model_config_path) 
        args.device = 'cuda' 
        #args.device = 'cpu' 
        args.num_select = 200

        corpus_folder = Path(IMG_PATH) # TODO: changer ceci par le dossier d'entrée des images que vous voulez considérer
        image_paths = glob.glob(str(corpus_folder / self.doc_id) + "/*.jpg") # TODO: si vos images sont au format png, changez à /*.png 
        npz_dir = VEC_RESULTS_PATH / self.doc_id # Nommez actuellement le dossier pred_npz_{threshold}
        #os.makedirs(npz_dir) 
        os.makedirs(npz_dir, exist_ok=True)

        print(image_paths)
        print(corpus_folder.absolute())
        print(model_checkpoint_path)

        model, criterion, postprocessors = build_model_main(args)
        checkpoint = torch.load(model_checkpoint_path, map_location='cpu')
        model.load_state_dict(checkpoint['model'])
        _ = model.eval()

        image_set = "val"
        args.dataset_file = 'synthetic'
        args.mode = "primitives"
        args.relative = False
        args.common_queries = True
        args.eval = (image_set == "val")
        args.coco_path = "data/synthetic_processed" # the path of coco
        args.fix_size = False
        args.batch_size = 1
        args.boxes_only=False
        encoder_only = False
        vslzr = COCOVisualizer()
        id2name = {0: 'line', 1: 'circle', 2: 'arc'}
        primitives_to_show = ['line', 'circle', 'arc']

        torch.cuda.empty_cache()
        with torch.no_grad():
            # looping over images 
            for image_path in tqdm(image_paths): 

                # loading image
                im_name = os.path.basename(image_path)[:-4] # [:-4] is to get rid of .jpg in the name
                # im_name_0 = 'wit2_img2_0082_230,1314,859,848'
                # if im_name!= im_name_0:
                #     continue
                # print(im_name)
                # if os.path.exists(npz_dir / f"{im_name}.npz") and im_name!= 'wit185_pdf193_26_188,421,557,598':
                #     continue

                # if os.path.exists(npz_dir / f"{im_name}.npz"):
                #     continue
                # if im_name not in ['wit176_man179_0151_1261,1428,471,585', 'wit205_pdf216_099_1030,1839,509,505']: 
                #     continue
                image = Image.open(image_path).convert("RGB") # load image
                im_shape = image.size
                transform = T.Compose([
                    T.RandomResize([800], max_size=1333),
                    T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                ])
                input_image, _ = transform(image, None)
                size = torch.Tensor([input_image.shape[1], input_image.shape[2]])

                # output
                output = model.cuda()(input_image[None].cuda())   
                output = postprocessors['param'](output, torch.Tensor([[im_shape[1], im_shape[0]]]).cuda(), to_xyxy=False)[0]

                threshold, arc_threshold = 0.3, 0.3
                scores = output['scores']
                labels = output['labels']
                boxes = output['parameters']
                select_mask = ((scores > threshold) & (labels!=2)) | ((scores > arc_threshold) & (labels==2) )
                labels = labels[select_mask]
                boxes = boxes[select_mask]
                scores = scores[select_mask]
                pred_dict = {'parameters': boxes, 'labels': labels, 'scores': scores}
                lines, line_scores, circles, circle_scores, arcs, arc_scores = get_outputs_per_class(pred_dict)

                # some duplicate postprocessing
                lines, line_scores = remove_duplicate_lines(lines, im_shape, line_scores)
                lines, line_scores = remove_small_lines(lines, im_shape, line_scores)
                circles, circle_scores = remove_duplicate_circles(circles, im_shape, circle_scores)
                arcs, arc_scores = remove_duplicate_arcs(arcs, im_shape, arc_scores)
                arcs, arc_scores = remove_arcs_on_top_of_circles(arcs, circles, im_shape, arc_scores)
                arcs, arc_scores = remove_arcs_on_top_of_lines(arcs, lines, im_shape, arc_scores)

                # save to npz
                np.savez(
                    npz_dir / f"{im_name}.npz",
                    lines=lines,
                    line_scores=line_scores,
                    circles=circles,
                    circle_scores=circle_scores,
                    arcs=arcs,
                    arc_scores=arc_scores,
                ) 
                # break
                # if im_name== im_name_0:
                #     break

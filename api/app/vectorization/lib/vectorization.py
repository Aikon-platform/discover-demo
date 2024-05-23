import os, sys
import re
import shutil
from calendar import c
import xml.etree.ElementTree as ET
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
from .HDV.src.datasets import build_dataset
from .HDV.src.util.visualizer import COCOVisualizer, get_angles_from_arc_points
from .HDV.src.util import box_ops
from .HDV.src.datasets.transforms import arc_cxcywh2_to_xy3, arc_xy3_to_cxcywh2
from .utils import *
from pathlib import Path
from torch import nn
import matplotlib.pyplot as plt
from .HDV.src.datasets import transforms as T
import glob
import cv2
import svgwrite

from svg.path import parse_path
from svg.path.path import Line, Move, Arc

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
        #self.compute_vectorization()
        #self.get_svgs()
        self.process_inference()

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
    

    '''
    def compute_vectorization(self):
        model_folder = Path(MODEL_PATH) # changer le chemin du dossier du modèle
        model_config_path = f"{model_folder}/config_cfg.py" # changer le chemin du fichier de configuration du modèle
        epoch = '0036'
        model_checkpoint_path = f"{model_folder}/checkpoint{epoch}.pth"
        args = SLConfig.fromfile(model_config_path) 
        args.device = 'cuda' 
        #args.device = 'cpu' 
        args.num_select = 200

        corpus_folder = Path(IMG_PATH) # TODO: changer ceci par le dossier d'entrée des images que vous voulez considérer
        image_paths = glob.glob(str(corpus_folder / self.doc_id) + "/*.jpg") # TODO: si vos images sont au format png, changez à /*.png 
        npz_dir = VEC_RESULTS_PATH / self.doc_id 
        #os.makedirs(npz_dir) 
        os.makedirs(npz_dir, exist_ok=True)

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
            try:
                for image_path in image_paths:
                    try:
                        self.print_and_log(
                            f"[task.vectorization] Processing {image_path}", color="blue"
                            )
                        # loading image
                        im_name = os.path.basename(image_path)[:-4] # [:-4] is to get rid of .jpg in the name
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

                        self.print_and_log(
                            f"[task.vectorization] {image_path} successfully vectorized", color="yellow"
                            )

                    except Exception as e:
                        self.print_and_log(
                            f"[task.vectorization] Failed to vectorize {image_path}", e   
                        )
            
                self.print_and_log(
                    f"[task.vectorization] Task over", color="yellow"
                )

            except Exception as e:
                self.print_and_log(
                    f"[task.vectorization] Failed to vectorize image dataset", e
                )
    
    def get_svgs(self):
        model_folder = Path(MODEL_PATH) 
        id2name = {0: "line", 1: "circle", 2: "arc"}


        npz_dir = VEC_RESULTS_PATH / self.doc_id
        output_dir = npz_dir
        diagram_dir = Path(IMG_PATH)
        image_paths = glob.glob(str(diagram_dir / self.doc_id) + "/*.jpg") # si vos images sont au format png, changez à /*.png

        try : 
            for image_path in image_paths:

                try:

                    self.print_and_log(
                            f"[task.vectorization] Drawing {image_path}", color="blue"
                            )

                    shutil.copy2(image_path, output_dir)
                    diagram_name = Path(image_path).stem
                    image_name = os.path.basename(image_path)
                    image = Image.open(image_path).convert("RGB") # load image
                    size = image.size
                    lines, circles, arcs = read_npz(npz_dir, image_name[:-4])
                    lines = lines.reshape(-1, 2, 2)
                    arcs = arcs.reshape(-1, 3, 2)

                    
                    dwg = svgwrite.Drawing(str(output_dir / f"{diagram_name}.svg"), profile="tiny", size=size)
                    dwg.add(dwg.image(href=image_name, insert=(0, 0), size=size))
                    dwg = write_svg_dwg(dwg, lines, circles, arcs, show_image=False, image=None)
                    dwg.save(pretty=True)

                    ET.register_namespace('', "http://www.w3.org/2000/svg")
                    ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
                    ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
                    ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

                    input_folder = output_dir
                    file_name = output_dir / f"{diagram_name}.svg"
                    tree = ET.parse(file_name)
                    root = tree.getroot()

                    root.set('xmlns:inkscape', 'http://www.inkscape.org/namespaces/inkscape')
                    root.set('xmlns:sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd')
                    root.set('inkscape:version', '1.3 (0e150ed, 2023-07-21)')

                    # Regular expression to match the 'a' or 'A' command in the 'd' attribute
                    arc_regex = re.compile(r'[aA]')

                    # Iterate over all 'path' elements
                    for path in root.findall('{http://www.w3.org/2000/svg}path'):
                        # Get the 'd' attribute
                        d = path.get('d', '')

                        # If the 'd' attribute contains an arc
                        if arc_regex.search(d):
                            # Add the 'sodipodi:type' and 'sodipodi:arc-type' attributes
                            path.set('sodipodi:type', 'arc')
                            path.set('sodipodi:arc-type', 'arc')
                            path_parsed = parse_path(d)
                            
                            for e in path_parsed:
                                if isinstance(e, Line):
                                    continue
                                elif isinstance(e, Arc):
                                    center, radius, start_angle, end_angle, p0, p1 = get_arc_param([e])
                                    path.set('sodipodi:cx', f'{center[0]}')
                                    path.set('sodipodi:cy', f'{center[1]}')
                                    path.set('sodipodi:rx', f'{radius}')
                                    path.set('sodipodi:ry', f'{radius}')
                                    path.set('sodipodi:start', f'{start_angle}')
                                    path.set('sodipodi:end', f'{end_angle}')

                    # Write the changes back to the file
                    tree.write(file_name, xml_declaration=True)
                
                    self.print_and_log(
                        f"[task.vectorization] SVG for {image_path} drawn", color="yellow"
                    )

                except Exception as e:
                    self.print_and_log(
                        f"[task.vectorization] Failed to draw {image_path}", e
                    )
            
            self.print_and_log(
                    f"[task.vectorization] SVGs drawn", color="yellow"
                )
            
        except Exception as e :
            self.print_and_log(
                    f"[task.vectorization] Failed to draw SVGs", e
                )
'''
    def process_inference(self):
        model_folder = Path(MODEL_PATH) 
        model_config_path = f"{model_folder}/config_cfg.py" 
        epoch = '0036'
        model_checkpoint_path = f"{model_folder}/checkpoint{epoch}.pth"
        args = SLConfig.fromfile(model_config_path)
        args.device = 'cuda'
        args.num_select = 200

        corpus_folder = Path(IMG_PATH)
        image_paths = glob.glob(str(corpus_folder / self.doc_id) + "/*.jpg")
        output_dir = VEC_RESULTS_PATH / self.doc_id
        os.makedirs(output_dir, exist_ok=True)

        model, criterion, postprocessors = build_model_main(args)
        checkpoint = torch.load(model_checkpoint_path, map_location='cpu')
        model.load_state_dict(checkpoint['model'])
        model.eval()

        args.dataset_file = 'synthetic'
        args.mode = "primitives"
        args.relative = False
        args.common_queries = True
        args.eval = True
        args.coco_path = "data/synthetic_processed"
        args.fix_size = False
        args.batch_size = 1
        args.boxes_only = False
        vslzr = COCOVisualizer()
        id2name = {0: 'line', 1: 'circle', 2: 'arc'}
        primitives_to_show = ['line', 'circle', 'arc']

        torch.cuda.empty_cache()
        transform = T.Compose([
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        with torch.no_grad():
            for image_path in image_paths:
                try:
                    self.print_and_log(
                        f"[task.vectorization] Processing {image_path}", color="blue"
                    )
                    # Load and process image
                    im_name = os.path.basename(image_path)[:-4]
                    image = Image.open(image_path).convert("RGB")
                    im_shape = image.size
                    input_image, _ = transform(image, None)
                    size = torch.Tensor([input_image.shape[1], input_image.shape[2]])

                    # Model inference
                    output = model.cuda()(input_image[None].cuda())
                    output = postprocessors['param'](output, torch.Tensor([[im_shape[1], im_shape[0]]]).cuda(), to_xyxy=False)[0]

                    threshold, arc_threshold = 0.3, 0.3
                    scores = output['scores']
                    labels = output['labels']
                    boxes = output['parameters']
                    select_mask = ((scores > threshold) & (labels != 2)) | ((scores > arc_threshold) & (labels == 2))
                    labels = labels[select_mask]
                    boxes = boxes[select_mask]
                    scores = scores[select_mask]
                    pred_dict = {'parameters': boxes, 'labels': labels, 'scores': scores}
                    lines, line_scores, circles, circle_scores, arcs, arc_scores = get_outputs_per_class(pred_dict)

                    # Postprocess the outputs
                    lines, line_scores = remove_duplicate_lines(lines, im_shape, line_scores)
                    lines, line_scores = remove_small_lines(lines, im_shape, line_scores)
                    circles, circle_scores = remove_duplicate_circles(circles, im_shape, circle_scores)
                    arcs, arc_scores = remove_duplicate_arcs(arcs, im_shape, arc_scores)
                    arcs, arc_scores = remove_arcs_on_top_of_circles(arcs, circles, im_shape, arc_scores)
                    arcs, arc_scores = remove_arcs_on_top_of_lines(arcs, lines, im_shape, arc_scores)

                    # Generate and save SVG
                    self.print_and_log(f"[task.vectorization] Drawing {image_path}", color="blue")
                    #shutil.copy2(image_path, output_dir)
                    #décommenter cette ligne si on veut obtenir les images dans le répertoire de sortie
                    diagram_name = Path(image_path).stem
                    image_name = os.path.basename(image_path)
                    lines = lines.reshape(-1, 2, 2)
                    arcs = arcs.reshape(-1, 3, 2)

                    dwg = svgwrite.Drawing(str(output_dir / f"{diagram_name}.svg"), profile="tiny", size=im_shape)
                    dwg.add(dwg.image(href=image_name, insert=(0, 0), size=im_shape))
                    dwg = write_svg_dwg(dwg, lines, circles, arcs, show_image=False, image=None)
                    dwg.save(pretty=True)

                    ET.register_namespace('', "http://www.w3.org/2000/svg")
                    ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
                    ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
                    ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

                    file_name = output_dir / f"{diagram_name}.svg"
                    tree = ET.parse(file_name)
                    root = tree.getroot()

                    root.set('xmlns:inkscape', 'http://www.inkscape.org/namespaces/inkscape')
                    root.set('xmlns:sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd')
                    root.set('inkscape:version', '1.3 (0e150ed, 2023-07-21)')

                    arc_regex = re.compile(r'[aA]')
                    for path in root.findall('{http://www.w3.org/2000/svg}path'):
                        d = path.get('d', '')
                        if arc_regex.search(d):
                            path.set('sodipodi:type', 'arc')
                            path.set('sodipodi:arc-type', 'arc')
                            path_parsed = parse_path(d)
                            for e in path_parsed:
                                if isinstance(e, Line):
                                    continue
                                elif isinstance(e, Arc):
                                    center, radius, start_angle, end_angle, p0, p1 = get_arc_param([e])
                                    path.set('sodipodi:cx', f'{center[0]}')
                                    path.set('sodipodi:cy', f'{center[1]}')
                                    path.set('sodipodi:rx', f'{radius}')
                                    path.set('sodipodi:ry', f'{radius}')
                                    path.set('sodipodi:start', f'{start_angle}')
                                    path.set('sodipodi:end', f'{end_angle}')

                    tree.write(file_name, xml_declaration=True)

                    self.print_and_log(f"[task.vectorization] SVG for {image_path} drawn", color="yellow")

                except Exception as e:
                    self.print_and_log(f"[task.vectorization] Failed to process {image_path}", e)

            self.print_and_log(f"[task.vectorization] Task over", color="yellow")

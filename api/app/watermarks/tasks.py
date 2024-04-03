import dramatiq
from dramatiq.middleware import CurrentMessage
from PIL import ImageOps, Image
from torchvision import transforms
import torch
from typing import List, Dict, Optional
from pathlib import Path
import json
import os
from .const import MODEL_PATHS, DEVICE, WATERMARKS_DATA_FOLDER
from .sources import WatermarkSource

from ..shared.utils.logging import notifying, TLogger, LoggerHelper

FEATURE_TRANSFORMS = lambda sz: transforms.Compose([
    transforms.Resize((sz, sz)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.75, 0.70, 0.65], std=[0.14, 0.15, 0.16])
])

DETECT_TRANSFORMS = transforms.Compose([
    transforms.Resize((1200, 1200)),
    transforms.ToTensor(),
])

MODELS = {}


def auto_load_models(models: List[str] = None):
    global MODELS
    if models is None:
        models = MODEL_PATHS.keys()
    for model in models:
        if model not in MODELS:
            MODELS[model] = torch.load(MODEL_PATHS[model], map_location=torch.device(DEVICE)).eval()

@torch.no_grad()
def detect_watermarks(model: torch.nn.Module, img: Image.Image) -> Dict:
    img = DETECT_TRANSFORMS(img)
    h, w = img.shape[-2:]
    img = img.unsqueeze(0).to(next(model.parameters()).device)

    preds = model(img)

    return {
        "boxes": [
            [x0 / w, y0 / h, x1 / w, y1 / h]
            for x0, y0, x1, y1 in preds[0]["boxes"].cpu().numpy().tolist()
        ],
        "scores": preds[0]["scores"].cpu().numpy().tolist(),
    }

@torch.no_grad()
def extract_features(model: torch.nn.Module, images: List[Image.Image], resize_to: int=352, transpositions: List[int|None]|None=None) -> torch.Tensor:
    device = next(model.parameters()).device
    imgs = []
    if transpositions is None: transpositions = [None]
    tf = FEATURE_TRANSFORMS(resize_to)

    for image in images:
        for transp in transpositions:
            img = image.transpose(transp) if transp else image
            img = tf(img).to(device)
            imgs.append(img)

    imgs = torch.stack(imgs)
    feats = model(img)

    return feats.reshape(len(images), len(transpositions), -1)

@torch.no_grad()
def get_closest_matches(queries: torch.Tensor, source: WatermarkSource, topk: int=20, min_sim=0.3) -> torch.Tensor:
    n_queries, n_query_flips = queries.shape[:2]
    n_compare, n_compare_flips, n_feats = source.features.shape
    sim = torch.nn.functional.cosine_similarity(queries.reshape((-1, n_feats)), source.features.reshape((-1, n_feats)), dim=1)
    sim = sim.reshape(n_queries, n_query_flips, n_compare, n_compare_flips)
    best_qsim, best_qflip = sim.max(dim=1)
    best_ssim, best_sflip = best_qsim.max(dim=2)
    tops = best_ssim.topk(topk, dim=1)
    return [
        {
            "similarity": sim.item(),
            "best_source_flip": best_sflip[i, j].item(),
            "best_query_flip": best_qflip[i, j, best_sflip[i, j]].item(),
            "query_index": i,
            "source_index": j,
        }
        for i, (j, sim) in enumerate(zip(tops.indices, tops.values))
    ]

@torch.no_grad()
def _pipeline(image: Image.Image, detect: bool=True, compare_to: Optional[WatermarkSource]=None) -> Dict:
    to_load = []
    if detect: to_load.append("detection")
    if compare_to: to_load.append("features")
    auto_load_models(to_load)

    image = ImageOps.exif_transpose(image).convert("RGB")

    crops = [image]
    output = {}

    resize = compare_to.metadata.get("resize", 352) if compare_to else 352

    if detect:
        boxes = detect_watermarks(MODELS["detection"], image)
        output["boxes"] = boxes
        crops = []
        if compare_to:
            for box, score in zip(boxes["boxes"], boxes["scores"]):
                if score < 0.5 and len(crops) > 0:
                    break
                box = [box[0] * image.width, box[1] * image.height, box[2] * image.width, box[3] * image.height]
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                sz = max(box[2] - box[0], box[3] - box[1]) * 1.20
                x0, y0, x1, y1 = int(cx - sz / 2), int(cy - sz / 2), int(cx + sz / 2), int(cy + sz / 2)
                crops.append(image.crop((x0, y0, x1, y1)).resize((resize, resize)))

    if compare_to:
        feats1 = extract_features(MODELS["features"], crops, resize, [None, Image.ROTATE_90, Image.ROTATE_180, Image.ROTATE_270])
        feats2 = torch.load(MODEL_PATHS[compare_to]).eval().to(DEVICE)
        output["matches"] = get_closest_matches(feats1, feats2)
    
    return output

@dramatiq.actor(time_limit=60000, max_retries=0, store_results=True)
@notifying
def pipeline(image_path: str, detect: bool=True, experiment_id: str="", compare_to: Optional[str]=None, logger: TLogger=LoggerHelper):
    image = Image.open(image_path)
    compare_to = WatermarkSource(compare_to) if compare_to else None
    output = _pipeline(image, detect, compare_to)

    logger.info(f"Experiment {experiment_id} finished with result {output}")

    result_dir = WATERMARKS_DATA_FOLDER / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    with open(result_dir / f"{CurrentMessage.get_current_message().message_id}.json", "w") as f:
        json.dump(output, f)
    os.unlink(image_path)

    return output
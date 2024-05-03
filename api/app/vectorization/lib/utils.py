import os
import sys
from itertools import combinations_with_replacement
from tqdm import tqdm

import requests
import urllib.request
import json
import shutil

from pathlib import Path
from PIL import Image

from ..const import IMG_PATH, LIB_PATH
from .const import MAX_SIZE
from ...shared.utils.fileutils import create_dir
from ...shared.utils.logging import console




def save_img(
    img: Image,
    img_filename,
    doc_dir,
    max_dim=MAX_SIZE,
    img_format="JPEG",
):
    try:
        if img.mode != "RGB":
            img = img.convert("RGB")

        if img.width > max_dim or img.height > max_dim:
            img.thumbnail(
                (max_dim, max_dim), Image.ANTIALIAS
            )  # Image.Resampling.LANCZOS
        img_path = os.path.join(doc_dir, img_filename + ".jpg")
        img.save(img_path, format=img_format)
        return img 
    
    except Exception as e:
        console(f"Failed to save {img_filename} as JPEG", e=e)
        return False




def get_json(url):
    with urllib.request.urlopen(url) as url:
        return json.loads(url.read().decode())




def download_img(img_url, doc_id, img_name):
    doc_dir = f"{IMG_PATH}/{doc_id}"
    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)
    try:
        with requests.get(img_url, stream=True) as response:
            response.raw.decode_content = True
            img = Image.open(response.raw)
            save_img(img, img_name, doc_dir)

    except requests.exceptions.RequestException as e:
        shutil.copyfile(
            f"{LIB_PATH}/media/placeholder.jpg",
            f"{doc_dir}/{img_name}",
        )
        # log_failed_img(img_name, img_url)
        console(f"[download_img] {img_url} is not a valid img file", e=e)
    except Exception as e:
        shutil.copyfile(
            f"{LIB_PATH}/media/placeholder.jpg",
            f"{doc_dir}/{img_name}",
        )
        # log_failed_img(img_name, img_url)
        console(f"[download_img] {img_url} image was not downloaded", e=e)



def is_downloaded(doc_id, image_id):
    path = Path(f"{IMG_PATH}/{doc_id}/{image_id}.jpg")
    return path.exists()


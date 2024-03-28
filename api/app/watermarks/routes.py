from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    url_for,
    jsonify,
)
from pathlib import Path
from PIL import Image, ImageOps
from torchvision import transforms
import torch
import traceback

from api.app.main import app
from api.app.config import WATERMARKS_MODEL_FOLDER

MODEL = None
MODEL_PATH = Path(WATERMARKS_MODEL_FOLDER) / "detection.pth"
DEVICE = "cpu"


@app.route("/watermarks/detect", methods=["POST"])
def annotator():
    try:
        global MODEL
        if MODEL is None:
            MODEL = torch.load(MODEL_PATH).eval().to(DEVICE)

        image = request.files["image"]
        img = Image.open(image)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = transforms.Resize((1000, 1000))(img)
        img = transforms.ToTensor()(img)
        h, w = img.shape[-2:]
        img = img.unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            preds = MODEL(img)

        output = {
            "boxes": [
                [x0 / w, y0 / h, x1 / w, y1 / h]
                for x0, y0, x1, y1 in preds[0]["boxes"].cpu().numpy().tolist()
            ],
            "scores": preds[0]["scores"].cpu().numpy().tolist(),
        }

        return jsonify(output)
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

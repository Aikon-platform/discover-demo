"""
Appariement image <-> transcription à l'ingestion d'un dataset paléographie (D1).

Contrat réunion (15/07) :
- upload = Zip contenant images + .txt de même radical (nom) ; sous-dossiers autorisés ;
- appariement par (sous-dossier, radical) : un .txt matche l'image de même radical
  DANS LE MÊME dossier (deux `line_1` dans deux sous-dossiers ne se télescopent pas) ;
- seules les PAIRES sont retenues (décision #5) :
    * image sans .txt        -> ignorée ;
    * .txt sans image        -> ignoré ;
    * radical d'image ambigu -> ignoré.

Volontairement sans dépendance plateforme (stdlib) : testable en isolation.
"""

from __future__ import annotations

import zipfile
from pathlib import PurePosixPath

IMAGE_EXTENSIONS = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff", ".webp", ".bmp"}
)
TXT_EXTENSION = ".txt"


def pair_transcriptions_from_zip(zip_path, *, encoding: str = "utf-8") -> dict:
    """
    Apparie les images et les .txt d'un zip, par (dossier, radical).

    Retourne::

        {
          "pairs": { "<dossier>/<radical>": "<transcription>", ... },  # paires retenues
          "n_images_ignored": int,   # images sans .txt (ou radical ambigu)
          "n_txt_ignored": int,      # .txt sans image (ou radical ambigu)
        }

    NB: la clé "<dossier>/<radical>" est l'identifiant relatif de la ligne. Son
    alignement avec l'identifiant d'image extrait par l'API (`Image.src`) est à
    valider à l'étape visualisation (#8) — voir `Dataset.get_doc_image_mapping`.
    """
    images: dict[tuple, str] = {}   # (dossier, radical) -> arcname image
    txts: dict[tuple, str] = {}     # (dossier, radical) -> arcname txt
    dup_images: set[tuple] = set()

    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            p = PurePosixPath(info.filename)
            if p.name.startswith(".") or "__MACOSX" in p.parts:
                continue  # fichiers cachés / artefacts macOS
            ext = p.suffix.lower()
            key = (str(p.parent), p.stem)
            if ext == TXT_EXTENSION:
                txts[key] = info.filename
            elif ext in IMAGE_EXTENSIONS:
                if key in images:
                    dup_images.add(key)  # radical ambigu dans le même dossier
                images[key] = info.filename

        pairs: dict[str, str] = {}
        for key, img_arc in images.items():
            if key in dup_images:
                continue  # ambigu -> ignoré
            txt_arc = txts.get(key)
            if txt_arc is None:
                continue  # image sans .txt -> ignorée
            with zf.open(txt_arc) as fh:
                text = fh.read().decode(encoding, errors="replace")
            folder, stem = key
            relkey = stem if folder in (".", "") else f"{folder}/{stem}"
            pairs[relkey] = text

    n_txt_ignored = sum(1 for k in txts if (k not in images) or (k in dup_images))
    n_images_ignored = sum(1 for k in images if (k in dup_images) or (k not in txts))
    return {
        "pairs": pairs,
        "n_images_ignored": n_images_ignored,
        "n_txt_ignored": n_txt_ignored,
    }

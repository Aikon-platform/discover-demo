from django.utils.deconstruct import deconstructible
import os
import uuid
from pathlib import Path
from typing import List, Dict
import requests
from stream_unzip import stream_unzip
import re
import zipfile

from shared.utils import pprint
from pathlib import PurePosixPath

TXT_EXTENSION = ".txt"

IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".tiff"}


@deconstructible
class PathAndRename(object):
    """
    This class is used to rename the uploaded files
    """

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        # Generate UUID if not already set (should be rare since UUID is default)
        filename = f"{instance.id or uuid.uuid4()}.{ext}"
        return os.path.join(self.path, filename)


def unzip_on_the_fly(
    zip_url_or_path: str | Path, target_path: str | Path, allowed_extensions=None
) -> List[Path]:
    """
    Unzip an internet file in a streaming fashion

    Ignores hidden files (starting with a dot or in a folder starting with a dot)

    Args:
        zip_url_or_path: The URL of the ZIP file
        target_path: The path where the files are extracted
        allowed_extensions: A list of allowed extensions (default: None)

    Returns:
        A list of all the files extracted
    """
    if isinstance(zip_url_or_path, str) and "://" in zip_url_or_path:

        def zipped_chunks():
            with requests.get(zip_url_or_path, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    yield chunk

    else:

        def zipped_chunks():
            with open(zip_url_or_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk

    target_path = Path(target_path)
    all_files = []

    for file_name, file_size, unzipped_chunks in stream_unzip(zipped_chunks()):
        file_name = file_name.decode("utf-8")
        path = target_path / file_name
        if "/." in "/" + file_name.replace("\\", "/"):  # hidden file
            continue
        if (
            allowed_extensions is not None
            and path.suffix.lower() not in allowed_extensions
        ):
            continue
        all_files.append(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            for chunk in unzipped_chunks:
                f.write(chunk)

    return all_files


def sanitize_str(string: str) -> str:
    """
    Sanitize a URL string to make it a valid filename
    (remove http, https, www, /, ., :, spaces)
    """
    return (
        re.sub(r"^https?\:\/\/|www\.|\.|:|%|\s", "", string.strip())
        .replace("/", "^")
        .replace(" ", "_")
    )


class TreeDict:
    """
    a dict representation of a directory tree,
    along with helper functions to convert the tree to HTML

    tree structure:
        {
            curdir  : Str,  # name of the current directory
            files   : List[str],  # list of file names in the current directory
            subdirs : List[dict],  # a list of subdirectories, each represented by the same structure
        }

    """

    tree: Dict

    def __init__(self, path: str | os.PathLike) -> Dict:
        to_abspath = lambda _path, _file: os.path.join(_path, _file)
        to_basename = lambda _path: Path(_path).name

        self.tree = {"curdir": to_basename(path), "files": [], "subdirs": []}

        if os.path.exists(path):
            for el in sorted(os.listdir(path)):
                el_abspath = to_abspath(path, el)
                if os.path.isfile(el_abspath):
                    self.tree["files"].append(to_basename(el_abspath))
                elif os.path.isdir(el_abspath):
                    self.tree["subdirs"].append(TreeDict(el_abspath))

    def to_html_list(self) -> str:
        filearray_to_html = (
            lambda files: f"""
            <li>Files:
                <ul>
                    {"".join(f"<li>{f}</li>" for f in files)}
                </ul>
            </li>
        """
            if len(files)
            else ""
        )

        subdirarray_to_html = (
            lambda subdirs: f"""
            <li>Directories:
                <ul>
                    {"".join(f"{dir_to_html(d)}" for d in subdirs)}
                </ul>
            </li>
        """
            if len(subdirs)
            else ""
        )

        dir_to_html = (
            lambda dir: f"""
            <li>{dir["curdir"]}/
                <ul>
                    {filearray_to_html(dir["files"])}
                    {subdirarray_to_html(dir["subdirs"])}
                </ul>
            </li>
        """
        )
        return f"<ul>{dir_to_html(self.tree)}</ul>"

    # as pre
    def to_html_pre(self) -> str:
        num_spaces = 4
        indent = lambda lvl, spaces: " " * (lvl * spaces)

        filearray_to_html = (
            lambda files, lvl: (
                "".join(f"{indent(num_spaces, lvl+1)}{f}\n" for f in files)
            )
            if len(files)
            else ""
        )

        subdirarray_to_html = (
            lambda subdirs, lvl: (
                "".join(f"{dir_to_html(d.tree, lvl+1)}\n" for d in subdirs)
            )
            if len(subdirs)
            else ""
        )

        dir_to_html = lambda dir, lvl: (
            f"{indent(num_spaces, lvl)}{dir['curdir']}/\n"
            + filearray_to_html(dir["files"], lvl)
            + subdirarray_to_html(dir["subdirs"], lvl)
        )
        return f"<pre>{dir_to_html(self.tree, 0)}</pre>"
    

def pair_transcriptions_from_zip(zip_path, *, encoding: str = "utf-8") -> dict:
    """
    Apparie les images et les fichiers .txt d'un zip, par (sous-dossier, radical).

    Convention d'import (module paléographie) : un .txt porte le même nom que son
    image, dans le même dossier. Les sous-dossiers sont autorisés.

    Seules les PAIRES STRICTES sont retenues (décision #5, réunion 15 juil.).
    Tout le reste est ignoré mais COMPTÉ, pour qu'un dataset mal formé soit
    visible au lieu de passer inaperçu :
      - image sans .txt          -> ignorée
      - .txt sans image          -> ignoré
      - radical d'image ambigu   -> ignoré (plusieurs images pour un radical)
      - radical de .txt ambigu   -> ignoré (ex. l1.txt ET l1.TXT : à l'utilisateur
                                    de trancher, on ne choisit pas)
      - fichier ni image ni .txt -> ignoré (ex. XML, PDF)

    Retourne::

        {
          "pairs": {"<dossier>/<radical>": "<transcription>", ...},
          "n_images_ignored": int,   # en fichiers
          "n_txt_ignored": int,      # en fichiers
          "n_other_files": int,      # fichiers ni image ni .txt
          "report": str,             # résumé lisible, vide si tout est propre
          "dropped": {               # détail nominatif (pour debug / affichage)
              "img_no_txt": [str, ...],
              "txt_no_img": [str, ...],
              "ambiguous_img": [str, ...],
              "ambiguous_txt": [str, ...],
              "other": [str, ...],
          },
        }
    """
    from collections import defaultdict

    # ---- 1er passage : indexer, sans rien décider ----
    by_key: dict[tuple, dict] = defaultdict(
        lambda: {"images": [], "txts": [], "other": []}
    )
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            p = PurePosixPath(info.filename)
            if p.name.startswith(".") or "__MACOSX" in p.parts:
                continue
            key = (str(p.parent), p.stem)
            ext = p.suffix.lower()
            if ext == TXT_EXTENSION:
                by_key[key]["txts"].append(info.filename)
            elif ext in IMG_EXTENSIONS:
                by_key[key]["images"].append(info.filename)
            else:
                by_key[key]["other"].append(info.filename)

        # ---- 2e passage : classer chaque radical, lire seulement les paires ----
        pairs: dict[str, str] = {}
        dropped = {
            "img_no_txt": [],
            "txt_no_img": [],
            "ambiguous_img": [],
            "ambiguous_txt": [],
            "other": [],
        }

        for (folder, stem), e in by_key.items():
            imgs, txts, other = e["images"], e["txts"], e["other"]
            dropped["other"].extend(other)

            img_ambiguous = len(imgs) > 1
            txt_ambiguous = len(txts) > 1

            if img_ambiguous:
                dropped["ambiguous_img"].extend(imgs)
            if txt_ambiguous:
                dropped["ambiguous_txt"].extend(txts)

            # une paire n'existe que si EXACTEMENT une image ET un .txt non ambigus
            if len(imgs) == 1 and len(txts) == 1:
                with zf.open(txts[0]) as fh:
                    text = fh.read().decode(encoding, errors="replace")
                relkey = stem if folder in (".", "") else f"{folder}/{stem}"
                pairs[relkey] = text
                continue

            # sinon, ranger les orphelins non-ambigus dans le bon bucket
            if imgs and not txts and not img_ambiguous:
                dropped["img_no_txt"].extend(imgs)
            if txts and not imgs and not txt_ambiguous:
                dropped["txt_no_img"].extend(txts)

    # ---- comptes = simple len() des listes, exacts par construction ----
    n_images_ignored = len(dropped["img_no_txt"]) + len(dropped["ambiguous_img"])
    n_txt_ignored = len(dropped["txt_no_img"]) + len(dropped["ambiguous_txt"])
    n_other_files = len(dropped["other"])

    # ---- rapport lisible : uniquement ce qui pose problème ----
    problems = []
    if n_images_ignored:
        problems.append(f"{n_images_ignored} image(s) sans transcription appariée")
    if n_txt_ignored:
        problems.append(f"{n_txt_ignored} transcription(s) sans image")
    if dropped["ambiguous_img"] or dropped["ambiguous_txt"]:
        problems.append("radicaux ambigus détectés (plusieurs fichiers de même nom)")
    if n_other_files:
        problems.append(f"{n_other_files} fichier(s) non reconnu(s) (ni image ni .txt)")
    report = "; ".join(problems)

    return {
        "pairs": pairs,
        "n_images_ignored": n_images_ignored,
        "n_txt_ignored": n_txt_ignored,
        "n_other_files": n_other_files,
        "report": report,
        "dropped": dropped,
    }

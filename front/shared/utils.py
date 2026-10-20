import json
from urllib.parse import urlsplit
from stat import S_IFREG
from stream_zip import ZIP_64, ZIP_32, stream_zip
from typing import List, Tuple, Iterable, Generator, Union

from pathlib import Path
import os
from datetime import datetime

from demowebsite.settings import BASE_URL, API_URL, APP_URL_FROM_API


TPath = Union[str, Path]


def sanitize_for_regex(s: str) -> str:
    """
    sanitize user inputted string `s` so that it can be safely passed to a regular expression
    """
    chars = ["[", "\\", "$", "^", "*", "+", "?", "(", ")", "[", "{", "|", "]"]
    if not isinstance(s, str):
        raise TypeError(f"expected s to be a string, got {type(s)}")
    for c in chars:
        s = s.replace(c, "")
    return s


def zip_on_the_fly(files: List[Tuple[str, TPath]]) -> Iterable[bytes]:
    """
    Zip files on the fly

    Args:
        files: List of tuples (filename, path)
    """

    def contents(path: TPath) -> Generator[bytes, None, None]:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    def iter_files() -> (
        Generator[Tuple[str, int, int, int, Generator[bytes, None, None]], None, None]
    ):
        for i, (name, path) in enumerate(files):
            # NOTE: we zip the 1st file with ZIP_32, the others with ZIP_64.
            # on MacOS Safari, "Open after downloading", if the 1st file in the zip
            # is a Zip64, only the 1st file is extracted and the rest are silently deleted
            # ZIP_32 doesn't have this bug but can't be used on large archives:
            # - max number of zipped files is 65_000
            # - max archive size is 4GB
            # - max size of a single file in the zip is 4GB
            # see warnings on ZIP_64 here: https://stream-zip.docs.trade.gov.uk/api/methods/#the-64-methods
            # NOTE: only possible pitfall: if the 1st file is >4GB, it can't be zipped with ZIP_32 => archive creation will fail.
            zip_type = ZIP_32 if i == 0 else ZIP_64
            if not os.path.exists(path):
                print(f"File {path} does not exist")
                continue
            dt = datetime.fromtimestamp(os.path.getmtime(path))
            yield (name, dt, S_IFREG | 0o600, zip_type, contents(path))

    return stream_zip(iter_files())


def pprint(o):
    if isinstance(o, str):
        try:
            return json.dumps(json.loads(o), indent=4, sort_keys=True)
        except ValueError:
            return o
    elif isinstance(o, dict) or isinstance(o, list) or isinstance(o, tuple):
        if isinstance(o, list):
            o = list(o)
        try:
            return json.dumps(o, indent=4, sort_keys=True)
        except TypeError:
            dict_str = ""
            if isinstance(o, list):
                for v in o:
                    dict_str += f"{v}\n"
            if isinstance(o, dict):
                for k, v in o.items():
                    dict_str += f"{k}:\n{v}\n"
            return dict_str
    else:
        return str(o)


def get_url_host_and_scheme(url: str) -> str:
    """
    return 'scheme://host' or 'scheme://host:port' (port only if explicit).
    works for local, domain-names and docker URLs.
    """
    parts = urlsplit(url)
    if not parts.scheme or not parts.hostname:
        raise ValueError(f"not an absolute URL with a host: {url!r}")

    host = parts.hostname # lowercased, IPv6 brackets stripped
    if ":" in host:       # IPv6 literal needs brackets back
        host = f"[{host}]"

    port = parts.port      # int or None; raises ValueError if invalid
    base = f"{parts.scheme}://{host}"
    return f"{base}:{port}" if port is not None else base


def rewrite_front_url_for_api(front_url: str) -> str:
    """
    rewrite an URL to the front so that it can be reached fron API when mode==local
    (in these cases, the api URL should be: `http://front:$FRONT_PORT` since API and front
    are bundled in a docker network)
    """
    front_url = front_url.replace(BASE_URL, APP_URL_FROM_API)
    return front_url


@staticmethod
def rewrite_api_url_for_front(api_url: str) -> str:
    """
    rewrite an URL to the api so that it can be reached from the front when mode==local
    (in these cases, the front URL should be: `http://api:$API_PORT` since API and front
    are bundled in a docker network)
    """
    api_url = api_url.replace(get_url_host_and_scheme(api_url), API_URL)
    return api_url


from stat import S_IFREG
from stream_zip import ZIP_32, stream_zip
from typing import List, Tuple, Iterable, Generator, Union

from pathlib import Path
import os
from datetime import datetime

TPath = Union[str, Path]


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

    def iter_files() -> Generator[
        Tuple[str, int, int, int, Generator[bytes, None, None]], None, None
    ]:
        for name, path in files:
            if not os.path.exists(path):
                print(f"File {path} does not exist")
                continue
            dt = datetime.fromtimestamp(os.path.getmtime(path))
            yield (name, dt, S_IFREG | 0o600, ZIP_32, contents(path))

    return stream_zip(iter_files())

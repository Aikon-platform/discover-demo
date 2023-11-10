import os

from werkzeug.exceptions import NotFound
from pathlib import Path
from flask import Response
import mimetypes
from typing import Union

from slugify import slugify

TPath = Union[str, os.PathLike]

def xaccel_send_from_directory(directory: TPath, redirect: TPath, path: TPath):
    """
    Send a file from a given directory using X-Accel-Redirect
    """
    try:
        path = Path(path)
        directory = Path(directory)
        file_path = directory / path

        assert file_path.is_relative_to(directory)
        redirect_path = Path(redirect) / file_path.relative_to(directory)

        content_length = file_path.stat().st_size
        content_type = mimetypes.guess_type(str(file_path))[0]
        filename = file_path.name

        if not content_length or not content_type or not filename:
            return None

        response = Response()
        response.headers['Content-Length'] = content_length
        response.headers['Content-Type'] = content_type
        response.headers['Content-Disposition'] = f"attachment; filename={slugify(str(filename))}"
        response.headers['X-Accel-Redirect'] = str(redirect_path)
        response.headers['X-Accel-Buffering'] = "yes"
        response.headers['X-Accel-Charset'] = "utf-8"
        return response

    except:
        return None
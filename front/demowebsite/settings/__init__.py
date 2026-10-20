from .base import ENV

# Load the appropriate settings file based on the MODE environment variable

mode = ENV("MODE", default="").strip()

if mode in ("dev", "local"):
    from .dev import *
elif mode == "prod":
    from .prod import *
else:
    raise ValueError(
        f"MODE environment variable must be either 'dev', 'prod' or 'local'. got: '{mode}'"
    )

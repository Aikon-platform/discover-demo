from .base import ENV

# Load the appropriate settings file based on the MODE environment variable

if ENV("MODE", default="").strip() == "dev":
    from .dev import *
elif ENV("MODE", default="").strip() == "prod":
    from .prod import *
else:
    raise ValueError("MODE environment variable must be either 'dev' or 'prod'")

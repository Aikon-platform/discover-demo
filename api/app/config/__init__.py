from .base import ENV

if ENV("TARGET", default="").strip() == "dev":
    from .dev import *
elif ENV("TARGET", default="").strip() == "prod":
    from .prod import *
else:
    raise ValueError("TARGET environment variable must be either 'dev' or 'prod'")
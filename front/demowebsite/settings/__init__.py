from .base import ENV

if ENV("TARGET") == "dev":
    from .dev import *
elif ENV("TARGET") == "prod":
    from .prod import *
else:
    raise ValueError("TARGET environment variable must be either 'dev' or 'prod'")
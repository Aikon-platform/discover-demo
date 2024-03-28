from .config.base import INSTALLED_APPS


for app in INSTALLED_APPS:
    # import routes for each installed app
    exec(f"from .{app}.tasks import *")

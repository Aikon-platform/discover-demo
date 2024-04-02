from importlib import import_module

from .config.base import INSTALLED_APPS

for app in INSTALLED_APPS:
    # import routes for each installed app
    # exec(f"from .{app}.tasks import *")

    module = import_module(f".{app}.tasks", package=__package__)
    __all__ = getattr(module, "__all__", None)
    if __all__ is None:
        __all__ = [name for name in dir(module) if not name.startswith("_")]
    globals().update({name: getattr(module, name) for name in __all__})

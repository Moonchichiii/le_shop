from decouple import config

env = config("DJANGO_ENV", default="local")

if env == "production":
    from .production import *  # noqa: F401,F403
elif env == "test":
    from .test import *  # noqa: F401,F403
else:
    from .local import *  # noqa: F401,F403

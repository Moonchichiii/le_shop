import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

root_path = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_path / "src"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "le_shop.settings")

application = get_asgi_application()

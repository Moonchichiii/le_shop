import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Add src to path
root_path = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_path / "src"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "le_shop.settings")

application = get_wsgi_application()

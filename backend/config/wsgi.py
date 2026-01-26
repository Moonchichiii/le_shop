import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Add root to path
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

application = get_wsgi_application()

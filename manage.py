import os
import sys
from pathlib import Path


def main() -> None:
    root_path = Path(__file__).resolve().parent
    backend_path = root_path / "backend"

    # Make imports work no matter where you run from
    sys.path.insert(0, str(root_path))
    sys.path.insert(0, str(backend_path))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

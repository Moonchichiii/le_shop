import os
import sys
from pathlib import Path


def main() -> None:
    root_path = Path(__file__).resolve().parent
    sys.path.append(str(root_path))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

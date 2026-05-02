#!/usr/bin/env python
"""Django management entrypoint for NovaCommerce Core."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "novacommerce.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Couldn't import Django. Is it installed and on PYTHONPATH?") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

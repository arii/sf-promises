"""Shared local workspace defaults; explicit CLI paths take precedence."""

import os
from pathlib import Path


def workspace():
    return Path(os.environ.get("SF_PROMISES_WORKSPACE", "~/.local/share/sf-promises")).expanduser().resolve()


def database_path():
    return workspace() / "promises.db"

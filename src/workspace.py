"""Shared workspace defaults: the Archil disk mounted at /mnt/archil (see README,
Workspace setup). SF_PROMISES_WORKSPACE and explicit CLI paths take precedence."""

import os
from pathlib import Path


def workspace():
    return Path(os.environ.get("SF_PROMISES_WORKSPACE", "/mnt/archil/workspace")).expanduser().resolve()


def database_path():
    return workspace() / "promises.db"

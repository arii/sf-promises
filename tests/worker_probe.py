"""Local runner test protocol; contains no provider or network operations."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

try:
    import resource
except ImportError:
    resource = None


mode = sys.argv[1]
if mode == "environment":
    print(json.dumps({"environment": dict(os.environ), "cwd": os.getcwd()}))
elif mode == "timeout":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    Path(sys.argv[2]).write_text(json.dumps({"child": child.pid, "cwd": os.getcwd()}))
    time.sleep(30)
elif mode == "overflow":
    print("x" * 100_000)
elif mode == "invalid":
    print("not json")
elif mode == "failure":
    sys.exit(1)
elif mode == "empty":
    pass
elif mode == "limits":
    print(json.dumps({name: resource.getrlimit(getattr(resource, name)) for name in (
        "RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_FSIZE", "RLIMIT_NOFILE", "RLIMIT_CORE",
    )}))
else:
    raise ValueError(mode)

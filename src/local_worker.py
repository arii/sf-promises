"""Bounded processes, not a filesystem or network security boundary."""

import asyncio
import json
import os
from pathlib import Path
import signal
import sys
import tempfile

try:
    import resource
except ImportError:
    resource = None


class WorkerError(ValueError):
    pass


def _limits():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


async def run_worker(module, *, files, arguments=(), timeout=120, output_cap=2_500_000):
    with tempfile.TemporaryDirectory(prefix="sf-promises-worker-") as directory:
        root = Path(directory).resolve()
        for name, data in files.items():
            target = root / name
            if not target.resolve().is_relative_to(root):
                raise WorkerError("Invalid worker input path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        env = {
            "PATH": os.defpath, "HOME": directory, "TMPDIR": directory,
            "LANG": "C.UTF-8", "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", module, *arguments, cwd=root, env=env,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            start_new_session=True, preexec_fn=_limits if sys.platform == "linux" else None,
        )

        async def read(stream):
            data = bytearray()
            while chunk := await stream.read(65536):
                data.extend(chunk)
                if len(data) > output_cap:
                    raise WorkerError("Worker output exceeds limit")
            return bytes(data)

        tasks = [asyncio.create_task(read(process.stdout)),
                 asyncio.create_task(read(process.stderr)),
                 asyncio.create_task(process.wait())]
        try:
            stdout, _, code = await asyncio.wait_for(asyncio.gather(*tasks), timeout)
            if code != 0:
                raise WorkerError("Worker exited unsuccessfully")
            try:
                return json.loads(stdout)
            except (UnicodeError, ValueError):
                raise WorkerError("Invalid worker JSON") from None
        except asyncio.TimeoutError:
            raise WorkerError("Worker timed out") from None
        finally:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                elif process.returncode is None:
                    process.kill()
            except ProcessLookupError:
                pass
            await process.wait()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

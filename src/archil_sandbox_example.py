"""Demonstrate persistence across an Archil sandbox stop/start."""

import os
import uuid

import archil


def main():
    if not os.environ.get("ARCHIL_API_KEY", "").startswith("key-"):
        raise SystemExit("Set ARCHIL_API_KEY to an Archil account API key starting with key-.")
    if os.environ.get("ARCHIL_REGION") not in {
        "aws-us-east-1", "aws-us-west-2", "aws-eu-west-1", "gcp-us-central1"
    }:
        raise SystemExit("Set ARCHIL_REGION to a valid Archil region.")

    name = f"sf-promises-example-{uuid.uuid4().hex[:12]}"
    print(f"Creating sandbox {name}", flush=True)
    sandbox = archil.create_sandbox(name=name, max_ttl_seconds=300)
    try:
        result = sandbox.exec("printf 'persistent across restart\\n' > /root/archil-example.txt")
        if result.exit_code != 0:
            raise RuntimeError(f"Write failed: {result.stderr}")

        sandbox = sandbox.stop()
        sandbox = sandbox.start()

        result = sandbox.exec("cat /root/archil-example.txt")
        if result.exit_code != 0 or result.stdout != "persistent across restart\n":
            raise RuntimeError(f"Persistence check failed: {result.stderr}")
        print(f"After restart: {result.stdout}", end="")
    finally:
        sandbox.stop()
        print(f"Stopped sandbox {name}")


if __name__ == "__main__":
    main()

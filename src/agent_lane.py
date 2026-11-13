"""Queue-based model lane fulfilled by the workspace's own Obvious agents.

Pipeline stages that need model judgment (extraction, origin review, outcome
advocates) emit structured JSON requests to a request queue. An agent answers
them through the module's CLI, and responses are validated on return exactly
as provider API responses are validated — same schema checks, same
verbatim-quote snap-back and date normalization downstream in src/extract.py.

The OpenRouter/Nebius provider paths in src/model.py stay behind the same
completion interface and can be re-enabled with MODEL_PROVIDER; this lane is
the default and never touches an external provider.
"""

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.model import ModelResponseError, has_structured_response

AGENT_MODEL_ID = "obvious-agent"
REQUESTS_DIRNAME = "requests"
RESPONSES_DIRNAME = "responses"
DEFAULT_TIMEOUT_SECONDS = 3600.0
DEFAULT_POLL_SECONDS = 2.0


class LaneRequest(BaseModel):
    """One structured model request, mirroring the prompt schemas in use."""

    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str
    kind: str = Field(min_length=1, max_length=128)
    created_at: str
    messages: list[dict[str, str]]
    tools: list[dict] | None = None
    tool_choice: dict | None = None
    max_tokens: int = Field(default=4096, ge=1)
    temperature: float = Field(default=0, ge=0, le=2)


class LaneTimeout(TimeoutError):
    """No validated response arrived within the lane's timeout."""


def request_kind(messages, tool_choice):
    """Derive a stable request kind from the prompt shape."""
    if isinstance(tool_choice, dict):
        name = tool_choice.get("function", {}).get("name")
        if isinstance(name, str) and name:
            return name
    return "completion"


class AgentLane:
    """File-backed request queue between pipeline stages and an agent."""

    def __init__(self, root, *, timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
                 poll_seconds=DEFAULT_POLL_SECONDS, sleep=asyncio.sleep):
        self.root = Path(root)
        self.requests_dir = self.root / REQUESTS_DIRNAME
        self.responses_dir = self.root / RESPONSES_DIRNAME
        self.timeout_seconds = timeout_seconds
        self.poll_seconds = poll_seconds
        self._sleep = sleep

    def _ensure_dirs(self):
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

    def _request_path(self, request_id):
        return self.requests_dir / f"{request_id}.json"

    def _response_path(self, request_id):
        return self.responses_dir / f"{request_id}.json"

    def emit(self, messages, *, tools=None, tool_choice=None,
             max_tokens=4096, temperature=0, kind=None):
        """Write one structured request to the queue and return its ID."""
        if not isinstance(messages, list) or not messages:
            raise ValueError("A request requires a non-empty message list")
        request_id = uuid.uuid4().hex
        request = LaneRequest(
            request_id=request_id,
            kind=kind or request_kind(messages, tool_choice),
            created_at=datetime.now(timezone.utc).isoformat(),
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        self._ensure_dirs()
        self._request_path(request_id).write_text(
            request.model_dump_json(), encoding="utf-8"
        )
        return request_id

    def pending(self):
        """List request IDs that have no response yet, oldest first."""
        if not self.requests_dir.exists():
            return []
        ids = []
        for path in sorted(self.requests_dir.glob("*.json")):
            if not self._response_path(path.stem).exists():
                ids.append(path.stem)
        return ids

    def read_request(self, request_id):
        """Return a pending request dict, or None when it does not exist."""
        path = self._request_path(request_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def fulfill(self, request_id, response):
        """Agent side: record a response for a pending request.

        Only checks that the payload is a JSON object; structural validation
        against the caller's schema happens on return, exactly as provider
        responses are validated today.
        """
        if not isinstance(response, dict):
            raise ValueError("A lane response must be a JSON object")
        self._ensure_dirs()
        self._response_path(request_id).write_text(
            json.dumps(response), encoding="utf-8"
        )

    def collect(self, request_id):
        """Return the raw response for a request, or None when pending."""
        path = self._response_path(request_id)
        if not path.exists():
            return None
        try:
            response = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise ModelResponseError(
                f"Lane response {request_id} is not valid JSON"
            ) from error
        if not isinstance(response, dict):
            raise ModelResponseError(
                f"Lane response {request_id} is not a JSON object"
            )
        return response

    def _validated(self, request_id, response, tool_choice):
        if not has_structured_response(response, tool_choice or {}):
            raise ModelResponseError(
                f"Lane response {request_id} failed structural validation"
            )
        # The lane stamps its own model identity so provenance cannot be forged.
        response["model_id"] = AGENT_MODEL_ID
        return response

    async def completion(self, messages, *, tools=None, tool_choice=None,
                         max_tokens=4096, temperature=0, kind=None):
        """Emit a request and await a validated response on the queue."""
        request_id = self.emit(
            messages, tools=tools, tool_choice=tool_choice,
            max_tokens=max_tokens, temperature=temperature, kind=kind,
        )
        waited = 0.0
        while True:
            response = self.collect(request_id)
            if response is not None:
                return self._validated(request_id, response, tool_choice)
            if waited >= self.timeout_seconds:
                raise LaneTimeout(
                    f"No lane response for request {request_id} within "
                    f"{self.timeout_seconds:g}s"
                )
            await self._sleep(self.poll_seconds)
            waited += self.poll_seconds


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Agent model lane queue")
    parser.add_argument("command", choices=("pending", "show", "fulfill"))
    parser.add_argument("--lane-root", type=Path, required=True)
    parser.add_argument("--request-id")
    parser.add_argument("--response-file", type=Path)
    args = parser.parse_args()
    lane = AgentLane(args.lane_root)

    if args.command == "pending":
        print(json.dumps(lane.pending()))
        return
    if args.command == "show":
        if not args.request_id:
            parser.error("show requires --request-id")
        request = lane.read_request(args.request_id)
        if request is None:
            parser.exit(2, f"Unknown request: {args.request_id}\n")
        print(json.dumps(request, indent=2))
        return
    if not args.request_id or not args.response_file:
        parser.error("fulfill requires --request-id and --response-file")
    response = json.loads(args.response_file.read_text(encoding="utf-8"))
    lane.fulfill(args.request_id, response)
    print(f"Fulfilled: {args.request_id}")


if __name__ == "__main__":
    main()

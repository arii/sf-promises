"""Agent lane queue in/out with a scripted responder.

The lane must exchange structured requests/responses over its queue, validate
responses on return exactly as provider responses are validated, stamp its own
model identity, and time out when no validated response arrives.
"""
import asyncio
import json
from pathlib import Path

import pytest

from src.agent_lane import AGENT_MODEL_ID, AgentLane, LaneTimeout
from src.model import ModelResponseError


def _tool_response(name, arguments):
    return {"choices": [{"message": {"tool_calls": [{"function": {
        "name": name, "arguments": json.dumps(arguments),
    }}]}}]}


def _messages():
    return [{"role": "user", "content": "Review the archived source."}]


def _tool_choice():
    return {"type": "function", "function": {"name": "verify_origin"}}


def test_queue_round_trip_with_scripted_responder(tmp_path):
    lane = AgentLane(tmp_path / "lane", poll_seconds=0.01)
    request_id = lane.emit(
        _messages(), tools=[{"type": "function"}], tool_choice=_tool_choice(),
    )
    assert lane.pending() == [request_id]

    request = lane.read_request(request_id)
    assert request["request_id"] == request_id
    assert request["kind"] == "verify_origin"
    assert request["messages"] == _messages()
    assert request["tool_choice"] == _tool_choice()

    async def scenario():
        task = asyncio.ensure_future(lane.completion(
            _messages(), tools=[{"type": "function"}], tool_choice=_tool_choice(),
        ))
        await asyncio.sleep(0)
        # The request emitted by the test above is still pending, so
        # pending()[0] is either request with ~50% probability (uuid sort
        # order); fulfilling the wrong one left the completion polling for
        # its 3600s default timeout — the intermittent CI pytest hang.
        # Fulfill the request the completion under test actually emitted.
        in_flight = next(
            (rid for rid in lane.pending() if rid != request_id), None
        )
        assert in_flight is not None, "completion did not enqueue its request"
        lane.fulfill(in_flight, _tool_response(
            "verify_origin", {"action": True, "explanation": "ok"},
        ))
        return await task

    result = asyncio.run(scenario())
    assert result["model_id"] == AGENT_MODEL_ID
    assert result["choices"][0]["message"]["tool_calls"][0]["function"][
        "arguments"] == json.dumps({"action": True, "explanation": "ok"})


def test_request_kind_defaults_to_completion_for_plain_prompts(tmp_path):
    lane = AgentLane(tmp_path / "lane")
    request_id = lane.emit(_messages())
    assert lane.read_request(request_id)["kind"] == "completion"


def test_fulfill_rejects_non_object_responses(tmp_path):
    lane = AgentLane(tmp_path / "lane")
    with pytest.raises(ValueError, match="JSON object"):
        lane.fulfill("anything", ["not", "an", "object"])


def test_validation_rejects_malformed_tool_response(tmp_path):
    lane = AgentLane(tmp_path / "lane", poll_seconds=0.01)

    async def scenario():
        task = asyncio.ensure_future(lane.completion(
            _messages(), tools=[{"type": "function"}], tool_choice=_tool_choice(),
        ))
        await asyncio.sleep(0)
        request_id = lane.pending()[0]
        # Wrong function name in the response.
        lane.fulfill(request_id, _tool_response("verify_evidence", {"action": True}))
        with pytest.raises(ModelResponseError, match="structural validation"):
            await task

    asyncio.run(scenario())


def test_validation_rejects_unparseable_arguments(tmp_path):
    lane = AgentLane(tmp_path / "lane", poll_seconds=0.01)

    async def scenario():
        task = asyncio.ensure_future(lane.completion(
            _messages(), tools=[{"type": "function"}], tool_choice=_tool_choice(),
        ))
        await asyncio.sleep(0)
        request_id = lane.pending()[0]
        lane.fulfill(request_id, {"choices": [{"message": {"tool_calls": [{
            "function": {"name": "verify_origin", "arguments": "{not json"},
        }]}}]})
        with pytest.raises(ModelResponseError, match="structural validation"):
            await task

    asyncio.run(scenario())


def test_collect_rejects_invalid_json_response_file(tmp_path):
    lane = AgentLane(tmp_path / "lane")
    lane._ensure_dirs()
    (lane.responses_dir / "abc.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(ModelResponseError, match="not valid JSON"):
        lane.collect("abc")


def test_completion_times_out_without_a_response(tmp_path):
    lane = AgentLane(tmp_path / "lane", poll_seconds=0.01, timeout_seconds=0.05)
    with pytest.raises(LaneTimeout, match="No lane response"):
        asyncio.run(lane.completion(_messages()))

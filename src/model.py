"""Bounded model requests."""

import asyncio
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sqlite3
import uuid

import httpx


NEBIUS_MAX_COMPLETION_TOKENS = 4096
NEBIUS_SPEND_LIMIT_USD = Decimal("5")
OPENROUTER_MODELS = (
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3.8-27b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)
NEBIUS_MODELS = (
    "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "nvidia/Nemotron-3.5-Lightning",
    "nvidia/Nemotron-3_5-Lightning",
    "MiniMaxAI/MiniMax-M3",
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
)


class ModelResponseError(ValueError):
    """A provider responded, but did not produce usable structured output."""


def _has_structured_response(response, tool_choice):
    try:
        message = response["choices"][0]["message"]
        calls = message.get("tool_calls")
        if calls:
            function = calls[0]["function"]
            if function["name"] != tool_choice["function"]["name"]:
                return False
            content = function["arguments"]
        else:
            content = message["content"]
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I).strip()
        return isinstance(content, str) and isinstance(json.loads(content), dict)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return False


def _zero_priced(entry):
    pricing = entry.get("pricing")
    if not isinstance(pricing, dict) or not {"prompt", "completion"} <= pricing.keys():
        return False
    try:
        return all(Decimal(str(value)) == 0 for value in pricing.values())
    except (InvalidOperation, ValueError):
        return False


async def free_completion(
    client, api_key, models, messages, *, tools=None, tool_choice=None,
    max_tokens=NEBIUS_MAX_COMPLETION_TOKENS, temperature=0, sleep=asyncio.sleep,
):
    if not api_key or not models or any(not model.endswith(":free") for model in models):
        raise ValueError("An API key and only :free models are required")
    if sum(len(message.get("content", "")) for message in messages) > 16000:
        raise ValueError("Model input exceeds the size limit")

    catalog = await client.get("https://openrouter.ai/api/v1/models")
    catalog.raise_for_status()
    data = catalog.json().get("data", [])
    verified = {
        entry["id"] for entry in data
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        and entry["id"].endswith(":free") and _zero_priced(entry)
    }
    available = [model for model in models if model in verified]
    if not available:
        raise ValueError("No requested model is currently listed and zero-priced")

    last_response = None
    invalid_models = set()
    for attempt in range(3):
        for model_index, model in enumerate(available):
            if model in invalid_models:
                continue
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model, "messages": messages,
                    "max_tokens": max_tokens, "temperature": temperature,
                    **({"tools": tools, "tool_choice": tool_choice} if tools else {}),
                },
            )
            if response.status_code != 429:
                response.raise_for_status()
                try:
                    result = response.json()
                except ValueError:
                    invalid_models.add(model)
                    continue
                if tools and not _has_structured_response(result, tool_choice):
                    invalid_models.add(model)
                    continue
                return result
            last_response = response
            if attempt < 2 or model_index < len(available) - 1:
                await sleep(min(2 ** attempt, 8))
    if invalid_models:
        raise ModelResponseError("Free models returned invalid structured responses")
    last_response.raise_for_status()


class NebiusBudgetExceeded(RuntimeError):
    pass


class NebiusSpendLedger:
    """Persist conservative reservations and actual Nebius spend."""

    def __init__(self, path, *, limit_usd=NEBIUS_SPEND_LIMIT_USD):
        if not isinstance(limit_usd, Decimal) or not limit_usd.is_finite() or limit_usd <= 0:
            raise ValueError("Nebius spend limit must be a positive Decimal")
        self.path = Path(path)
        self.limit_usd = limit_usd
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS model_spend (
                    request_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    amount_usd TEXT NOT NULL
                )"""
            )

    @property
    def spent_usd(self):
        with sqlite3.connect(self.path) as conn:
            values = conn.execute("SELECT amount_usd FROM model_spend").fetchall()
        return sum((Decimal(row[0]) for row in values), Decimal(0))

    def reserve(self, model_id, amount_usd):
        if (not isinstance(amount_usd, Decimal)
                or not amount_usd.is_finite() or amount_usd < 0):
            raise ValueError("Nebius spend reservation is invalid")
        request_id = uuid.uuid4().hex
        with sqlite3.connect(self.path, isolation_level=None) as conn:
            conn.execute("BEGIN IMMEDIATE")
            spent = sum(
                (Decimal(row[0]) for row in
                 conn.execute("SELECT amount_usd FROM model_spend")),
                Decimal(0),
            )
            if spent + amount_usd > self.limit_usd:
                conn.execute("ROLLBACK")
                raise NebiusBudgetExceeded(
                    f"Nebius spend cap of ${self.limit_usd} would be exceeded"
                )
            conn.execute(
                "INSERT INTO model_spend VALUES (?, ?, ?)",
                (request_id, model_id, str(amount_usd)),
            )
            conn.execute("COMMIT")
        return request_id

    def settle(self, request_id, amount_usd):
        if not amount_usd.is_finite() or amount_usd < 0:
            raise ValueError("Nebius usage amount is invalid")
        with sqlite3.connect(self.path) as conn:
            updated = conn.execute(
                "UPDATE model_spend SET amount_usd=? WHERE request_id=?",
                (str(amount_usd), request_id),
            )
            if updated.rowcount != 1:
                raise ValueError("Nebius spend reservation was not found")


async def _nebius_catalog(client, api_key):
    response = await client.get(
        "https://api.tokenfactory.nebius.com/v1/models?verbose=true",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    response.raise_for_status()
    try:
        rows = response.json()["data"]
        if not isinstance(rows, list):
            raise TypeError
        models = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                continue
            pricing = row.get("pricing")
            if not isinstance(pricing, dict):
                continue
            try:
                prompt = Decimal(pricing["prompt"])
                completion = Decimal(pricing["completion"])
            except (KeyError, TypeError, InvalidOperation):
                continue
            if (prompt.is_finite() and completion.is_finite()
                    and prompt >= 0 and completion >= 0):
                models[row["id"]] = (prompt, completion)
    except (KeyError, StopIteration, TypeError, InvalidOperation, ValueError):
        raise ValueError("Nebius model catalog is invalid") from None
    return models


async def completion_with_fallback(
    client, openrouter_key, models, messages, *, nebius_key, nebius_models,
    spend_ledger, tools=None, tool_choice=None,
    max_tokens=NEBIUS_MAX_COMPLETION_TOKENS, temperature=0, sleep=asyncio.sleep,
):
    """Use Nebius only after OpenRouter exhausts its 429 retries."""
    try:
        return await free_completion(
            client, openrouter_key, models, messages, tools=tools,
            tool_choice=tool_choice, max_tokens=max_tokens,
            temperature=temperature, sleep=sleep,
        )
    except httpx.HTTPStatusError as error:
        if error.response.status_code != 429:
            raise

    if not nebius_key:
        raise ValueError("Nebius key is required after OpenRouter rate limiting")
    catalog = await _nebius_catalog(client, nebius_key)
    available = [model for model in nebius_models if model in catalog]
    if not available:
        raise ValueError("No preferred Nebius model is available on this account")
    serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":"))
    max_input_tokens = len(serialized.encode("utf-8")) + 32 * len(messages)
    last_error = None
    for model in available:
        prompt_price, completion_price = catalog[model]
        reservation = (
            Decimal(max_input_tokens) * prompt_price
            + Decimal(max_tokens) * completion_price
        )
        request_id = spend_ledger.reserve(model, reservation)
        try:
            response = await nebius_completion(
                client, nebius_key, model, messages, tools=tools,
                tool_choice=tool_choice, max_tokens=max_tokens,
                temperature=temperature,
            )
        except httpx.HTTPStatusError as error:
            if error.response.status_code != 429:
                raise
            last_error = error
            continue
        try:
            usage = response["usage"]
            prompt_tokens = usage["prompt_tokens"]
            completion_tokens = usage["completion_tokens"]
            if type(prompt_tokens) is not int or type(completion_tokens) is not int:
                raise ValueError
            actual = (
                Decimal(prompt_tokens) * prompt_price
                + Decimal(completion_tokens) * completion_price
            )
            spend_ledger.settle(request_id, actual)
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "Nebius usage metadata is invalid; maximum reservation retained"
            ) from None
        return response
    if last_error is not None:
        raise last_error
    raise ValueError("No Nebius model completed the request")


async def nebius_completion(
    client, api_key, model, messages, *, tools=None, tool_choice=None,
    max_tokens=NEBIUS_MAX_COMPLETION_TOKENS, temperature=0,
):
    if not api_key or not model:
        raise ValueError("A Nebius API key and model are required")
    if type(max_tokens) is not int or not 1 <= max_tokens <= 4096:
        raise ValueError("Invalid Nebius completion token limit")
    if sum(len(message.get("content", "")) for message in messages) > 16000:
        raise ValueError("Model input exceeds the size limit")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload.update({"tools": tools, "tool_choice": tool_choice})
    else:
        payload["response_format"] = {"type": "json_object"}
    response = await client.post(
        "https://api.tokenfactory.nebius.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
    )
    response.raise_for_status()
    result = response.json()
    try:
        if result["choices"][0]["finish_reason"] == "length":
            raise ValueError("Model response was truncated")
    except (KeyError, IndexError, TypeError):
        raise ValueError("Model returned an invalid response") from None
    return result

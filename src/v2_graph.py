"""Bounded fan-out for independently audited promises."""

import asyncio
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class AuditState(TypedDict):
    items: list[dict]
    results: Annotated[list[dict], operator.add]


def build_audit_graph(worker, *, max_concurrency=1, verified_capacity=None, checkpointer=None):
    """Bound one graph; reviewed capacity does not coordinate other processes."""
    if type(max_concurrency) is not int or max_concurrency < 1:
        raise ValueError("max_concurrency must be a positive integer")
    if max_concurrency > 1 and (
        type(verified_capacity) is not int or verified_capacity < max_concurrency
    ):
        raise ValueError("Parallelism requires verified account capacity")
    semaphore = asyncio.Semaphore(max_concurrency)

    def fan_out(state):
        return [Send("worker", {"item": item}) for item in state["items"]] or END

    async def run_worker(state):
        async with semaphore:
            return {"results": [await worker(state["item"])]}

    graph = StateGraph(AuditState)
    graph.add_node("worker", run_worker)
    graph.add_conditional_edges(START, fan_out)
    graph.add_edge("worker", END)
    return graph.compile(checkpointer=checkpointer)

"""Fail fast on any test that opens a real network socket.

The suite is fully offline: every HTTP interaction goes through
httpx.MockTransport and every CLI test runs against local sqlite or a
missing-database error path. A test (or code under test) that reaches for a
live endpoint would otherwise hang on a blackholed connection and burn the
CI runner for its whole timeout — seen as 50-120 minute pytest steps. This
guard turns that hang into an immediate, named failure.

Opt out for a test that genuinely needs a socket with:

    @pytest.mark.allow_network

and see tests/test_network_guard.py for the enforcement check.
"""

import socket

import pytest

_REAL_SOCKET = socket.socket
_REAL_CREATE_CONNECTION = socket.create_connection


class BlockedNetworkCall(AssertionError):
    """Raised when a test tries to open a live network socket."""


def _guarded_socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, fileno=None):
    # socketpair()/AF_UNIX plumbing (asyncio wakeup pipes, local IPC) is not
    # network egress and stays allowed.
    if family in (socket.AF_INET, socket.AF_INET6):
        raise BlockedNetworkCall(
            "test opened a live network socket (AF_INET/AF_INET6). "
            "All suite traffic must be mocked; use @pytest.mark.allow_network "
            "if this test genuinely needs a socket."
        )
    return _REAL_SOCKET(family, type, proto, fileno)


def pytest_addoption(parser):
    parser.addoption(
        "--allow-network", action="store_true", default=False,
        help="Disable the no-network guard (for local debugging only).",
    )


@pytest.fixture(autouse=True)
def _block_live_network(request):
    if request.config.getoption("--allow-network"):
        yield
        return
    marker = request.node.get_closest_marker("allow_network")
    if marker is not None:
        yield
        return
    socket.socket = _guarded_socket
    socket.create_connection = _blocked_create_connection
    try:
        yield
    finally:
        socket.socket = _REAL_SOCKET
        socket.create_connection = _REAL_CREATE_CONNECTION


def _blocked_create_connection(*args, **kwargs):
    raise BlockedNetworkCall(
        "test called socket.create_connection. "
        "All suite traffic must be mocked; use @pytest.mark.allow_network "
        "if this test genuinely needs a socket."
    )

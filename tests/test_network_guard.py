"""Prove the CI network guard works: live sockets raise, mocked paths don't.

Also registers the allow_network marker so a future genuinely-live test can
opt out explicitly and stays greppable in CI configuration.
"""

import socket
from unittest.mock import MagicMock

import pytest

pytest.importorskip("httpx")

import httpx  # noqa: E402


def test_guard_blocks_live_inet_socket():
    with pytest.raises(AssertionError, match="live network socket"):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_guard_blocks_create_connection():
    with pytest.raises(AssertionError, match="create_connection"):
        socket.create_connection(("example.invalid", 80), timeout=1)


def test_unix_sockets_stay_allowed():
    # asyncio wakeup pipes and local IPC use AF_UNIX; the guard must not
    # break them.
    pair = socket.socketpair()
    try:
        pair[0].send(b"x")
        assert pair[1].recv(1) == b"x"
    finally:
        pair[0].close()
        pair[1].close()


def test_mocked_httpx_transports_still_work():
    handler = MagicMock(return_value=httpx.Response(200, json={"ok": True}))
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert client.get("https://unit.test/").json() == {"ok": True}


@pytest.mark.allow_network
def test_allow_network_marker_opts_out():
    # Would attempt a real connection to a reserved test address; the marker
    # removes the guard, so the failure mode is a connection error, not the
    # guard's assertion. An invalid TLD keeps the test hermetic either way.
    with pytest.raises(OSError):
        socket.create_connection(("example.invalid", 80), timeout=1)

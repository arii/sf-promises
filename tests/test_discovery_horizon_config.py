"""OD-20 H1: the rolling discovery horizon is config-sourced, never hardcoded.

The planner's default time window and cli_search's published_after/before
defaults must both come from config/discovery.json (relative days only),
with concrete dates computed relative to the run date.
"""

import asyncio
import json
from datetime import date, timedelta

import pytest

from src import cli_search, discovery_config
from src.discovery_config import (
    DiscoveryConfig,
    load_discovery_config,
    rolling_time_window,
)
from src.sourcing.planner import SearchPlanner

TEST_TODAY = date(2026, 11, 14)


class FakeResponse:
    results = []


@pytest.fixture
def config_with(tmp_path, monkeypatch):
    """Point the loader's default at a throwaway config and clear its cache."""

    def _install(rolling_days=183):
        config_path = tmp_path / "discovery.json"
        config_path.write_text(
            json.dumps(
                {
                    "rolling_days": rolling_days,
                    "added_reason": "test fixture",
                    "added_by": "test",
                    "added_at": "2026-11-14",
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            discovery_config, "DEFAULT_DISCOVERY_CONFIG_PATH", config_path
        )
        load_discovery_config.cache_clear()
        return config_path

    yield _install
    load_discovery_config.cache_clear()


def test_repo_config_is_valid_and_provenance_tracked():
    config = load_discovery_config()
    assert isinstance(config, DiscoveryConfig)
    assert config.rolling_days == 183
    assert config.added_reason.strip()
    assert config.added_by.strip()
    assert config.added_at.strip()


def test_rolling_window_computed_relative_to_run_date():
    window = rolling_time_window(today=TEST_TODAY)
    expected_start = (TEST_TODAY - timedelta(days=183)).isoformat()
    assert window == f"{expected_start}..{TEST_TODAY.isoformat()}"


def test_loader_rejects_bad_configs(tmp_path):
    base = {"added_reason": "r", "added_by": "b", "added_at": "2026-11-14"}

    def _write(payload):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    with pytest.raises(ValueError, match="rolling_days"):
        load_discovery_config(_write({**base, "rolling_days": 0}))
    with pytest.raises(ValueError, match="rolling_days"):
        load_discovery_config(_write({**base, "rolling_days": "183"}))
    with pytest.raises(ValueError, match="missing required fields"):
        load_discovery_config(_write({"rolling_days": 183}))


def test_planner_default_sourced_from_config(config_with):
    """Mutating rolling_days changes the window every generated query carries."""
    config_with(rolling_days=10)
    stratified = SearchPlanner().generate_stratified_queries(max_per_pillar=2)
    variants = SearchPlanner().generate_diversified_variants()
    expected_start = (date.today() - timedelta(days=10)).isoformat()
    expected_window = f"{expected_start}..{date.today().isoformat()}"
    assert {s.time_window for s in stratified} == {expected_window}
    assert {s.time_window for s in variants} == {expected_window}


def test_planner_default_tracks_config_changes(config_with):
    config_with(rolling_days=10)
    first = SearchPlanner().generate_stratified_queries(max_per_pillar=1)[0]
    config_with(rolling_days=30)
    second = SearchPlanner().generate_stratified_queries(max_per_pillar=1)[0]
    assert first.time_window != second.time_window


def test_explicit_time_window_overrides_config():
    stratified = SearchPlanner().generate_stratified_queries(
        time_window="2016-01-01..2016-12-31", max_per_pillar=1
    )
    variants = SearchPlanner().generate_diversified_variants(
        time_window="2016-01-01..2016-12-31"
    )
    assert {s.time_window for s in stratified + variants} == {
        "2016-01-01..2016-12-31"
    }


def test_resolve_search_window_defaults_from_config(config_with):
    config_with(rolling_days=10)
    after, before = cli_search.resolve_search_window(None, None, today=TEST_TODAY)
    assert after == (TEST_TODAY - timedelta(days=10)).isoformat()
    assert before == TEST_TODAY.isoformat()


def test_resolve_search_window_explicit_flags_win(config_with):
    config_with(rolling_days=10)
    resolved = cli_search.resolve_search_window(
        "2024-01-01", "2024-07-01", today=TEST_TODAY
    )
    assert resolved == ("2024-01-01", "2024-07-01")


def test_cli_search_passes_config_derived_dates(config_with, monkeypatch):
    """search_keenable sends the config window as published_after/before."""
    captured: dict = {}

    class RecordingClient:
        class _Http:
            async def aclose(self):
                pass

        def __init__(self, api_key):
            self._http = self._Http()

        async def search(self, query, **kwargs):
            captured.update(kwargs)
            return FakeResponse()

        async def aclose(self):
            pass

    config_with(rolling_days=10)
    monkeypatch.setenv("KEENABLE_API_KEY", "test-key")
    monkeypatch.setattr(cli_search, "RetryingKeenable", RecordingClient)
    leads = asyncio.run(cli_search.search_keenable("test query"))
    assert leads == []
    expected_start = (date.today() - timedelta(days=10)).isoformat()
    assert captured["published_after"] == expected_start
    assert captured["published_before"] == date.today().isoformat()

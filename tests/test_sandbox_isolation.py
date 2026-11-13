"""Verify that sandboxed advocate workers cannot access each other's staging files."""

import pytest
from src.advocates import (
    check_staging_isolation,
    check_sandbox_network,
)


def test_kept_sandbox_cannot_read_broken_staging(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    broken_file = staging_dir / "broken_P02.json"
    broken_file.write_text('{"promise_id": "P02", "role": "broken", "claims": []}')

    # Role 'kept' attempting to access broken staging file must fail
    with pytest.raises(PermissionError, match="Isolation violation.*kept advocate cannot read broken"):
        check_staging_isolation(role="kept", target_path=broken_file)


def test_broken_sandbox_cannot_read_kept_staging(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    kept_file = staging_dir / "kept_P02.json"
    kept_file.write_text('{"promise_id": "P02", "role": "kept", "claims": []}')

    # Role 'broken' attempting to access kept staging file must fail
    with pytest.raises(PermissionError, match="Isolation violation.*broken advocate cannot read kept"):
        check_staging_isolation(role="broken", target_path=kept_file)


def test_investigator_cannot_read_advocate_staging(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    kept_file = staging_dir / "kept_P02.json"
    broken_file = staging_dir / "broken_P02.json"

    with pytest.raises(PermissionError):
        check_staging_isolation(role="investigate", target_path=kept_file)
    with pytest.raises(PermissionError):
        check_staging_isolation(role="investigate", target_path=broken_file)


def test_allowed_role_staging_access(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    kept_file = staging_dir / "kept_P02.json"
    broken_file = staging_dir / "broken_P02.json"
    inv_file = staging_dir / "investigate_P02.json"

    # Permitted accesses do not raise
    check_staging_isolation(role="kept", target_path=kept_file)
    check_staging_isolation(role="broken", target_path=broken_file)
    check_staging_isolation(role="investigate", target_path=inv_file)


def test_advocate_cannot_write_to_other_role_staging(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    broken_file = staging_dir / "broken_P02.json"
    kept_file = staging_dir / "kept_P02.json"

    # Kept advocate attempting to write to broken file must fail
    with pytest.raises(PermissionError, match="Isolation violation.*kept advocate cannot write"):
        check_staging_isolation(role="kept", target_path=broken_file, mode="write")

    # Broken advocate attempting to write to kept file must fail
    with pytest.raises(PermissionError, match="Isolation violation.*broken advocate cannot write"):
        check_staging_isolation(role="broken", target_path=kept_file, mode="write")

    # Valid writes pass
    check_staging_isolation(role="kept", target_path=kept_file, mode="write")
    check_staging_isolation(role="broken", target_path=broken_file, mode="write")


def test_advocate_cannot_touch_core_database(tmp_path):
    db_file = tmp_path / "promises.db"

    # No role can read or write directly to core database promises.db
    with pytest.raises(PermissionError, match="cannot write core database"):
        check_staging_isolation(role="kept", target_path=db_file, mode="write")

    with pytest.raises(PermissionError, match="cannot read core database"):
        check_staging_isolation(role="broken", target_path=db_file, mode="read")


def test_advocate_network_egress_blocked():
    # Kept and broken advocates cannot perform raw outbound network calls
    with pytest.raises(ConnectionRefusedError, match="Network egress blocked in advocate sandbox"):
        check_sandbox_network(role="kept", target_url="https://api.external.com/data")

    with pytest.raises(ConnectionRefusedError, match="Network egress blocked in advocate sandbox"):
        check_sandbox_network(role="broken", target_url="https://raw.githubusercontent.com/leak")


def test_fetcher_network_allowlist_enforcement():
    # Fetcher allowed on official municipal / news allowlist
    check_sandbox_network(role="fetcher", target_url="https://sf.gov/news/budget-2024")
    check_sandbox_network(role="fetcher", target_url="https://www.flysfo.com/about/press-releases")

    # Fetcher blocked on unapproved external domain
    with pytest.raises(ConnectionRefusedError, match="not on allowlist"):
        check_sandbox_network(role="fetcher", target_url="https://untrusted-site.xyz/fake-news")

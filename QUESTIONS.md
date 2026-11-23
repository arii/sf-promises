# Questions and blockers

Open items for a person to decide or approve. Move resolved items to
`WORKING_NOTES.md`.

## Open

1. **Shared `promises.db` fails `PRAGMA foreign_key_check`** (checked
   read-only 2026-11-23). `quick_check` is ok. 52 violations, all rows whose
   `promise_id` has no `promises` row: `test_cases` 39, `sources` 7,
   `relevance_checks` 4, `change_log` 1, `quarantined` 1. This matches the
   documented design that staging references dangle before a verdict (see
   `docs/export_data.py`). `workspace_backup verify --allow-existing-fk-violations`
   on the live workspace reports "baseline mismatch" because the live
   workspace has no recorded baseline manifest; the baseline is recorded by
   the first `backup --allow-existing-fk-violations`. Decide: accept the 52 as
   the legacy baseline (take that backup), or clean them up (needs approval).
2. **Leftover files on the Archil disk** (identified read-only 2026-11-23):
   - `promises.db.pre-e1b.bak` (Nov 14 01:35): an older copy of the legacy
     database, 62 promises / 85 verdicts (live `promises.db`: 62 / 87).
     Looks like a manual backup before the "E1b" change.
   - `promises_v2.db` (Nov 11): a v2-schema database (application ID set),
     0 promises, 0 verdicts, 2 `promises_pending` rows; `-wal` is empty.
   Ask before deleting. Moving them to a dated `archive/` folder on the disk
   is the reversible option.
3. **#82 / #83 (images):** a person must approve image licenses and the
   workspace data used by the staging job.
4. **#44 (map basemap):** third-party map tiles conflict with #82's
   no-third-party-requests rule. Decide: self-host tiles, or keep the SVG map.
5. **Resolved (2026-11-23): mounting needs no password.** `archil mount`
   must run as root (Archil Linux docs, "Requirements"), and this host has
   `/etc/sudoers.d/archil` granting `NOPASSWD: SETENV: /usr/bin/archil`, so
   `scripts/mount_archil.sh` mounts without a prompt. On a new machine, add the
   same rule (`sudo visudo -f /etc/sudoers.d/archil`):
   `<user> ALL=(ALL) SETENV: NOPASSWD: /usr/bin/archil`.
   The mount still does not survive a reboot; re-run the script.

6. **Root-owned files in the checkout** (written by the terminal container):
   `config/`, `docs/fonts/`, `docs/media/`, `.td_rag/`. Fix once with
   `sudo chown -R ari:ari config docs/fonts docs/media .td_rag`.

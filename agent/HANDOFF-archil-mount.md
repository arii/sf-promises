# Handoff: mount the Archil workspace on the S5 host (2026-11-23)

Use this to restart the work in a new agent session after the terminal
container is recreated. Paste into the new session: "read
agent/HANDOFF-archil-mount.md and continue".

## Decision

The shared database and saved sources live on the Archil disk `promises`
(`ARCHIL_DISK_ID` in `.env`, region `aws-us-east-1`), on Archil's **free
plan**. Only Archil storage is used; no Archil sandboxes or serverless
execution. Every machine mounts the disk at `/mnt/archil`; the workspace is
`/mnt/archil/workspace`. Nothing is copied to a machine-local database.
Hugging Face (`onasafari/sf-promises`) stays as the published copy, not the
working store. Full setup: README, "Workspace setup" (PR #96).

Facts checked on 2026-11-23:

- Account plan: Free, no payment method (hard caps, cannot be billed).
- Disk contents: about 4 MB in 255 files under `workspace/` (10 GB free-plan
  limit): `promises.db` (774 KB, last written 2026-11-14), `sources/`,
  `staging/`, plus `promises.db.pre-e1b.bak`, `promises_v2.db` and its
  `-shm`/`-wal` files (the `-wal` is 0 bytes).
- A read-only `--shared` mount from a throwaway container on this host
  worked on the free plan.

## Step 1: mount on the host (do this outside the container)

```bash
curl -s https://archil.com/install | sh
cd /home/ari/repos/sf-promises && set -a && source .env && set +a
sudo mkdir -p /mnt/archil
sudo --preserve-env=ARCHIL_MOUNT_TOKEN archil mount "$ARCHIL_DISK_ID" /mnt/archil \
  --region "$ARCHIL_REGION" --shared
ls /mnt/archil/workspace        # expect promises.db  sources/  staging/
```

Unmount with `sudo archil unmount /mnt/archil` (not `umount`). The mount
does not survive a host reboot; re-run the mount command after a reboot.

## Step 2: pass the mount into the terminal container

In `/home/ari/remote-server/docker-compose.yml`, under
`services: terminal: volumes:`, add:

```yaml
      # Shared SF Promises workspace (Archil disk mounted on the host).
      # rslave: a host remount shows up here without recreating the container.
      - /mnt/archil:/mnt/archil:rslave
```

Then recreate only the terminal container (this ends any session running
inside it):

```bash
cd /home/ari/remote-server && docker compose up -d terminal
```

## Step 3: verify inside the new session

```bash
cd /srv/repos/sf-promises
ls /mnt/archil/workspace
python3 -c "from src.workspace import workspace; print(workspace())"   # /mnt/archil/workspace once PR #96 is merged
python3 -m scripts.workspace_backup verify --workspace /mnt/archil/workspace
```

`verify` is read-only. The `verify` step is expected to fail today with
"Database foreign key check failed" (see Next work, item 1).

## State at handoff

Open PRs (arii/sf-promises):

- **#96** docs: Archil disk is the shared workspace; setup and credentials.
  README "Workspace setup", `.env.example`, default workspace
  `/mnt/archil/workspace` in `src/workspace.py`, PRD/AGENTS updated. Tests
  622 passed. Merge after Step 3 confirms the mount.
- **#95** feat(media): entity avatars on Entity Profiles (refs #83). CI to
  check, then merge.
- **#94** Fix open bugs #84–#87. Its squash commit `cf1e44c` is already on
  `main`, but GitHub still shows the PR open (a 502 during merge). Close it
  by hand; issues #84–#87 are already closed.

Open issues: #82 and #83 (images; need a person to approve image licenses
and the workspace data for the staging job), #44 (map basemap; third-party
tiles conflict with #82's no-third-party-requests rule; needs a decision).

## Next work

1. **Foreign-key failure in the shared `promises.db`.** A read of the disk
   copy failed `PRAGMA foreign_key_check`. This is likely the legacy archive
   that PR #39 added `--allow-existing-fk-violations` and a recorded baseline
   for. Investigate read-only first:
   `sqlite3 "file:/mnt/archil/workspace/promises.db?mode=ro" "PRAGMA foreign_key_check;"`.
   Do not modify the database without the user's approval.
2. Leftover files on the disk (`promises.db.pre-e1b.bak`, `promises_v2.db*`):
   identify what they are; ask before deleting anything.
3. Merge #96 and #95, close #94 (see above).

## Rules that still apply

- One writer at a time on `promises.db`; only the Verdict lane writes
  `promises`/`verdicts`/`verifications`/`quarantined`.
- Back up before any change to the shared database
  (`python3 -m scripts.workspace_backup backup --destination <new path>`).
- `.env` stays out of version control.

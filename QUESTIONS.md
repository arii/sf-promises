# Questions and blockers

Open items for a person to decide or approve. Move resolved items to
`WORKING_NOTES.md`.

## Open

1. **Resolved (2026-11-23):** shared `promises.db` FK cleanup and leftover
   database deletion. See `WORKING_NOTES.md`, 2026-11-23. 39 `test_cases`
   violations remain as the recorded legacy baseline; verify with
   `--allow-existing-fk-violations` against the post-fk backup.
2. **Writing `promises.db` on the shared mount:** take delegations first
   (`archil checkout /mnt/archil/workspace` and `.../promises.db`), or SQLite
   fails at commit with "disk I/O error".
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

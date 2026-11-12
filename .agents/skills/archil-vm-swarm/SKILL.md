---
name: archil-vm-swarm
description: Use when implementing or operating SF Promises Archil sandbox workers, forks, or isolated PDF processing.
---

# Archil worker safety

Use the official Python `archil` SDK and the documented `.aio` methods:
https://docs.archil.com/sdks/python.md#persistent-sandboxes

- Keep the coordinator, checkpoints and v2 SQLite database in the runner
  workspace. The golden sandbox is an immutable template; do not install,
  stop, delete or alter it without authorization.
- Check the golden sandbox state, account limits, mounts and network policy
  before a live fork. This project currently requires a stopped template.
  Forked root filesystems are independent, but mounted disks are shared.
- `run_in_fork` refuses unknown or external mounts and requires explicit
  confirmation that the template has been independently reviewed for secrets
  and that its network policy has been reviewed; those flags are not a
  substitute for the reviews.
- Pass `run_in_fork` a `WorkerLeases` ledger backed by a dedicated persistent
  SQLite file and a unique run/job pair. A `creating` record can represent a
  lost fork response: do not automatically retry or delete by name. A `created`
  record identifies a worker needing cleanup, but only after confirming the
  original coordinator is no longer active. Remote recovery is not automated
  or live-verified.
- Bound worker concurrency with a semaphore, defaulting to one. Stop then
  delete only forks created by this run in `finally`. Record a cleanup failure
  or uncertain fork creation as blocked, not successful.
- Transfer structured public inputs through sandbox file APIs, not shell
  interpolation. Do not copy credentials into sandbox snapshots, logs,
  SQLite or source files.
- `extract_archived_pdf` uses a tracked fork and returns bounded page text
  linked to the saved PDF hash. This is unverified derived text, not proof or
  an OCR substitute. The worker must already have `pdfplumber` installed; do
  not install it into the golden template without authorization.
- The SDK's `exec` waits for a command result; `run` returns a process handle.
  Lifecycle methods return refreshed sandbox objects. Set explicit timeouts
  and check exit codes; verify live behavior before claiming isolation.
- `Disk.exec` is a separate one-shot microVM with a mounted disk. It is not a
  persistent sandbox; use it for suitable isolated single-command work only.

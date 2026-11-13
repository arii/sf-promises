# Runbook — Publishing the SF Promises dataset to Hugging Face

How to publish the exported snapshot (`docs/data.json`, `data/sf_promises_master.csv`,
`data/intake_ledger.csv`) as the Hugging Face dataset
[`onasafari/sf-promises`](https://huggingface.co/datasets/onasafari/sf-promises)
using `scripts/upload_to_huggingface.py`.

## Preconditions

1. **Fresh export.** The script stages from the repo's export artifacts, not the
   database directly. Re-export first so the snapshot is current:
   - `python docs/export_data.py` (refreshes `docs/data.json` and `docs/data.js`)
   - confirm `data/sf_promises_master.csv` and `data/intake_ledger.csv` are current
     (regenerate them with the export/consolidation scripts if a live round just ran).
2. **Token.** A Hugging Face token with **write** access to `onasafari/sf-promises`
   must be present in the environment as `HF_TOKEN`. The script reads the token
   from the environment only — it is never inlined, prompted for, or stored in the
   repo. In Obvious the value lives in the `HF_TOKEN` secret; inject it into the
   shell session before running the upload.
3. **Dependencies.** The dry-run path needs only the Python standard library. The
   real upload additionally needs `huggingface_hub` (`pip install huggingface_hub`).
   No network access is required for the dry-run.

## Dry-run (no token, no network)

Stage and validate every config/split locally:

```bash
python scripts/upload_to_huggingface.py --validate-only \
    --staging-dir /tmp/hf_sf_promises_dataset
```

This stages `data/commitments/train.csv`, `data/standardized_16col/train.csv`,
`data/quarantined/train.csv`, `data/intake_ledger/train.csv`, the root convenience
files (`promises.csv`, `promises.json`, `promises.sqlite`, `SCHEMA.json`,
`data_summary.json`), and the dataset card (`README.md`), then asserts:

- every split exists with the expected column count,
- row counts reconcile against the live export — commitments and quarantined
  counts against `docs/data.json`, the 16-column split against
  `data/sf_promises_master.csv`, and the intake ledger against its CSV.

Exit code 0 and the "Validate-only mode complete" line mean the staged dataset is
consistent. Do not upload from a failed dry-run.

## Real upload

```bash
export HF_TOKEN="<write token>"   # from the secret store; never commit this line
python scripts/upload_to_huggingface.py --staging-dir /tmp/hf_sf_promises_dataset
```

Without `HF_TOKEN` set the script exits with a clear error before touching the
network — that is the expected offline failure mode. With the token present it
uploads the staged folder to the dataset repository and prints the live URL:
`https://huggingface.co/datasets/onasafari/sf-promises`.

## Dataset target

- **Repo:** `onasafari/sf-promises` (dataset, hardcoded as `REPO_ID` in the script).
- **Configs:** `default` / `commitments`, `standardized_16col`, `quarantined`,
  `intake_ledger` — each reading an isolated split under `data/` so the HF Dataset
  Viewer never mixes schemas.
- After upload, spot-check the viewer renders all configs and that row counts on
  the Hub match the dry-run output.

## Offline tests

`tests/test_hf_dataset.py` runs the dry-run end-to-end and the token-absent
failure path with no network access:

```bash
pytest tests/test_hf_dataset.py
```

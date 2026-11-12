Here are the terminal commands to cleanly isolate your v1 files into an `archive/` folder and automate the renaming/path adjustments for your v2 codebase.

### 1. Archive the v1 Legacy Files

Run this in your container terminal (`root@8a849214cacf:/srv/repos/sf-promises#`) to move v1 files out of the active namespace while keeping them safe for hackathon reference:

```bash
# Create the archive directory structure
mkdir -p archive/src archive/tests

# Move v1 specific implementation and test files safely
mv src/extract.py archive/src/
mv src/checks.py archive/src/
mv src/arbitrator.py archive/src/
mv src/relevance.py archive/src/
mv src/schema.sql archive/src/

mv tests/test_checks.py archive/tests/

```

---

### 2. Streamline & Clean Up v2 Naming via `sed` and Shell Commands

Since you have many `v2_*` prefixes (`src/v2_discovery.py`, `src/v2_extract.py`, etc.), you can use `sed` to update module cross-references, clean up file headers, and point imports to standard clean names if needed.

#### A. Strip the `v2_` prefix internally or update cross-imports

If your files reference each other using `from src.v2_model import ...`, but you want to ensure clean module resolution, run this `sed` command across your python files to normalize paths and imports:

```bash
# Update internal imports across all src files to handle clean references
find src/ -name "*.py" -type f -exec sed -i 's/from src\.v2_/from src./g' {} +
find src/ -name "*.py" -type f -exec sed -i 's/import v2_/import /g' {} +

```

#### B. Clean up test references to point to the active source modules

```bash
# Update test imports to align with the active src layout
find tests/ -name "*.py" -type f -exec sed -i 's/from src\.v2_/from src./g' {} +

```

#### C. Set up the Demo / Candidate Promotion Hook

To automate promoting your candidate export data to the live demo preview without manual copying, add this handy alias or short script to your workspace:

```bash
cat << 'EOF' > promote_demo.sh
#!/bin/bash
if [ -f "data/data.candidate.json" ]; then
    cp data/data.candidate.json docs/data.json
    echo "[+] Promoted data.candidate.json to docs/data.json successfully!"
else
    echo "[-] Error: data/data.candidate.json not found. Run the backfill first."
fi
EOF
chmod +x promote_demo.sh

```

Now, whenever you want to test your v2 candidate results inside the live `docs/` static demo preview, you just run `./promote_demo.sh`!

---

### 3. Archil Sandbox & Disk Cleanup

#### A. Deprecate & Delete Unmounted/Stale Sandboxes
The following stopped sandboxes were created without disk mounts and should be deleted to keep the Archil account clean:
- `01a1cc58-088b-779c-831a-a8710de837ad` (`sf-promises-v2-template`)
- `01a1ccce-3dd3-7c3e-b7e2-1219d264594e` (`sf-promises-clean-a9df37e5`)

Keep or update `sf-promises-golden` (`01a1cbee-e36f-7872-8b6e-d42f1a13a5a5`) as the single golden template mounted with disk `dsk-000000000018f6e1` at `/mnt/archil`.

#### B. Clean Stale Disk Delegations
Ensure `dsk-000000000018f6e1` has no orphaned checkout delegations before forking worker VMs:
```python
for d in disk.list_delegations():
    if d.is_orphaned:
        disk.revoke_delegation(d)
```


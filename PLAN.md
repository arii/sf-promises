You will review this document and then create a file called PROGRESS_REPORT.md which will have -[ ] check boxes that you will mark -[x] after each task is completed.  You will review this document to create the list of steps you need to hav einthe progress report and you will have verificiation steps to make sure it is complete.  


We are making V2 of this project.  The hackathon is over but since we still have access to archil vm and keenable we will work to improve the limitations from the current version.  


# SF Promises v2: Swarm-First Architecture & Rebuild Guide

## 1. Executive Summary & v2 Design Principles

SF Promises v1 relied on pre-cached planning documents, fragile single-pass extraction, and a binary (`KEPT` / `BROKEN`) schema. That caused six systemic issues in the live dataset:
1. **Retrospective Quote Extraction:** Pulling backward-looking news retrospectives ("X opened in 2019") and mislabeling them as forward-looking promises.
2. **Temporal Collapse ("The Whole Foods Bug"):** Missing post-delivery reversals, closures, or suspensions (e.g., Trinity Whole Foods opening in 2022 and closing in 2023).
3. **Impossible Future Verdicts:** Marking promises with future deadlines (e.g., Joe Lacob's 2028 WNBA championship guarantee) as `KEPT`.
4. **Category & Geocode Hallucinations:** Misassigning neighborhoods and civic topics (e.g., mapping Care Not Cash to Police Oversight, or Parkmerced to Treasure Island).
5. **Entity Confusion:** Mixing up spokespeople, contractors, and regulators with the primary promising entity.
6. **Duplicate & Fragmented Promises:** Splitting single projects (like the Central Subway or the 2004 Homelessness Plan) into multiple disconnected records.

### The v2 Architecture
v2 is a **clean-slate rebuild** designed to run autonomously inside your **Archil Persistent Sandboxes**[cite: 1, 2, 3], orchestrated by a deterministic **LangGraph State Machine**, and powered by your **$1,000 Keenable Search API credit pool**.
* **Zero-Cost Infrastructure:** Uses your 100,000 free Archil vCPU-hours, 400,000 GiB-hours, and 10,000,000 serverless tool calls.
* **True VM Swarm Isolation:** Uses Archil's `sandbox.fork()` to give every promise audit worker its own isolated Linux microVM for downloading PDFs, running `pdfplumber`, and executing deterministic `pytest` checks without locking SQLite or polluting context windows.
* **Two-Phase Temporal Search:** Uses Keenable's `published_before` and `published_after` filters to separate **Origin Discovery ($T_0$)**, **Initial Delivery ($T_1$)**, and **Current Survival ($T_{now}$)**.

---

## 2. System Topology: The Hierarchical LangGraph Swarm

Instead of free-form chatting agents, v2 uses a **Two-Level Deterministic State Machine**:

```text
================================================================================
LEVEL 1: DISCOVERY & DEDUPLICATION GRAPH (Runs in Golden Master Sandbox)
================================================================================
[Seed Targets: Mayors, Agencies, Major Corps (1996–2026)]
       │
       ▼
[Keenable Origin Harvester] ──► Queries contemporaneous $T_0$ pledges & permits
       │
       ▼
[Canonical Deduplicator]    ──► Merges duplicate claims into canonical IDs
       │                        Normalizes Entity, Sector Enum, & SF Neighborhood
       ▼
[LangGraph Send() Fan-Out]  ──► Calls `golden_vm.fork()` per canonical promise
       │
=======┼========================================================================
LEVEL 2: PER-PROMISE VERIFICATION STATE MACHINE (Runs across N Forked VMs)
=======┼========================================================================
       ├──► [Worker VM #1: Promise P01]
       ├──► [Worker VM #2: Promise P02]
       └──► [Worker VM #N: Promise P_N]
                 │
                 ├─► 1. Origin_Validator_Node (Keenable `published_before: T0 + 30d`)
                 │      Ensures quote is genuinely forward-looking at $T_0$.
                 │
                 ├─► 2. Delivery_Scout_Node   (Keenable `T0` -> `Deadline + 6mo`)
                 │      Checks Tier 1 (Gov/DBI/SFMTA) + Tier 2 (Local News) for delivery.
                 │      Parses heavy PDFs inside the forked Archil VM via `pdfplumber`.
                 │
                 ├─► 3. Survival_Scout_Node   (Keenable `Delivery` -> `2026-11-11`)
                 │      Queries canary signals ("closed", "shuttered", "suspended", "halted").
                 │
                 ├─► 4. Structured_Extractor  (LLM w/ strict Pydantic schema)
                 │      Populates timeline milestones, metrics, and citations.
                 │
                 ├─► 5. VM_Deterministic_Gate (`src/checks.py` + `src/arbitrator.py`)
                 │      Pure Python verification inside the VM.
                 │      ├── PASS ──► Commit to SQLite & destroy VM fork
                 │      └── FAIL (Contradiction/Date Error & retry < 2)
                 │            └──► 6. Targeted_Resolver_Node ──► Loops to Node 4




Upgraded Data Model & Deterministic Schema (src/schema.sql)
Replace the v1 binary schema with a lifecycle-aware schema that enforces strict enums and tracks both initial delivery and current operational status.


```sql
-- src/schema.sql
CREATE TABLE IF NOT EXISTS promises (
    promise_id TEXT PRIMARY KEY,
    canonical_slug TEXT UNIQUE NOT NULL,       -- Deduplication key: e.g., "whole-foods-trinity-2022"
    
    -- Normalized Entity & Classification (Fixes Bugs C & E)
    entity_name TEXT NOT NULL,                 -- Canonical organization/leader (never a spokesperson)
    entity_type TEXT CHECK(entity_type IN (
        'Mayor / Executive', 'City Agency', 'Board of Supervisors', 
        'State Regulator', 'Private Corporation', 'Sports Franchise', 'Developer'
    )) NOT NULL,
    sector TEXT CHECK(sector IN (
        'Housing & Land Use', 'Transit & Streets', 'Homelessness & Behavioral Health',
        'Public Safety & Justice', 'Energy & Infrastructure', 'Autonomous Vehicles',
        'Parks & Recreation', 'Sports, Culture & Retail', 'Governance & Finance'
    )) NOT NULL,
    neighborhood TEXT NOT NULL,                -- Validated against strict SF Neighborhood list
    
    -- Forward-Looking Origin Claim (Fixes Bug B)
    promise_headline TEXT NOT NULL,
    verbatim_quote TEXT NOT NULL,
    quote_source_url TEXT NOT NULL,
    quote_published_date TEXT NOT NULL,        -- Must be <= date_promised + 30 days
    date_promised TEXT NOT NULL,               -- ISO YYYY-MM-DD
    date_deadline TEXT NOT NULL,               -- ISO YYYY-MM-DD
    target_metric TEXT,                        -- e.g., "3,000 supportive housing units"
    
    -- Lifecycle & Temporal States (Fixes Bugs A & F)
    initial_delivery TEXT CHECK(initial_delivery IN (
        'DELIVERED_ON_TIME', 'DELIVERED_LATE', 'PARTIALLY_DELIVERED', 
        'NOT_DELIVERED', 'PENDING_FUTURE_DEADLINE'
    )) NOT NULL,
    current_survival TEXT CHECK(current_survival IN (
        'ACTIVE_OPERATIONAL', 'SHUTTERED_OR_CLOSED', 'REVOKED_OR_HALTED', 
        'SUPERSEDED', 'NOT_YET_OPEN'
    )) NOT NULL,
    
    -- Final Computed Verdict (Computed deterministically by arbitrator.py, NEVER by LLM)
    verdict TEXT CHECK(verdict IN (
        'KEPT',                 -- Delivered on time & still active
        'KEPT_THEN_REVERSED',   -- Delivered, later closed/revoked (e.g., Whole Foods, 2004 Marriages)
        'DELAYED_OR_PARTIAL',   -- Delivered significantly late or scaled back (e.g., Central Subway)
        'BROKEN',               -- Missed deadline & never delivered, or abandoned
        'IN_PROGRESS'           -- Deadline is in the future (> 2026-11-11) or active phased build
    )) NOT NULL,
    
    confidence_score REAL NOT NULL,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_ledger (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    phase TEXT CHECK(phase IN ('ORIGIN', 'DELIVERY', 'SURVIVAL')) NOT NULL,
    source_tier TEXT CHECK(source_tier IN ('TIER1_GOV', 'TIER2_NEWS', 'TIER3_CANARY')) NOT NULL,
    url TEXT NOT NULL,
    published_date TEXT,
    extracted_fact TEXT NOT NULL,
    verbatim_snippet TEXT NOT NULL
);
```



The 6 Deterministic Gates (src/checks.py & src/arbitrator.py)In v2, the LLM never chooses the final verdict or invents a neighborhood name. The LLM populates structured facts, and src/checks.py + src/arbitrator.py enforce these six hard Python gates inside the Archil VM:   

Gate 1: Forward-Looking Claim Check (Eliminates Retrospective Quotes)

```python3
from datetime import date

def check_forward_looking_quote(
    date_promised: date,
    quote_published_date: date,
    verbatim_quote: str
) -> list[str]:
    errors = []
    # 1. Source document cannot be a retrospective written years after the promise
    if (quote_published_date - date_promised).days > 45:
        errors.append(
            f"Retrospective source rejected: quote published on {quote_published_date} "
            f"is >45 days after promise date {date_promised}. Search with published_before={date_promised}."
        )
    # 2. Reject retrospective critique phrasing
    retrospective_red_flags = [
        "didn't last long", "failed to", "had promised", "pledged in 20",
        "was originally scheduled", "sold out all", "opened with"
    ]
    lower_q = verbatim_quote.lower()
    for phrase in retrospective_red_flags:
        if phrase in lower_q:
            errors.append(f"Quote contains retrospective phrasing ('{phrase}'). Find original T0 pledge.")
    return errors
```

Gate 2: Temporal Arithmetic & Future Deadline Gate (Eliminates Lacob 2028 = KEPT)


```python3
TODAY = date(2026, 11, 11)

def compute_deterministic_verdict(
    date_deadline: date,
    initial_delivery: str,
    current_survival: str,
    explicitly_abandoned: bool = False
) -> str:
    # Future deadlines cannot be BROKEN (unless explicitly cancelled) or KEPT (unless already achieved & verified)
    if date_deadline > TODAY:
        if explicitly_abandoned:
            return "BROKEN"
        if initial_delivery == "DELIVERED_ON_TIME" and current_survival == "ACTIVE_OPERATIONAL":
            return "KEPT"
        return "IN_PROGRESS"

    # Past deadlines
    if initial_delivery == "NOT_DELIVERED":
        return "BROKEN"
    if initial_delivery in ("DELIVERED_ON_TIME", "DELIVERED_LATE", "PARTIALLY_DELIVERED"):
        if current_survival in ("SHUTTERED_OR_CLOSED", "REVOKED_OR_HALTED"):
            return "KEPT_THEN_REVERSED"
        if initial_delivery in ("DELIVERED_LATE", "PARTIALLY_DELIVERED"):
            return "DELAYED_OR_PARTIAL"
        return "KEPT"
    return "IN_PROGRESS"
```

Gate 3: Strict SF Geography & Sector Dictionary (Eliminates Hallucinated Titles)

```python3
VALID_SF_LOCATIONS = {
    "Citywide", "Mid-Market & Civic Center", "Tenderloin", "SoMa", "Mission Bay & Mission Rock",
    "Treasure Island", "Parkmerced", "Pier 70 & Dogpatch", "Chinatown & North Beach",
    "Golden Gate Park", "The Embarcadero", "Union Square & Financial District",
    "Twin Peaks", "Haight-Ashbury", "Presidio & Doyle Drive", "Bayview-Hunters Point",
    "Regional / Northern California"
}

def check_geography_and_entity(neighborhood: str, entity_name: str, quote: str) -> list[str]:
    errors = []
    if neighborhood not in VALID_SF_LOCATIONS:
        errors.append(f"Invalid neighborhood '{neighborhood}'. Must be one of {VALID_SF_LOCATIONS}.")
    if "spokesman" in entity_name.lower() or "spokesperson" in entity_name.lower():
        errors.append(f"Entity '{entity_name}' is a spokesperson. Use the parent organization.")
    if neighborhood == "Treasure Island" and "parkmerced" in quote.lower():
        errors.append("Geographic mismatch: Quote is about Parkmerced, not Treasure Island.")
    return errors
```



Gate 4: Tiered Evidence Rule (Allows Canary Signals Without Citing Unverified Rumors)Rule: A promise cannot be marked KEPT, BROKEN, or KEPT_THEN_REVERSED using only TIER3_CANARY sources (Reddit, social media, blogs).If the Survival Scout finds a Tier 3 signal (e.g., Reddit thread saying a store closed), checks.py returns an error forcing Targeted_Resolver_Node to find at least one corroborating TIER1_GOV or TIER2_NEWS document before locking the verdict. 



Step-by-Step Setup in Archil Console & CLIPhase 1: Provision the "Golden Master" Sandbox in ArchilOpen console.archil.com/sandboxes and click + Create your first Sandbox.   Configure the instance:   Sandbox Name: sf-promises-golden   Base Image: ubuntu:24.04 (or ubuntu:26.04)   Region: AWS N. Virginia (us-east-1)   Size: Large (4 vCPU · 8 GiB) — gives plenty of memory to run the LangGraph coordinator while spawning lightweight 1-vCPU worker forks.   Environment Variables:   ARCHIL_API_KEY=<your_archil_api_key>[cite: 2]KEENABLE_API_KEY=<your_keenable_1000_credit_key>OPENROUTER_API_KEY=<your_openrouter_or_nebius_key>PYTHONUNBUFFERED=1Click Create Sandbox.  

 Phase 2: Bootstrap the Environment Inside the SandboxSSH or open the web terminal into sf-promises-golden and run:  

```bash
# 1. Install system dependencies & persistent workspace tools
sudo apt-get update && sudo apt-get install -y \
    git curl jq ripgrep tmux sqlite3 \
    python3-pip python3-venv build-essential poppler-utils

# 2. Clone repo into persistent storage (/workspace)
mkdir -p /workspace
cd /workspace
git clone [https://github.com/arii/sf-promises.git](https://github.com/arii/sf-promises.git)
cd sf-promises

# 3. Create virtual environment and install v2 swarm stack
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install \
    archil \
    langgraph \
    langchain-core \
    langchain-openai \
    pydantic \
    httpx \
    pdfplumber \
    pytest
```
. Core v2 Implementation Blueprint
Create these three modular files inside /workspace/sf-promises/src/ to replace the single-threaded pipeline.


A. Keenable Temporal Search Client (src/keenable_tools.py)

```python3
import os
import httpx
from typing import Optional

KEENABLE_API_KEY = os.environ["KEENABLE_API_KEY"]
BASE_URL = "[https://api.keenable.ai/v1](https://api.keenable.ai/v1)"
HEADERS = {"X-API-Key": KEENABLE_API_KEY, "Content-Type": "application/json"}

async def search_keenable(
    query: str,
    published_before: Optional[str] = None,
    published_after: Optional[str] = None,
    domains: Optional[list[str]] = None,
    num_results: int = 8
) -> list[dict]:
    """Executes time-bounded searches using the $1,000 Keenable credit pool."""
    scoped_query = query
    if domains:
        site_filter = " OR ".join(f"site:{d}" for d in domains)
        scoped_query = f"({scoped_query}) ({site_filter})"

    payload = {"query": scoped_query, "num_results": num_results}
    if published_before:
        payload["published_before"] = published_before
    if published_after:
        payload["published_after"] = published_after

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE_URL}/search", headers=HEADERS, json=payload)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def fetch_markdown_keenable(url: str) -> str:
    """Fetches clean page Markdown via Keenable to avoid raw HTML token bloat."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE_URL}/extract", headers=HEADERS, json={"url": url})
        resp.raise_for_status()
        return resp.json().get("markdown", "")[:15000]
```


. Three-Phase Temporal Search Strategy per PromiseEvery worker VM executes three distinct Keenable queries:Phase 1: Origin Query ($T_0$)query: "{entity}" "{topic_keywords}" ("pledged" OR "promised" OR "announced" OR "will open" OR "contract")published_before: "{promised_year}-12-31"Purpose: Finds the contemporaneous forward-looking commitment.Phase 2: Delivery Query ($T_1$)query: "{entity}" "{project_name}" ("opened" OR "completed" OR "launched" OR "failed" OR "delayed")published_after: "{date_promised}"published_before: "{deadline_year + 1}-12-31"domains: ["sfgov.org", "sfplanning.org", "sfmta.com", "sfstandard.com", "sfchronicle.com", "missionlocal.org"]Phase 3: Survival / Reversal Query ($T_{now}$)query: "{project_name}" ("closed" OR "shuttered" OR "suspended" OR "halted" OR "vacant" OR "paused")published_after: "{deadline_year}-01-01"published_before: "2026-11-11"Purpose: Catches Whole Foods closing in 2023, Cruise losing its CPUC permit in late 2023, or projects stalling after ribbon-cutting.


C. LangGraph + Archil VM Fork Orchestrator (src/swarm_runner.py)

```python3

import asyncio
import json
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from archil import AsyncArchilClient
from src.checks import check_forward_looking_quote, check_geography_and_entity
from src.arbitrator import compute_deterministic_verdict

archil_client = AsyncArchilClient()

async def run_in_forked_vm(golden_sandbox_id: str, script_cmd: str) -> dict:
    """Forks the Golden Sandbox VM, runs an isolated command, and cleans up."""
    golden = await archil_client.get_sandbox(golden_sandbox_id)
    worker_vm = await golden.fork()
    try:
        proc = await worker_vm.run(script_cmd)
        result = await proc.wait()
        return {"exit_code": result.exit_code, "stdout": result.stdout, "stderr": result.stderr}
    finally:
        await worker_vm.delete()

async def vm_verification_node(state: dict) -> dict:
    """Writes extracted JSON into a forked Archil VM and runs pytest + checks.py."""
    payload_str = json.dumps(state["candidate_record"])
    cmd = f"python3 -m src.verify_candidate --json '{payload_str}'"
    res = await run_in_forked_vm(state["golden_sandbox_id"], cmd)
    
    if res["exit_code"] == 0:
        return {"check_errors": [], "verified": True}
    else:
        return {
            "check_errors": res["stdout"].splitlines(),
            "retry_count": state.get("retry_count", 0) + 1,
            "verified": False
        }
```


7. Clean-Slate Collection & Backfill Plan (Step-by-Step Execution)Instead of patching the corrupted docs/data.json strings by hand, run a clean 3-stage regeneration inside a persistent tmux session on your Archil VM:   Step 1: Canonical Seed Normalization (10 Minutes)Run a deduplication pass over your 62 existing topics to produce a clean seeds/canonical_targets.json (roughly ~55 unique promises after merging duplicates #4/#5 and #11/#12/#26):Each seed contains only: canonical_slug, entity_name, sector (from strict Enum), neighborhood (from strict SF dictionary), topic_summary, approx_promise_year, and approx_deadline_year.Step 2: Run the Swarm Audit in Batches of 10 Forked VMs (30–45 Minutes Unattended)Launch inside tmux on your Archil sandbox so you can close your laptop:



```bash
tmux new -s sf-promises-v2
source /workspace/sf-promises/.venv/bin/activate

# Run the LangGraph swarm across all canonical seeds with concurrency=10 forked VMs
python -m src.swarm_runner \
    --seeds seeds/canonical_targets.json \
    --concurrency 10 \
    --db data/promises_v2.db \
    --export docs/data.json \
    2>&1 | tee swarm_run.log
```


Step 3: Run the Automated Quality Gate Suite (tests/verify_demo.py)Add these five assertions to tests/test_checks.py so CI/CD refuses to export docs/data.json if any v1 bug regresses:   assert_no_future_kept_unverified(): Ensures no promise with date_deadline > 2026-11-11 is marked KEPT unless explicitly verified complete.assert_forward_looking_quotes(): Ensures quote_published_date <= date_promised + 45 days for 100% of records.assert_valid_taxonomy(): Ensures every sector and neighborhood matches the strict Enum sets.assert_unique_canonical_slugs(): Prevents duplicate extraction of the same policy/project.assert_known_canary_cases():Whole Foods Mid-Market (#36) must resolve to KEPT_THEN_REVERSED.Joe Lacob WNBA Championship (#45) must resolve to IN_PROGRESS.Ed Lee 2011 No-Run Pledge (#8) must resolve to BROKEN.Central Subway (#11/#12) must resolve to DELAYED_OR_PARTIAL (or BROKEN against original 2018 contract, with 2022 completion noted in current_survival).Step 4: Update Frontend Badges in docs/app.js & docs/styles.css[cite: 4]   Add support for the two new high-signal status badges in docs/app.js[cite: 4]:KEPT_THEN_REVERSED → Render as "KEPT → LATER CLOSED / REVERSED" (Amber/Purple badge).DELAYED_OR_PARTIAL → Render as "DELIVERED LATE / PARTIAL" (Yellow/Orange badge).Commit the updated docs/data.json and docs/data.js[cite: 4] directly from the Archil sandbox to GitHub to update arii.github.io/sf-promises automatically.

To equip your coding agent (Claude Code, Codex, Cursor, or your custom runner) inside the sf-promises workspace and your Archil sandbox, install these specific npx skills packages (requires Node.js 22.20+).1. Official Stack Skills (Install in /workspace/sf-promises)These map directly to the v2 architecture (LangGraph state machines, Remotion video pipeline in video/, and headless browser verification in docs/capture_screenshots.js):   LangGraph & Deep Agents (langchain-ai/langchain-skills):
Teaches your agent current LangGraph StateGraph, Send() fan-out, and checkpointing syntax so it doesn't write deprecated LangChain boilerplate.

```
npx skills add langchain-ai/langchain-skills --skill langgraph-fundamentals --skill langgraph-persistence --skill deep-agents-memory -y
```


Remotion Video Pipeline (remotion-dev/skills):
Covers video/src/PromisesVideo.tsx and headless rendering (remotion-markup, remotion-render, remotion-docs)
Playwright / Headless Verification (microsoft/playwright-cli):
For running docs/capture_screenshots.js, video/record_site.js, and tests/verify_demo.py inside the sandbox.   
Spec-Driven & Test-First Workflows (addyosmani/agent-skills):
Provides /spec, /test, and /review workflows that pair cleanly with your PRD.md and pytest verification gates.
Skill Discovery (vercel-labs/skills@find-skills):
Allows your coding agent to search skills.sh autonomously when it hits a new library during the weekend hackathon

```bash

npx skills add remotion-dev/skills -y
npx skills add microsoft/playwright-cli -y
npx skills add addyosmani/agent-skills -y
npx skills add vercel-labs/skills@find-skills -g -y
```

2. Scaffold 2 Local Skills (npx skills init) for Archil & Keenable
Because Archil VM Forking and Keenable Temporal Search are specialized APIs, coding agents will hallucinate their SDK methods unless given explicit SKILL.md instructions. Scaffold both locally so your swarm and coding agents use them deterministically:

```
# 1. Create a local skill for Archil Sandbox VM Forking
npx skills init archil-vm-swarm

# 2. Create a local skill for Keenable Temporal Search + Tiered Evidence
npx skills init keenable-temporal-audit
```


What to put in archil-vm-swarm/SKILL.md:When to trigger: Whenever executing untrusted code, parsing PDFs with pdfplumber, or running parallel pytest checks.   Core Pattern: Always use worker = await golden_sandbox.fork(), run commands via proc = await worker.run(...), await proc.wait(), and always wrap in try...finally: await worker.delete()


What to put in keenable-temporal-audit/SKILL.md:When to trigger: Whenever searching or verifying facts for a promise.Core Pattern: Enforce the 3-Phase Temporal Search against [https://api.keenable.ai/v1/search](https://api.keenable.ai/v1/search) using published_before and published_after (Origin $T_0$, Delivery $T_1$, and Survival $T_{now}$), and never cite Tier 3 canary sources without a corroborating Tier 1/2 link.


One-Shot Bootstrap Script for Your Archil Sandbox
Run this inside /workspace/sf-promises on your Golden Sandbox so every forked VM inherits the skills and lockfile (skills-lock.json):


```
# Install project skills & lock them for CI/forked VMs
npx skills@latest add langchain-ai/langchain-skills --skill langgraph-fundamentals --skill langgraph-persistence -y
npx skills@latest add remotion-dev/skills -y
npx skills@latest add microsoft/playwright-cli -y
npx skills@latest add addyosmani/agent-skills -y

# Verify installed skills
npx skills list
```


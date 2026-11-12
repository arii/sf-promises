# SF Promises — Architecture Status & Engineering Roadmap

**System Status:** Production Ready · 54 Published Commitments · 13 Quarantined Checks · 192/192 Unit Tests Green · Impeccable Design Bar: 0 Anti-Patterns

---

## 1. System Overview

SF Promises is an open-source civic verification pipeline that tracks public commitments across San Francisco — spanning City Hall, SFO International Airport, transit agencies, sports franchises, and neighborhood housing developments. 

Every commitment is verified against cryptographically archived primary sources using deterministic Python rules (domain allowlists, SHA-256 byte-level hashes, exact quote substring matching, and temporal bounds), with zero LLM model calls in the Arbitrator decision path.

### Core Architecture Highlights
- **Deterministic Arbitration:** 7 rigorous checks executed strictly in Python code (`src/checks.py`, `src/arbitrator.py`).
- **Sandboxed Agent Isolation:** Advocate agents (Kept and Broken) run in isolated workspaces with strictly partitioned staging files (`staging/kept_<id>.json`, `staging/broken_<id>.json`), mathematically prevented from cross-contaminating evidence.
- **Keenable 3-Phase Temporal Discovery:** Origin ($T_0$), Delivery ($T_1$), and Survival ($T_{now}$) searches ensure claims reflect full lifecycle durability rather than unverified announcement press releases.
- **Editorial Promise Explorer:** High-craft user interface featuring ranked editorial cards, compact directory table view, instant search, and complete cryptographic inspect modals.

---

## 2. Citywide Scope & SFO Integration

The tracked commitments reflect the full geographic and civic spectrum of San Francisco:
- **Airport & Airlines (SFO):** Official municipal airfield commitments including the $51M Runway 28L safety realignment (accelerated completion ahead of July 1 deadline), the $2.4B LEED Platinum Harvey Milk Terminal 1 modernization (25 operational gates), United Airlines commercial SAF delivery infrastructure, and Alaska Airlines flagship lounge relocation.
- **Civic Governance:** Mayoral and Board of Supervisors initiatives (Mayor Lurie's 24/7 Crisis Stabilization Center at 822 Geary St, the Fentanyl State of Emergency Ordinance, Care Not Cash, 425 officer hiring goals).
- **Transit & Streets:** Vision Zero traffic safety, Car-Free JFK Promenade in Golden Gate Park (Prop J), Waymo and Zoox commercial robotaxi services, and Central Subway capital delivery.
- **Housing & Neighborhoods:** Mission Rock 40% affordable homes, Embarcadero Navigation Center, 82,200 Housing Element state mandate, and Mid-Market retail recovery.
- **Sports & Culture:** Golden State Valkyries sell-out inaugural season at Chase Center, Joe Lacob's 5-year WNBA championship target, and Dead & Company career farewell tour.

---

## 3. Engineering Roadmap & Next Revisions

The following forward-looking initiatives represent the next development milestones for SF Promises:

### 3.1 Automated Durability Polling (Continuous Lifecycle Monitoring)
- **Challenge:** Under the current rubric, a verified facility opening (such as the 822 Geary Crisis Center or the Mid-Market Whole Foods) receives a point-in-time verdict. If the facility later suspends operations or closes, human review is currently required to re-open the case.
- **Roadmap:** Implement an automated cron daemon that schedules 90-day survival re-checks for all `kept` promises, executing Keenable queries for operational suspensions, lease forfeitures, or Board of Supervisors inquiries.

### 3.2 Formal Absence Proofing for Negative Commitments
- **Challenge:** Promises phrased as "we will never do X again" (e.g. touring pledges, fossil-fuel financing bans) require proving an absence, which challenges deterministic affirmative evidence standards.
- **Roadmap:** Formalize a statistical absence verification rubric that evaluates lack of contradicting public filings across specified regulatory windows.

### 3.3 Dynamic Allowlist Expansion via Granicus & Legistar Ingestion
- **Challenge:** Strict allowlisting avoids counterfeit evidence but occasionally excludes valid regional investigative reporting until mirrored in official filings.
- **Roadmap:** Build direct webhook listeners for San Francisco Board of Supervisors Legistar and Granicus meeting minutes, enabling zero-latency primary source ingestion.

### 3.4 Open Keenable CLI Pipeline Ingestion
- Use `python -m src.cli_search --topic "<topic>" --limit 5` to dynamically explore civic commitments, verify candidate URLs against allowlists, and generate initial candidate intake payloads.

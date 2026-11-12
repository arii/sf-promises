-- SQLite database schema. Enable foreign_keys on every connection.
CREATE TABLE IF NOT EXISTS candidates (
    promise_id TEXT PRIMARY KEY,
    canonical_slug TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS promises_pending (
    pending_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES candidates(promise_id),
    source_url TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    metadata_path TEXT NOT NULL,
    metadata_sha256 TEXT NOT NULL,
    proposal_json TEXT NOT NULL,
    loaded_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'quarantined')),
    quarantine_id INTEGER,
    FOREIGN KEY (quarantine_id, promise_id) REFERENCES quarantined(quarantine_id, promise_id),
    CHECK ((status IN ('pending', 'published') AND quarantine_id IS NULL) OR
           (status = 'quarantined' AND quarantine_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS promises (
    promise_id TEXT PRIMARY KEY REFERENCES candidates(promise_id),
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    sector TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    promise_text TEXT NOT NULL,
    date_promised TEXT NOT NULL,
    date_deadline TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_ledger (
    evidence_id INTEGER PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES candidates(promise_id),
    phase TEXT NOT NULL CHECK (phase IN ('ORIGIN', 'DELIVERY', 'SURVIVAL')),
    source_tier TEXT NOT NULL CHECK (source_tier IN ('TIER1_GOV', 'TIER2_NEWS', 'TIER3_CANARY')),
    url TEXT NOT NULL,
    published_date TEXT,
    local_source_path TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    verbatim_quote TEXT NOT NULL,
    quote_verified INTEGER NOT NULL CHECK (quote_verified IN (0, 1)),
    verification_record_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verifications (
    verification_id INTEGER PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES candidates(promise_id),
    evidence_id INTEGER REFERENCES evidence_ledger(evidence_id),
    check_type TEXT NOT NULL,
    passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
    reason TEXT NOT NULL,
    checked_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relevance_assessments (
    assessment_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES candidates(promise_id),
    input_json TEXT NOT NULL,
    real_promise INTEGER NOT NULL CHECK (real_promise BETWEEN 0 AND 2),
    measurable INTEGER NOT NULL CHECK (measurable BETWEEN 0 AND 2),
    sf_relevant INTEGER NOT NULL CHECK (sf_relevant BETWEEN 0 AND 2),
    interesting INTEGER NOT NULL CHECK (interesting BETWEEN 0 AND 2),
    total INTEGER NOT NULL CHECK (total = real_promise + measurable + sf_relevant + interesting),
    passed INTEGER NOT NULL CHECK (passed = (total >= 5 AND real_promise >= 1)),
    evaluated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verdicts (
    verdict_id INTEGER PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    verdict TEXT NOT NULL CHECK (verdict IN
        ('KEPT', 'KEPT_THEN_REVERSED', 'DELAYED_OR_PARTIAL', 'BROKEN', 'IN_PROGRESS')),
    reason TEXT NOT NULL,
    decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quarantined (
    quarantine_id INTEGER PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES candidates(promise_id),
    stage TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    candidate_payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (quarantine_id, promise_id)
);

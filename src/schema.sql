-- SF Promises Tracker SQLite Schema
-- Source: 02-technical-design.md & 16-observability-and-frontend.md

CREATE TABLE IF NOT EXISTS cities (
    city_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    timezone TEXT NOT NULL,
    meeting_body TEXT NOT NULL,
    minutes_source_type TEXT NOT NULL,
    minutes_url TEXT NOT NULL,
    transcript_url TEXT,
    speaker_roles TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('politician','company','sports_team','artist','official','other')),
    name TEXT NOT NULL,
    role TEXT,
    city_id TEXT NOT NULL REFERENCES cities(city_id)
);

CREATE TABLE IF NOT EXISTS promises (
    promise_id TEXT PRIMARY KEY,
    city_id TEXT NOT NULL REFERENCES cities(city_id),
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    promise_text TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','kept','in_progress','broken','stalled','undecided')),
    source_file_path TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS promises_pending (
    promise_id TEXT PRIMARY KEY,
    city_id TEXT NOT NULL REFERENCES cities(city_id),
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    promise_text TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','kept','in_progress','broken','stalled','undecided')),
    source_file_path TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    promise_id TEXT REFERENCES promises(promise_id),
    file_path TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    source_type TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS legistar_matters (
    matter_id INTEGER PRIMARY KEY,
    matter_guid TEXT NOT NULL,
    matter_file TEXT NOT NULL,
    matter_name TEXT NOT NULL,
    matter_title TEXT NOT NULL,
    matter_type TEXT NOT NULL,
    matter_status TEXT NOT NULL,
    matter_body_id INTEGER NOT NULL,
    matter_body TEXT NOT NULL,
    intro_date TEXT,
    agenda_date TEXT,
    passed_date TEXT,
    enactment_number TEXT,
    requester TEXT,
    source_file_path TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    advocate_role TEXT NOT NULL CHECK (advocate_role IN ('kept_advocate','broken_advocate')),
    claim_text TEXT NOT NULL,
    quote TEXT NOT NULL,
    quote_match TEXT NOT NULL CHECK (quote_match IN ('exact','close','none')),
    evidence_type TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    source_url TEXT NOT NULL,
    page_number INTEGER,
    evidence_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verifications (
    verification_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    evidence_id TEXT REFERENCES evidence(evidence_id),
    check_type TEXT NOT NULL CHECK (check_type IN ('authenticity_domain','authenticity_hash','authenticity_speaker','accuracy_quote','accuracy_date','accuracy_evidence','verdict_rubric')),
    passed INTEGER NOT NULL CHECK (passed IN (0,1)),
    reason TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    checked_by TEXT NOT NULL CHECK (checked_by IN ('kept_advocate','broken_advocate','arbitrator'))
);

CREATE TABLE IF NOT EXISTS verdicts (
    verdict_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    verdict TEXT NOT NULL CHECK (verdict IN ('kept','in_progress','broken','stalled','undecided')),
    reason TEXT NOT NULL,
    reading_used TEXT,
    decided_at TEXT NOT NULL,
    decided_by TEXT NOT NULL CHECK (decided_by IN ('arbitrator'))
);

CREATE TABLE IF NOT EXISTS relevance_checks (
    check_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    criterion TEXT NOT NULL CHECK (criterion IN ('real_promise','measurable','sf_relevant','interesting')),
    score INTEGER NOT NULL CHECK (score IN (0,1,2)),
    reason TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    checked_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outcome_evidence (
    outcome_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    external_id TEXT NOT NULL,
    source_dataset TEXT NOT NULL,
    measure TEXT NOT NULL,
    value_text TEXT NOT NULL,
    status TEXT,
    address TEXT,
    evidence_date TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quarantined (
    quarantine_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    reason TEXT NOT NULL,
    quarantined_at TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS change_log (
    log_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    change_date TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_file_path TEXT
);

CREATE TABLE IF NOT EXISTS test_cases (
    test_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL REFERENCES promises(promise_id),
    expected_verdict TEXT NOT NULL,
    expected_evidence TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    tests_what TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_runs (
    run_id TEXT PRIMARY KEY,
    run_at TEXT NOT NULL,
    run_by TEXT NOT NULL,
    total_tests INTEGER NOT NULL,
    passed_tests INTEGER NOT NULL,
    failed_tests INTEGER NOT NULL,
    blocked_tests INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS test_results (
    result_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES test_runs(run_id),
    test_id TEXT NOT NULL REFERENCES test_cases(test_id),
    actual_verdict TEXT NOT NULL,
    expected_verdict TEXT NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('pass','fail','blocked')),
    failure_reason TEXT,
    evidence_checked INTEGER NOT NULL,
    evidence_passed INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    promise_id TEXT,
    step TEXT NOT NULL CHECK (step IN ('setup','fetch','extract','relevance_2_5','kept_advocate','broken_advocate','arbitrate_checks','arbitrate_rubric','verdict_write','recheck','export','demo')),
    agent TEXT NOT NULL CHECK (agent IN ('setup_agent','fetcher_agent','extractor_agent','kept_advocate','broken_advocate','arbitrator','relevance_gate','demo_agent','test_agent')),
    sandbox TEXT NOT NULL CHECK (sandbox IN ('none','A','B','C','D','fetcher','extractor','demo','test')),
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pass','fail','blocked')),
    error_reason TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    promise_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending','fetching','extracting','advocating','arbitrating','published','quarantined')),
    event_count INTEGER NOT NULL DEFAULT 0,
    total_duration_ms INTEGER NOT NULL DEFAULT 0,
    last_step TEXT,
    last_error TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    lane TEXT,
    promise_id TEXT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_runs (
    agent_run_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    agent TEXT NOT NULL CHECK (agent IN ('setup_agent','fetcher_agent','extractor_agent','kept_advocate','broken_advocate','arbitrator','relevance_gate','demo_agent','test_agent')),
    sandbox TEXT NOT NULL CHECK (sandbox IN ('none','A','B','C','D','fetcher','extractor','demo','test')),
    lane TEXT,
    promise_id TEXT,
    input_file_path TEXT,
    output_file_path TEXT,
    search_queries TEXT NOT NULL DEFAULT '[]',
    urls_fetched TEXT NOT NULL DEFAULT '[]',
    evidence_count INTEGER NOT NULL DEFAULT 0,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pass','fail','blocked')),
    error_reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_relevance_promise ON relevance_checks(promise_id);
CREATE INDEX IF NOT EXISTS idx_promises_city ON promises(city_id);
CREATE INDEX IF NOT EXISTS idx_promises_status ON promises(status);
CREATE INDEX IF NOT EXISTS idx_evidence_promise ON evidence(promise_id);
CREATE INDEX IF NOT EXISTS idx_verifications_promise ON verifications(promise_id);
CREATE INDEX IF NOT EXISTS idx_legistar_passed ON legistar_matters(passed_date);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_events_promise ON events(promise_id);
CREATE INDEX IF NOT EXISTS idx_events_step ON events(step);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_traces_run ON traces(run_id);
CREATE INDEX IF NOT EXISTS idx_traces_promise ON traces(promise_id);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);

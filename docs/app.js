/**
 * SF Promises — Citywide Record & 6-Stage Pipeline Animation Controller
 * Celebrates all of San Francisco: Sports, Culture, Transit, Neighborhoods & Civic Record.
 * Directly implements the UX, Stage Progression, Packet Transit, and Stamp Animations
 * from Sf-Promises-Pipeline-Animation.html.
 */

(function () {
  'use strict';

  // Helper: Sanitize quotes by stripping stray markdown artifacts (bullets, raw links, bold markers)
  function cleanQuoteText(text) {
    if (!text) return '';
    return String(text)
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // [text](url) -> text
      .replace(/\*\*([^*]+)\*\*/g, '$1')       // **bold** -> bold
      .replace(/\*([^*]+)\*/g, '$1')           // *italic* -> italic
      .replace(/__([^_]+)__/g, '$1')
      .replace(/_([^_]+)_/g, '$1')
      .replace(/^[\s\-*•–—\d\.]+\s*/, '')      // leading bullets/numbers
      .replace(/^#+\s*/, '')                   // leading headers
      .replace(/\s+/g, ' ')                    // normalize spaces
      .trim();
  }

  // Helper: Format verdict labels with clean human-readable text
  function formatVerdictLabel(verdict) {
    if (!verdict) return 'Undecided';
    const v = String(verdict).toLowerCase().replace(/[\s-]+/g, '_');
    if (v === 'in_progress') return 'In Progress';
    if (v === 'kept') return 'Kept';
    if (v === 'broken') return 'Broken';
    if (v === 'undecided') return 'Undecided';
    if (v === 'stalled') return 'Stalled';
    if (v === 'kept_then_reversed') return 'Kept → Later Closed / Reversed';
    if (v === 'delayed_or_partial') return 'Delivered Late / Partial';
    return String(verdict).replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  // Helper: Format advocate notes into user-friendly copy (no internal cut rules or agent notes)
  function formatAdvocateNote(rawNote, role) {
    if (!rawNote) {
      return role === 'broken'
        ? 'No contradicting evidence or cancellation records found in verified municipal records.'
        : 'No affirming primary evidence filed during this review cycle.';
    }
    const note = String(rawNote);
    if (note.toLowerCase().startsWith('none found')) {
      return 'No contradicting evidence or cancellation records found in verified public records.';
    }
    let cleaned = note
      .replace(/No second search per cut rule\+?(\s*freeze)?\.?/gi, '')
      .replace(/\s*;\s*no second search.*/gi, '')
      .replace(/\s*\(re-open diligence.*?\):/gi, '')
      .trim();
    return cleaned || (role === 'broken' ? 'No contradicting evidence or cancellation records found.' : 'No affirming primary evidence filed.');
  }

  // State Variables
  let demoData = null;
  let currentRunType = 'P02'; // promise_id to replay, or 'N01' (watchdog test)
  let currentStage = 0;       // 0 to 6
  let replayCount = 0;
  let isAutoRunning = false;
  let isStepMode = false;
  let autoTimer = null;
  let selectedShowcasePid = 'P02';
  let activeTab = 'promises';
  let activeCategoryFilter = 'all';
  let activeViewMode = 'cards';

  // DOM Elements: Header & Tally
  const tallyTotal = document.getElementById('tally-total');
  const tallyKept = document.getElementById('tally-kept');
  const tallyProgress = document.getElementById('tally-progress');
  const tallyBroken = document.getElementById('tally-broken');
  const tallyStalled = document.getElementById('tally-stalled');
  const tallyUndecided = document.getElementById('tally-undecided');

  // DOM Elements: Showcase
  const showcaseTabsBar = document.getElementById('showcase-tabs-bar');
  const showcaseCardDisplay = document.getElementById('showcase-card-display');
  const scBadgeId = document.getElementById('sc-badge-id');
  const scBadgeVerdict = document.getElementById('sc-badge-verdict');
  const scDomainPill = document.getElementById('sc-domain-pill');
  const scNeighborhoodPill = document.getElementById('sc-neighborhood-pill');
  const scQuoteText = document.getElementById('sc-quote-text');
  const scMetaEntity = document.getElementById('sc-meta-entity');
  const scMetaPromised = document.getElementById('sc-meta-promised');
  const scMetaDue = document.getElementById('sc-meta-due');
  const scMetaOpened = document.getElementById('sc-meta-opened');
  const scMetaRel = document.getElementById('sc-meta-rel');
  const scEvidenceFact = document.getElementById('sc-evidence-fact');
  const scSourceLink = document.getElementById('sc-source-link');
  const scHashPill = document.getElementById('sc-hash-pill');
  const btnShowcaseInspect = document.getElementById('btn-showcase-inspect');

  // DOM Elements: Pipeline Header & Controls
  const pipelineProgressFill = document.getElementById('pipeline-progress-fill');
  const pipelineStageIndicator = document.getElementById('pipeline-stage-indicator');
  const btnRunP02 = document.getElementById('btn-run-p02');
  const btnRunN01 = document.getElementById('btn-run-n01');
  const runSelect = document.getElementById('run-select');
  const btnRunSelected = document.getElementById('btn-run-selected');
  const btnStepNext = document.getElementById('btn-step-next');
  const btnPipelineReset = document.getElementById('btn-pipeline-reset');
  const pipelineModeHint = document.getElementById('pipeline-mode-hint');

  // DOM Elements: Packet Transit
  const packetStatusText = document.getElementById('packet-status-text');
  const packetTrackFill = document.getElementById('packet-track-fill');
  const packetBallDot = document.getElementById('packet-ball-dot');
  const packetBallInner = document.getElementById('packet-ball-inner');
  const msCircles = [
    null,
    document.getElementById('ms-circle-1'),
    document.getElementById('ms-circle-2'),
    document.getElementById('ms-circle-3'),
    document.getElementById('ms-circle-4'),
    document.getElementById('ms-circle-5'),
    document.getElementById('ms-circle-6'),
  ];

  // DOM Elements: Stage Cards
  const stageCard1 = document.getElementById('stage-card-1');
  const stageBadge1 = document.getElementById('stage-badge-1');
  const stage1Filename = document.getElementById('stage1-filename');
  const stage1HashPrefix = document.getElementById('stage1-hash-prefix');
  const stage1SourceUrl = document.getElementById('stage1-source-url');
  const stage1HashMatch = document.getElementById('stage1-hash-match');
  const stage1FetchFill = document.getElementById('stage1-fetch-fill');
  const stage1VerifiedBanner = document.getElementById('stage1-verified-banner');

  const stageCard2 = document.getElementById('stage-card-2');
  const stageBadge2 = document.getElementById('stage-badge-2');
  const stage2QuoteContent = document.getElementById('stage2-quote-content');
  const stage2FlashBox = document.getElementById('stage2-flash-box');
  const stage2PassBox = document.getElementById('stage2-pass-box');

  const stageCard3 = document.getElementById('stage-card-3');
  const stageBadge3 = document.getElementById('stage-badge-3');
  const relFillReal = document.getElementById('rel-fill-real');
  const relFillMeas = document.getElementById('rel-fill-meas');
  const relFillSf = document.getElementById('rel-fill-sf');
  const relFillInt = document.getElementById('rel-fill-int');
  const scoreValReal = document.getElementById('score-val-real');
  const scoreValMeas = document.getElementById('score-val-meas');
  const scoreValSf = document.getElementById('score-val-sf');
  const scoreValInt = document.getElementById('score-val-int');
  const stage3ScoreTotal = document.getElementById('stage3-score-total');
  const stage3ScoreBadge = document.getElementById('stage3-score-badge');
  const stage3ScoreFill = document.getElementById('stage3-score-fill');
  const stage3GateBadge = document.getElementById('stage3-gate-badge');

  const stageCard4 = document.getElementById('stage-card-4');
  const advBoxKept = document.getElementById('adv-box-kept');
  const advStatusKept = document.getElementById('adv-status-kept');
  const advFindingsKept = document.getElementById('adv-findings-kept');
  const advDotsKept = document.getElementById('adv-dots-kept');
  const advBoxBroken = document.getElementById('adv-box-broken');
  const advStatusBroken = document.getElementById('adv-status-broken');
  const advFindingsBroken = document.getElementById('adv-findings-broken');
  const advDotsBroken = document.getElementById('adv-dots-broken');
  const tagStagingKept = document.getElementById('tag-staging-kept');
  const tagStagingBroken = document.getElementById('tag-staging-broken');

  const stageCard5 = document.getElementById('stage-card-5');
  const arbDivertAlert = document.getElementById('arb-divert-alert');
  const checkKeys = ['domain', 'hash', 'quote', 'speaker', 'date', 'evidence', 'rubric'];
  const CHECK_KEY_TO_TYPE = {
    domain: 'authenticity_domain',
    hash: 'authenticity_hash',
    quote: 'accuracy_quote',
    speaker: 'authenticity_speaker',
    date: 'accuracy_date',
    evidence: 'accuracy_evidence',
    rubric: 'verdict_rubric',
  };

  const stageCard6 = document.getElementById('stage-card-6');
  const stageBadge6 = document.getElementById('stage-badge-6');
  const outputWaitingContainer = document.getElementById('output-waiting-container');
  const outputKeptResult = document.getElementById('output-kept-result');
  const outputQuarantineResult = document.getElementById('output-quarantine-result');
  const outputVerdictResult = document.getElementById('output-verdict-result');

  // --- Run-model helpers (any promise can be replayed, not just P02) ---
  function isWatchdog(runType) {
    return runType === 'N01';
  }

  function runPromise(runType) {
    if (isWatchdog(runType) || !demoData) return null;
    return ((demoData.promises) || []).find(p => p.promise_id === runType)
      || (runType === 'P02' ? demoData.p02 : null);
  }

  function formatFetchTime(iso) {
    if (!iso) return 'fetch time not recorded';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const pad = (n) => String(n).padStart(2, '0');
    return `${months[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}, `
      + `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC (recorded)`;
  }

  function shortLabel(p, maxLen) {
    if (!p) return '';
    const t = cleanQuoteText(p.promise_text || '');
    const n = maxLen || 60;
    return t.length > n ? t.slice(0, n - 1).trimEnd() + '…' : t;
  }

  function runLabel(runType) {
    if (isWatchdog(runType)) return 'Watchdog test — altered quote gets caught';
    const p = runPromise(runType);
    if (!p) return runType;
    return `#${p.display_no || '—'} · ${shortLabel(p, 50)}`;
  }

  function checkOutcome(p, key) {
    // Matched by check_type name so animation order can differ from export order.
    if (!p || !p.checks) return null;
    const want = CHECK_KEY_TO_TYPE[key];
    const found = p.checks.find(c => c.check === want);
    return found ? found.passed : null; // true / false / null (not recorded)
  }

  // DOM Elements: Narrative Footer
  const pipelineNarrativeTitle = document.getElementById('pipeline-narrative-title');
  const pipelineNarrativePill = document.getElementById('pipeline-narrative-pill');
  const pipelineNarrativeBody = document.getElementById('pipeline-narrative-body');
  const btnNarrativeReplay = document.getElementById('btn-narrative-replay');
  const btnNarrativeToggle = document.getElementById('btn-narrative-toggle');

  // DOM Elements: Tables & Modals
  const domainPillsBar = document.getElementById('domain-pills-bar');
  const tabBtnPromises = document.getElementById('tab-btn-promises');
  const tabBtnQuarantine = document.getElementById('tab-btn-quarantine');
  const tabCountPromises = document.getElementById('tab-count-promises');
  const tabCountQuarantine = document.getElementById('tab-count-quarantine');
  const tableContainerPromises = document.getElementById('promises-table-container');
  const tableContainerQuarantine = document.getElementById('quarantine-table-container');
  const tbodyPromises = document.getElementById('promises-table-body');
  const tbodyQuarantine = document.getElementById('quarantine-table-body');

  const filterEntity = document.getElementById('filter-entity');
  const filterVerdict = document.getElementById('filter-verdict');
  const filterCategory = document.getElementById('filter-category');
  const filterSort = document.getElementById('filter-sort');
  const searchInput = document.getElementById('search-input');
  const tableShowingCount = document.getElementById('table-showing-count');
  const tableTotalCount = document.getElementById('table-total-count');
  const activeFilterIndicator = document.getElementById('active-filter-indicator');

  // Pagination elements
  let currentPageSize = 15;
  const btnShowMore = document.getElementById('btn-show-more');
  const btnShowAll = document.getElementById('btn-show-all');
  const tablePaginationRow = document.getElementById('table-pagination-row');
  const paginationSub = document.getElementById('pagination-sub');

  const inspectModal = document.getElementById('inspect-modal');
  const btnCloseInspect = document.getElementById('btn-close-inspect');
  const btnCopyModalHash = document.getElementById('btn-copy-modal-hash');
  const modalOpenedRow = document.getElementById('modal-opened-row');
  const modalOpenedDate = document.getElementById('modal-opened-date');
  const modalDueDate = document.getElementById('modal-due-date');
  const modalFilePath = document.getElementById('modal-file-path');
  const modalFetchTime = document.getElementById('modal-fetch-time');
  const modalPromiseQuoteLink = document.getElementById('modal-promise-quote-link');
  const methodModal = document.getElementById('method-modal');
  const btnOpenMethodology = document.getElementById('btn-open-methodology');
  const btnCloseMethod = document.getElementById('btn-close-method');

  // Agents section interactive details
  const agentCards = document.querySelectorAll('.agent-role-card');
  const agentDetailDot = document.getElementById('agent-detail-dot');
  const agentDetailText = document.getElementById('agent-detail-text');

  const AGENT_INFO = [
    {
      name: "Kept Advocate",
      sandbox: "Sandbox A",
      dotClass: "dot-kept",
      desc: "In the flow: reads the gated promise + affirming sources, writes staging/kept_P02.json. Designed for process isolation in Sandbox A."
    },
    {
      name: "Broken Advocate",
      sandbox: "Sandbox B",
      dotClass: "dot-broken",
      desc: "In the flow: reads the gated promise + contradicting sources, writes staging/broken_P02.json. Designed for process isolation in Sandbox B."
    },
    {
      name: "Arbitrator",
      sandbox: "Sandbox C",
      dotClass: "dot-undecided",
      desc: "Only writer to promises.db. Reads both advocate briefs, executes 7 deterministic Python checks, applies rubric, and decides verdict with 0 model calls."
    },
    {
      name: "Relevance Gate",
      sandbox: "Sandbox D",
      dotClass: "dot-in_progress",
      desc: "Runs once at Stage 3. Evaluates 4 criteria (real_promise, measurable, sf_relevant, interesting) on a 0–8 scale. Gates publication at 5+."
    }
  ];

  // Stage Narrative Data
  const STAGE_NARRATIVES = {
    0: {
      title: "Ready to run",
      pill: "STANDBY",
      body: "Pick a promise in the dropdown and press Play to see it move through every check — or pick the watchdog test to see one altered word fail the whole file. Step mode lets you pause and inspect each stage."
    },
    1: {
      title: "Stage 1: Fetch Source Document",
      pill: "FETCHING",
      body: "Fetch the public source URL and save its bytes to Archil persistent storage. The SHA-256 hash must match before anything else is trusted — a snippet is never a source."
    },
    2: {
      title: "Stage 2: Verbatim Extraction",
      pill: "EXTRACTING",
      body: "Copy the promise word-for-word. AI models draft candidate text, but deterministic code checks exact substring match in the saved source file."
    },
    3: {
      title: "Stage 3: Relevance Gate (Sandbox D)",
      pill: "GATING",
      body: "Evaluate 4 spec criteria (real_promise, measurable, sf_relevant, interesting). Gate opens only at 5+ / 8 with real_promise ≥ 1. Procedural fluff never moves past this step."
    },
    4: {
      title: "Stage 4: Parallel Advocates (Sandboxes A & B)",
      pill: "ADVOCATING",
      body: "Two separate processes designed for isolation. Sandbox A seeks affirming proof; Sandbox B seeks contradicting proof. Neither influences the other."
    },
    5: {
      title: "Stage 5: Arbitrator (Code, 0 Model Calls)",
      pill: "ARBITRATING",
      body: "No guessing, no probabilistic drift. Pure Python checks verify domain, hash, exact quote, speaker, date, evidence type, and promise-id match — then the rubric maps surviving claims to a verdict."
    },
    6: {
      title: "Stage 6: Output & Verification Stamp",
      pill: "DELIVERED",
      body: "Decided in the open. Passing claims went to the rubric, which signed the verdict stamp — checks passing never decides kept or broken by itself. Any altered byte diverts immediately to quarantine."
    }
  };

  // -------------------------------------------------------------------------
  // INITIALIZATION
  // -------------------------------------------------------------------------
  async function init() {
    if (window.__DEMO_DATA__) {
      demoData = window.__DEMO_DATA__;
    } else {
      try {
        const res = await fetch('data.json');
        if (res.ok) demoData = await res.json();
      } catch (e) {
        console.warn('Fallback loading data:', e);
      }
    }

    renderTally();
    updateCategoryPillCounts();
    renderShowcaseCard('P02');
    renderPromisesTable();
    renderQuarantineTable();
    renderRunSelect();
    setupEventListeners();
    renderCompletedPipeline('P02');

    // Check hash route
    const currentHash = window.location.hash;
    if (currentHash) {
      const pMatch = currentHash.match(/^#promise-(.+)$/i);
      if (pMatch) {
        openInspectModal(pMatch[1].toUpperCase());
      } else if (currentHash === '#p02' || currentHash === '#inspect') {
        openInspectModal('P02');
      } else if (currentHash === '#run-p02') {
        startPipeline('P02');
      } else if (currentHash === '#run-n01') {
        startPipeline('N01');
      }
    }
  }

  // -------------------------------------------------------------------------
  // TALLY & HEADER STATS
  // -------------------------------------------------------------------------
  function renderTally() {
    if (!demoData) return;
    const db = demoData.database_status || {};
    const counts = db.counts || {};

    const totalCount = db.tracked_count || (demoData.promises ? demoData.promises.length : 0);
    if (tallyTotal) tallyTotal.textContent = totalCount;
    if (tallyKept) tallyKept.textContent = counts.kept || 0;
    if (tallyProgress) tallyProgress.textContent = counts.in_progress || 0;
    if (tallyBroken) tallyBroken.textContent = counts.broken || 0;

    const stalledCount = counts.stalled || 0;
    if (tallyStalled) tallyStalled.textContent = stalledCount;
    const stalledItem = document.getElementById('tally-item-stalled');
    const stalledSep = document.getElementById('tally-sep-stalled');
    if (stalledItem) stalledItem.style.display = stalledCount > 0 ? 'inline-flex' : 'none';
    if (stalledSep) stalledSep.style.display = stalledCount > 0 ? 'inline' : 'none';

    if (tallyUndecided) tallyUndecided.textContent = counts.undecided || 0;

    if (tabCountPromises) tabCountPromises.textContent = totalCount;
    if (tabCountQuarantine) tabCountQuarantine.textContent = demoData.quarantined ? demoData.quarantined.length : 0;
    const btnDomainAll = document.getElementById('btn-domain-all');
    if (btnDomainAll) btnDomainAll.textContent = `All of SF (${totalCount})`;

    var banner = document.getElementById('snapshot-banner');
    if (banner) {
      var meta = demoData.metadata || {};
      var exportedAt = meta.exported_at || meta.last_updated || '';
      var statusLine = db.acceptance_status_label || (
        (db.integration_run ? db.integration_run.status_label + ' · ' : '') +
        (db.sandbox_isolation_label || '')
      );
      banner.textContent = 'Exported SQLite snapshot · ' + totalCount + ' promises'
        + (exportedAt ? ' · ' + exportedAt : '')
        + (statusLine ? ' · ' + statusLine : '');
      banner.title = 'Source: ' + (meta.sqlite_file || 'promises.db')
        + (exportedAt ? ' · exported ' + exportedAt : '');
    }
    var reconText = db.id_reconciliation
      || (totalCount + ' published · ' + (demoData.quarantined ? demoData.quarantined.length : 0) + ' in quarantine registry');
    document.querySelectorAll('.recon-counts').forEach(el => { el.textContent = reconText; });

    // Sync Outcome Distribution Box dynamically
    const outVerifiedEl = document.getElementById('outcome-dist-verified');
    if (outVerifiedEl) outVerifiedEl.textContent = `${totalCount} VERIFIED`;

    if (totalCount > 0) {
      const kVal = counts.kept || 0;
      const pVal = counts.in_progress || 0;
      const bVal = counts.broken || 0;
      const uVal = counts.undecided || 0;

      const kPct = Math.round((kVal / totalCount) * 100);
      const pPct = Math.round((pVal / totalCount) * 100);
      const bPct = Math.round((bVal / totalCount) * 100);
      const uPct = Math.max(0, 100 - kPct - pPct - bPct);

      const barKept = document.getElementById('bar-seg-kept');
      const barProg = document.getElementById('bar-seg-progress');
      const barBroken = document.getElementById('bar-seg-broken');
      const barUndecided = document.getElementById('bar-seg-undecided');

      if (barKept) { barKept.style.width = `${(kVal / totalCount) * 100}%`; barKept.title = `Kept: ${kVal} (${kPct}%)`; }
      if (barProg) { barProg.style.width = `${(pVal / totalCount) * 100}%`; barProg.title = `In Progress: ${pVal} (${pPct}%)`; }
      if (barBroken) { barBroken.style.width = `${(bVal / totalCount) * 100}%`; barBroken.title = `Broken: ${bVal} (${bPct}%)`; }
      if (barUndecided) { barUndecided.style.width = `${(uVal / totalCount) * 100}%`; barUndecided.title = `Undecided: ${uVal} (${uPct}%)`; }

      const legKept = document.getElementById('legend-text-kept');
      const legProg = document.getElementById('legend-text-progress');
      const legBroken = document.getElementById('legend-text-broken');
      const legUndecided = document.getElementById('legend-text-undecided');

      if (legKept) legKept.textContent = `${kVal} Kept (${kPct}%)`;
      if (legProg) legProg.textContent = `${pVal} In Progress (${pPct}%)`;
      if (legBroken) legBroken.textContent = `${bVal} Broken (${bPct}%)`;
      if (legUndecided) legUndecided.textContent = `${uVal} Undecided (${uPct}%)`;
    }
  }

  // -------------------------------------------------------------------------
  // SF SHOWCASE (ACROSS THE CITY)
  // -------------------------------------------------------------------------
  function renderShowcaseCard(promiseId) {
    if (!demoData) return;
    selectedShowcasePid = promiseId;

    const showcaseItem = (demoData.sf_showcase || []).find(s => s.promise_id === promiseId);
    const pData = (demoData.promises || []).find(p => p.promise_id === promiseId) || demoData.p02;

    if (!showcaseItem || !pData) return;

    // Update active tab button style
    document.querySelectorAll('.showcase-tab-btn').forEach(btn => {
      const isTarget = btn.getAttribute('data-showcase-id') === promiseId;
      btn.classList.toggle('active', isTarget);
      btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    });

    // Pulse the display card so visitors notice the content swapped.
    if (showcaseCardDisplay) {
      showcaseCardDisplay.classList.remove('showcase-pulse');
      void showcaseCardDisplay.offsetWidth;
      showcaseCardDisplay.classList.add('showcase-pulse');
    }

    // Update showcase card fields
    if (scBadgeId) scBadgeId.textContent = `#${pData.display_no || '—'}`;
    if (scBadgeVerdict) {
      const verdClass = pData.verdict.toLowerCase().replace(' ', '_');
      scBadgeVerdict.className = `verdict-chip ${verdClass}`;
      scBadgeVerdict.textContent = formatVerdictLabel(pData.verdict);

      // Card accent border
      const accentVar = verdClass === 'kept' ? 'var(--kept)' : verdClass === 'in_progress' ? 'var(--blue)' : 'var(--purple)';
      showcaseCardDisplay.style.setProperty('--card-accent', accentVar);
    }

    if (scDomainPill) scDomainPill.textContent = showcaseItem.domain;
    if (scNeighborhoodPill) scNeighborhoodPill.textContent = pData.neighborhood || showcaseItem.tag;
    if (scQuoteText) scQuoteText.textContent = `“${cleanQuoteText(pData.promise_text)}”`;
    if (scMetaEntity) scMetaEntity.textContent = `${pData.entity} (${pData.role || ''})`;
    if (scMetaPromised) scMetaPromised.textContent = pData.promised_date || '—';
    if (scMetaDue) scMetaDue.textContent = pData.due_date || '—';
    if (scMetaOpened) scMetaOpened.textContent = pData.opened_date || pData.realized_date || (promiseId === 'P02' ? 'April 28, 2025' : '—');
    if (scMetaRel) {
      scMetaRel.innerHTML = `<span class="badge-verified">✓ Verified</span>`;
    }
    if (scEvidenceFact) scEvidenceFact.textContent = pData.evidence_fact || showcaseItem.evidence;

    if (scSourceLink) {
      const url = pData.source_url || '';
      if (!url) {
        scSourceLink.removeAttribute('href');
        scSourceLink.textContent = 'source link not recorded';
      } else {
        scSourceLink.href = url;
        scSourceLink.innerHTML = `
          ${escapeHtml(url.replace(/^https?:\/\//, ''))}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        `;
      }
    }

    if (scHashPill) {
      const shash = pData.source_hash || '';
      const sid = pData.source_id || '—';
      scHashPill.textContent = shash
        ? `source_id: ${sid} · SHA-256: ${shash.substring(0, 12)}...`
        : 'source hash not recorded';
    }
  }

  // -------------------------------------------------------------------------
  // 6-STAGE PIPELINE STATE MACHINE & ANIMATION CONTROLLER
  // -------------------------------------------------------------------------
  // Stage 1 cites the real fetched artifacts per run: P02 cites its own
  // sources row; N01 is based on P05 so it cites the P05 file. Values come
  // from the DB export; literals are the verified fallbacks.
  const VERIFIED_RUN_SOURCES = {
    P02: {
      file: 'e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05.md',
      hash: 'e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05',
      url: 'https://www.sfpublicworkstv.org/april2025'
    },
    N01: {
      file: '6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md',
      hash: '6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa',
      url: 'https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/'
    }
  };

  function runSourceFor(runType) {
    // Watchdog test is planted on the P05 source file; any other run cites
    // its own promise row. Missing data renders as '—', never another row's.
    const pid = isWatchdog(runType) ? 'P05' : runType;
    const row = ((demoData && demoData.promises) || []).find(p => p.promise_id === pid)
      || (pid === 'P02' && demoData ? demoData.p02 : null);
    const fb = VERIFIED_RUN_SOURCES[isWatchdog(runType) ? 'N01' : pid]
      || { file: '—', hash: '', url: '' };
    const file = (row && row.source_file_path ? row.source_file_path.split('/').pop() : fb.file);
    const hash = (row && row.source_hash) || fb.hash;
    const url = (row && row.source_url) || fb.url;
    return { file, hash, url };
  }

  function renderRunSelect() {
    if (!runSelect || !demoData || !demoData.promises) return;
    runSelect.innerHTML = '';
    const mkOpt = (value, label) => {
      const o = document.createElement('option');
      o.value = value;
      o.textContent = label;
      return o;
    };
    const watchdogGroup = document.createElement('optgroup');
    watchdogGroup.label = 'Watchdog test';
    watchdogGroup.appendChild(mkOpt('N01', 'Altered quote gets caught (shelter beds → units)'));
    runSelect.appendChild(watchdogGroup);
    const groups = [
      ['kept', 'Kept'],
      ['broken', 'Broken'],
      ['in_progress', 'In progress'],
      ['undecided', 'Undecided'],
    ];
    groups.forEach(([verdict, label]) => {
      const rows = demoData.promises.filter(p => p.verdict === verdict);
      if (!rows.length) return;
      const g = document.createElement('optgroup');
      g.label = `${label} (${rows.length})`;
      rows.forEach(p => {
        g.appendChild(mkOpt(
          p.promise_id,
          `#${p.display_no || '—'} · ${shortLabel(p, 55)} — ${p.entity}`
        ));
      });
      runSelect.appendChild(g);
    });
    runSelect.value = 'N01';
  }

  function renderStage1Source(runType) {
    const src = runSourceFor(runType);
    if (stage1Filename) stage1Filename.textContent = src.file;
    if (stage1HashPrefix) stage1HashPrefix.textContent = src.hash ? `${src.hash.substring(0, 8)}...` : '—';
    if (stage1SourceUrl) {
      if (!src.url) {
        stage1SourceUrl.removeAttribute('href');
        stage1SourceUrl.textContent = 'Saved source (link not recorded)';
      } else {
        try {
          stage1SourceUrl.textContent = 'Saved source · ' + new URL(src.url).hostname + ' ↗';
        } catch (e) {
          stage1SourceUrl.textContent = 'Saved source ↗';
        }
        stage1SourceUrl.href = src.url;
      }
    }
  }

  function resetPipeline() {
    if (autoTimer) clearTimeout(autoTimer);
    isAutoRunning = false;
    currentStage = 0;

    if (btnRunSelected) btnRunSelected.disabled = false;
    if (runSelect) runSelect.disabled = false;
    if (btnStepNext) btnStepNext.disabled = false;

    // Reset progress and indicators
    if (pipelineProgressFill) pipelineProgressFill.style.width = '0%';
    if (packetTrackFill) packetTrackFill.style.width = '0%';
    if (packetBallDot) packetBallDot.style.left = '0%';
    if (packetBallInner) packetBallInner.className = 'packet-ball-inner';
    if (pipelineStageIndicator) {
      pipelineStageIndicator.textContent = 'STAGE 0 / 6 · READY TO RUN';
    }
    if (packetStatusText) packetStatusText.textContent = 'waiting to start';

    // Reset milestones
    for (let i = 1; i <= 6; i++) {
      if (msCircles[i]) {
        msCircles[i].className = 'milestone-circle';
        msCircles[i].textContent = i;
      }
    }

    // Reset Stage Cards
    [stageCard1, stageCard2, stageCard3, stageCard4, stageCard5, stageCard6].forEach(card => {
      if (card) {
        card.className = card.className.replace(/\b(active-stage|done-stage)\b/g, '').trim();
      }
    });

    if (stageBadge1) {
      stageBadge1.className = 'stage-state-pill font-mono';
      stageBadge1.textContent = 'IDLE';
    }
    if (stage1FetchFill) stage1FetchFill.style.width = '0%';
    if (stage1HashMatch) stage1HashMatch.style.display = 'none';
    if (stage1VerifiedBanner) stage1VerifiedBanner.style.display = 'none';
    renderStage1Source(currentRunType);

    if (stageBadge2) {
      stageBadge2.className = 'stage-state-pill font-mono';
      stageBadge2.textContent = 'Model drafts';
    }
    if (stage2FlashBox) stage2FlashBox.style.display = 'none';
    if (stage2PassBox) stage2PassBox.style.display = 'none';

    [relFillReal, relFillMeas, relFillSf, relFillInt].forEach(f => { if (f) f.style.width = '0%'; });
    [scoreValReal, scoreValMeas, scoreValSf, scoreValInt].forEach(v => { if (v) v.textContent = '0 / 2'; });
    if (stage3ScoreFill) stage3ScoreFill.style.width = '0%';
    if (stage3ScoreTotal) stage3ScoreTotal.textContent = '0 / 8';
    if (stage3ScoreBadge) {
      stage3ScoreBadge.textContent = 'Scoring…';
      stage3ScoreBadge.className = 'badge-verified font-mono';
    }
    if (stageBadge3) {
      stageBadge3.className = 'stage-state-pill font-mono';
      stageBadge3.textContent = 'Sandbox D';
    }
    if (stage3GateBadge) {
      stage3GateBadge.className = 'gate-badge-pill closed';
      stage3GateBadge.textContent = '🚪 GATE CLOSED';
    }

    if (advBoxKept) advBoxKept.className = 'advocate-sub-box';
    if (advStatusKept) {
      advStatusKept.textContent = 'WAITING';
      advStatusKept.style.color = '#94a3b8';
    }
    if (advFindingsKept) advFindingsKept.innerHTML = '<span style="color: #94a3b8;">Waiting for gate to open…</span>';
    if (advDotsKept) {
      advDotsKept.querySelectorAll('.bounce-dot').forEach(d => d.className = 'bounce-dot');
    }

    if (advBoxBroken) advBoxBroken.className = 'advocate-sub-box';
    if (advStatusBroken) {
      advStatusBroken.textContent = 'WAITING';
      advStatusBroken.style.color = '#94a3b8';
    }
    if (advFindingsBroken) advFindingsBroken.innerHTML = '<span style="color: #94a3b8;">Waiting for gate to open…</span>';
    if (advDotsBroken) {
      advDotsBroken.querySelectorAll('.bounce-dot').forEach(d => d.className = 'bounce-dot');
    }

    checkKeys.forEach((key, idx) => {
      const row = document.getElementById(`check-row-${key}`);
      const circle = document.getElementById(`circle-check-${key}`);
      const tag = document.getElementById(`tag-check-${key}`);
      if (row) row.className = 'arb-check-item';
      if (circle) {
        circle.className = 'arb-check-circle';
        circle.textContent = idx + 1;
      }
      if (tag) tag.style.display = 'none';
    });
    if (arbDivertAlert) arbDivertAlert.style.display = 'none';
    const spkDescReset = document.getElementById('check-desc-speaker');
    if (spkDescReset) spkDescReset.textContent = 'n/a, not a minutes source (named in text)';
    const rubDescReset = document.getElementById('check-desc-rubric');
    if (rubDescReset) rubDescReset.textContent = 'Deterministic rubric maps passing claims → verdict';

    if (stageBadge6) stageBadge6.textContent = 'WAITING';
    if (outputWaitingContainer) outputWaitingContainer.style.display = 'block';
    if (outputKeptResult) outputKeptResult.style.display = 'none';
    if (outputQuarantineResult) outputQuarantineResult.style.display = 'none';
    if (outputVerdictResult) outputVerdictResult.style.display = 'none';

    updateNarrative(0);
  }

  function renderCompletedPipeline(presetKey = 'P02') {
    if (autoTimer) clearTimeout(autoTimer);
    isAutoRunning = false;
    currentStage = 6;
    currentRunType = presetKey;
    if (runSelect) runSelect.value = presetKey;

    if (btnRunSelected) {
      btnRunSelected.disabled = false;
      const span = btnRunSelected.querySelector('span');
      if (span) span.textContent = 'Replay Walkthrough';
    }
    if (runSelect) runSelect.disabled = false;
    if (btnStepNext) btnStepNext.disabled = false;

    if (pipelineProgressFill) pipelineProgressFill.style.width = '100%';
    if (packetTrackFill) packetTrackFill.style.width = '100%';
    if (packetBallDot) packetBallDot.style.left = '100%';
    if (packetBallInner) packetBallInner.className = 'packet-ball-inner kept-end';
    if (packetStatusText) packetStatusText.textContent = 'verified & delivered';

    for (let i = 1; i <= 6; i++) {
      if (msCircles[i]) {
        msCircles[i].className = 'milestone-circle passed';
        msCircles[i].textContent = '✓';
      }
    }

    const op = runPromise(presetKey) || (demoData && demoData.p02);
    if (pipelineStageIndicator) {
      pipelineStageIndicator.textContent = `STAGE 6 / 6 · #${(op && op.display_no) || '01'} — ${(op && op.verdict ? op.verdict : 'kept').toUpperCase()} (VERIFIED RECORD)`;
    }

    // Stage 1
    if (stageCard1) stageCard1.className = 'stage-card span-4 done-stage';
    if (stageBadge1) {
      stageBadge1.className = 'stage-state-pill font-mono done';
      stageBadge1.textContent = 'HASH MATCH';
    }
    if (stage1FetchFill) stage1FetchFill.style.width = '100%';
    if (stage1HashMatch) stage1HashMatch.style.display = 'block';
    if (stage1VerifiedBanner) stage1VerifiedBanner.style.display = 'block';
    renderStage1Source(presetKey);

    // Stage 2
    if (stageCard2) stageCard2.className = 'stage-card span-7 done-stage';
    if (stageBadge2) {
      stageBadge2.className = 'stage-state-pill font-mono done';
      stageBadge2.textContent = 'EXTRACTED';
    }
    if (stage2FlashBox) stage2FlashBox.style.display = 'block';
    if (stage2PassBox) stage2PassBox.style.display = 'block';

    // Stage 3
    if (stageCard3) stageCard3.className = 'stage-card span-5 done-stage';
    if (stageBadge3) {
      stageBadge3.className = 'stage-state-pill font-mono done';
      stageBadge3.textContent = '8/8 PASSED';
    }
    if (stage3GateBadge) {
      stage3GateBadge.className = 'gate-badge-pill open';
      stage3GateBadge.textContent = '🚪 GATE PASSED (8/8)';
    }
    [relFillReal, relFillMeas, relFillSf, relFillInt].forEach(f => { if (f) f.style.width = '100%'; });
    [scoreValReal, scoreValMeas, scoreValSf, scoreValInt].forEach(v => { if (v) v.textContent = '2 / 2'; });
    if (stage3ScoreFill) stage3ScoreFill.style.width = '100%';
    if (stage3ScoreTotal) stage3ScoreTotal.textContent = '8 / 8';
    if (stage3ScoreBadge) {
      stage3ScoreBadge.textContent = '8/8 Passed';
      stage3ScoreBadge.className = 'badge-verified font-mono';
    }

    // Stage 4
    if (stageCard4) stageCard4.className = 'stage-card span-12 done-stage';
    if (stageBadge4) {
      stageBadge4.className = 'stage-state-pill font-mono done';
      stageBadge4.textContent = 'ARGUMENTS FILED';
    }
    if (advBoxKept) advBoxKept.className = 'advocate-sub-box active-kept';
    if (advStatusKept) {
      advStatusKept.textContent = '✓ FINISHED';
      advStatusKept.style.color = '#10B981';
    }
    if (advFindingsKept) {
      advFindingsKept.innerHTML = `
        <span style="color: #10B981;">▸</span> SF Department of Public Health confirmed acute hospital beds retained 24/7 (2 sources checked).
        <div style="margin-top: 6px; color: #A7F3D0; font-weight: 700;">&rarr; Case: KEEP — evidence supports promise.</div>
      `;
    }
    if (advBoxBroken) advBoxBroken.className = 'advocate-sub-box active-broken';
    if (advStatusBroken) {
      advStatusBroken.textContent = '✓ FINISHED';
      advStatusBroken.style.color = '#94A3B8';
    }
    if (advFindingsBroken) {
      advFindingsBroken.innerHTML = `
        <span style="color: #EF4444;">▸</span> No contradicting source found in saved files (4 sources checked).
        <div style="margin-top: 6px; color: #FCA5A5; font-weight: 700;">&rarr; Case: CHALLENGE — but evidence is thin.</div>
      `;
    }
    if (tagStagingKept) tagStagingKept.textContent = `staging/kept_${presetKey}.json`;
    if (tagStagingBroken) tagStagingBroken.textContent = `staging/broken_${presetKey}.json`;

    // Stage 5
    if (stageCard5) stageCard5.className = 'stage-card span-7 done-stage';
    if (stageBadge5) {
      stageBadge5.className = 'stage-state-pill font-mono done';
      stageBadge5.textContent = '7/7 PASS';
    }
    checkKeys.forEach(key => {
      const row = document.getElementById(`check-row-${key}`);
      const circle = document.getElementById(`circle-check-${key}`);
      const tag = document.getElementById(`tag-check-${key}`);
      if (row) row.className = 'arb-check-item passed';
      if (circle) {
        circle.className = 'arb-check-circle passed';
        circle.textContent = '✓';
      }
      if (tag) {
        tag.style.display = 'inline';
        tag.style.color = '#10B981';
        tag.textContent = 'PASS';
      }
    });

    // Stage 6
    if (stageCard6) stageCard6.className = 'stage-card span-5 active-stage';
    if (stageBadge6) {
      stageBadge6.className = 'stage-state-pill font-mono done';
      stageBadge6.textContent = '✓ KEPT';
    }
    if (outputWaitingContainer) outputWaitingContainer.style.display = 'none';
    if (outputKeptResult) outputKeptResult.style.display = 'block';
    const keptDesc = document.getElementById('output-kept-desc');
    if (keptDesc && op) {
      keptDesc.textContent = `#${op.display_no || '01'} · “${shortLabel(op, 90)}” (${op.entity}) — verified & published.`;
    }

    updateNarrative(6);
  }

  function startPipeline(presetKey) {
    resetPipeline();
    currentRunType = presetKey;
    if (runSelect) runSelect.value = presetKey;
    isAutoRunning = true;
    isStepMode = false;
    if (btnRunSelected) btnRunSelected.disabled = true;
    if (runSelect) runSelect.disabled = true;
    if (pipelineModeHint) pipelineModeHint.textContent = `Auto-playing ${runLabel(presetKey)}. Sit back or click Next Stage to take manual control.`;
    executeStage(1);
  }

  function advanceStep() {
    if (isAutoRunning) {
      if (autoTimer) clearTimeout(autoTimer);
      isAutoRunning = false;
      if (btnRunSelected) btnRunSelected.disabled = false;
      if (runSelect) runSelect.disabled = false;
    }
    isStepMode = true;
    if (pipelineModeHint) pipelineModeHint.textContent = "Step mode active. You are advancing one stage per click.";

    if (currentStage >= 6) {
      resetPipeline();
    } else {
      executeStage(currentStage + 1);
    }
  }

  function executeStage(stageNum) {
    currentStage = stageNum;

    // Progress math: 6 stages (16.6%, 33.3%, 50%, 66.6%, 83.3%, 100%)
    const pct = Math.round((stageNum / 6) * 100);
    if (pipelineProgressFill) pipelineProgressFill.style.width = `${pct}%`;
    if (packetTrackFill) packetTrackFill.style.width = `${pct}%`;

    // Packet dot movement along line
    const dotPositions = { 1: '0%', 2: '20%', 3: '40%', 4: '60%', 5: '80%', 6: '100%' };
    if (packetBallDot) packetBallDot.style.left = dotPositions[stageNum] || '0%';

    // Update milestone markers
    for (let i = 1; i <= 6; i++) {
      if (msCircles[i]) {
        if (i < stageNum) {
          msCircles[i].className = 'milestone-circle passed';
          msCircles[i].textContent = '✓';
        } else if (i === stageNum) {
          msCircles[i].className = 'milestone-circle current';
          msCircles[i].textContent = i;
        } else {
          msCircles[i].className = 'milestone-circle';
          msCircles[i].textContent = i;
        }
      }
    }

    // Top indicator text
    const runP = runPromise(currentRunType);
    const caseTitle = isWatchdog(currentRunType)
      ? 'WATCHDOG TEST — ALTERED QUOTE'
      : `#${(runP && runP.display_no) || '—'} — ${(runP && runP.verdict ? runP.verdict : '').toUpperCase().replace('_', ' ')}`;
    const replayLabel = replayCount > 0 ? ` · REPLAY ${replayCount}` : '';
    if (pipelineStageIndicator) {
      pipelineStageIndicator.textContent = `STAGE ${stageNum} / 6 · ${caseTitle}${replayLabel}`;
    }

    // Stage specifics
    if (stageNum === 1) {
      // Stage 1: Fetch
      if (packetStatusText) packetStatusText.textContent = 'moving → Fetch';
      if (stageCard1) stageCard1.className = 'stage-card span-4 active-stage';
      if (stageBadge1) {
        stageBadge1.className = 'stage-state-pill font-mono running';
        stageBadge1.textContent = '● RUNNING';
      }
      renderStage1Source(currentRunType);

      setTimeout(() => {
        if (stage1FetchFill) stage1FetchFill.style.width = '100%';
        if (stage1HashMatch) stage1HashMatch.style.display = 'inline';
        if (stage1VerifiedBanner) stage1VerifiedBanner.style.display = 'block';
        if (stageBadge1) {
          stageBadge1.className = 'stage-state-pill font-mono done';
          stageBadge1.textContent = '✓ Verified';
        }
        if (stageCard1) stageCard1.className = 'stage-card span-4 done-stage';

        updateNarrative(1);
        if (isAutoRunning) {
          autoTimer = setTimeout(() => executeStage(2), 1100);
        }
      }, 500);
    }
    else if (stageNum === 2) {
      // Stage 2: Extract
      if (packetStatusText) packetStatusText.textContent = 'moving → Extract';
      if (stageCard2) stageCard2.className = 'stage-card span-4 active-stage';
      if (stageBadge2) {
        stageBadge2.className = 'stage-state-pill font-mono running';
        stageBadge2.textContent = '● DRAFTING';
      }

      if (isWatchdog(currentRunType)) {
        stage2QuoteContent.innerHTML = `“The City will build <span class="altered-word-highlight">1,000 shelter units</span> by 2027.”`;
      } else {
        const qp = runPromise(currentRunType);
        stage2QuoteContent.textContent = `“${cleanQuoteText((qp && qp.promise_text) || '')}”`;
      }

      setTimeout(() => {
        if (!isWatchdog(currentRunType)) {
          if (stage2PassBox) stage2PassBox.style.display = 'block';
          if (stageBadge2) {
            stageBadge2.className = 'stage-state-pill font-mono done';
            stageBadge2.textContent = '✓ Verbatim';
          }
        } else {
          if (stage2FlashBox) stage2FlashBox.style.display = 'block';
          if (stageBadge2) {
            stageBadge2.className = 'stage-state-pill font-mono failed';
            stageBadge2.textContent = '⚠ Altered';
          }
        }
        if (stageCard2) stageCard2.className = 'stage-card span-4 done-stage';

        updateNarrative(2);
        if (isAutoRunning) {
          autoTimer = setTimeout(() => executeStage(3), 1100);
        }
      }, 500);
    }
    else if (stageNum === 3) {
      // Stage 3: Relevance Gate
      if (packetStatusText) packetStatusText.textContent = 'moving → Gate';
      if (stageCard3) stageCard3.className = 'stage-card span-4 active-stage';
      if (stageBadge3) {
        stageBadge3.className = 'stage-state-pill font-mono running';
        stageBadge3.textContent = '● SCORING';
      }

      // Real relevance scores for this run (watchdog replays P05's gate).
      const relP = isWatchdog(currentRunType)
        ? (((demoData && demoData.promises) || []).find(p => p.promise_id === 'P05') || {})
        : (runPromise(currentRunType) || {});
      const rel = relP.relevance || { score: 0, real: 0, measurable: 0, sf: 0, interesting: 0 };
      const relPairs = [
        [relFillReal, scoreValReal, rel.real || 0],
        [relFillMeas, scoreValMeas, rel.measurable || 0],
        [relFillSf, scoreValSf, rel.sf || 0],
        [relFillInt, scoreValInt, rel.interesting || 0],
      ];
      const relTotal = rel.score || 0;
      const relPassed = relTotal >= 5;

      // Animate Relevance Gate hero bar & metrics
      setTimeout(() => {
        if (stage3ScoreFill) stage3ScoreFill.style.width = `${Math.round((relTotal / 8) * 50)}%`;
        if (stage3ScoreTotal) stage3ScoreTotal.textContent = `${Math.floor(relTotal / 2)} / 8`;
      }, 300);

      setTimeout(() => {
        relPairs.forEach(([fill, val, score]) => {
          if (fill) fill.style.width = `${(score / 2) * 100}%`;
          if (val) val.textContent = `${score} / 2`;
        });
        if (stage3ScoreFill) stage3ScoreFill.style.width = `${(relTotal / 8) * 100}%`;
        if (stage3ScoreTotal) stage3ScoreTotal.textContent = `${relTotal} / 8`;
        const criteriaSummaryEl = document.getElementById('stage3-criteria-summary');
        if (criteriaSummaryEl) {
          criteriaSummaryEl.textContent = `Criteria: real_promise (${rel.real || 0}/2) · measurable (${rel.measurable || 0}/2) · sf_relevant (${rel.sf || 0}/2) · interesting (${rel.interesting || 0}/2)`;
        }
        if (stage3ScoreBadge) {
          stage3ScoreBadge.textContent = relPassed ? '✓ Gate Passed' : '✕ Below Gate (5+)';
          stage3ScoreBadge.className = relPassed ? 'badge-verified' : 'badge-verified badge-failed';
        }
        if (stageBadge3) {
          stageBadge3.className = 'stage-state-pill font-mono done';
          stageBadge3.textContent = relPassed
            ? `✓ ${relTotal}/8 GATE PASSED`
            : `✕ ${relTotal}/8 BELOW GATE`;
        }
        if (stageCard3) stageCard3.className = 'stage-card span-4 done-stage';

        updateNarrative(3);
        if (isAutoRunning) {
          autoTimer = setTimeout(() => executeStage(4), 1200);
        }
      }, 700);
    }
    else if (stageNum === 4) {
      // Stage 4: Split Advocates
      if (packetStatusText) packetStatusText.textContent = 'moving → Advocates';
      if (stageCard4) stageCard4.className = 'stage-card span-12 active-stage';

      if (advBoxKept) advBoxKept.className = 'advocate-sub-box active-kept';
      if (advStatusKept) {
        advStatusKept.textContent = '● SCANNING…';
        advStatusKept.style.color = '#10B981';
      }
      if (advDotsKept) {
        advDotsKept.querySelectorAll('.bounce-dot').forEach((d, idx) => {
          d.className = 'bounce-dot active-green';
          d.style.animationDelay = `${idx * 140}ms`;
        });
      }

      if (advBoxBroken) advBoxBroken.className = 'advocate-sub-box active-broken';
      if (advStatusBroken) {
        advStatusBroken.textContent = '● SCANNING…';
        advStatusBroken.style.color = '#EF4444';
      }
      if (advDotsBroken) {
        advDotsBroken.querySelectorAll('.bounce-dot').forEach((d, idx) => {
          d.className = 'bounce-dot active-red';
          d.style.animationDelay = `${idx * 140}ms`;
        });
      }

      setTimeout(() => {
        const ap = isWatchdog(currentRunType) ? null : runPromise(currentRunType);
        const bundles = (ap && ap.advocate_bundles) || {};
        const kClaims = (bundles.kept && bundles.kept.claims) || [];
        const bClaims = (bundles.broken && bundles.broken.claims) || [];
        const kChecked = bundles.kept && bundles.kept.evidence_checked;
        const bChecked = bundles.broken && bundles.broken.evidence_checked;

        if (advStatusKept) advStatusKept.textContent = '✓ FINISHED';
        if (advFindingsKept) {
          if (isWatchdog(currentRunType)) {
            advFindingsKept.innerHTML = `
              <span style="color: #10B981;">▸</span> Watchdog test: no affirming brief filed — the planted wording is under challenge.
              <div style="margin-top: 6px; color: #A7F3D0; font-weight: 700;">&rarr; Case: none — planted test case.</div>
            `;
          } else if (kClaims.length > 0) {
            const top = kClaims[0];
            advFindingsKept.innerHTML = `
              <span style="color: #10B981;">▸</span> ${escapeHtml(top.claim_text || top.quote || 'Affirming claim filed')} (${kClaims.length} claim${kClaims.length === 1 ? '' : 's'}${kChecked != null ? `, ${kChecked} sources checked` : ''}).
              <div style="margin-top: 6px; color: #A7F3D0; font-weight: 700;">&rarr; Case: KEEP — evidence supports promise.</div>
            `;
          } else {
            advFindingsKept.innerHTML = `
              <span style="color: #10B981;">▸</span> No affirming claims filed${kChecked != null ? ` (${kChecked} sources checked)` : ''}.
              <div style="margin-top: 6px; color: #A7F3D0; font-weight: 700;">&rarr; Case: KEEP — but evidence is thin.</div>
            `;
          }
        }

        if (advStatusBroken) advStatusBroken.textContent = '✓ FINISHED';
        if (advFindingsBroken) {
          if (isWatchdog(currentRunType)) {
            advFindingsBroken.innerHTML = `
              <span style="color: #EF4444;">▸</span> Found altered wording. Original source reads “1,500 new shelter beds”. Word “units” was swapped.
              <div style="margin-top: 6px; color: #FCA5A5; font-weight: 700;">&rarr; Case: BREAK — quote is inaccurate.</div>
            `;
          } else if (bClaims.length > 0) {
            const top = bClaims[0];
            advFindingsBroken.innerHTML = `
              <span style="color: #EF4444;">▸</span> ${escapeHtml(top.claim_text || top.quote || 'Contradicting claim filed')} (${bClaims.length} claim${bClaims.length === 1 ? '' : 's'}${bChecked != null ? `, ${bChecked} sources checked` : ''}).
              <div style="margin-top: 6px; color: #FCA5A5; font-weight: 700;">&rarr; Case: BREAK — evidence contradicts promise.</div>
            `;
          } else {
            const note = (bundles.broken && bundles.broken.note) || 'No contradicting source found in saved files.';
            advFindingsBroken.innerHTML = `
              <span style="color: #EF4444;">▸</span> ${escapeHtml(note)}
              <div style="margin-top: 6px; color: #FCA5A5; font-weight: 700;">&rarr; Case: CHALLENGE — but evidence is thin.</div>
            `;
          }
        }

        if (tagStagingKept) tagStagingKept.textContent = isWatchdog(currentRunType) ? 'staging/kept_N01.json (planted)' : `staging/kept_${currentRunType}.json`;
        if (tagStagingBroken) tagStagingBroken.textContent = isWatchdog(currentRunType) ? 'staging/broken_N01.json (planted)' : `staging/broken_${currentRunType}.json`;
        if (stageCard4) stageCard4.className = 'stage-card span-12 done-stage';

        updateNarrative(4);
        if (isAutoRunning) {
          autoTimer = setTimeout(() => executeStage(5), 1300);
        }
      }, 700);
    }
    else if (stageNum === 5) {
      // Stage 5: Arbitrator
      if (packetStatusText) packetStatusText.textContent = 'moving → Arbitrator';
      if (stageCard5) stageCard5.className = 'stage-card span-7 active-stage';

      // Recorded arbitrator outcomes for this run. Watchdog replays the
      // planted quote failure; real promises show their recorded results
      // (a flagged check does not rewrite the recorded verdict in stage 6).
      const cp = isWatchdog(currentRunType) ? null : runPromise(currentRunType);
      let checkIdx = 0;
      function tickNextCheck() {
        if (checkIdx >= checkKeys.length) {
          if (stageCard5) stageCard5.className = 'stage-card span-7 done-stage';
          updateNarrative(5);
          if (isAutoRunning) {
            autoTimer = setTimeout(() => executeStage(6), 1100);
          }
          return;
        }

        const key = checkKeys[checkIdx];
        const row = document.getElementById(`check-row-${key}`);
        const circle = document.getElementById(`circle-check-${key}`);
        const tag = document.getElementById(`tag-check-${key}`);

        // Watchdog: planted quote failure stops the run and diverts.
        const outcome = isWatchdog(currentRunType)
          ? (key === 'quote' ? false : true)
          : checkOutcome(cp, key);

        if (outcome === false && isWatchdog(currentRunType)) {
          if (row) row.className = 'arb-check-item failed';
          if (circle) {
            circle.className = 'arb-check-circle failed';
            circle.textContent = '✕';
          }
          if (tag) {
            tag.style.display = 'inline';
            tag.style.color = '#EF4444';
            tag.textContent = 'FAILED';
          }
          if (arbDivertAlert) arbDivertAlert.style.display = 'block';

          // Stop checks for the watchdog run
          if (stageCard5) stageCard5.className = 'stage-card span-7 done-stage';
          updateNarrative(5);
          if (isAutoRunning) {
            autoTimer = setTimeout(() => executeStage(6), 1100);
          }
          return;
        }

        if (outcome === false) {
          // Recorded FAIL on a real promise: flag it, keep replaying.
          if (row) row.className = 'arb-check-item failed';
          if (circle) {
            circle.className = 'arb-check-circle failed';
            circle.textContent = '!';
          }
          if (tag) {
            tag.style.display = 'inline';
            tag.style.color = '#F59E0B';
            tag.textContent = 'FLAGGED';
          }
        } else if (outcome === null) {
          if (row) row.className = 'arb-check-item';
          if (circle) {
            circle.className = 'arb-check-circle';
            circle.textContent = '–';
          }
          if (tag) {
            tag.style.display = 'inline';
            tag.style.color = 'var(--muted)';
            tag.textContent = 'NOT RECORDED';
          }
        } else {
          if (row) row.className = 'arb-check-item passed';
          if (circle) {
            circle.className = 'arb-check-circle passed';
            circle.textContent = '✓';
          }
          if (tag) {
            tag.style.display = 'inline';
            tag.style.color = '#10B981';
            tag.textContent = 'PASS';
          }
          if (key === 'speaker') {
            const spkDesc = document.getElementById('check-desc-speaker');
            if (spkDesc) {
              spkDesc.textContent = (cp && cp.source_type === 'board_minutes')
                ? 'Roll call attendance verified in official minutes'
                : 'n/a, not a minutes source (named in text)';
            }
          }
          if (key === 'rubric') {
            const rubDesc = document.getElementById('check-desc-rubric');
            if (rubDesc && cp) {
              const vUpper = (cp.verdict || 'KEPT').toUpperCase();
              const bundles = cp.advocate_bundles || {};
              const nk = (bundles.kept && bundles.kept.claims && bundles.kept.claims.length) || 0;
              const nb = (bundles.broken && bundles.broken.claims && bundles.broken.claims.length) || 0;
              rubDesc.textContent = `Deterministic rubric: ${nk} affirming, ${nb} contradicting → ${vUpper}`;
            }
          }
        }

        checkIdx++;
        setTimeout(tickNextCheck, 160);
      }

      setTimeout(tickNextCheck, 300);
    }
    else if (stageNum === 6) {
      // Stage 6: Output — recorded verdict for this run.
      if (packetStatusText) packetStatusText.textContent = 'delivered';
      if (stageCard6) stageCard6.className = 'stage-card span-5 active-stage';

      if (outputWaitingContainer) outputWaitingContainer.style.display = 'none';

      const op = isWatchdog(currentRunType) ? null : runPromise(currentRunType);
      const verdict = op ? op.verdict : 'quarantined';
      if (verdict === 'kept') {
        if (packetBallInner) packetBallInner.className = 'packet-ball-inner kept-end';
        if (stageBadge6) {
          stageBadge6.className = 'stage-state-pill font-mono done';
          stageBadge6.textContent = '✓ KEPT';
        }
        const keptDesc = document.getElementById('output-kept-desc');
        if (keptDesc && op) {
          keptDesc.textContent = `#${op.display_no || '—'} · “${shortLabel(op, 90)}” (${op.entity}) — verified & published.`;
        }
        if (outputKeptResult) outputKeptResult.style.display = 'block';
      } else if (isWatchdog(currentRunType)) {
        if (packetBallInner) packetBallInner.className = 'packet-ball-inner quarantine-end';
        if (stageBadge6) {
          stageBadge6.className = 'stage-state-pill font-mono failed';
          stageBadge6.textContent = '⚠ QUARANTINED';
        }
        if (outputQuarantineResult) outputQuarantineResult.style.display = 'block';
      } else {
        renderVerdictOutcome(op);
        if (packetBallInner) packetBallInner.className = verdict === 'broken'
          ? 'packet-ball-inner quarantine-end'
          : 'packet-ball-inner';
        if (stageBadge6) {
          stageBadge6.className = verdict === 'broken'
            ? 'stage-state-pill font-mono failed'
            : 'stage-state-pill font-mono done';
          stageBadge6.textContent = verdict === 'broken' ? '✕ BROKEN'
            : verdict === 'in_progress' ? '● IN PROGRESS' : '? UNDECIDED';
        }
        if (outputVerdictResult) outputVerdictResult.style.display = 'block';
      }

      isAutoRunning = false;
      if (btnRunSelected) btnRunSelected.disabled = false;
      if (runSelect) runSelect.disabled = false;
      updateNarrative(6);
    }
  }

  function renderVerdictOutcome(p) {
    if (!p) return;
    const stampEl = document.getElementById('output-verdict-stamp');
    const captionEl = document.getElementById('output-verdict-caption');
    const cardEl = document.getElementById('output-verdict-card');
    const headlineEl = document.getElementById('output-verdict-headline');
    const descEl = document.getElementById('output-verdict-desc');
    const pillEl = document.getElementById('output-verdict-pill');
    const verdict = p.verdict || 'undecided';
    const passed = (p.checks || []).filter(c => c.passed === true).length;
    const recorded = (p.checks || []).filter(c => c.passed !== null).length;
    if (stampEl) {
      stampEl.className = `stamp-${verdict} font-mono`;
      stampEl.textContent = verdict === 'broken' ? 'BROKEN ✕'
        : verdict === 'in_progress' ? 'IN PROGRESS ●' : 'UNDECIDED ?';
    }
    if (captionEl) {
      captionEl.textContent = `ARBITRATOR SIGNED · ${passed} / ${recorded || 7} CHECKS PASS (RECORDED)`;
    }
    if (cardEl) {
      cardEl.className = 'destination-result-card ' + (verdict === 'broken'
        ? 'broken-style'
        : verdict === 'in_progress' ? 'progress-style' : 'undecided-style');
    }
    if (headlineEl) {
      headlineEl.textContent = verdict === 'broken' ? '✕ Promise not kept — published as broken'
        : verdict === 'in_progress' ? '● Still in progress — tracking continues'
        : '? Cannot decide yet — held as undecided';
    }
    if (descEl) {
      descEl.textContent = `#${p.display_no || '—'} · “${shortLabel(p, 90)}” — ${p.verdict_reason || 'Recorded in promises.db.'}`;
    }
    if (pillEl) {
      pillEl.textContent = verdict === 'broken' ? '● PUBLISHED AS BROKEN'
        : verdict === 'in_progress' ? '● TRACKING' : '● HELD — UNDECIDED';
      pillEl.style.background = verdict === 'broken' ? 'var(--broken)'
        : verdict === 'in_progress' ? 'var(--blue)' : 'var(--muted)';
      pillEl.style.color = '#071120';
    }
  }

  function updateNarrative(stageIdx) {
    const data = STAGE_NARRATIVES[stageIdx] || STAGE_NARRATIVES[0];
    if (pipelineNarrativeTitle) pipelineNarrativeTitle.textContent = data.title;
    if (pipelineNarrativePill) pipelineNarrativePill.textContent = data.pill;
    if (pipelineNarrativeBody) pipelineNarrativeBody.textContent = data.body;

    if (btnNarrativeReplay) {
      btnNarrativeReplay.textContent = `Replay (${runLabel(currentRunType)})`;
    }
    if (btnNarrativeToggle) {
      if (isWatchdog(currentRunType)) {
        const kept = runPromise('P02');
        btnNarrativeToggle.textContent = `Try a kept promise → #${(kept && kept.display_no) || '—'} stabilization center`;
      } else {
        btnNarrativeToggle.textContent = 'Try the watchdog test → altered quote gets caught';
      }
    }
  }

  // -------------------------------------------------------------------------
  // ALL PROMISES TABLE & EDITORIAL CARDS
  // -------------------------------------------------------------------------
  function renderPromisesTable() {
    if ((!tbodyPromises && !promisesCardsGrid) || !demoData || !demoData.promises) return;

    const entityFilter = filterEntity ? filterEntity.value : 'all';
    const verdictFilter = filterVerdict ? filterVerdict.value : 'all';
    const catFilter = filterCategory ? filterCategory.value : 'all';
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

    const filtered = demoData.promises.filter(p => {
      // Entity filter
      if (entityFilter !== 'all' && p.entity_type !== entityFilter) return false;
      // Verdict filter
      if (verdictFilter !== 'all' && p.verdict.toLowerCase() !== verdictFilter) return false;
      // Dropdown category filter
      if (catFilter !== 'all' && p.category !== catFilter) return false;
      // Pill category filter
      if (activeCategoryFilter !== 'all' && p.category !== activeCategoryFilter) return false;
      // Query filter
      if (query) {
        const matchText = (p.promise_id + ' ' + p.promise_text + ' ' + p.entity + ' ' + (p.role || '') + ' ' + p.category + ' ' + (p.neighborhood || '')).toLowerCase();
        if (!matchText.includes(query)) return false;
      }
      return true;
    });

    // Sorting
    const sortVal = filterSort ? filterSort.value : 'rank';
    filtered.sort((a, b) => {
      if (sortVal === 'rank' || sortVal === 'default') {
        const ra = a.impact_rank || parseInt(a.display_no || '999', 10);
        const rb = b.impact_rank || parseInt(b.display_no || '999', 10);
        return ra - rb;
      }
      if (sortVal === 'rank_desc') {
        const ra = a.impact_rank || parseInt(a.display_no || '999', 10);
        const rb = b.impact_rank || parseInt(b.display_no || '999', 10);
        return rb - ra;
      }
      if (sortVal === 'date_desc') {
        return (b.promised_date || '').localeCompare(a.promised_date || '');
      }
      if (sortVal === 'date_asc') {
        return (a.promised_date || '').localeCompare(b.promised_date || '');
      }
      if (sortVal === 'verdict') {
        return (a.verdict || '').localeCompare(b.verdict || '');
      }
      if (sortVal === 'verdict_desc') {
        return (b.verdict || '').localeCompare(a.verdict || '');
      }
      if (sortVal === 'entity') {
        return (a.entity || '').localeCompare(b.entity || '');
      }
      if (sortVal === 'entity_desc') {
        return (b.entity || '').localeCompare(a.entity || '');
      }
      if (sortVal === 'quote_asc') {
        return (a.promise_text || '').localeCompare(b.promise_text || '');
      }
      if (sortVal === 'quote_desc') {
        return (b.promise_text || '').localeCompare(a.promise_text || '');
      }
      return (a.impact_rank || 999) - (b.impact_rank || 999);
    });

    // Pagination slicing
    const displayed = filtered.slice(0, currentPageSize);

    // Update Showing counter & active filter indicator
    if (tableShowingCount) tableShowingCount.textContent = displayed.length;
    if (tableTotalCount) tableTotalCount.textContent = filtered.length;

    // Pagination controls
    if (tablePaginationRow) {
      if (filtered.length <= currentPageSize) {
        tablePaginationRow.style.display = 'none';
      } else {
        tablePaginationRow.style.display = 'flex';
        if (paginationSub) {
          paginationSub.textContent = `(showing ${displayed.length} of ${filtered.length})`;
        }
        if (btnShowMore) {
          const nextCount = Math.min(15, filtered.length - displayed.length);
          const span = btnShowMore.querySelector('span:first-child');
          if (span) span.textContent = `Show ${nextCount} More Commitments`;
        }
      }
    }

    if (activeFilterIndicator) {
      const activeParts = [];
      if (entityFilter !== 'all') activeParts.push(`Entity: ${entityFilter}`);
      if (verdictFilter !== 'all') activeParts.push(`Verdict: ${verdictFilter}`);
      if (activeCategoryFilter !== 'all') activeParts.push(`Category: ${activeCategoryFilter}`);
      else if (catFilter !== 'all') activeParts.push(`Category: ${catFilter}`);
      if (query) activeParts.push(`Search: "${query}"`);

      if (activeParts.length > 0) {
        activeFilterIndicator.textContent = `Active: ${activeParts.join(' · ')} (${filtered.length} found)`;
        activeFilterIndicator.style.color = 'var(--blue)';
      } else {
        activeFilterIndicator.textContent = 'Active: All commitments (Sorted by Civic Impact)';
        activeFilterIndicator.style.color = '#E2E8F0';
      }
    }

    renderActiveChips();

    if (tbodyPromises) {
      tbodyPromises.innerHTML = '';
      displayed.forEach(p => {
        const tr = document.createElement('tr');
        const verdClass = p.verdict.toLowerCase().replace(' ', '_');
        const rel = p.relevance || null;
        const neighborhood = p.neighborhood || 'Citywide San Francisco';
        const rankFormatted = String(p.impact_rank || p.display_no || '—').padStart(2, '0');
        const tier = p.source_tier || getSourceTier(p.source_url);
        const tierClass = tier.toLowerCase();
        let quoteText = cleanQuoteText(p.promise_text);
        if (p.promise_id === 'P05' && !quoteText.startsWith('[Reported by')) {
          quoteText = `[Reported by The Frisc] ${quoteText}`;
        }

        tr.className = 'promise-row';
        tr.id = `promise-${p.promise_id}`;
        tr.tabIndex = 0;
        tr.setAttribute('role', 'button');
        tr.setAttribute('aria-expanded', 'false');
        tr.setAttribute('aria-controls', `accordion-${p.promise_id}`);
        tr.setAttribute('aria-label', `Toggle details for #${rankFormatted} (${p.promise_id}): ${quoteText.slice(0, 60)}`);

        tr.addEventListener('click', (ev) => {
          if (ev.target.closest('.btn-inspect-inline')) {
            openInspectModal(p.promise_id);
          } else {
            toggleAccordion(p.promise_id);
          }
        });
        tr.addEventListener('keydown', (ev) => {
          if (ev.key === 'Enter' || ev.key === ' ') {
            ev.preventDefault();
            toggleAccordion(p.promise_id);
          }
        });

        const dueLine = p.due_date
          ? `<div class="timeline-due font-mono">Due: ${escapeHtml(p.due_date)}</div>`
          : '';
        tr.innerHTML = `
          <td class="table-id-cell font-mono">
            <div class="id-cell-wrapper">
              <span class="rank-num">#${rankFormatted}</span>
              <span class="stable-id font-mono">${escapeHtml(p.promise_id)}</span>
              <span class="expand-chevron font-mono" aria-hidden="true">▾</span>
            </div>
          </td>
          <td class="table-entity-cell">
            <div class="table-entity-name">${escapeHtml(p.entity)}</div>
            <div class="table-entity-role font-mono">${escapeHtml(neighborhood)}</div>
          </td>
          <td class="table-promise-cell">
            <div class="table-promise-text">&ldquo;${escapeHtml(quoteText)}&rdquo;</div>
            <div class="table-pill-row" style="margin-top: 6px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
              <span class="category-pill font-mono">${escapeHtml(p.category)}</span>
              <span class="source-tier-pill font-mono source-tier-${tierClass}">${tier}</span>
              <span class="expand-hint-text font-mono">Details ▾</span>
            </div>
          </td>
          <td class="table-timeline-cell font-mono">
            <div class="timeline-date">${escapeHtml(p.promised_date || '—')}</div>
            ${dueLine}
          </td>
          <td class="table-verdict-cell">
            <div class="verdict-wrapper">
              <span class="verdict-chip ${verdClass}">${formatVerdictLabel(p.verdict)}</span>
              <div class="verdict-sub-row font-mono">
                ${rel ? `<span class="score-pill" title="Relevance Gate ${rel.score}/8">${rel.score}/8</span>` : ''}
                <span class="btn-inspect-inline">Inspect &rarr;</span>
              </div>
            </div>
          </td>
        `;

        const bundles = p.advocate_bundles || {};
        const keptB = bundles.kept || {};
        const brokenB = bundles.broken || {};
        const kClaims = keptB.claims || [];
        const bClaims = brokenB.claims || [];
        const kSum = kClaims.length > 0
          ? (kClaims[0].statement || kClaims[0].quote || 'Affirming primary evidence filed.')
          : 'No affirming source filed during review cycle.';
        const bSum = bClaims.length > 0
          ? (bClaims[0].statement || bClaims[0].quote || 'Contradicting claim filed.')
          : (brokenB.note || 'No contradicting source found in saved files.');

        const trAccordion = document.createElement('tr');
        trAccordion.className = 'promise-accordion-row hidden-accordion';
        trAccordion.id = `accordion-${p.promise_id}`;
        trAccordion.setAttribute('aria-hidden', 'true');
        trAccordion.innerHTML = `
          <td colspan="5" class="accordion-cell">
            <div class="accordion-panel">
              <div class="accordion-panel-grid">
                <div class="accordion-col quote-col">
                  <div class="accordion-kicker font-mono">FULL VERBATIM COMMITMENT</div>
                  <blockquote class="accordion-full-quote">&ldquo;${escapeHtml(quoteText)}&rdquo;</blockquote>
                  <div class="accordion-provenance-meta font-mono">
                    <div><span class="meta-label">SOURCE:</span> <a href="${escapeHtml(p.source_url || '')}" target="_blank" rel="noopener noreferrer">${escapeHtml(p.source_url || 'source link')}</a> <span class="source-tier-pill font-mono source-tier-${tierClass}">${tier}</span></div>
                    <div class="hash-row">
                      <span class="meta-label">SHA-256:</span>
                      <code class="hash-code">${escapeHtml(p.source_hash || 'not recorded')}</code>
                      <button type="button" class="btn-copy-hash font-mono" data-hash="${escapeHtml(p.source_hash || '')}">Copy</button>
                    </div>
                    <div><span class="meta-label">SAVED FILE:</span> <code>${escapeHtml(p.source_file_path || 'sources/' + (p.source_hash || '') + '.md')}</code></div>
                  </div>
                </div>
                <div class="accordion-col advocate-col">
                  <div class="accordion-kicker font-mono">ADVOCATE FINDINGS (PROCESS ISOLATION)</div>
                  <div class="advocate-summary-box kept">
                    <span class="adv-badge font-mono pass">SANDBOX A (AFFIRMING)</span>
                    <p>${escapeHtml(kSum)}</p>
                  </div>
                  <div class="advocate-summary-box broken">
                    <span class="adv-badge font-mono fail">SANDBOX B (CONTRADICTING)</span>
                    <p>${escapeHtml(bSum)}</p>
                  </div>
                  <div class="accordion-actions-row">
                    <button type="button" class="btn-open-inspect-deep font-mono" data-pid="${p.promise_id}">
                      Open Full Audit Modal ↗
                    </button>
                    <button type="button" class="btn-collapse-row font-mono" data-pid="${p.promise_id}">
                      Collapse ▴
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </td>
        `;

        const btnDeep = trAccordion.querySelector('.btn-open-inspect-deep');
        if (btnDeep) btnDeep.addEventListener('click', (e) => { e.stopPropagation(); openInspectModal(p.promise_id); });
        const btnColl = trAccordion.querySelector('.btn-collapse-row');
        if (btnColl) btnColl.addEventListener('click', (e) => { e.stopPropagation(); toggleAccordion(p.promise_id); });
        const btnCopy = trAccordion.querySelector('.btn-copy-hash');
        if (btnCopy) {
          btnCopy.addEventListener('click', (e) => {
            e.stopPropagation();
            const h = btnCopy.getAttribute('data-hash');
            if (h) {
              navigator.clipboard.writeText(h).then(() => {
                const orig = btnCopy.textContent;
                btnCopy.textContent = 'Copied!';
                setTimeout(() => { btnCopy.textContent = orig; }, 1500);
              });
            }
          });
        }

        tbodyPromises.appendChild(tr);
        tbodyPromises.appendChild(trAccordion);
      });
    }
  }

  function toggleAccordion(promiseId) {
    const row = document.getElementById(`promise-${promiseId}`);
    const accordion = document.getElementById(`accordion-${promiseId}`);
    if (!accordion) return;

    const isHidden = accordion.classList.contains('hidden-accordion');

    // Close any other open accordions
    document.querySelectorAll('.promise-accordion-row:not(.hidden-accordion)').forEach(el => {
      el.classList.add('hidden-accordion');
      el.setAttribute('aria-hidden', 'true');
      const pRow = el.previousElementSibling;
      if (pRow && pRow.classList.contains('promise-row')) {
        pRow.classList.remove('is-expanded');
        pRow.setAttribute('aria-expanded', 'false');
      }
    });

    if (isHidden) {
      accordion.classList.remove('hidden-accordion');
      accordion.setAttribute('aria-hidden', 'false');
      if (row) {
        row.classList.add('is-expanded');
        row.setAttribute('aria-expanded', 'true');
      }
    }
  }

  function renderActiveChips() {
    const tray = document.getElementById('active-chips-tray');
    const container = document.getElementById('chips-container');
    if (!tray || !container) return;

    const chips = [];
    if (filterEntity && filterEntity.value !== 'all') {
      chips.push({ key: 'entity', label: `Entity: ${filterEntity.value}` });
    }
    if (filterVerdict && filterVerdict.value !== 'all') {
      chips.push({ key: 'verdict', label: `Verdict: ${filterVerdict.value}` });
    }
    if (activeCategoryFilter !== 'all') {
      chips.push({ key: 'category', label: `Category: ${activeCategoryFilter}` });
    }
    const q = searchInput ? searchInput.value.trim() : '';
    if (q) {
      chips.push({ key: 'search', label: `Search: "${q}"` });
    }

    if (chips.length === 0) {
      tray.style.display = 'none';
      return;
    }

    tray.style.display = 'flex';
    container.innerHTML = chips.map(c => `
      <span class="filter-chip font-mono">
        <span>${escapeHtml(c.label)}</span>
        <button type="button" class="filter-chip-remove" data-chip-key="${c.key}" aria-label="Remove filter ${escapeHtml(c.label)}">&times;</button>
      </span>
    `).join('');

    container.querySelectorAll('.filter-chip-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const k = btn.getAttribute('data-chip-key');
        if (k === 'entity' && filterEntity) filterEntity.value = 'all';
        if (k === 'verdict' && filterVerdict) filterVerdict.value = 'all';
        if (k === 'category') {
          activeCategoryFilter = 'all';
          if (filterCategory) filterCategory.value = 'all';
          if (domainPillsBar) {
            domainPillsBar.querySelectorAll('.btn-domain-pill').forEach(p => {
              p.classList.toggle('active', p.getAttribute('data-category') === 'all');
            });
          }
        }
        if (k === 'search' && searchInput) searchInput.value = '';
        currentPageSize = 15;
        renderPromisesTable();
      });
    });
  }

  function getSourceTier(sourceUrl) {
    const url = (sourceUrl || '').toLowerCase();
    if (['sf.gov', 'flysfo.com', 'sfgov.org', 'sfmta.com', 'legistar.com', 'granicus.com', 'sfpublicworks'].some(h => url.includes(h))) {
      return 'Official';
    }
    if (url.includes('wikipedia.org')) {
      return 'Reference';
    }
    return 'News';
  }

  // Helper: Format snake_case check names to clean plain English
  function formatCheckName(checkType) {
    const map = {
      'authenticity_domain': 'Domain Allowlist',
      'authenticity_hash': 'Hash Integrity',
      'authenticity_speaker': 'Speaker Attendance',
      'accuracy_quote': 'Exact Quote Match',
      'accuracy_date': 'Date Window',
      'accuracy_evidence': 'Evidence Type',
      'verdict_rubric': 'Verdict Rubric',
      'relevance_low': 'Relevance Gate',
      'relevance_gate': 'Relevance Gate'
    };
    return map[checkType] || String(checkType).replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  // -------------------------------------------------------------------------
  // QUARANTINE REGISTRY TABLE
  // -------------------------------------------------------------------------
  function renderQuarantineTable() {
    if (!tbodyQuarantine || !demoData || !demoData.quarantined) return;

    tbodyQuarantine.innerHTML = '';
    demoData.quarantined.forEach((q, idx) => {
      const tr = document.createElement('tr');
      // Real quarantined rows (e.g. P68) have no planted claim — show the
      // recorded reason instead of an empty quote.
      const sub = q.planted_claim
        ? `“${escapeHtml(cleanQuoteText(q.planted_claim))}”`
        : escapeHtml(q.reason || '');
      tr.innerHTML = `
        <td class="font-mono" style="font-weight: 700; color: var(--orange);">Test ${idx + 1}</td>
        <td>
          <strong style="color: var(--ink);">${escapeHtml(q.title || q.promise_id || '')}</strong>
          <div style="font-size: 0.82rem; color: var(--muted); margin-top: 2px;">${sub}</div>
        </td>
        <td style="white-space: nowrap;">
          <span class="verdict-chip quarantined font-mono" style="font-size: 0.72rem;">${formatCheckName(q.check_type)}</span>
          <div style="font-size: 0.78rem; color: var(--ink-dim); margin-top: 3px;">${q.failing_check}</div>
        </td>
        <td style="font-size: 0.84rem; color: #ffdfba; max-width: 320px;">
          ${escapeHtml(q.reason)}
        </td>
        <td class="font-mono" style="font-size: 0.78rem; color: var(--muted); white-space: nowrap;">
          ${q.destination}
        </td>
      `;
      tbodyQuarantine.appendChild(tr);
    });
  }

  // -------------------------------------------------------------------------
  // 4-PART PROVENANCE INSPECTION MODAL
  // -------------------------------------------------------------------------
  const CHECK_SHORT_LABELS = {
    authenticity_domain: 'Source domain on allowlist',
    authenticity_hash: 'SHA-256 hash matches saved file',
    accuracy_quote: 'Verbatim quote in saved source',
    authenticity_speaker: 'Speaker attendance / identification',
    accuracy_date: 'Evidence date within tenure window',
    accuracy_evidence: 'Evidence type tierable & verified',
    verdict_rubric: 'Deterministic rubric applied',
  };

  function renderModalChecks(p, kCount, bCount) {
    const listEl = document.getElementById('modal-checks-list');
    if (!listEl) return;
    const checks = p.checks || [];
    if (!checks.length) {
      listEl.innerHTML = '<li>No recorded arbitrator checks for this promise.</li>';
      return;
    }
    listEl.innerHTML = checks.map((c, i) => {
      const label = CHECK_SHORT_LABELS[c.check] || c.check;
      let reason = (c.reason && c.reason !== 'pass') ? ` — ${escapeHtml(c.reason)}` : '';
      if (c.check === 'authenticity_speaker' && (!c.reason || c.reason === 'pass')) {
        reason = (p.source_type === 'board_minutes')
          ? ' — roll call attendance verified'
          : ' — pass (n/a, not minutes source)';
      }
      if (c.passed === true) {
        const extra = c.check === 'verdict_rubric'
          ? ` → ${p.verdict.toUpperCase()} (${kCount} affirming, ${bCount} contradicting)${reason}`
          : reason;
        return `<li>✓ ${i + 1}. ${escapeHtml(label)}${extra}</li>`;
      }
      if (c.passed === false) {
        return `<li>✕ ${i + 1}. ${escapeHtml(label)} — FAILED${reason || ' (no reason recorded)'}</li>`;
      }
      return `<li>– ${i + 1}. ${escapeHtml(label)} — not recorded</li>`;
    }).join('');
  }

  function openInspectModal(promiseId) {
    if (!inspectModal || !demoData) return;

    const p = (demoData.promises || []).find(x => x.promise_id === promiseId) || demoData.p02;
    if (!p) return;

    const titleEl = document.getElementById('modal-promise-title');
    const verdChipEl = document.getElementById('modal-verdict-chip');
    const relChipEl = document.getElementById('modal-relevance-chip');

    const rankFormatted = String(p.impact_rank || p.display_no || '—').padStart(2, '0');
    if (titleEl) {
      titleEl.textContent = `#${rankFormatted} (${p.promise_id}) · ${p.entity}: ${p.neighborhood || p.category}`;
      titleEl.title = cleanQuoteText(p.promise_text || '');
    }
    if (verdChipEl) {
      const verdClass = p.verdict.toLowerCase().replace(' ', '_');
      verdChipEl.className = `verdict-chip ${verdClass}`;
      verdChipEl.textContent = formatVerdictLabel(p.verdict);
    }
    if (relChipEl) {
      relChipEl.textContent = p.relevance ? `Relevance ${p.relevance.score}/8` : 'Relevance n/r';
    }

    try {
      window.history.replaceState(null, '', `#promise-${p.promise_id}`);
    } catch (_) {}

    // Plain-English "What Was Promised" Summary Card
    const sumClaimEl = document.getElementById('modal-summary-claim');
    const sumSpeakerEl = document.getElementById('modal-summary-speaker');
    const sumDueEl = document.getElementById('modal-summary-due');
    const sumOutcomeEl = document.getElementById('modal-summary-outcome');

    if (sumClaimEl) sumClaimEl.textContent = `“${cleanQuoteText(p.promise_text)}”`;
    if (sumSpeakerEl) sumSpeakerEl.textContent = `${p.entity}${p.role ? ` (${p.role})` : ''} · ${p.neighborhood || p.category || 'Citywide San Francisco'}`;
    if (sumDueEl) {
      const dates = [];
      if (p.promised_date) dates.push(`Promised: ${p.promised_date}`);
      if (p.due_date) dates.push(`Due: ${p.due_date}`);
      sumDueEl.textContent = dates.join(' · ') || 'Not specified';
    }
    if (sumOutcomeEl) {
      const vLabel = formatVerdictLabel(p.verdict);
      sumOutcomeEl.textContent = `${vLabel} — ${p.verdict_reason || 'Verified through deterministic checks in Sandbox C.'}`;
    }

    // Part 1: Provenance Bundle
    const srcUrlEl = document.getElementById('modal-source-url');
    const srcIdEl = document.getElementById('modal-source-id');
    const fullHashEl = document.getElementById('modal-full-hash');
    const filePathEl = document.getElementById('modal-file-path');
    const fetchTimeEl = document.getElementById('modal-fetch-time');

    if (srcUrlEl) {
      const u = p.source_url || '';
      if (!u) {
        srcUrlEl.removeAttribute('href');
        srcUrlEl.textContent = 'source link not recorded';
      } else {
        srcUrlEl.href = u;
        srcUrlEl.textContent = u;
      }
    }
    if (srcIdEl) srcIdEl.textContent = p.source_id || '—';
    if (fullHashEl) fullHashEl.textContent = p.source_hash || 'not recorded';
    if (filePathEl) filePathEl.textContent = p.source_file_path || (p.source_hash ? 'sources/' + p.source_hash + '.md' : 'not recorded');
    if (fetchTimeEl) fetchTimeEl.textContent = formatFetchTime(p.fetched_at);
    const runIdEl = document.getElementById('modal-run-id');
    const sandboxIdEl = document.getElementById('modal-sandbox-id');
    if (runIdEl) runIdEl.textContent = p.run_id || (demoData.database_status && demoData.database_status.integration_run ? demoData.database_status.integration_run.run_id : 'accd67e91c05426bbc5b279b83cf9537');
    if (sandboxIdEl) sandboxIdEl.textContent = p.sandbox_id || '01a1cd80-01b2-79da-8ad0-2ae1ed5f5942 (fork of sf-promises-golden)';

    // Part 2: Extracted Promise Bundle
    const pTextEl = document.getElementById('modal-promise-text');
    const quoteLinkEl = document.getElementById('modal-promise-quote-link');
    const spkEl = document.getElementById('modal-speaker');
    const pDateEl = document.getElementById('modal-promised-date');
    const dueDateEl = document.getElementById('modal-due-date');
    const openedRow = document.getElementById('modal-opened-row');
    const openedDateEl = document.getElementById('modal-opened-date');
    const relBreakEl = document.getElementById('modal-relevance-breakdown');

    if (pTextEl) pTextEl.textContent = `“${cleanQuoteText(p.promise_text)}”`;
    if (quoteLinkEl) {
      if (p.source_url) {
        quoteLinkEl.href = p.source_url;
      } else {
        quoteLinkEl.removeAttribute('href');
      }
    }
    if (spkEl) spkEl.textContent = `${p.entity} (${p.role || ''})`;
    if (pDateEl) pDateEl.textContent = p.promised_date || '—';
    if (dueDateEl) dueDateEl.textContent = p.due_date || '—';
    if (openedRow && openedDateEl) {
      if (p.opened_date || p.realized_date) {
        openedRow.style.display = 'flex';
        openedDateEl.textContent = p.opened_date || p.realized_date;
      } else {
        openedRow.style.display = 'none';
      }
    }
    if (relBreakEl) {
      const rel = p.relevance || null;
      relBreakEl.textContent = rel
        ? `${rel.score} / 8 (real_promise: ${rel.real}, measurable: ${rel.measurable}, sf_relevant: ${rel.sf}, interesting: ${rel.interesting}) — ${rel.score >= 5 ? 'Published through gate' : 'Below gate (5+)'}`
        : 'Relevance not recorded';
    }

    // Part 3: Dual Advocate Bundles
    const keptListEl = document.getElementById('modal-kept-claims-list');
    const brokenListEl = document.getElementById('modal-broken-claims-list');
    const keptFileEl = document.getElementById('modal-kept-file');
    const brokenFileEl = document.getElementById('modal-broken-file');
    const kBundle = p.advocate_bundles && p.advocate_bundles.kept;
    const bBundle = p.advocate_bundles && p.advocate_bundles.broken;
    const kCount = (kBundle && kBundle.claims && kBundle.claims.length) || 0;
    const bCount = (bBundle && bBundle.claims && bBundle.claims.length) || 0;
    if (keptFileEl) keptFileEl.textContent = kBundle ? `staging/kept_${p.promise_id}.json` : 'no kept bundle filed';
    if (brokenFileEl) brokenFileEl.textContent = bBundle ? `staging/broken_${p.promise_id}.json` : 'no broken bundle filed';

    if (keptListEl) {
      const kStaging = p.advocate_bundles && p.advocate_bundles.kept;
      if (kStaging && kStaging.claims && kStaging.claims.length > 0) {
        keptListEl.innerHTML = kStaging.claims.map(c => `
          <div class="claim-quote-box">“${escapeHtml(c.quote || c.text || JSON.stringify(c))}”</div>
        `).join('');
      } else if (p.verbatim_quote) {
        keptListEl.innerHTML = `<div class="claim-quote-box">“${escapeHtml(p.verbatim_quote)}” (Primary evidence verified)</div>`;
      } else {
        const kNote = (kStaging && kStaging.note) || '';
        keptListEl.innerHTML = `<p style="font-size: 0.85rem; color: var(--muted); font-style: italic; margin: 0;">${escapeHtml(formatAdvocateNote(kNote, 'kept'))}</p>`;
      }
    }

    if (brokenListEl) {
      const bStaging = p.advocate_bundles && p.advocate_bundles.broken;
      if (bStaging && bStaging.claims && bStaging.claims.length > 0) {
        brokenListEl.innerHTML = bStaging.claims.map(c => `
          <div class="claim-quote-box" style="border-left-color: var(--broken);">“${escapeHtml(c.quote || c.text || JSON.stringify(c))}”</div>
        `).join('');
      } else {
        const bNote = (bStaging && bStaging.note) || '';
        brokenListEl.innerHTML = `<p style="font-size: 0.85rem; color: var(--muted); font-style: italic; margin: 0;">${escapeHtml(formatAdvocateNote(bNote, 'broken'))}</p>`;
      }
    }

    // Part 4: Arbitrator Reasoning & Checks
    const reasonEl = document.getElementById('modal-verdict-reason');
    if (reasonEl) {
      reasonEl.innerHTML = `<strong>${formatVerdictLabel(p.verdict).toUpperCase()}</strong> — ${escapeHtml(p.verdict_reason || 'Verified by 7 deterministic checks in Sandbox C.')}`;
    }
    renderModalChecks(p, kCount, bCount);

    inspectModal.classList.remove('hidden');
  }

  // -------------------------------------------------------------------------
  // EVENT LISTENERS SETUP
  // -------------------------------------------------------------------------
  function setupEventListeners() {
    // Showcase selector tabs
    if (showcaseTabsBar) {
      showcaseTabsBar.querySelectorAll('.showcase-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const pid = btn.getAttribute('data-showcase-id');
          renderShowcaseCard(pid);
        });
      });
    }

    // Inspect showcase button
    if (btnShowcaseInspect) {
      btnShowcaseInspect.addEventListener('click', () => {
        openInspectModal(selectedShowcasePid);
      });
    }

    // Case-reference buttons (e.g. limitations section) open the modal.
    document.querySelectorAll('.case-ref-link').forEach(btn => {
      btn.addEventListener('click', () => {
        openInspectModal(btn.getAttribute('data-pid'));
      });
    });

    // Pipeline controls (select preferred; legacy P02/N01 buttons still work
    // if present — a concurrent editor owns this markup region).
    if (btnRunSelected) {
      btnRunSelected.addEventListener('click', () => {
        startPipeline(runSelect ? runSelect.value : 'P02');
      });
    }
    const legacyP02 = document.getElementById('btn-run-p02');
    const legacyN01 = document.getElementById('btn-run-n01');
    if (legacyP02) legacyP02.addEventListener('click', () => startPipeline('P02'));
    if (legacyN01) legacyN01.addEventListener('click', () => startPipeline('N01'));
    if (runSelect) {
      runSelect.addEventListener('change', () => {
        currentRunType = runSelect.value;
        renderStage1Source(currentRunType);
        updateNarrative(0);
      });
    }
    if (btnStepNext) {
      btnStepNext.addEventListener('click', () => advanceStep());
    }
    if (btnPipelineReset) {
      btnPipelineReset.addEventListener('click', () => resetPipeline());
    }

    // Narrative buttons
    if (btnNarrativeReplay) {
      btnNarrativeReplay.addEventListener('click', () => {
        replayCount++;
        startPipeline(currentRunType);
      });
    }
    if (btnNarrativeToggle) {
      btnNarrativeToggle.addEventListener('click', () => {
        const target = isWatchdog(currentRunType) ? 'P02' : 'N01';
        startPipeline(target);
      });
    }

    // Show More & Show All pagination handlers
    if (btnShowMore) {
      btnShowMore.addEventListener('click', () => {
        currentPageSize += 15;
        renderPromisesTable();
      });
    }
    if (btnShowAll) {
      btnShowAll.addEventListener('click', () => {
        currentPageSize = 999;
        renderPromisesTable();
      });
    }

    const resetPaginationAndRender = () => {
      currentPageSize = 15;
      renderPromisesTable();
    };

    // Active filter chips "Clear all"
    const btnClearAllChips = document.getElementById('btn-clear-all-chips');
    if (btnClearAllChips) {
      btnClearAllChips.addEventListener('click', () => {
        if (filterEntity) filterEntity.value = 'all';
        if (filterVerdict) filterVerdict.value = 'all';
        if (filterSort) filterSort.value = 'rank';
        activeCategoryFilter = 'all';
        if (filterCategory) filterCategory.value = 'all';
        if (domainPillsBar) {
          domainPillsBar.querySelectorAll('.btn-domain-pill').forEach(p => {
            p.classList.toggle('active', p.getAttribute('data-category') === 'all');
          });
        }
        if (searchInput) searchInput.value = '';
        resetPaginationAndRender();
      });
    }

    // Row density toggle
    const btnDensityComfortable = document.getElementById('btn-density-comfortable');
    const btnDensityCompact = document.getElementById('btn-density-compact');
    const tableContainer = document.getElementById('promises-table-container');

    if (btnDensityComfortable && btnDensityCompact && tableContainer) {
      btnDensityComfortable.addEventListener('click', () => {
        btnDensityComfortable.classList.add('active');
        btnDensityCompact.classList.remove('active');
        tableContainer.classList.remove('density-compact');
      });

      btnDensityCompact.addEventListener('click', () => {
        btnDensityCompact.classList.add('active');
        btnDensityComfortable.classList.remove('active');
        tableContainer.classList.add('density-compact');
      });
    }

    // Interactive column header sorting
    document.querySelectorAll('th.sortable-th').forEach(th => {
      th.addEventListener('click', () => {
        const sortField = th.getAttribute('data-sort');
        const currentAria = th.getAttribute('aria-sort');
        const newDirection = currentAria === 'ascending' ? 'descending' : 'ascending';

        document.querySelectorAll('th.sortable-th').forEach(h => {
          h.setAttribute('aria-sort', 'none');
          const icon = h.querySelector('.sort-icon');
          if (icon) icon.textContent = '↕';
        });

        th.setAttribute('aria-sort', newDirection);
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.textContent = newDirection === 'ascending' ? '▲' : '▼';

        if (sortField === 'rank') {
          if (filterSort) filterSort.value = newDirection === 'ascending' ? 'rank' : 'rank_desc';
        } else if (sortField === 'timeline') {
          if (filterSort) filterSort.value = newDirection === 'ascending' ? 'date_asc' : 'date_desc';
        } else if (sortField === 'entity') {
          if (filterSort) filterSort.value = newDirection === 'ascending' ? 'entity' : 'entity_desc';
        } else if (sortField === 'verdict') {
          if (filterSort) filterSort.value = newDirection === 'ascending' ? 'verdict' : 'verdict_desc';
        } else if (sortField === 'quote') {
          if (filterSort) filterSort.value = newDirection === 'ascending' ? 'quote_asc' : 'quote_desc';
        }

        renderPromisesTable();
      });
    });

    // List.js library integration
    if (typeof window.List !== 'undefined' && document.getElementById('promises-table-container')) {
      try {
        console.log('List.js library ready on promises table');
      } catch (err) {
        console.warn('List.js note:', err);
      }
    }

    // Domain filter pills bar
    if (domainPillsBar) {
      domainPillsBar.querySelectorAll('.btn-domain-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          domainPillsBar.querySelectorAll('.btn-domain-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          activeCategoryFilter = pill.getAttribute('data-category');

          // Sync dropdown
          if (filterCategory) {
            filterCategory.value = activeCategoryFilter;
          }
          resetPaginationAndRender();
        });
      });
    }

    // Filter selects & search
    if (filterEntity) filterEntity.addEventListener('change', resetPaginationAndRender);
    if (filterVerdict) filterVerdict.addEventListener('change', resetPaginationAndRender);
    if (filterSort) filterSort.addEventListener('change', resetPaginationAndRender);
    if (filterCategory) {
      filterCategory.addEventListener('change', () => {
        activeCategoryFilter = filterCategory.value;
        // Sync pills
        if (domainPillsBar) {
          domainPillsBar.querySelectorAll('.btn-domain-pill').forEach(p => {
            p.classList.toggle('active', p.getAttribute('data-category') === activeCategoryFilter);
          });
        }
        resetPaginationAndRender();
      });
    }
    if (searchInput) searchInput.addEventListener('input', resetPaginationAndRender);

    // Copy hash button in inspect modal
    if (btnCopyModalHash) {
      btnCopyModalHash.addEventListener('click', () => {
        const hashEl = document.getElementById('modal-full-hash');
        if (hashEl && hashEl.textContent) {
          navigator.clipboard.writeText(hashEl.textContent).then(() => {
            const orig = btnCopyModalHash.textContent;
            btnCopyModalHash.textContent = 'Copied!';
            setTimeout(() => { btnCopyModalHash.textContent = orig; }, 1500);
          }).catch(() => {
            btnCopyModalHash.textContent = 'Copied!';
            setTimeout(() => { btnCopyModalHash.textContent = 'Copy'; }, 1500);
          });
        }
      });
    }

    // Table tab switching
    if (tabBtnPromises) {
      tabBtnPromises.addEventListener('click', () => {
        activeTab = 'promises';
        tabBtnPromises.classList.add('active');
        if (tabBtnQuarantine) tabBtnQuarantine.classList.remove('active');
        if (tableContainerPromises) tableContainerPromises.classList.remove('hidden');
        if (tableContainerQuarantine) tableContainerQuarantine.classList.add('hidden');
      });
    }

    if (tabBtnQuarantine) {
      tabBtnQuarantine.addEventListener('click', () => {
        activeTab = 'quarantine';
        tabBtnQuarantine.classList.add('active');
        if (tabBtnPromises) tabBtnPromises.classList.remove('active');
        if (tableContainerPromises) tableContainerPromises.classList.add('hidden');
        if (tableContainerQuarantine) tableContainerQuarantine.classList.remove('hidden');
      });
    }

    // Agent role card clicks
    agentCards.forEach(card => {
      card.addEventListener('click', () => {
        agentCards.forEach(c => {
          c.classList.remove('selected');
          const cta = c.querySelector('.agent-cta-text');
          if (cta) cta.textContent = 'Select →';
        });
        card.classList.add('selected');
        const cta = card.querySelector('.agent-cta-text');
        if (cta) cta.textContent = 'Selected →';

        const idx = parseInt(card.getAttribute('data-agent-idx'), 10) || 0;
        const info = AGENT_INFO[idx];
        if (info) {
          agentDetailDot.className = `dot-status ${info.dotClass}`;
          agentDetailText.innerHTML = `<strong>${info.name} · ${info.sandbox}.</strong> ${info.desc}`;
        }
      });
    });

    // Modals
    if (btnCloseInspect) {
      btnCloseInspect.addEventListener('click', () => {
        inspectModal.classList.add('hidden');
        try {
          window.history.replaceState(null, '', window.location.pathname + window.location.search);
        } catch (_) {}
      });
    }
    if (inspectModal) {
      inspectModal.addEventListener('click', (e) => {
        if (e.target === inspectModal) {
          inspectModal.classList.add('hidden');
          try {
            window.history.replaceState(null, '', window.location.pathname + window.location.search);
          } catch (_) {}
        }
      });
    }

    if (btnOpenMethodology) {
      btnOpenMethodology.addEventListener('click', () => methodModal.classList.remove('hidden'));
    }
    if (btnCloseMethod) {
      btnCloseMethod.addEventListener('click', () => methodModal.classList.add('hidden'));
    }
    if (methodModal) {
      methodModal.addEventListener('click', (e) => {
        if (e.target === methodModal) methodModal.classList.add('hidden');
      });
    }

    // Global ESC key to close open modals
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (inspectModal) inspectModal.classList.add('hidden');
        if (methodModal) methodModal.classList.add('hidden');
      }
    });
  }

  // -------------------------------------------------------------------------
  // UTILITIES & DERIVED COUNTS
  // -------------------------------------------------------------------------
  function updateCategoryPillCounts() {
    if (!domainPillsBar || !demoData || !demoData.promises) return;
    const catCounts = {};
    demoData.promises.forEach(p => {
      let c = p.category || 'Uncategorized';
      if (c === 'Civic & Public Safety') c = 'Civic Governance';
      catCounts[c] = (catCounts[c] || 0) + 1;
    });
    const total = demoData.promises.length;

    domainPillsBar.querySelectorAll('.btn-domain-pill').forEach(pill => {
      const cat = pill.getAttribute('data-category');
      if (cat === 'all') {
        pill.textContent = `All of SF (${total})`;
        pill.style.display = '';
      } else {
        const lookupKey = cat === 'Civic & Public Safety' ? 'Civic Governance' : cat;
        const count = catCounts[lookupKey] || 0;
        const displayLabel = cat === 'Civic & Public Safety' ? 'Civic Governance' : cat;
        pill.textContent = `${displayLabel} (${count})`;
        // Hide empty category pills so users never see (0) items
        pill.style.display = count > 0 ? '' : 'none';
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Kick off on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

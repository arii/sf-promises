/**
 * SF Promises - Main Client Application
 * Grounded Civic Accountability with Pure Deterministic Verification
 */

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  let demoData = null;
  let activeTab = 'promises';
  let activeViewMode = 'table';
  let filterVerdict = 'all';
  let filterCategory = 'all';
  let filterEntity = 'all';
  let filterTier = 'all';
  let filterPillar = 'all';
  let filterAuditFlag = 'all';
  let filterSort = 'rank';
  let searchTerm = '';
  let visibleRowsCount = 10;
  let currentRunType = 'P02'; // Default to #01 · 24/7 Crisis Center
  let currentStage = 1;
  let isAutoPlaying = true;
  let autoTimer = null;
  const STAGE_INTERVAL_MS = 1800;
  let lastActiveElement = null;
  // Replay scenarios are built from the exported snapshot in init(); the
  // walkthrough showcases are the pipeline demo records, with every stage
  // string derived from the record's own fields.
  let SCENARIOS = {};
  const SCENARIO_SHOWCASE_IDS = ['P02', 'P05', 'SFO-01', 'P06'];

  function formatPrecisionDate(dateStr, precision) {
    if (!dateStr || String(dateStr).trim() === '' || dateStr === 'None' || dateStr === '—' || dateStr === 'not recorded') {
      return 'not recorded';
    }
    const s = String(dateStr).trim();
    if (precision === 'year' && s.length >= 4) return s.slice(0, 4);
    if (precision === 'month' && s.length >= 7) return s.slice(0, 7);
    return s;
  }

  // -------------------------------------------------------------------------
  // Plain Reason Lookup (1.3)
  // -------------------------------------------------------------------------
  function formatPlainVerdictReason(reason, verdict, promiseId) {
    if (promiseId && demoData && demoData.promises) {
      const match = demoData.promises.find(x => x.promise_id === promiseId);
      if (match && match.factual_outcome) return match.factual_outcome;
    }
    if (!reason) {
      const v = (verdict || '').toLowerCase();
      if (v === 'kept') return 'Official primary records confirm this commitment was completed as promised.';
      if (v === 'broken') return 'Target was not met or the commitment was not fulfilled.';
      if (v === 'in_progress') return 'Active initiative with progress underway, awaiting final milestone delivery.';
      if (v === 'undecided') return 'Untestable: verifiable metrics or outcome records were not documented.';
      return 'Not recorded.';
    }

    const r = String(reason).trim();
    if (r.startsWith('official primary evidence confirms completion')) {
      return 'Official primary records confirm completion with zero contradicting claims.';
    }
    if (r.startsWith('numeric target not met or plan abandoned')) {
      return 'Numeric target was not met or the initiative was abandoned before completion.';
    }
    if (r.startsWith('due date passed with no passing kept evidence')) {
      return 'Scheduled deadline passed with no official evidence verifying completion.';
    }
    if (r.startsWith('due date in future and no definitive resolution yet')) {
      return 'Deadline is in the future; ongoing work has not yet met final completion.';
    }
    if (r.startsWith('genuine partial completion')) {
      return 'Milestones partially delivered, but the full promised scope remains unfinished.';
    }
    if (r.startsWith('in_progress:')) {
      return 'Active initiative with progress underway, awaiting final milestone delivery.';
    }
    if (r.startsWith('contradicting primary evidence outranks affirmative claims')) {
      return 'Verified contradicting evidence outranks initial affirmative claims.';
    }
    if (r.toLowerCase().includes('untestable')) {
      return 'Untestable: verifiable metrics or baseline counts were not recorded.';
    }
    if (r.startsWith('ordinance signed pre-deadline')) {
      return 'Enabling legislation was enacted before the stated deadline.';
    }
    const cleaned = r.replace(/\s*\([^)]*\)/g, '').replace(/\s*\[[^\]]*\]/g, '').trim() || r;
    // Display strings must not start lowercase: pipeline reasons like
    // "re-open: 30-show Sphere leg..." surface verbatim in the drawer.
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  }

  function formatVerdictLabel(verdict) {
    const v = (verdict || '').toLowerCase().replace(/[\s-]+/g, '_');
    if (v === 'in_progress') return 'In progress';
    if (v === 'kept') return 'Kept';
    if (v === 'kept_then_reversed') return 'Later closed / reversed';
    if (v === 'broken') return 'Broken';
    if (v === 'undecided') return 'Undecided';
    if (v === 'quarantined') return 'Quarantined';
    return verdict ? verdict.charAt(0).toUpperCase() + verdict.slice(1) : 'Undecided';
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

  function cleanQuoteText(text) {
    if (!text) return '';
    let t = String(text);
    // Strip markdown links [link text](http...) -> link text
    t = t.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    // Strip editorial notes like [Reported by The Frisc] or [Reported by ...]
    t = t.replace(/\[(?:Reported by|Source:|Note:)[^\]]+\]\s*/gi, '');
    // Strip bracketed words if any leftover
    t = t.replace(/\[([^\]]+)\]/g, '$1');
    // Strip formatting
    t = t.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1').replace(/`([^`]+)`/g, '$1');
    t = t.replace(/\s+/g, ' ').trim();
    while ((t.startsWith('“') && t.endsWith('”')) || (t.startsWith('"') && t.endsWith('"'))) {
      t = t.slice(1, -1).trim();
    }
    return t;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // -------------------------------------------------------------------------
  // Visualization derivations (pure) — the marked block is executed standalone
  // by tests/test_demo_visualizations.py to reconcile chart counts against the
  // exported snapshot.
  // -------------------------------------------------------------------------
  /* SFPVIZ_PURE_START */
  const VERDICT_ORDER = ['kept', 'delayed_or_partial', 'in_progress', 'broken', 'stalled', 'undecided', 'kept_then_reversed'];

  function normalizeVerdict(value) {
    return String(value || 'undecided').toLowerCase().replace(/[\s-]+/g, '_');
  }

  function countByVerdict(promises) {
    // The export already collapses each promise's verdict history to the
    // latest applicable verdict, so each record counts exactly once.
    const counts = {};
    (promises || []).forEach(p => {
      const v = normalizeVerdict(p && p.verdict);
      counts[v] = (counts[v] || 0) + 1;
    });
    return counts;
  }

  function countByField(promises, field, fallback) {
    const counts = {};
    (promises || []).forEach(p => {
      const key = String((p && p[field]) || '').trim() || fallback;
      counts[key] = (counts[key] || 0) + 1;
    });
    return counts;
  }

  function countByCategory(promises) {
    return countByField(promises, 'category', 'Other');
  }

  function countBySourceType(promises) {
    return countByField(promises, 'source_type', 'unknown');
  }

  function countByYearAndVerdict(promises) {
    // Stacked buckets per year of promised_date, zero-filling every year
    // between the earliest and latest so coverage gaps stay visible.
    const buckets = {};
    let minYear = null;
    let maxYear = null;
    (promises || []).forEach(p => {
      const year = String((p && p.promised_date) || '').slice(0, 4);
      if (!/^\d{4}$/.test(year)) return;
      const v = normalizeVerdict(p.verdict);
      const bucket = buckets[year] || (buckets[year] = {});
      bucket[v] = (bucket[v] || 0) + 1;
      if (minYear === null || year < minYear) minYear = year;
      if (maxYear === null || year > maxYear) maxYear = year;
    });
    if (minYear === null) return [];
    const out = [];
    for (let y = Number(minYear); y <= Number(maxYear); y++) {
      const key = String(y);
      out.push({ year: key, verdicts: buckets[key] || {} });
    }
    return out;
  }

  function funnelStages(databaseStatus) {
    // Stage rows from the exported funnel summary; rows without a finite
    // count are dropped rather than charted as zero.
    const funnel = (databaseStatus && databaseStatus.funnel) || {};
    const stages = Array.isArray(funnel.stages) ? funnel.stages : [];
    return stages.filter(s => s && s.stage && Number.isFinite(Number(s.count)))
      .map(s => ({
        stage: String(s.stage),
        count: Number(s.count),
        universe: String(s.universe || 'database'),
        conversion: Number.isFinite(Number(s.conversion_from_previous))
          ? Number(s.conversion_from_previous)
          : null
      }));
  }

  function windowFunnelStages(databaseStatus) {
    // Per-window funnel summaries from the exported snapshot; each window's
    // stages flow raw -> allowlisted -> archived -> leads -> gate. Windows
    // without a window label or a stages array are dropped.
    const funnel = (databaseStatus && databaseStatus.funnel) || {};
    const windows = Array.isArray(funnel.windows) ? funnel.windows : [];
    return windows.filter(w => w && w.window && Array.isArray(w.stages))
      .map(w => ({
        window: String(w.window),
        roundCount: Array.isArray(w.round_ids) ? w.round_ids.length : 0,
        stages: w.stages.filter(s => s && s.stage && Number.isFinite(Number(s.count)))
          .map(s => ({
            stage: String(s.stage),
            count: Number(s.count),
            conversion: Number.isFinite(Number(s.conversion_from_previous))
              ? Number(s.conversion_from_previous)
              : null
          }))
      }));
  }

  function quarantineReasons(databaseStatus) {
    // Reason-code distribution over the exported quarantine registry.
    const qr = (databaseStatus && databaseStatus.quarantine_reasons) || {};
    const src = (qr.by_reason && typeof qr.by_reason === 'object') ? qr.by_reason : {};
    const byReason = {};
    Object.keys(src).forEach(code => {
      const n = Number(src[code]);
      if (Number.isFinite(n) && n > 0) byReason[String(code)] = n;
    });
    return {
      totalQuarantined: Number.isFinite(Number(qr.total_quarantined)) ? Number(qr.total_quarantined) : null,
      totalReasonCodes: Number.isFinite(Number(qr.total_reason_codes)) ? Number(qr.total_reason_codes) : null,
      byReason
    };
  }

  function denialDomains(databaseStatus) {
    // Per-domain denial histogram, tallest first; ties break alphabetically.
    const denials = (databaseStatus && databaseStatus.denials) || {};
    const byDomain = (denials.by_domain && typeof denials.by_domain === 'object') ? denials.by_domain : {};
    return Object.keys(byDomain).map(domain => ({
      domain: String(domain),
      count: Number(byDomain[domain] && byDomain[domain].count) || 0,
      sourceTypes: (byDomain[domain] && byDomain[domain].source_types) || {}
    })).sort((a, b) => (b.count - a.count) || a.domain.localeCompare(b.domain));
  }

    // Human-readable labels for the source-type enum values; anything not
    // mapped falls back to a title-cased version of the raw value.
    function formatSourceTypeLabel(t) {
      const k = String(t || 'unknown').toLowerCase().replace(/[\s-]+/g, '_');
      const labels = {
        news_report: 'News report',
        press_release: 'Press release',
        official_press_release: 'Official press release',
        sf_gov_page: 'SF government page',
        other_official: 'Other official source',
        social_media: 'Social media post',
        unknown: 'Unknown'
      };
      if (labels[k]) return labels[k];
      return t ? String(t).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : 'Unknown';
    }

  // -------------------------------------------------------------------------
  // Outcome-phase timeline (E5): per-promise made -> due -> delivered ->
  // reversed, derived purely from the exported snapshot. Dates come from the
  // existing enrichment fields (promise_made_date, deadline_date,
  // completion_date) and the evidence dates already carried by the advocate
  // bundles and verdict history — no new collection, no invented dates.
  // -------------------------------------------------------------------------
  const PHASE_LABELS = {
    made: 'Made',
    due: 'Due',
    delivered: 'Delivered',
    reversed: 'Reversed'
  };

  const PHASE_ORDER = ['made', 'due', 'delivered', 'reversed'];

  // 'YYYY-MM-DD…' -> 'YYYY-MM-DD'; null when absent or unparseable. A missing
  // export date is never replaced with a guessed one.
  function dateKey(value) {
    const s = String(value || '').trim();
    return /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : null;
  }

  // '2023-04-01T…' -> 'April 2023'; '' when absent or unparseable. Same
  // month-year form the drawer's verdict timeline displays, so the chart-level
  // phase display and the drawer stay consistent.
  function formatPhaseMonth(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleString('en-US', { month: 'long', year: 'numeric' });
  }

  // Earliest DELIVERY evidence date from one advocate bundle's claims; null
  // when the bundle carries no dated claim.
  function earliestBundleEvidenceDate(promise, side) {
    const bundle = ((promise || {}).advocate_bundles || {})[side];
    const claims = (bundle && Array.isArray(bundle.claims)) ? bundle.claims : [];
    const dates = claims.map(c => dateKey(c && c.evidence_date)).filter(Boolean).sort();
    return dates.length ? dates[0] : null;
  }

  // SURVIVAL transition date: the decided_at of the record's most recent
  // kept_then_reversed verdict-history entry — the same date the drawer's
  // verdict timeline renders for the reversal step. Null when the record was
  // never reversed.
  function reversalDate(promise) {
    const history = Array.isArray((promise || {}).verdict_history) ? promise.verdict_history : [];
    for (let i = history.length - 1; i >= 0; i--) {
      const entry = history[i] || {};
      if (normalizeVerdict(entry.verdict) === 'kept_then_reversed') {
        return dateKey(entry.decided_at);
      }
    }
    return null;
  }

  // Ordered dated phases for one record. A phase appears only when the
  // snapshot records a date for it:
  //   made      — ORIGIN: promise_made_date (falling back to promised_date)
  //   due       — deadline_date (falling back to due_date)
  //   delivered — DELIVERY: completion_date, else for verdicts whose outcome
  //               confirms delivery (kept / kept_then_reversed) the earliest
  //               kept-advocate evidence date
  //   reversed  — SURVIVAL: the kept_then_reversed verdict-history date
  function outcomePhases(p) {
    if (!p || typeof p !== 'object') return [];
    const phases = [];
    const made = dateKey(p.promise_made_date) || dateKey(p.promised_date);
    if (made) phases.push({ phase: 'made', date: made });
    const due = dateKey(p.deadline_date) || dateKey(p.due_date);
    if (due) phases.push({ phase: 'due', date: due });
    const verdict = normalizeVerdict(p.verdict);
    let delivered = dateKey(p.completion_date);
    if (!delivered && (verdict === 'kept' || verdict === 'kept_then_reversed')) {
      delivered = earliestBundleEvidenceDate(p, 'kept');
    }
    if (delivered) phases.push({ phase: 'delivered', date: delivered });
    if (verdict === 'kept_then_reversed') {
      const reversed = reversalDate(p);
      if (reversed) phases.push({ phase: 'reversed', date: reversed });
    }
    return phases.sort((a, b) =>
      (PHASE_ORDER.indexOf(a.phase) - PHASE_ORDER.indexOf(b.phase)) ||
      a.date.localeCompare(b.date));
  }

  // Timeline rows for the outcome-timelines card: one per record carrying at
  // least two dated phases. Records whose verdict history shows a transition
  // lead the card (P83, kept -> reversed, is the showcase), then by display
  // order, so the sort is fully determined by the snapshot.
  function phaseTimelines(promises) {
    const rows = [];
    (promises || []).forEach(p => {
      if (!p || typeof p !== 'object') return;
      const phases = outcomePhases(p);
      if (phases.length < 2) return;
      const history = Array.isArray(p.verdict_history) ? p.verdict_history : [];
      rows.push({
        promiseId: String(p.promise_id || ''),
        displayNo: Number.isFinite(Number(p.display_no)) ? Number(p.display_no) : null,
        label: String(p.document_title || p.title || `${p.entity || 'Unknown'} commitment`),
        historyChanged: history.length > 1,
        reversed: phases.some(ph => ph.phase === 'reversed'),
        phases: phases.map(ph => ({
          phase: ph.phase,
          label: PHASE_LABELS[ph.phase] || ph.phase,
          date: ph.date,
          display: formatPhaseMonth(ph.date)
        }))
      });
    });
    // Reversed records lead (P83 is the showcase), then other verdict
    // transitions, then display order — all determined by the snapshot.
    return rows.sort((a, b) =>
      (Number(b.reversed) - Number(a.reversed)) ||
      (Number(b.historyChanged) - Number(a.historyChanged)) ||
      ((a.displayNo == null ? Infinity : a.displayNo) - (b.displayNo == null ? Infinity : b.displayNo)) ||
      a.promiseId.localeCompare(b.promiseId));
  }

  const SFPViz = {
    VERDICT_ORDER,
    countByVerdict,
    countByCategory,
    countBySourceType,
    formatSourceTypeLabel,
    countByYearAndVerdict,
    funnelStages,
    windowFunnelStages,
    quarantineReasons,
    denialDomains,
    outcomePhases,
    phaseTimelines,
    formatPhaseMonth
  };
  /* SFPVIZ_PURE_END */

  /* SFPUX_PURE_START */
  // Pure UX-state helpers: the error-banner and empty-state copy and the
  // focus-trap cycling math live here so the node harness can exercise them
  // without a DOM.
  const SFPUX = {
    // Visible failure copy for a failed snapshot load. Empty return means the
    // banner stays hidden.
    dataLoadErrorHtml() {
      return 'The live dataset could not be loaded. The record list below is ' +
        'the last statically published snapshot, but filters, charts and the ' +
        'inspect drawer are unavailable. Try refreshing the page.';
    },
    // Prompt rendered when the active filters match zero records.
    noResultsHtml() {
      return '<div class="no-results-inner">' +
        '<p class="no-results-title">No commitments match the current filters.</p>' +
        '<p class="no-results-sub">Try a different search, or clear the filters to see every record.</p>' +
        '<button type="button" class="btn-clear-filters-empty" id="btn-clear-filters-empty">Clear filters</button>' +
        '</div>';
    },
    // Focus-trap cycling: given the count of focusable nodes, the index of the
    // currently focused one (-1 when focus is outside the set) and the
    // direction (Tab vs Shift+Tab), return the next index, wrapping at both
    // ends so Tab can never escape the container.
    nextFocusableIndex(count, currentIndex, backward) {
      if (!Number.isFinite(count) || count <= 0) return currentIndex;
      if (count === 1) return 0;
      const cur = Number.isFinite(currentIndex) && currentIndex >= 0
        ? currentIndex
        : (backward ? count : -1);
      return backward ? (cur - 1 + count) % count : (cur + 1) % count;
    }
  };
  /* SFPUX_PURE_END */


  // -------------------------------------------------------------------------
  // Initialization
  // -------------------------------------------------------------------------
  // Toggle the data-load status and error-banner elements from init().
  // 'loading' shows the status line, 'error' swaps it for the alert banner,
  // 'loaded' hides both.
  function setDataLoadState(state) {
    const errEl = document.getElementById('data-load-error');
    const statusEl = document.getElementById('data-load-status');
    if (errEl) {
      errEl.hidden = state !== 'error';
      if (state === 'error') errEl.textContent = SFPUX.dataLoadErrorHtml();
    }
    if (statusEl) statusEl.hidden = state !== 'loading';
  }

  // Same-origin avatar manifest (issue #83). Optional: any failure leaves avatars off.
  let entityMedia = new Map();
  async function loadEntityMedia() {
    try {
      const res = await fetch('media/manifest.json');
      if (!res.ok) return;
      entityMedia = window.SFPDrawer.entityMediaFromManifest(await res.json());
    } catch (err) {
      console.warn('media manifest unavailable', err);
    }
  }

  async function init() {
    if (window.__DEMO_DATA__) {
      demoData = window.__DEMO_DATA__;
    } else {
      // Late-data path: show a loading state while fetching, and a visible
      // error banner on failure — the statically-baked table stays readable,
      // but the user must know that charts, filters and the drawer are dead.
      setDataLoadState('loading');
      try {
        const res = await fetch('data.json');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        demoData = await res.json();
      } catch (err) {
        console.error('Failed to load data.json', err);
        setDataLoadState('error');
        return;
      }
    }
    setDataLoadState('loaded');
    await loadEntityMedia();

    SCENARIOS = buildScenarios(demoData && demoData.promises);
    if (!SCENARIOS[currentRunType]) {
      const first = Object.keys(SCENARIOS)[0];
      if (first) currentRunType = first;
    }
    setupReplayScenarios();
    // isAutoPlaying starts true (button reads "Pause"), so the timer must actually start.
    scheduleNextAutoStage();
    setupEventListeners();
    enhanceRegistryRows();
    syncCardsLayout();
    renderExplore();
    renderQuarantineTable();
    setupFeaturedStories();
    renderVisualizations();
    const lastCheckedEl = document.getElementById('methodology-last-checked');
    const lastChecked = demoData && demoData.metadata && demoData.metadata.last_checked;
    if (lastCheckedEl && lastChecked) lastCheckedEl.textContent = lastChecked;
    openPermalinkDrawer();
    window.addEventListener('hashchange', openPermalinkDrawer);
  }

  // Per-record permalink: #promise-P02 opens that record's drawer.
  function permalinkId() {
    const m = /^#promise-([A-Za-z0-9_-]+)$/.exec(window.location.hash || '');
    return m ? m[1] : null;
  }

  function openPermalinkDrawer() {
    const pid = permalinkId();
    if (!pid || !demoData) return;
    const exists = (demoData.promises || []).some(x => x.promise_id === pid);
    if (exists) openInspectDrawer(pid);
  }
  // -------------------------------------------------------------------------
  // Replay State Machine (0.5) - Real Commitments, Auto-Play, Zero Layout Shift
  // -------------------------------------------------------------------------
  // Replay scenarios are derived from the exported snapshot: the walkthrough
  // showcases are selected from demoData.promises and every stage string is
  // built from the record's own fields (source, quote, gate score, claim
  // counts, check outcomes, verdict reason). No hardcoded record copy.
  function scenarioFromRecord(p) {
    const rank = String(p.impact_rank || p.display_no || '').padStart(2, '0');
    const rel = p.relevance || {};
    const bundles = p.advocate_bundles || {};
    const keptClaims = ((bundles.kept || {}).claims || []).length;
    const brokenClaims = ((bundles.broken || {}).claims || []).length;
    const checks = p.checks || [];
    const passedChecks = checks.filter(c => c.passed).length;
    const verdict = String(p.verdict || 'undecided').toUpperCase();
    const title = p.document_title || p.title || `${p.entity} Commitment`;
    const quote = cleanQuoteText(p.promise_text || '');
    const hash = String(p.source_hash || '');
    const relTotal = (rel.score != null) ? `${rel.score}/8` : 'recorded in the export';
    return {
      id: p.promise_id,
      label: `#${rank} · ${title}`,
      speaker: p.entity || 'Unknown speaker',
      title,
      expectedVerdict: p.verdict === 'broken' ? 'broken' : 'kept',
      verdictLabel: verdict,
      stages: {
        1: {
          title: 'Source Fetched',
          desc: `Archived ${p.source_type || 'source'} ${hash.slice(0, 8)}… from the ${p.source_tier || 'recorded'} tier.`
        },
        2: {
          title: 'Quote Extracted',
          desc: `“${quote.slice(0, 220)}${quote.length > 220 ? '…' : ''}”`
        },
        3: {
          title: 'Relevance Gate Passed',
          desc: `Relevance gate score ${relTotal} across real-promise, measurable, SF-relevant and interesting signals.`
        },
        4: {
          title: 'Evidence Evaluated',
          desc: `Adjudicated ${keptClaims} supporting vs ${brokenClaims} contradicting claims from the archived record set.`
        },
        5: {
          title: 'Code Checks Passed',
          desc: checks.length
            ? `${passedChecks} of ${checks.length} deterministic code checks passed on the archived source.`
            : 'Deterministic code checks are recorded in the verification history.'
        },
        6: {
          title: 'Verdict Published',
          desc: `Published ${verdict} verdict: ${p.factual_outcome || formatPlainVerdictReason(p.verdict_reason, p.verdict, p.promise_id)}`
        }
      }
    };
  }

  function buildScenarios(promises) {
    const byId = {};
    (promises || []).forEach(p => { byId[p.promise_id] = p; });
    const scenarios = {};
    SCENARIO_SHOWCASE_IDS.forEach(pid => {
      if (byId[pid]) scenarios[pid] = scenarioFromRecord(byId[pid]);
    });
    // Honest degradation: if none of the showcase records are in the
    // snapshot, build the walkthrough from whatever records the snapshot has.
    if (!Object.keys(scenarios).length) {
      (promises || []).slice(0, 2).forEach(p => { scenarios[p.promise_id] = scenarioFromRecord(p); });
    }
    return scenarios;
  }

  function triggerProgressBar() {
    const bar = document.getElementById('pipeline-progress-bar');
    if (!bar) return;
    bar.style.transition = 'none';
    bar.style.width = '0%';
    void bar.offsetWidth; // force reflow
    if (isAutoPlaying && currentStage < 6) {
      bar.style.transition = `width ${STAGE_INTERVAL_MS}ms linear`;
      bar.style.width = '100%';
    } else if (currentStage >= 6) {
      bar.style.transition = 'none';
      bar.style.width = '100%';
    }
  }

  function setupReplayScenarios() {
    const runSelect = document.getElementById('run-select');
    if (!runSelect) return;
    runSelect.innerHTML = '';
    Object.keys(SCENARIOS).forEach(key => {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = SCENARIOS[key].label;
      if (key === currentRunType) opt.selected = true;
      runSelect.appendChild(opt);
    });

    renderActiveStage(currentRunType, currentStage);
  }

  function renderActiveStage(scenarioKey, stageNum) {
    currentStage = stageNum;
    const scenario = SCENARIOS[scenarioKey] || SCENARIOS[currentRunType] || Object.values(SCENARIOS)[0] || {};
    const stageIndicator = document.getElementById('pipeline-stage-indicator');
    const statusText = document.getElementById('packet-status-text');
    const trackFill = document.getElementById('packet-track-fill');
    const ballDot = document.getElementById('packet-ball-dot');
    const ballInner = document.getElementById('packet-ball-inner');
    const primaryIcon = document.getElementById('pipeline-primary-icon');
    const primaryText = document.getElementById('pipeline-primary-text');
    const btnNext = document.getElementById('btn-step-next');
    const btnReset = document.getElementById('btn-pipeline-reset');

    triggerProgressBar();

    // Update contextual buttons (clean Pause / Resume / Replay, Reset)
    if (btnReset) {
      btnReset.disabled = false;
    }

    if (primaryText) {
      if (stageNum >= 6) {
        primaryText.textContent = 'Replay';
        if (primaryIcon) primaryIcon.textContent = '↺';
        if (btnNext) btnNext.setAttribute('aria-label', 'Replay walkthrough from Stage 1');
      } else if (isAutoPlaying) {
        primaryText.textContent = 'Pause';
        if (primaryIcon) primaryIcon.textContent = '⏸';
        if (btnNext) btnNext.setAttribute('aria-label', 'Pause walkthrough');
      } else {
        primaryText.textContent = 'Resume';
        if (primaryIcon) primaryIcon.textContent = '▶';
        if (btnNext) btnNext.setAttribute('aria-label', 'Resume walkthrough');
      }
    }

    // Update 6 Stage Cards inside CSS Grid stack (Zero Layout Shift)
    for (let s = 1; s <= 6; s++) {
      const card = document.querySelector(`.active-stage-panel-wrapper [data-stage="${s}"]`);
      if (card) {
        const sData = scenario.stages[s] || {};
        const isActive = (s === stageNum);
        card.className = `stage-card ${isActive ? 'active-stage' : 'inactive-stage'}`;
        if (isActive) {
          card.id = 'pipeline-active-stage-panel';
        } else {
          card.id = `pipeline-stage-${s}`;
        }

        if (s === 6) {
          const vCls = scenario.expectedVerdict === 'broken' ? 'broken' : 'kept';
          card.innerHTML = `
            <div class="stage-card-header">
              <h3 class="stage-heading">${escapeHtml(sData.title)}</h3>
              <span class="verdict-chip ${vCls}">${escapeHtml(scenario.verdictLabel)}</span>
            </div>
            <p class="stage-desc">${escapeHtml(sData.desc)}</p>
          `;
        } else if (s === 2) {
          card.innerHTML = `
            <div class="stage-card-header">
              <h3 class="stage-heading">${escapeHtml(sData.title)}</h3>
            </div>
            <blockquote class="stage-quote font-serif">${escapeHtml(sData.desc)}</blockquote>
          `;
        } else {
          card.innerHTML = `
            <div class="stage-card-header">
              <h3 class="stage-heading">${escapeHtml(sData.title)}</h3>
            </div>
            <p class="stage-desc">${escapeHtml(sData.desc)}</p>
          `;
        }
      }
    }

    // Update milestone indicators and calculate dead-center active dot
    let activeCenterLeft = 0;
    for (let i = 1; i <= 6; i++) {
      const circle = document.getElementById(`ms-circle-${i}`);
      if (circle) {
        if (i < stageNum) {
          circle.className = 'milestone-circle passed';
          circle.textContent = '✓';
        } else if (i === stageNum) {
          if (stageNum === 6) {
            if (scenario.expectedVerdict === 'broken') {
              circle.className = 'milestone-circle active broken';
              circle.textContent = '✕';
            } else {
              circle.className = 'milestone-circle active kept';
              circle.textContent = '✓';
            }
          } else {
            circle.className = 'milestone-circle active';
            circle.textContent = i;
          }

          const trackContainer = circle.closest('.packet-track-container');
          if (trackContainer) {
            const parentRect = trackContainer.getBoundingClientRect();
            const circleRect = circle.getBoundingClientRect();
            if (parentRect.width > 0) {
              activeCenterLeft = (circleRect.left - parentRect.left) + (circleRect.width / 2);
            }
          }
        } else {
          circle.className = 'milestone-circle';
          circle.textContent = i;
        }
      }
    }

    if (ballInner) {
      ballInner.className = 'packet-ball-inner';
      if (stageNum === 6) {
        if (scenario.expectedVerdict === 'broken') {
          ballInner.classList.add('broken');
        } else {
          ballInner.classList.add('kept');
        }
      }
    }

    if (trackFill) {
      if (stageNum === 6 && scenario.expectedVerdict === 'broken') {
        trackFill.style.background = '#EF4444';
      } else {
        trackFill.style.background = '#10B981';
      }
    }

    if (stageNum >= 1 && stageNum <= 6) {
      if (activeCenterLeft > 0) {
        if (trackFill) trackFill.style.width = `${Math.round(activeCenterLeft)}px`;
        if (ballDot) {
          ballDot.style.left = `${Math.round(activeCenterLeft)}px`;
          ballDot.style.display = 'block';
        }
      } else {
        const fallbackPct = Math.round(((stageNum - 1) / 5) * 100);
        if (trackFill) trackFill.style.width = `${fallbackPct}%`;
        if (ballDot) {
          ballDot.style.left = `${fallbackPct}%`;
          ballDot.style.display = 'block';
        }
      }
    } else {
      if (trackFill) trackFill.style.width = '0%';
      if (ballDot) ballDot.style.display = 'none';
    }

    if (stageIndicator) {
      stageIndicator.textContent = `Stage ${stageNum} of 6`;
    }
    if (statusText) {
      if (stageNum === 6) {
        if (scenario.expectedVerdict === 'broken') {
          statusText.textContent = 'Verified Broken';
          statusText.style.color = '#F87171';
        } else {
          statusText.textContent = 'Verified Kept';
          statusText.style.color = '#34D399';
        }
      } else {
        statusText.textContent = 'In progress';
        statusText.style.color = 'var(--muted)';
      }
    }
  }

  function scheduleNextAutoStage() {
    clearTimeout(autoTimer);
    if (!isAutoPlaying) return;
    if (currentStage >= 6) {
      autoTimer = setTimeout(() => {
        isAutoPlaying = false;
        renderActiveStage(currentRunType, 6);
      }, 2500);
      return;
    }
    autoTimer = setTimeout(() => {
      if (!isAutoPlaying) return;
      if (currentStage < 6) {
        currentStage++;
        renderActiveStage(currentRunType, currentStage);
        scheduleNextAutoStage();
      }
    }, STAGE_INTERVAL_MS);
  }

  function togglePlayPause() {
    if (currentStage >= 6) {
      // Replay from Stage 1
      currentStage = 1;
      isAutoPlaying = true;
      renderActiveStage(currentRunType, 1);
      scheduleNextAutoStage();
      return;
    }

    if (isAutoPlaying) {
      // Pause
      isAutoPlaying = false;
      clearTimeout(autoTimer);
      renderActiveStage(currentRunType, currentStage);
    } else {
      // Resume
      isAutoPlaying = true;
      renderActiveStage(currentRunType, currentStage);
      scheduleNextAutoStage();
    }
  }

  function resetPipeline() {
    console.log('resetPipeline called, setting stage to 1');
    clearTimeout(autoTimer);
    isAutoPlaying = false;
    currentStage = 1;
    renderActiveStage(currentRunType, 1);
  }

  function jumpToStage(num) {
    clearTimeout(autoTimer);
    isAutoPlaying = false;
    currentStage = num;
    renderActiveStage(currentRunType, num);
  }

  window.jumpToStage = jumpToStage;
  window.resetPipeline = resetPipeline;
  window.togglePlayPause = togglePlayPause;
  window.getCurrentStage = () => currentStage;

  // -------------------------------------------------------------------------
  // Visualizations — every chart derives from the exported snapshot
  // -------------------------------------------------------------------------
  const VERDICT_COLORS = {
    kept: '#10B981',
    in_progress: 'var(--verdict-progress)',
    broken: '#EF4444',
    stalled: '#C084FC',
    kept_then_reversed: '#F97316',
    delayed_or_partial: '#F59E0B',
    undecided: 'var(--verdict-undecided)'
  };

  function renderBarRows(container, entries, total) {
    if (!container) return;
    if (!entries.length) {
      container.innerHTML = '<p class="viz-empty">No records in the exported dataset.</p>';
      return;
    }
    const max = Math.max(...entries.map(e => e.count), 1);
    container.innerHTML = entries.map(e => {
      const pct = total ? ` <span class="viz-bar-pct">(${Math.round((e.count / total) * 100)}%)</span>` : '';
      return `
        <div class="viz-bar-row">
          <span class="viz-bar-label" title="${escapeHtml(e.label)}">${escapeHtml(e.label)}</span>
          <span class="viz-bar-track">
            <span class="viz-bar-fill" style="width:${((e.count / max) * 100).toFixed(2)}%; background:${e.color}"></span>
          </span>
          <span class="viz-bar-count font-mono">${e.count}${pct}</span>
        </div>
      `;
    }).join('');
  }

  function renderTimelineChart(promises) {
    const wrap = document.getElementById('viz-timeline');
    if (!wrap) return;
    const buckets = SFPViz.countByYearAndVerdict(promises);
    if (!buckets.length) {
      wrap.innerHTML = '<p class="viz-empty">No dated records in the exported dataset.</p>';
      return;
    }

    const compact = window.matchMedia('(max-width: 600px)').matches;
    const W = compact ? 360 : 760;
    const H = compact ? 280 : 250;
    const pad = { top: 14, right: 12, bottom: 26, left: compact ? 38 : 34 };
    const innerW = W - pad.left - pad.right;
    const innerH = H - pad.top - pad.bottom;
    const perYear = buckets.map(b => Object.values(b.verdicts).reduce((a, c) => a + c, 0));
    const yMax = Math.max(...perYear, 1);
    const colW = innerW / buckets.length;
    const barW = Math.min(30, colW * 0.62);

    let barsSvg = '';
    buckets.forEach((b, i) => {
      const x = pad.left + i * colW + (colW - barW) / 2;
      let y = pad.top + innerH;
      const segs = SFPViz.VERDICT_ORDER.map(v => {
        const c = b.verdicts[v] || 0;
        if (!c) return '';
        const h = Math.max(1.5, (c / yMax) * innerH);
        y -= h;
        return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${h.toFixed(1)}" fill="${VERDICT_COLORS[v]}" rx="1.5"><title>${b.year}: ${c} ${formatVerdictLabel(v)}</title></rect>`;
      }).join('');
      barsSvg += segs;
    });

    const tickStep = yMax > 8 ? Math.ceil(yMax / 4) : (yMax > 4 ? 2 : 1);
    let gridSvg = '';
    for (let t = 0; t <= yMax; t += tickStep) {
      const y = (pad.top + innerH - (t / yMax) * innerH).toFixed(1);
      gridSvg += `<line x1="${pad.left}" y1="${y}" x2="${W - pad.right}" y2="${y}" stroke="var(--line-soft)" stroke-width="1" />`;
      gridSvg += `<text x="${pad.left - 6}" y="${Number(y) + 3}" text-anchor="end" font-size="${compact ? 11 : 9}" fill="var(--muted)" font-family="monospace">${t}</text>`;
    }

    let axisSvg = '';
    let previousLabelX = -Infinity;
    const lastLabelX = pad.left + (buckets.length - 0.5) * colW;
    const labelGap = compact ? 40 : 30;
    buckets.forEach((b, i) => {
      const endpoint = i === 0 || i === buckets.length - 1;
      const x = pad.left + i * colW + colW / 2;
      const showLabel = endpoint || (Number(b.year) % 5 === 0 &&
        x - previousLabelX >= labelGap && lastLabelX - x >= labelGap);
      if (!showLabel) return;
      previousLabelX = x;
      axisSvg += `<text x="${x.toFixed(1)}" y="${H - 8}" text-anchor="middle" font-size="${compact ? 11 : 9}" fill="var(--muted)" font-family="monospace">${b.year}</text>`;
    });

    wrap.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Stacked bar chart of promises per year, colored by verdict">
        ${gridSvg}
        ${barsSvg}
        ${axisSvg}
      </svg>
    `;
  }

  function renderVisualizations() {
    if (!demoData || !Array.isArray(demoData.promises)) return;
    const promises = demoData.promises;
    const total = promises.length;

    const verdictCounts = SFPViz.countByVerdict(promises);
    const verdictEntries = SFPViz.VERDICT_ORDER
      .filter(v => verdictCounts[v])
      .map(v => ({ label: formatVerdictLabel(v), count: verdictCounts[v], color: VERDICT_COLORS[v] }));
    renderBarRows(document.getElementById('viz-verdict-bars'), verdictEntries, total);

    const catEntries = Object.entries(SFPViz.countByCategory(promises))
      .sort((a, b) => b[1] - a[1])
      .map(([label, count]) => ({ label, count, color: 'var(--blue)' }));
    renderBarRows(document.getElementById('viz-domain-bars'), catEntries, total);

    const stEntries = Object.entries(SFPViz.countBySourceType(promises))
      .sort((a, b) => b[1] - a[1])
      .map(([st, count]) => ({ label: SFPViz.formatSourceTypeLabel(st), count, color: 'var(--purple)' }));
    renderBarRows(document.getElementById('viz-source-bars'), stEntries, total);

    renderTimelineChart(promises);

    const totalEl = document.getElementById('viz-total');
    if (totalEl) totalEl.textContent = String(total);

    const legendEl = document.getElementById('viz-timeline-legend');
    if (legendEl) {
      // Legend derives from the data: only verdicts actually present get a
      // row, so the timeline legend matches the verdict-distribution charts
      // (a verdict like 'stalled' shows up only when a record carries it).
      legendEl.innerHTML = SFPViz.VERDICT_ORDER
        .filter(v => (verdictCounts[v] || 0) > 0)
        .map(v => `
        <span class="viz-legend-item"><span class="viz-legend-swatch" style="background:${VERDICT_COLORS[v]}"></span>${formatVerdictLabel(v)}</span>
      `).join('');
    }

    renderPhaseTimelines(promises);
  }

  // Outcome-timelines card (E5): one phase row per record with >= 2 dated
  // phases, derived by SFPViz.phaseTimelines from the exported snapshot. Row
  // count must reconcile with the export (tests + verify_demo node harness).
  function renderPhaseTimelines(promises) {
    const listEl = document.getElementById('viz-phase-timelines');
    if (!listEl) return;
    const rows = SFPViz.phaseTimelines(promises);
    listEl.innerHTML = rows.map(row => {
      const steps = row.phases.map(ph =>
        `<span class="viz-phase-chip ${escapeHtml(ph.phase)}" title="${escapeHtml(ph.display)}">${escapeHtml(ph.label)} &mdash; ${escapeHtml(ph.display)}</span>`
      ).join('<span class="viz-phase-arrow" aria-hidden="true">&rarr;</span>');
      const spoken = row.phases.map(ph => `${ph.label} ${ph.display}`).join(', ');
      return `
        <div class="viz-phase-row${row.historyChanged ? ' showcase' : ''}" role="listitem"
             aria-label="${escapeHtml(row.promiseId)} outcome timeline: ${escapeHtml(spoken)}">
          <span class="viz-phase-id font-mono">${escapeHtml(row.promiseId)}</span>
          <span class="viz-phase-name">${escapeHtml(row.label)}</span>
          <span class="viz-phase-steps">${steps}</span>
        </div>`;
    }).join('');
  }

  // -------------------------------------------------------------------------
  // Quarantine Registry (0.1) - Unified responsive card registry
  // -------------------------------------------------------------------------
  function renderQuarantineTable() {
    if (!demoData) return;
    const quarantined = demoData.quarantined || [];
    const listEl = document.getElementById('quarantine-cards-list');
    if (!listEl) return;

    listEl.innerHTML = quarantined.map((q, idx) => {
      const qid = escapeHtml(q.quarantine_id || `Q-${idx+1}`);
      const pid = escapeHtml(q.promise_id || '');
      const typeBadge = (q.planted_claim || q.original_text) ? 'Test case' : 'Rejected candidate';
      const typeCls = typeBadge === 'Test case' ? 'test-case' : 'rejected-candidate';
      const claim = escapeHtml(cleanQuoteText(q.planted_claim || q.claim || q.title || ''));

      let diffHtml = '';
      if (q.original_text && q.altered_text) {
        diffHtml = `<div class="quarantine-diff-row font-mono"><span class="diff-label">Mutation:</span> <span class="diff-orig">${escapeHtml(q.original_text)}</span> &rarr; <span class="diff-alt">${escapeHtml(q.altered_text)}</span></div>`;
      } else if (q.change_diff) {
        diffHtml = `<div class="quarantine-diff-row font-mono"><span class="diff-label">Change:</span> <span class="diff-alt">${escapeHtml(q.change_diff)}</span></div>`;
      }

      const failingPlain = escapeHtml(q.failing_check || 'Integrity check failed');
      const checkType = escapeHtml(q.check_type || 'accuracy_quote');
      const reason = escapeHtml(q.reason || 'Held back from published dataset.');
      const agent = escapeHtml(q.agent || 'Extractor Agent');
      const dateStr = escapeHtml(q.quarantined_date || 'Nov 10, 2026');
      const hash = escapeHtml(q.source_hash || '');
      const hashHtml = hash ? `<div class="quarantine-hash-row font-mono"><span class="hash-label">SHA-256:</span> <code class="quarantine-hash">${hash.slice(0, 12)}…</code> <button type="button" class="btn-copy-hash font-mono" data-hash="${hash}">Copy</button></div>` : '';

      return `
        <div class="quarantine-card" id="quarantine-card-${qid}" data-qid="${qid}">
          <div class="quarantine-card-header">
            <div class="quarantine-badge-group">
              <span class="quarantine-type-badge ${typeCls}">${typeBadge}</span>
              <span class="quarantine-pid font-mono">${pid}</span>
            </div>
            <span class="verdict-chip quarantined">QUARANTINED</span>
          </div>
          <blockquote class="quarantine-claim-quote font-serif">&ldquo;${claim}&rdquo;</blockquote>
          ${diffHtml}
          <div class="quarantine-check-block">
            <div class="quarantine-check-plain">${failingPlain} <code class="quarantine-check-code font-mono">${checkType}</code></div>
            <p class="quarantine-reason-text">${reason}</p>
          </div>
          <div class="quarantine-card-footer font-mono">
            <span class="quarantine-catcher-meta">Caught by ${agent} &middot; ${dateStr}</span>
            ${hashHtml}
          </div>
        </div>
      `;
    }).join('');
  }

  function setViewMode(mode, shouldRender = true) {
    activeViewMode = mode || 'table';
    document.querySelectorAll('.btn-view-mode').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-view') === activeViewMode);
    });
    const tableEl = document.getElementById('promises-table-container');
    const mapEl = document.getElementById('explore-map-view');
    const entEl = document.getElementById('explore-entities-view');
    const auditEl = document.getElementById('explore-audit-view');
    const paginationEl = document.getElementById('pagination-controls');

    if (activeTab !== 'promises') {
      if (tableEl) tableEl.classList.add('hidden');
      if (mapEl) mapEl.classList.add('hidden');
      if (entEl) entEl.classList.add('hidden');
      if (auditEl) auditEl.classList.add('hidden');
      if (paginationEl) paginationEl.classList.add('hidden');
      return;
    }

    const listLike = activeViewMode === 'table' || activeViewMode === 'grid';
    if (tableEl) tableEl.classList.toggle('hidden', !listLike);
    syncCardsLayout();
    if (mapEl) mapEl.classList.toggle('hidden', activeViewMode !== 'map');
    if (entEl) entEl.classList.toggle('hidden', activeViewMode !== 'entities');
    if (auditEl) auditEl.classList.toggle('hidden', activeViewMode !== 'audit');
    if (paginationEl) paginationEl.classList.toggle('hidden', !listLike);
    if (shouldRender) renderExplore();
  }

  function setTab(tabName) {
    activeTab = tabName;
    const tabPromises = document.getElementById('tab-btn-promises');
    const tabQuarantine = document.getElementById('tab-btn-quarantine');
    const tablePromises = document.getElementById('promises-table-container');
    const containerQuarantine = document.getElementById('quarantine-table-container');
    const qHeader = document.getElementById('quarantine-header-status');
    const primaryControls = document.querySelector('.explore-primary-controls');
    const moreFiltersPanel = document.getElementById('more-filters-panel');
    const showingStatus = document.getElementById('table-showing-status');
    const paginationControls = document.getElementById('pagination-controls');
    const viewSwitcher = document.getElementById('view-mode-switcher');

    if (tabName === 'quarantine') {
      if (tabPromises) {
        tabPromises.classList.remove('active');
        tabPromises.setAttribute('aria-selected', 'false');
      }
      if (tabQuarantine) {
        tabQuarantine.classList.add('active');
        tabQuarantine.setAttribute('aria-selected', 'true');
      }

      // Hide verified-only controls and alternate views
      if (viewSwitcher) viewSwitcher.classList.add('hidden');
      if (primaryControls) primaryControls.classList.add('hidden');
      if (moreFiltersPanel) moreFiltersPanel.classList.add('hidden');
      if (showingStatus) showingStatus.classList.add('hidden');
      if (paginationControls) paginationControls.classList.add('hidden');
      if (tablePromises) tablePromises.classList.add('hidden');
      setViewMode(activeViewMode, false);

      // Show quarantine elements
      if (qHeader) qHeader.classList.remove('hidden');
      if (containerQuarantine) containerQuarantine.classList.remove('hidden');
    } else {
      if (tabQuarantine) {
        tabQuarantine.classList.remove('active');
        tabQuarantine.setAttribute('aria-selected', 'false');
      }
      if (tabPromises) {
        tabPromises.classList.add('active');
        tabPromises.setAttribute('aria-selected', 'true');
      }

      // Restore verified controls
      if (viewSwitcher) viewSwitcher.classList.remove('hidden');
      if (primaryControls) primaryControls.classList.remove('hidden');
      if (showingStatus) showingStatus.classList.remove('hidden');

      // Hide quarantine elements
      if (qHeader) qHeader.classList.add('hidden');
      if (containerQuarantine) containerQuarantine.classList.add('hidden');

      setViewMode(activeViewMode, true);
    }
  }

  function switchToQuarantineAndHighlight(qid) {
    setTab('quarantine');
    const el = document.getElementById(`quarantine-card-${qid}`) || document.getElementById(`quarantine-row-${qid}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.style.outline = '3px solid #F59E0B';
      setTimeout(() => {
        el.style.outline = '';
      }, 2500);
    }
  }

  // -------------------------------------------------------------------------
  // Explore All Promises (1.1, 1.2, 1.3)
  // -------------------------------------------------------------------------
  function filterAndSortPromises() {
    if (!demoData) return [];
    let list = (demoData.promises || []).slice();

    // Verdict filter
    if (filterVerdict !== 'all') {
      list = list.filter(p => (p.verdict || '').toLowerCase() === filterVerdict.toLowerCase());
    }

    // Category filter
    if (filterCategory !== 'all') {
      list = list.filter(p => p.category === filterCategory);
    }

    // Entity filter
    if (filterEntity !== 'all') {
      list = list.filter(p => (p.entity_type || '').toLowerCase() === filterEntity.toLowerCase());
    }

    // Source Tier filter
    if (filterTier !== 'all') {
      list = list.filter(p => getSourceTier(p.source_url).toLowerCase() === filterTier.toLowerCase());
    }

    // Pillar filter
    if (filterPillar !== 'all') {
      list = list.filter(p => (p.pillar || '') === filterPillar);
    }

    // Audit & Evidence Flag filter
    if (filterAuditFlag === 'exceptions') {
      list = list.filter(p => p.all_checks_passed === false || (p.failed_check_count || 0) > 0);
    } else if (filterAuditFlag === 'contradictions') {
      list = list.filter(p => Boolean(p.has_contradictory_evidence));
    } else if (filterAuditFlag === 'exact_pin') {
      list = list.filter(p => p.is_centroid === false);
    }

    // Keyword search
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase().trim();
      list = list.filter(p => {
        const text = `${p.promise_id} ${p.entity} ${p.entity_canonical_name || ''} ${p.role || ''} ${p.promise_text} ${p.factual_outcome || ''} ${p.neighborhood || ''} ${p.category} ${p.pillar || ''}`.toLowerCase();
        return text.includes(q);
      });
    }

    // Sort
    if (filterSort === 'rank') {
      list.sort((a, b) => (a.impact_rank || 999) - (b.impact_rank || 999));
    } else if (filterSort === 'default') {
      list.sort((a, b) => String(b.promised_date || '').localeCompare(String(a.promised_date || '')));
    } else if (filterSort === 'date_asc') {
      list.sort((a, b) => String(a.promised_date || '').localeCompare(String(b.promised_date || '')));
    } else if (filterSort === 'verdict') {
      list.sort((a, b) => String(a.verdict || '').localeCompare(String(b.verdict || '')));
    } else if (filterSort === 'entity') {
      list.sort((a, b) => String(a.entity || '').localeCompare(String(b.entity || '')));
    }

    return list;
  }

  // Segmented verdict control: keep the pressed state programmatic, not
  // color-only (issue #50), and keep the status-line Clear filters button
  // live only when there is a non-default filter or sort to clear.
  function syncVerdictControl() {
    document.querySelectorAll('.btn-seg-verdict').forEach(b => {
      b.setAttribute('aria-pressed', b.classList.contains('active') ? 'true' : 'false');
    });
    const btnClear = document.getElementById('btn-clear-filters');
    if (btnClear) {
      btnClear.disabled = filterVerdict === 'all'
        && filterCategory === 'all'
        && filterEntity === 'all'
        && filterTier === 'all'
        && filterPillar === 'all'
        && filterAuditFlag === 'all'
        && filterSort === 'rank'
        && !searchTerm.trim();
    }
  }

  function renderExplore() {
    const list = filterAndSortPromises();
    const totalCount = (demoData && demoData.promises && demoData.promises.length) || 54;
    const showingCount = Math.min(visibleRowsCount, list.length);

    // Zero-match empty state: at the point of emptiness, say so and offer the
    // way out instead of rendering a bare header row.
    const emptyStateEl = document.getElementById('promises-empty-state');
    if (emptyStateEl) {
      if (!list.length) {
        emptyStateEl.innerHTML = SFPUX.noResultsHtml();
        emptyStateEl.hidden = false;
      } else {
        emptyStateEl.innerHTML = '';
        emptyStateEl.hidden = true;
      }
    }

    // Update status line
    const showingCountEl = document.getElementById('table-showing-count');
    const totalCountEl = document.getElementById('table-total-count');
    const showingTextEl = document.getElementById('table-showing-text');
    if (showingTextEl) {
      showingTextEl.innerHTML = `Showing <strong id="table-showing-count">${showingCount}</strong> of <span id="table-total-count">${list.length}</span> commitments`;
    }

    // Update pagination buttons
    const btnShowMore = document.getElementById('btn-show-more');
    const btnShowAll = document.getElementById('btn-show-all');
    if (btnShowMore) {
      if (showingCount >= list.length) {
        btnShowMore.style.display = 'none';
      } else {
        btnShowMore.style.display = 'inline-flex';
        btnShowMore.textContent = `Show 10 more`;
      }
    }
    if (btnShowAll) {
      if (showingCount >= list.length) {
        btnShowAll.style.display = 'none';
      } else {
        btnShowAll.style.display = 'inline-flex';
        btnShowAll.textContent = `Show all ${list.length}`;
      }
    }

    // Single render path: the exporter bakes the one record markup (the
    // <tr class="promise-row"> rows in this tbody). Filtering, sorting and
    // pagination reuse those baked rows — reorder them for sort, and toggle
    // the paged classes for visibility — instead of regenerating a second
    // client-side template that can drift from the baked one.
    const tbody = document.getElementById('promises-table-body');

    if (tbody) {
      const rowsById = {};
      Array.prototype.forEach.call(
        tbody.querySelectorAll('tr[data-promise-id]'),
        row => { rowsById[row.getAttribute('data-promise-id')] = row; }
      );

      if (!Object.keys(rowsById).length) {
        console.warn('renderExplore: no baked promise rows found in the table body; nothing to render');
      }

      const visible = list.slice(0, showingCount);
      const shownIds = new Set(visible.map(p => String(p.promise_id)));

      visible.forEach(p => {
        const row = rowsById[String(p.promise_id)];
        if (!row) return;
        row.classList.remove('paged-row', 'hidden-page-row');
        tbody.appendChild(row); // appendChild moves the node, producing sort order
      });

      Object.keys(rowsById).forEach(pid => {
        if (!shownIds.has(pid)) {
          rowsById[pid].classList.add('paged-row', 'hidden-page-row');
        }
      });
    }

    if (activeViewMode === 'map') {
      renderMapAndDistrictsView(list);
    } else if (activeViewMode === 'entities') {
      renderEntityProfilesView(list);
    } else if (activeViewMode === 'audit') {
      renderQualityAuditView();
    }

    syncVerdictControl();
  }

  /* SFPMAP_PURE_START */
  // Marker clustering for the self-hosted SVG map (issue #44). Clusters whose
  // centres are closer than minDist (SVG units) are merged, closest pair first,
  // and the scan repeats until no pair is left, so hit circles of diameter
  // minDist never overlap. City and SFO-inset pins stay separate. Pure: no DOM.
  function clusterPins(pins, minDist) {
    const byId = (a, b) => String(a.p.promise_id).localeCompare(String(b.p.promise_id));
    let clusters = pins.slice().sort(byId).map(pin => ({ x: pin.x, y: pin.y, inSFO: !!pin.inSFO, items: [pin] }));
    for (;;) {
      let bi = -1, bj = -1, best = Infinity;
      for (let i = 0; i < clusters.length; i++) {
        for (let j = i + 1; j < clusters.length; j++) {
          if (clusters[i].inSFO !== clusters[j].inSFO) continue;
          const d = Math.hypot(clusters[i].x - clusters[j].x, clusters[i].y - clusters[j].y);
          if (d < minDist && d < best) { best = d; bi = i; bj = j; }
        }
      }
      if (bi < 0) break;
      const home = clusters[bi];
      home.items = home.items.concat(clusters[bj].items).sort(byId);
      home.x = home.items.reduce((sum, it) => sum + it.x, 0) / home.items.length;
      home.y = home.items.reduce((sum, it) => sum + it.y, 0) / home.items.length;
      clusters.splice(bj, 1);
    }
    return clusters;
  }

  // Touch target diameter in CSS px: 44 on phones and coarse pointers (WCAG 2.5.5 / Apple HIG), 28 otherwise.
  function mapHitDiameterPx(isMobile) {
    return isMobile ? 44 : 28;
  }

  // The SVG is a labelled group, not role="img": img makes its children
  // presentational and would hide the focusable marker buttons.
  function mapSvgOpenTag(W, H) {
    return `<svg class="sf-svg-map" viewBox="0 0 ${W} ${H}" role="group" aria-label="San Francisco commitment coordinates map. Markers are buttons.">`;
  }

  function mapActivationKey(e) {
    return !!e && (e.key === 'Enter' || e.key === ' ');
  }

  // Wire click and Enter/Space on markers. actions.openPromise(pid, node) and
  // actions.openCluster(ids, node) do the work.
  function bindMapMarkers(root, actions) {
    root.querySelectorAll('[data-promise-id]').forEach(node => {
      const run = () => actions.openPromise(node.getAttribute('data-promise-id'), node);
      node.addEventListener('click', run);
      node.addEventListener('keydown', e => { if (mapActivationKey(e)) { e.preventDefault(); run(); } });
    });
    root.querySelectorAll('[data-cluster-ids]').forEach(node => {
      const run = () => actions.openCluster((node.getAttribute('data-cluster-ids') || '').split(',').filter(Boolean), node);
      node.addEventListener('click', run);
      node.addEventListener('keydown', e => { if (mapActivationKey(e)) { e.preventDefault(); run(); } });
    });
  }

  // Marker (single or cluster) that stands for promise id pid, or null.
  function findMapMarker(root, pid) {
    const nodes = Array.from(root.querySelectorAll('[data-promise-id],[data-cluster-ids]'));
    for (const n of nodes) {
      if (n.getAttribute('data-promise-id') === pid) return n;
      const ids = n.getAttribute('data-cluster-ids');
      if (ids && ids.split(',').indexOf(pid) >= 0) return n;
    }
    return null;
  }

  // Show a cluster list in the card and move focus into it.
  function openMapCluster(card, html) {
    card.classList.remove('hidden');
    card.innerHTML = html;
    const first = card.querySelector('.btn-map-cluster-item');
    if (first) first.focus();
    return !!first;
  }

  // Hide the cluster list and return focus to the marker that opened it.
  function closeMapCluster(card, root, ids) {
    card.classList.add('hidden');
    const marker = ids && ids.length ? findMapMarker(root, ids[0]) : null;
    if (marker) marker.focus();
    return !!marker;
  }
  /* SFPMAP_PURE_END */
  window.SFPMap = { clusterPins, mapHitDiameterPx, mapSvgOpenTag, bindMapMarkers, findMapMarker, openMapCluster, closeMapCluster };

  let lastMapList = null;
  let lastMapWidth = 0;
  let mapResizeTimer = null;
  let openClusterIds = null;
  let mapCardEscBound = null;

  function inspectDrawerOpen() {
    const backdrop = document.getElementById('inspect-drawer-backdrop');
    return !!(backdrop && !backdrop.classList.contains('hidden'));
  }

  // Promise id behind the marker that has focus (or opened the drawer), so a
  // re-render can put focus back on the equivalent new marker.
  function focusedMapPromiseId(wrap) {
    const candidates = [document.activeElement];
    if (inspectDrawerOpen()) candidates.push(lastActiveElement);
    for (const el of candidates) {
      const m = el && el.closest && el.closest('[data-promise-id],[data-cluster-ids]');
      if (m && wrap.contains(m)) {
        return m.getAttribute('data-promise-id') || (m.getAttribute('data-cluster-ids') || '').split(',')[0];
      }
    }
    return null;
  }

  // Cluster radius depends on rendered width, so re-cluster when the map is resized.
  window.addEventListener('resize', () => {
    clearTimeout(mapResizeTimer);
    mapResizeTimer = setTimeout(() => {
      const wrap = document.getElementById('sf-svg-map-wrap');
      if (!lastMapList || !wrap || activeViewMode !== 'map' || wrap.classList.contains('hidden')) return;
      if (Math.abs(wrap.clientWidth - lastMapWidth) <= 40) return;
      const pid = focusedMapPromiseId(wrap);
      const drawerOpen = inspectDrawerOpen();
      renderMapAndDistrictsView(lastMapList);
      const marker = pid ? window.SFPMap.findMapMarker(wrap, pid) : null;
      if (!marker) return;
      if (drawerOpen) lastActiveElement = marker; else marker.focus();
    }, 150);
  });

  // -------------------------------------------------------------------------
  // Street basemap (issue #44). Self-hosted MapLibre + Protomaps tiles, loaded
  // only when the Map & Districts view is first opened. Every asset is served
  // from docs/map/; nothing is requested from a third-party host. The SVG map
  // above stays the keyboard-accessible alternative ("Simple map").
  // -------------------------------------------------------------------------
  const STREET_MAP_ASSETS = {
    css: 'map/vendor/maplibre-gl.css',
    maplibre: 'map/vendor/maplibre-gl.js',
    pmtiles: 'map/vendor/pmtiles.js',
    basemaps: 'map/vendor/basemaps.js',
    tiles: 'map/sf-z14.pmtiles',
    sprite: 'map/sprites/light',
    fonts: 'map/fonts/'
  };
  // Glyph ranges on disk: 0-255, 256-511 and 8192-8447 for these three stacks.
  const STREET_MAP_FONTS = ['Noto Sans Regular', 'Noto Sans Medium', 'Noto Sans Italic'];
  // Tile extent of sf-z14.pmtiles (SF incl. SFO): [west, south, east, north].
  const STREET_MAP_TILE_BOUNDS = [-122.53, 37.60, -122.35, 37.84];
  const STREET_MAP_MAX_BOUNDS = [[-122.60, 37.56], [-122.28, 37.88]];
  const STREET_MAP_FIT_BOUNDS = [[-122.52, 37.605], [-122.355, 37.835]];
  const STREET_MAP_OSM_ATTRIBUTION = '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">&copy; OpenStreetMap contributors</a>';
  const STREET_MAP_CREDITS = [
    '<a href="https://protomaps.com" target="_blank" rel="noopener">Protomaps</a>',
    '<a href="https://maplibre.org" target="_blank" rel="noopener">MapLibre</a>'
  ];
  const MAP_MODE_KEY = 'sfp-map-mode';

  let streetMap = null;            // maplibregl.Map once created
  let streetMapLoading = null;     // Promise while libraries/style load
  let streetMapFailure = '';       // reason the street map is unavailable
  let streetMapPendingList = null; // latest list to plot once the map is ready
  let mapModeBound = false;
  let clusterListOrigin = 'svg';   // which map opened the cluster list

  function storedMapMode() {
    try { return window.localStorage.getItem(MAP_MODE_KEY); } catch (e) { return null; }
  }

  function storeMapMode(mode) {
    try { window.localStorage.setItem(MAP_MODE_KEY, mode); } catch (e) { /* private mode */ }
  }

  // Probe once: every getContext call creates a WebGL context and browsers
  // cap how many may be alive, so repeated probes could evict the map's own.
  let webglProbe = null;
  function webglAvailable() {
    if (webglProbe !== null) return webglProbe;
    try {
      const c = document.createElement('canvas');
      const gl = window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl'));
      webglProbe = !!gl;
      const lose = gl && gl.getExtension && gl.getExtension('WEBGL_lose_context');
      if (lose) lose.loseContext();
    } catch (e) {
      webglProbe = false;
    }
    return webglProbe;
  }

  function streetMapActive() {
    if (streetMapFailure) return false;
    if (!webglAvailable()) {
      streetMapFailure = 'WebGL is not available in this browser';
      return false;
    }
    return storedMapMode() !== 'simple';
  }

  function syncMapModeUi(useStreet) {
    const btnStreet = document.getElementById('btn-map-mode-street');
    const btnSimple = document.getElementById('btn-map-mode-simple');
    const note = document.getElementById('map-mode-note');
    if (btnStreet) {
      btnStreet.setAttribute('aria-pressed', useStreet ? 'true' : 'false');
      btnStreet.disabled = !!streetMapFailure;
    }
    if (btnSimple) btnSimple.setAttribute('aria-pressed', useStreet ? 'false' : 'true');
    if (note) {
      note.textContent = streetMapFailure
        ? `Street map unavailable (${streetMapFailure}); showing the simple map. The simple map is keyboard accessible: every marker is a button.`
        : (useStreet
          ? 'Street map: drag or use arrow keys to pan. Switch to the simple map for keyboard access to each marker.'
          : 'The simple map is keyboard accessible: every marker is a button.');
    }
    if (mapModeBound) return;
    mapModeBound = true;
    [btnStreet, btnSimple].forEach(btn => {
      if (!btn) return;
      btn.addEventListener('click', () => {
        const mode = btn.getAttribute('data-map-mode');
        if (mode === 'street' && streetMapFailure) return;
        storeMapMode(mode);
        const card = document.getElementById('map-selected-card');
        if (card) card.classList.add('hidden');
        openClusterIds = null;
        renderMapAndDistrictsView(lastMapList);
        btn.focus();
      });
    });
  }

  function loadMapScript(src) {
    return new Promise((resolve, reject) => {
      const el = document.createElement('script');
      el.src = src;
      el.async = false; // keep execution order: maplibre before its plugins
      el.onload = () => resolve();
      el.onerror = () => reject(new Error(`could not load ${src}`));
      document.head.appendChild(el);
    });
  }

  function loadMapStylesheet(href) {
    return new Promise((resolve, reject) => {
      const el = document.createElement('link');
      el.rel = 'stylesheet';
      el.href = href;
      el.onload = () => resolve();
      el.onerror = () => reject(new Error(`could not load ${href}`));
      document.head.appendChild(el);
    });
  }

  function loadStreetMapLibraries() {
    if (window.maplibregl && window.pmtiles && window.basemaps) return Promise.resolve();
    return Promise.all([
      loadMapStylesheet(STREET_MAP_ASSETS.css),
      loadMapScript(STREET_MAP_ASSETS.maplibre),
      loadMapScript(STREET_MAP_ASSETS.pmtiles),
      loadMapScript(STREET_MAP_ASSETS.basemaps)
    ]).then(() => {
      if (!window.maplibregl || !window.pmtiles || !window.basemaps) throw new Error('map libraries did not initialise');
    });
  }

  // Resolve CSS custom properties (var(--verdict-progress)) to concrete colours
  // so WebGL paint properties get the same palette as the SVG map and legend.
  function resolveCssColor(value) {
    const m = /^var\((--[\w-]+)\)$/.exec(String(value || '').trim());
    if (!m) return value || '#94A3B8';
    const v = getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim();
    return v || '#94A3B8';
  }

  // Use only the glyph stacks shipped in docs/map/fonts (no Devanagari stack).
  function restrictMapFonts(value) {
    if (typeof value === 'string') {
      return /^Noto Sans/.test(value) && STREET_MAP_FONTS.indexOf(value) < 0 ? STREET_MAP_FONTS[0] : value;
    }
    if (Array.isArray(value)) return value.map(restrictMapFonts);
    return value;
  }

  function inStreetMapTiles(lat, lon) {
    const [w, sth, e, n] = STREET_MAP_TILE_BOUNDS;
    return lon >= w && lon <= e && lat >= sth && lat <= n;
  }

  function streetMapGeoJson(list) {
    const features = [];
    const regional = [];
    (list || []).forEach(p => {
      const lat = Number(p.latitude);
      const lon = Number(p.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        // No point to plot; list records whose source names no location.
        if (p.location_status === 'not_stated') regional.push(p);
        return;
      }
      if (!inStreetMapTiles(lat, lon)) { regional.push(p); return; }
      const v = (p.verdict || 'undecided').toLowerCase();
      features.push({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [lon, lat] },
        properties: {
          pid: p.promise_id || '',
          color: resolveCssColor(VERDICT_COLORS[v] || '#94A3B8'),
          centroid: p.is_centroid !== false
        }
      });
    });
    return { data: { type: 'FeatureCollection', features }, regional };
  }

  function hideStreetMap() {
    const wrap = document.getElementById('street-map-wrap');
    const regional = document.getElementById('street-map-regional');
    if (wrap) wrap.classList.add('hidden');
    if (regional) regional.classList.add('hidden');
  }

  function renderStreetRegional(items) {
    const el = document.getElementById('street-map-regional');
    if (!el) return;
    if (!items.length) { el.classList.add('hidden'); el.innerHTML = ''; return; }
    el.classList.remove('hidden');
    el.innerHTML = `
      <div class="map-regional-strip font-mono">
        <span class="regional-strip-label">OUTSIDE THE STREET MAP / REGIONAL OR LOCATION NOT STATED (${items.length}):</span>
        ${items.map(p => `<button type="button" class="btn-regional-pin" data-promise-id="${escapeHtml(p.promise_id)}">${escapeHtml(p.promise_id)} · ${escapeHtml(p.entity)}</button>`).join('')}
      </div>`;
    el.querySelectorAll('[data-promise-id]').forEach(btn => {
      btn.addEventListener('click', () => openInspectDrawer(btn.getAttribute('data-promise-id')));
    });
  }

  function streetMapFallback(err) {
    streetMapFailure = 'the map could not be started';
    streetMapLoading = null;
    console.warn('Street map unavailable, using the simple map:', err && err.message ? err.message : err);
    if (streetMap) { try { streetMap.remove(); } catch (e) { /* ignore */ } streetMap = null; }
    if (activeViewMode === 'map' && lastMapList) renderMapAndDistrictsView(lastMapList);
  }

  function renderStreetMap(list) {
    const wrap = document.getElementById('street-map-wrap');
    const container = document.getElementById('street-map');
    if (!wrap || !container) return;
    wrap.classList.remove('hidden');
    const { data, regional } = streetMapGeoJson(list);
    renderStreetRegional(regional);
    streetMapPendingList = data;
    if (streetMap) {
      streetMap.resize();
      const src = streetMap.getSource('promises');
      if (src) src.setData(data);
      return;
    }
    if (streetMapLoading) return;
    streetMapLoading = loadStreetMapLibraries()
      .then(() => createStreetMap(container))
      .catch(streetMapFallback);
  }

  function createStreetMap(container) {
    const maplibregl = window.maplibregl;
    if (!createStreetMap.protocol) {
      createStreetMap.protocol = new window.pmtiles.Protocol();
      maplibregl.addProtocol('pmtiles', createStreetMap.protocol.tile);
    }
    const page = window.location.href;
    const tilesUrl = new URL(STREET_MAP_ASSETS.tiles, page).href;
    const layers = window.basemaps.layers('protomaps', window.basemaps.namedFlavor('light'), { lang: 'en' })
      .map(layer => (layer.layout && layer.layout['text-font'])
        ? Object.assign({}, layer, { layout: Object.assign({}, layer.layout, { 'text-font': restrictMapFonts(layer.layout['text-font']) }) })
        : layer);
    const isMobile = !!(window.matchMedia && window.matchMedia('(max-width: 720px), (pointer: coarse)').matches);
    const map = new maplibregl.Map({
      container,
      style: {
        version: 8,
        glyphs: new URL(STREET_MAP_ASSETS.fonts, page).href + '{fontstack}/{range}.pbf',
        sprite: new URL(STREET_MAP_ASSETS.sprite, page).href,
        sources: {
          protomaps: { type: 'vector', url: `pmtiles://${tilesUrl}`, attribution: STREET_MAP_OSM_ATTRIBUTION }
        },
        layers
      },
      bounds: STREET_MAP_FIT_BOUNDS,
      fitBoundsOptions: { padding: 12 },
      maxBounds: STREET_MAP_MAX_BOUNDS,
      minZoom: 9,
      maxZoom: 16,
      attributionControl: false,
      cooperativeGestures: true,
      dragRotate: false,
      pitchWithRotate: false,
      touchPitch: false
    });
    map.touchZoomRotate.disableRotation();
    map.keyboard.disableRotation();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.addControl(new maplibregl.AttributionControl({ compact: isMobile, customAttribution: STREET_MAP_CREDITS }), 'bottom-right');
    map.getCanvas().setAttribute('aria-label', 'Street map of San Francisco commitments, coloured by verdict. Arrow keys pan and plus or minus zoom; markers are pointer-only here. Use the Simple map button for keyboard access to each marker.');
    streetMap = map;
    window.SFPMap.streetMap = () => streetMap; // read-only handle for browser checks

    map.on('error', (e) => {
      const msg = e && e.error && e.error.message ? e.error.message : String(e && e.error || 'map error');
      console.warn('Street map:', msg);
    });

    // The light sprite lacks a few POI icons the style names (e.g. "townhall");
    // draw nothing for them instead of logging a warning per tile.
    map.on('styleimagemissing', (e) => {
      if (!map.hasImage(e.id)) map.addImage(e.id, { width: 1, height: 1, data: new Uint8Array(4) });
    });

    map.on('load', () => {
      streetMapLoading = null;
      map.addSource('promises', {
        type: 'geojson',
        data: streetMapPendingList || { type: 'FeatureCollection', features: [] },
        cluster: true,
        clusterRadius: 36,
        clusterMaxZoom: 15
      });
      const single = ['!', ['has', 'point_count']];
      map.addLayer({
        id: 'promise-clusters', type: 'circle', source: 'promises', filter: ['has', 'point_count'],
        paint: {
          'circle-color': '#1E3A8A',
          'circle-radius': ['step', ['get', 'point_count'], 13, 5, 16, 15, 20],
          'circle-stroke-color': '#93C5FD',
          'circle-stroke-width': 2
        }
      });
      map.addLayer({
        id: 'promise-cluster-count', type: 'symbol', source: 'promises', filter: ['has', 'point_count'],
        layout: {
          'text-field': ['get', 'point_count_abbreviated'],
          'text-font': ['Noto Sans Medium'],
          'text-size': 12,
          'text-allow-overlap': true
        },
        paint: { 'text-color': '#F8FAFC' }
      });
      // Display centroids: a ring around a smaller, fainter dot (as in the SVG map).
      map.addLayer({
        id: 'promise-centroid-ring', type: 'circle', source: 'promises',
        filter: ['all', single, ['==', ['get', 'centroid'], true]],
        paint: {
          'circle-radius': 10,
          'circle-color': '#FFFFFF',
          'circle-opacity': 0.35,
          'circle-stroke-color': ['get', 'color'],
          'circle-stroke-width': 1.6,
          'circle-stroke-opacity': 0.9
        }
      });
      map.addLayer({
        id: 'promise-points', type: 'circle', source: 'promises', filter: single,
        paint: {
          'circle-radius': ['case', ['get', 'centroid'], 5, 7],
          'circle-color': ['get', 'color'],
          'circle-opacity': ['case', ['get', 'centroid'], 0.75, 0.96],
          'circle-stroke-color': '#0B1120',
          'circle-stroke-width': 1.5
        }
      });
      container.setAttribute('data-map-ready', 'true');
    });

    // Hit-test a touch-sized box (44px on phones) rather than the exact dot.
    function featuresNear(point) {
      const r = mapHitDiameterPx(isMobile) / 2;
      return map.queryRenderedFeatures([[point.x - r, point.y - r], [point.x + r, point.y + r]],
        { layers: ['promise-clusters', 'promise-points'] });
    }

    map.on('mousemove', (e) => {
      if (!map.getLayer('promise-points')) return;
      map.getCanvas().style.cursor = featuresNear(e.point).length ? 'pointer' : '';
    });

    map.on('click', (e) => {
      if (!map.getLayer('promise-points')) return;
      const hits = featuresNear(e.point);
      if (!hits.length) return;
      const dist = f => {
        const p = map.project(f.geometry.coordinates);
        return Math.hypot(p.x - e.point.x, p.y - e.point.y);
      };
      hits.sort((a, b) => dist(a) - dist(b));
      const nearest = hits[0];
      if (nearest.properties.cluster) {
        openStreetCluster(map, nearest);
        return;
      }
      // Stacked points (same or near-identical coordinates) open the list.
      const singles = hits.filter(f => !f.properties.cluster && dist(f) <= dist(nearest) + 2);
      const ids = Array.from(new Set(singles.map(f => f.properties.pid)));
      map.getCanvas().focus();
      if (ids.length > 1) showStreetClusterList(ids);
      else openInspectDrawer(ids[0]);
    });
  }

  async function openStreetCluster(map, feature) {
    const src = map.getSource('promises');
    const clusterId = feature.properties.cluster_id;
    try {
      const [zoom, leaves] = await Promise.all([
        src.getClusterExpansionZoom(clusterId),
        src.getClusterLeaves(clusterId, 1000, 0)
      ]);
      const first = leaves[0] && leaves[0].geometry.coordinates;
      const sameSpot = first && leaves.every(l => l.geometry.coordinates[0] === first[0] && l.geometry.coordinates[1] === first[1]);
      if (sameSpot || zoom > map.getMaxZoom()) {
        map.getCanvas().focus();
        showStreetClusterList(leaves.map(l => l.properties.pid));
        return;
      }
      map.easeTo({ center: feature.geometry.coordinates, zoom });
    } catch (err) {
      console.warn('Street map cluster:', err && err.message ? err.message : err);
    }
  }

  function showStreetClusterList(ids) {
    const card = document.getElementById('map-selected-card');
    const members = ids.map(id => (demoData && demoData.promises || []).find(item => item.promise_id === id)).filter(Boolean);
    showMapClusterList(card, members, 'street');
  }

  // Shared cluster list (SVG and street map): lists members, each opens the drawer.
  function showMapClusterList(card, members, origin) {
    if (!card || !members.length) return;
    clusterListOrigin = origin;
    openClusterIds = members.map(m => m.promise_id);
    openMapCluster(card, `
      <div class="map-selected-title" id="map-cluster-title">${members.length} commitments in this area</div>
      <ul class="map-cluster-list">
        ${members.map(m => `<li><button type="button" class="btn-map-cluster-item" data-inspect-id="${escapeHtml(m.promise_id)}"><span class="verdict-chip ${(m.verdict || '').toLowerCase()}">${formatVerdictLabel(m.verdict)}</span> <span>${escapeHtml(m.promise_id)} · ${escapeHtml(m.entity)}</span></button></li>`).join('')}
      </ul>
      <button type="button" class="btn-map-cluster-close">Close list (Esc)</button>
    `);
    card.querySelectorAll('.btn-map-cluster-item').forEach(btn => {
      btn.addEventListener('click', () => openInspectDrawer(btn.getAttribute('data-inspect-id')));
    });
    const closeBtn = card.querySelector('.btn-map-cluster-close');
    if (closeBtn) closeBtn.addEventListener('click', closeActiveMapClusterList);
  }

  // Hide the cluster list; focus returns to the SVG marker or the street map canvas.
  function closeActiveMapClusterList() {
    const card = document.getElementById('map-selected-card');
    if (!card) return;
    if (clusterListOrigin === 'street' && streetMap) {
      card.classList.add('hidden');
      streetMap.getCanvas().focus();
    } else {
      closeMapCluster(card, document.getElementById('sf-svg-map-wrap'), openClusterIds);
    }
    openClusterIds = null;
    clusterListOrigin = 'svg';
  }

  function renderMapAndDistrictsView(list) {
    const mapWrap = document.getElementById('sf-svg-map-wrap');
    const selectedCard = document.getElementById('map-selected-card');
    const districtBars = document.getElementById('district-bars-list');
    if (!mapWrap || !districtBars) return;

    lastMapList = list;
    if (selectedCard) selectedCard.setAttribute('aria-live', 'polite');
    if (selectedCard && mapCardEscBound !== selectedCard) {
      mapCardEscBound = selectedCard;
      selectedCard.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && openClusterIds && !inspectDrawerOpen()) {
          e.preventDefault();
          closeActiveMapClusterList();
        }
      });
    }
    const useStreet = streetMapActive();
    syncMapModeUi(useStreet);
    if (useStreet) {
      mapWrap.classList.add('hidden');
      renderStreetMap(list);
    } else {
      mapWrap.classList.remove('hidden');
      hideStreetMap();
      renderSvgMap();
    }

    function renderSvgMap() {
      const minLat = 37.704;
      const maxLat = 37.836;
      const minLon = -122.516;
      const maxLon = -122.354;
      const W = 560;
      const H = 430;

      function projectSF(lat, lon) {
        const x = ((lon - minLon) / (maxLon - minLon)) * (W - 60) + 30;
        const y = ((maxLat - lat) / (maxLat - minLat)) * (H - 70) + 28;
        return { x: Math.max(24, Math.min(W - 24, x)), y: Math.max(24, Math.min(H - 36, y)) };
      }

      function projectSFO(lat, lon) {
        const x = ((lon - (-122.405)) / (-122.365 - (-122.405))) * 116 + 426;
        const y = ((37.638 - lat) / (37.638 - 37.605)) * 78 + 332;
        return { x: Math.max(428, Math.min(540, x)), y: Math.max(336, Math.min(408, y)) };
      }

      const verdictColor = VERDICT_COLORS;

      const sfOutlinePath = 'M 55,298 L 62,210 L 66,142 L 88,92 L 154,68 L 238,68 L 315,76 L 372,110 L 398,176 L 408,248 L 392,302 L 320,312 L 222,312 L 125,308 Z';
      const tiPath = 'M 412,56 L 434,54 L 438,84 L 414,88 Z';
      const ggpPath = 'M 68,178 L 166,174 L 166,192 L 68,196 Z';

      const pins = [];
      const regionalItems = [];
      (list || []).forEach(p => {
        const lat = Number(p.latitude);
        const lon = Number(p.longitude);
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
          if (p.location_status === 'not_stated') regionalItems.push(p);
          return;
        }
        const inSFO = lat >= 37.59 && lat <= 37.65 && lon >= -122.42 && lon <= -122.35;
        const inSF = lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon;
        if (!inSF && !inSFO) {
          regionalItems.push(p);
          return;
        }
        const pt = inSFO ? projectSFO(lat, lon) : projectSF(lat, lon);
        pins.push({ p, x: pt.x, y: pt.y, inSFO });
      });

      const isMobile = !!(window.matchMedia && window.matchMedia('(max-width: 720px), (pointer: coarse)').matches);
      lastMapWidth = mapWrap.clientWidth;
      const scale = (mapWrap.clientWidth || W) / W;
      const hitDiameter = mapHitDiameterPx(isMobile) / scale;
      const clusters = clusterPins(pins, hitDiameter);
      openClusterIds = openClusterIds && selectedCard && !selectedCard.classList.contains('hidden') ? openClusterIds : null;

      const markersSvg = clusters.map(cluster => {
        const hit = `<circle class="map-pin-hit" cx="${cluster.x.toFixed(1)}" cy="${cluster.y.toFixed(1)}" r="${(hitDiameter / 2).toFixed(1)}" fill="transparent" />`;
        if (cluster.items.length > 1) {
          const ids = cluster.items.map(i => i.p.promise_id).join(',');
          const n = cluster.items.length;
          const label = escapeHtml(`${n} commitments in this area. Select to list them.`);
          return `
          <g class="map-cluster-node" data-cluster-ids="${escapeHtml(ids)}" tabindex="0" role="button" aria-label="${label}" style="cursor:pointer;">
            ${hit}
            <circle cx="${cluster.x.toFixed(1)}" cy="${cluster.y.toFixed(1)}" r="13" fill="#1E3A8A" stroke="#93C5FD" stroke-width="1.8" />
            <text x="${cluster.x.toFixed(1)}" y="${(cluster.y + 4).toFixed(1)}" text-anchor="middle" fill="#F8FAFC" font-size="12" font-weight="700" font-family="monospace" pointer-events="none">${n}</text>
          </g>`;
        }
        const { p, x, y } = cluster.items[0];
        const v = (p.verdict || 'undecided').toLowerCase();
        const color = verdictColor[v] || '#94A3B8';
        const isCentroid = p.is_centroid !== false;
        const pid = escapeHtml(p.promise_id || '');
        const title = escapeHtml(`${p.entity}: ${p.neighborhood || 'San Francisco'}`);
        return `
          <g class="map-pin-node" data-promise-id="${pid}" tabindex="0" role="button" aria-label="${title}" style="cursor:pointer;">
            ${hit}
            ${isCentroid ? `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9.5" fill="none" stroke="${color}" stroke-width="1.4" stroke-dasharray="2.5 2" opacity="0.78"/>` : ''}
            <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${isCentroid ? '4.8' : '6.5'}" fill="${color}" fill-opacity="${isCentroid ? '0.68' : '0.96'}" stroke="#0B1120" stroke-width="1.5">
              <title>${title} (${isCentroid ? 'Display Centroid' : 'Exact Address'})</title>
            </circle>
          </g>
        `;
      }).join('');

      const regionalHtml = regionalItems.length > 0 ? `
        <div class="map-regional-strip font-mono">
          <span class="regional-strip-label">REGIONAL / STATEWIDE / LOCATION NOT STATED (${regionalItems.length}):</span>
          ${regionalItems.map(p => `<button type="button" class="btn-regional-pin" data-promise-id="${escapeHtml(p.promise_id)}">${escapeHtml(p.promise_id)} · ${escapeHtml(p.entity)}</button>`).join('')}
        </div>
      ` : '';

      mapWrap.innerHTML = `
        ${mapSvgOpenTag(W, H)}
          <g aria-hidden="true">
          <rect x="0" y="0" width="${W}" height="${H}" rx="10" fill="#0B1324" />
          <path d="${sfOutlinePath}" fill="#131E36" stroke="#2D3E5E" stroke-width="1.5" />
          <path d="${tiPath}" fill="#172542" stroke="#364B73" stroke-width="1.2" />
          <path d="${ggpPath}" fill="#12302B" stroke="#1E4D42" stroke-width="1" />
          <text x="115" y="189" fill="#64748B" font-size="9" font-family="monospace">GOLDEN GATE PARK</text>
          <text x="275" y="138" fill="#64748B" font-size="9" font-family="monospace">TENDERLOIN / SOMA</text>
          <text x="225" y="232" fill="#64748B" font-size="9" font-family="monospace">MISSION</text>
          <text x="415" y="47" fill="#64748B" font-size="8.5" font-family="monospace">TREASURE ISL.</text>
          <rect x="422" y="322" width="124" height="94" rx="6" fill="#0F192E" stroke="#334155" stroke-width="1" />
          <text x="430" y="335" fill="#94A3B8" font-size="8.5" font-family="monospace">SFO INSET (AIRPORT)</text>
          </g>
          ${markersSvg}
        </svg>
        ${regionalHtml}
      `;

      bindMapMarkers(mapWrap, {
        // A single marker opens the record drawer directly (issue #44).
        openPromise: (pid, node) => {
          if (node && node.focus) node.focus();
          openInspectDrawer(pid);
        },
        openCluster: (ids) => {
          const members = ids.map(id => (demoData && demoData.promises || []).find(item => item.promise_id === id)).filter(Boolean);
          showMapClusterList(selectedCard, members, 'svg');
        }
      });
    }

    const districtCounts = {};
    for (let i = 1; i <= 11; i++) districtCounts[`D${i}`] = 0;
    let citywideCount = 0;
    (list || []).forEach(p => {
      const rawDist = p.supervisor_district;
      const d = (rawDist !== null && rawDist !== undefined && rawDist !== '')
        ? `D${String(rawDist).trim().replace(/^D/i, '')}`
        : '';
      if (/^D\d+$/.test(d) && Object.prototype.hasOwnProperty.call(districtCounts, d)) {
        districtCounts[d] += 1;
      } else {
        citywideCount += 1;
      }
    });

    const intakeDist = (demoData && demoData.database_status && demoData.database_status.sourcing_audit && demoData.database_status.sourcing_audit.qualified_district_distribution) || {};
    const maxCount = Math.max(8, ...Object.values(districtCounts));

    districtBars.innerHTML = Object.keys(districtCounts).map(dist => {
      const pub = districtCounts[dist];
      const intake = intakeDist[dist] || 0;
      const pct = Math.round((pub / maxCount) * 100);
      return `
        <div class="district-bar-row">
          <span class="district-code font-mono">${dist}</span>
          <div class="district-bar-track">
            <div class="district-bar-fill ${pub === 0 ? 'gap' : ''}" style="width:${Math.max(pub > 0 ? 8 : 0, pct)}%;"></div>
          </div>
          <span class="district-bar-counts font-mono">${pub} pub${intake > 0 ? ` · +${intake} intake` : ''}</span>
        </div>
      `;
    }).join('') + `
      <div class="district-citywide-note font-mono">
        Citywide / Regional (non-district-pinned): <strong>${citywideCount}</strong> commitments
      </div>
    `;
  }

  function renderEntityProfilesView(list) {
    const grid = document.getElementById('entities-profiles-grid');
    if (!grid) return;

    const groups = new Map();
    (list || []).forEach(p => {
      const name = p.entity_canonical_name || p.entity || 'Unknown';
      if (!groups.has(name)) {
        groups.set(name, {
          name,
          category: p.entity_category_canonical || 'city_government',
          datasetTotal: p.entity_promise_count || 1,
          sampleWarning: Boolean(p.entity_sample_warning),
          kept: 0,
          broken: 0,
          inProgress: 0,
          undecided: 0,
          items: [],
          entityImagePath: p.entity_image_path || '',
          entityImageCredit: p.entity_image_credit || '',
          entityImageLicenseUrl: p.entity_image_license_url || '',
          entityImageNote: p.entity_image_note || ''
        });
        const g0 = groups.get(name);
        if (!g0.entityImagePath) {
          const m = window.SFPDrawer.entityMediaFor(entityMedia, name);
          if (m) {
            g0.entityImagePath = m.path;
            g0.entityImageCredit = m.credit;
            g0.entityImageLicenseUrl = m.licenseUrl;
            g0.entityImageNote = m.note;
          }
        }
      }
      const g = groups.get(name);
      g.items.push(p);
      const v = (p.verdict || '').toLowerCase();
      if (v === 'kept') g.kept += 1;
      else if (v === 'broken') g.broken += 1;
      else if (v === 'in_progress') g.inProgress += 1;
      else g.undecided += 1;
    });

    const sorted = Array.from(groups.values()).sort((a, b) => (b.items.length - a.items.length) || a.name.localeCompare(b.name));
    if (sorted.length === 0) {
      grid.innerHTML = '<div class="empty-state-box">No entities match current filters.</div>';
      return;
    }

    grid.innerHTML = sorted.map(g => {
      const tot = g.items.length;
      const keptPct = Math.round((g.kept / tot) * 100);
      const progPct = Math.round((g.inProgress / tot) * 100);
      const brokPct = Math.max(0, 100 - keptPct - progPct);
      const catLabel = g.category.replace(/_/g, ' ');
      const cautionBadge = (g.datasetTotal < 3 || g.sampleWarning)
        ? `<span class="caution-badge-n1 font-mono" title="Small sample size: fewer than 3 tracked commitments">n=${g.datasetTotal} caution</span>`
        : `<span class="entity-count-pill font-mono">${g.datasetTotal} tracked</span>`;

      return `
        <div class="entity-profile-card">
          <div class="entity-card-top">
            ${window.SFPDrawer.entityAvatarHtml(g)}
            <div class="entity-card-title">
              <h4 class="entity-card-name">${escapeHtml(g.name)}</h4>
              <span class="entity-card-cat font-mono">${escapeHtml(catLabel)}</span>
            </div>
            ${cautionBadge}
          </div>
          <div class="entity-stacked-bar" aria-label="Verdict breakdown">
            ${g.kept > 0 ? `<span style="width:${keptPct}%;background:#10B981;" title="${g.kept} Kept"></span>` : ''}
            ${g.inProgress > 0 ? `<span style="width:${progPct}%;background:var(--verdict-progress);" title="${g.inProgress} In Progress"></span>` : ''}
            ${g.broken > 0 ? `<span style="width:${brokPct}%;background:#EF4444;" title="${g.broken} Broken"></span>` : ''}
            ${g.undecided > 0 ? `<span style="width:100%;background:#64748B;" title="${g.undecided} Undecided"></span>` : ''}
          </div>
          <div class="entity-verdict-summary font-mono">
            <span>${g.kept} kept</span> · <span>${g.inProgress} in prog</span> · <span>${g.broken} broken</span>
          </div>
          <div class="entity-item-links">
            ${g.items.slice(0, 3).map(item => `
              <button type="button" class="btn-entity-promise-link" data-promise-id="${escapeHtml(item.promise_id)}">
                <span class="font-mono">${escapeHtml(item.promise_id)}</span>
                <span>${escapeHtml((item.document_title || item.title || item.promise_text || '').slice(0, 48))}…</span>
              </button>
            `).join('')}
          </div>
        </div>
      `;
    }).join('');

    grid.querySelectorAll('.btn-entity-promise-link').forEach(btn => {
      btn.addEventListener('click', () => openInspectDrawer(btn.getAttribute('data-promise-id')));
    });
  }

  function renderQualityAuditView() {
    const kpisEl = document.getElementById('audit-kpis-grid');
    const matrixEl = document.getElementById('audit-pillar-matrix');
    const queueEl = document.getElementById('audit-review-queue-list');
    if (!kpisEl || !matrixEl || !queueEl || !demoData) return;

    const db = demoData.database_status || {};
    const recon = db.evidence_reconciliation || {};
    const q = db.evidence_review_queue || {};
    const sourcing = db.sourcing_audit || {};
    const promises = demoData.promises || [];

    renderAuditFunnelPanel(db);
    renderAuditWindowFunnelPanel(db);
    renderAuditReasonPanel(db);
    renderAuditDenialPanel(db);

    const passCount = promises.filter(p => p.all_checks_passed !== false).length;
    const failPromCount = promises.length - passCount;
    const contradictionCount = promises.filter(p => p.has_contradictory_evidence).length;

    kpisEl.innerHTML = `
      <div class="audit-kpi-card">
        <div class="audit-kpi-label font-mono">DETERMINISTIC CHECKS</div>
        <div class="audit-kpi-value">${passCount} / ${promises.length} pass</div>
        <div class="audit-kpi-sub">${failPromCount} commitments have ${q.total_verification_exception_checks || 22} flagged/unrecorded checks</div>
      </div>
      <div class="audit-kpi-card">
        <div class="audit-kpi-label font-mono">EVIDENCE RECONCILIATION</div>
        <div class="audit-kpi-value">${recon.total_database_evidence_records || 124} DB rows</div>
        <div class="audit-kpi-sub">${recon.verdict_cited_evidence_records || 99} verdict + ${recon.background_context_records || 11} background + ${recon.intake_screening_records || 8} intake + ${recon.duplicate_or_superseded_records || 6} dup</div>
      </div>
      <div class="audit-kpi-card">
        <div class="audit-kpi-label font-mono">CONTRADICTORY CLAIMS</div>
        <div class="audit-kpi-value">${contradictionCount} / ${promises.length}</div>
        <div class="audit-kpi-sub">Adjudicated with dual supporting &amp; refuting summaries</div>
      </div>
      <div class="audit-kpi-card">
        <div class="audit-kpi-label font-mono">OUTCOME-BLIND INTAKE</div>
        <div class="audit-kpi-value">${sourcing.qualified_count || 24} qualified</div>
        <div class="audit-kpi-sub">From ${sourcing.encountered_count || 63} discovered (${sourcing.needs_review_count || 38} review, ${sourcing.rejected_count || 1} rejected)</div>
      </div>
    `;

    const pillarNames = [
      'Civic Life',
      'Housing & Neighborhoods',
      'Transit & Movement',
      'Weather & Environment',
      'Work & Opportunity',
      'Sports & Recreation',
      'Arts, Music & Nightlife',
      'Food & Local Business',
      'People & Demographics',
      'Culture & Social Life'
    ];
    const pubByPillar = {};
    promises.forEach(p => {
      const k = p.pillar || 'Civic Life';
      pubByPillar[k] = (pubByPillar[k] || 0) + 1;
    });
    const intakeByPillar = sourcing.qualified_pillar_distribution || {};

    matrixEl.innerHTML = pillarNames.map(pillar => {
      const pub = pubByPillar[pillar] || 0;
      const intake = intakeByPillar[pillar] || 0;
      const isGap = pub === 0;
      return `
        <div class="pillar-matrix-row ${isGap ? 'gap-row' : ''}">
          <span class="pillar-name">${escapeHtml(pillar)}</span>
          <span class="pillar-counts font-mono">${pub} published · <strong>+${intake} intake</strong></span>
        </div>
      `;
    }).join('');

    const queueItems = [];
    promises.forEach(p => {
      if (p.all_checks_passed === false || (p.failed_check_count || 0) > 0) {
        const names = Array.isArray(p.failed_check_names) && p.failed_check_names.length
          ? p.failed_check_names.join(', ')
          : `${p.failed_check_count || 1} flagged check(s)`;
        queueItems.push({
          priority: 'P2 · CHECK',
          promise_id: p.promise_id,
          entity: p.entity_canonical_name || p.entity || '',
          reason: `Verification exceptions: ${names}`
        });
      }
    });
    promises.forEach(p => {
      if (p.has_contradictory_evidence) {
        queueItems.push({
          priority: 'P3 · CONTRA',
          promise_id: p.promise_id,
          entity: p.entity_canonical_name || p.entity || '',
          reason: `Contradictory evidence (${p.verdict_supporting_evidence_count || 0} supporting vs ${p.verdict_contradicting_evidence_count || 0} refuting)`
        });
      }
    });

    queueEl.innerHTML = queueItems.slice(0, 18).map(item => `
      <button type="button" class="audit-queue-item" data-promise-id="${escapeHtml(item.promise_id)}">
        <span class="queue-priority-tag font-mono">${escapeHtml(item.priority)}</span>
        <div class="queue-item-body">
          <div class="queue-item-head">${escapeHtml(item.promise_id)} · ${escapeHtml(item.entity)}</div>
          <div class="queue-item-reason">${escapeHtml(item.reason)}</div>
        </div>
      </button>
    `).join('');

    queueEl.querySelectorAll('.audit-queue-item').forEach(btn => {
      btn.addEventListener('click', () => openInspectDrawer(btn.getAttribute('data-promise-id')));
    });
  }

  const FUNNEL_STAGE_LABELS = {
    leads_encountered: 'Leads encountered',
    sources_archived: 'Sources archived',
    qualified: 'Qualified intake',
    screened: 'Screened',
    published: 'Published',
    quarantined: 'Quarantined'
  };

  function renderAuditFunnelPanel(db) {
    const el = document.getElementById('audit-funnel-bars');
    if (!el) return;
    const stages = SFPViz.funnelStages(db);
    if (!stages.length) {
      el.innerHTML = '<p class="viz-empty">No funnel stages in the exported snapshot.</p>';
      return;
    }
    const max = Math.max(...stages.map(s => s.count), 1);
    el.innerHTML = stages.map(s => {
      const label = FUNNEL_STAGE_LABELS[s.stage] || s.stage;
      const conv = s.conversion !== null
        ? ` <span class="viz-bar-pct">(${(s.conversion * 100).toFixed(1)}%)</span>`
        : '';
      const universe = s.universe === 'intake_register' ? 'intake' : 'db';
      return `
        <div class="viz-bar-row">
          <span class="viz-bar-label" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
          <span class="viz-bar-track">
            <span class="viz-bar-fill" style="width:${((s.count / max) * 100).toFixed(2)}%; background:var(--cyan)"></span>
          </span>
          <span class="viz-bar-count font-mono">${s.count}${conv} · ${universe}</span>
        </div>
      `;
    }).join('');
  }

  const WINDOW_FUNNEL_STAGE_LABELS = {
    raw: 'Raw results',
    allowlisted: 'Allowlisted',
    archived: 'Archived sources',
    leads: 'Leads',
    gate: 'Gate reached'
  };

  function renderAuditWindowFunnelPanel(db) {
    const el = document.getElementById('audit-window-funnel-bars');
    if (!el) return;
    const windows = SFPViz.windowFunnelStages(db);
    if (!windows.length) {
      el.innerHTML = '<p class="viz-empty">No per-window funnel rounds in the exported snapshot; discovery rounds append {window, round_id, counts} rows to data/window_funnel_rounds.json and this panel fills from the export.</p>';
      return;
    }
    el.innerHTML = windows.map(w => {
      const max = Math.max(...w.stages.map(s => s.count), 1);
      const rows = w.stages.map(s => {
        const label = WINDOW_FUNNEL_STAGE_LABELS[s.stage] || s.stage;
        const conv = s.conversion !== null
          ? ` <span class="viz-bar-pct">(${(s.conversion * 100).toFixed(1)}%)</span>`
          : '';
        return `
          <div class="viz-bar-row">
            <span class="viz-bar-label" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
            <span class="viz-bar-track">
              <span class="viz-bar-fill" style="width:${((s.count / max) * 100).toFixed(2)}%; background:var(--kept)"></span>
            </span>
            <span class="viz-bar-count font-mono">${s.count}${conv}</span>
          </div>
        `;
      }).join('');
      const header = `<p class="audit-panel-sub font-mono">${escapeHtml(w.window)} · ${w.roundCount} round${w.roundCount === 1 ? '' : 's'}</p>`;
      return header + rows;
    }).join('');
  }

  function renderAuditReasonPanel(db) {
    const el = document.getElementById('audit-reason-bars');
    if (!el) return;
    const reasons = SFPViz.quarantineReasons(db);
    const codes = Object.entries(reasons.byReason)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([code, count]) => ({ label: code.replace(/_/g, ' '), count, color: 'var(--purple)' }));
    const footer = (reasons.totalQuarantined !== null)
      ? `<p class="audit-panel-sub font-mono">${reasons.totalReasonCodes} codes across ${reasons.totalQuarantined} quarantined registry items</p>`
      : '';
    renderBarRows(el, codes, reasons.totalQuarantined || 0);
    el.innerHTML += footer;
  }

  function renderAuditDenialPanel(db) {
    const el = document.getElementById('audit-denial-bars');
    if (!el) return;
    const domains = SFPViz.denialDomains(db);
    if (!domains.length) {
      el.innerHTML = '<p class="viz-empty">No denied leads recorded in the current export; live discovery rounds append deny rows and this histogram fills from the export.</p>';
      return;
    }
    const max = Math.max(...domains.map(x => x.count), 1);
    el.innerHTML = domains.map(d => {
      const stypes = Object.keys(d.sourceTypes).sort().join(', ');
      const title = stypes ? ` title="${escapeHtml('Source types: ' + stypes)}"` : '';
      return `
        <div class="viz-bar-row"${title}>
          <span class="viz-bar-label">${escapeHtml(d.domain)}</span>
          <span class="viz-bar-track">
            <span class="viz-bar-fill" style="width:${((d.count / max) * 100).toFixed(2)}%; background:var(--red)"></span>
          </span>
          <span class="viz-bar-count font-mono">${d.count}${stypes ? ' · ' + escapeHtml(stypes) : ''}</span>
        </div>
      `;
    }).join('');
  }

  // -------------------------------------------------------------------------
  // Drawer pure render helpers (SFPDRAWER_PURE_START .. END)
  //
  // Self-contained (no closure over outer state) so tests/test_drawer_render.py
  // can execute this marked block with node against docs/data.json and assert
  // the drawer renders exactly what the export carries.
  // -------------------------------------------------------------------------
  /* SFPDRAWER_PURE_START */
  const DRAWER_HISTORY_LABELS = {
    kept: 'Kept',
    broken: 'Broken',
    in_progress: 'In progress',
    undecided: 'Undecided',
    delayed_or_partial: 'Delayed / partial',
    kept_then_reversed: 'Later closed / reversed',
    quarantined: 'Quarantined'
  };

  function drawerEscapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  // '2023-04-01T…' -> 'April 2023'; '' when absent or unparseable — a missing
  // export date is never replaced with an invented one.
  function formatHistoryMonth(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleString('en-US', { month: 'long', year: 'numeric' });
  }

  function verdictStepHtml(entry) {
    const v = String((entry && entry.verdict) || 'undecided').toLowerCase().replace(/[\s-]+/g, '_');
    const label = DRAWER_HISTORY_LABELS[v] || (entry && entry.verdict) || 'Undecided';
    const when = formatHistoryMonth(entry && entry.decided_at);
    const reason = entry && entry.reason ? ` title="${drawerEscapeHtml(entry.reason)}"` : '';
    return `<span class="verdict-chip ${drawerEscapeHtml(v)}"${reason}>${drawerEscapeHtml(label)}${when ? ' — ' + drawerEscapeHtml(when) : ''}</span>`;
  }

  // Timeline replaces the single static chip only when history carries more
  // than one verdict; single-verdict records keep the chip unchanged.
  function verdictTimelineHtml(history) {
    if (!Array.isArray(history) || history.length < 2) return null;
    return history.map(verdictStepHtml)
      .join('<span class="drawer-timeline-arrow" aria-hidden="true">&rarr;</span>');
  }

  // Provenance line for one verification row: model / reviewer / run / date,
  // each only when the export records it. No entry or no provenance -> ''.
  function checkProvenanceHtml(entry) {
    if (!entry) return '';
    const bits = [];
    if (entry.model_id) bits.push(`model ${entry.model_id}`);
    if (entry.checked_by) bits.push(`reviewer ${entry.checked_by}`);
    if (entry.run_id) bits.push(`run ${entry.run_id}`);
    if (entry.checked_at) bits.push(String(entry.checked_at).split('T')[0]);
    if (!bits.length) return '';
    return `<div class="drawer-check-provenance font-mono">${drawerEscapeHtml(bits.join(' · '))}</div>`;
  }

  // Outcome of each named check, derived only from what the export records:
  // 'pass' / 'fail' from a recorded result row (or recorded relevance scores),
  // 'unrecorded' when nothing was exported. A missing row is never a pass.
  const DRAWER_CHECK_IDS = [
    'authenticity_domain', 'authenticity_hash', 'accuracy_quote', 'authenticity_speaker',
    'accuracy_date', 'verdict_rubric', 'relevance_gate'
  ];

  function drawerCheckOutcomes(p) {
    const rows = {};
    (Array.isArray(p && p.checks) ? p.checks : []).forEach(c => { if (c && c.check) rows[c.check] = c; });
    const flagged = new Set(Array.isArray(p && p.failed_check_names) ? p.failed_check_names : []);
    const rel = p && p.relevance;
    const relRecorded = !!rel && typeof rel.score === 'number' && isFinite(rel.score);
    const out = {};
    DRAWER_CHECK_IDS.forEach(id => {
      const row = rows[id];
      if (row) {
        out[id] = { status: row.passed === true ? 'pass' : 'fail', reason: row.reason || '' };
      } else if (id === 'relevance_gate' && relRecorded) {
        out[id] = { status: rel.score >= 5 ? 'pass' : 'fail', reason: '' };
      } else if (flagged.has(id)) {
        out[id] = { status: 'fail', reason: '' };
      } else {
        out[id] = { status: 'unrecorded', reason: '' };
      }
    });
    return out;
  }

  function drawerChecksSummary(outcomes, p) {
    const ids = Object.keys(outcomes);
    const count = s => ids.filter(id => outcomes[id].status === s).length;
    const passed = count('pass');
    const unrecorded = count('unrecorded');
    const failures = Math.max(count('fail'), (p && p.failed_check_count) || 0);
    if (failures > 0 || (p && p.all_checks_passed === false)) {
      return { kind: 'fail', failures, passed, unrecorded };
    }
    if (unrecorded > 0) return { kind: 'partial', failures: 0, passed, unrecorded };
    return { kind: 'pass', failures: 0, passed, unrecorded: 0 };
  }

  // Header line for the checks accordion: the icon and tone must match what
  // was actually recorded, so a record with 2 of 7 passed never shows a
  // green check.
  function drawerChecksSummaryView(summary) {
    const base = `${summary.passed}/7 Verification Checks Recorded as Passed`;
    if (summary.kind === 'fail') {
      return { kind: 'fail', icon: '\u2715', label: `${base} \u00b7 ${summary.failures} failed` };
    }
    if (summary.kind === 'partial') {
      return { kind: 'partial', icon: '!', label: `${base} \u00b7 ${summary.unrecorded} not recorded` };
    }
    if (summary.kind === 'pass') return { kind: 'pass', icon: '\u2713', label: base };
    throw new Error(`drawerChecksSummaryView: unknown summary kind ${summary.kind}`);
  }

  // The contradiction banner shows only when the record itself says its evidence
  // conflicts. Claim lists and free-text notes do not count: a note such as
  // "no contradicting hiring count" used to trip a regex and put a
  // "contradictory evidence" banner on a record with zero contradicting items.
  function drawerContradictionView(p) {
    if (typeof p.has_contradictory_evidence !== 'boolean') {
      throw new Error(`drawerContradictionView: record ${p.promise_id} has no has_contradictory_evidence flag`);
    }
    const supporting = p.verdict_supporting_evidence_count || 0;
    const contradicting = Math.max(p.verdict_contradicting_evidence_count || 0, p.refuting_evidence_count || 0);
    // P64 carries 2 contradicting claims with the flag false, so a recorded contradicting count also qualifies.
    if (!p.has_contradictory_evidence && contradicting === 0) return null;
    return { supporting, contradicting };
  }

  // Entity avatar (issue #83): same-origin relative path from the media
  // manifest, shown with a visible credit. '' when the export carries no entity
  // image or the path is not a plain relative one, so the card is unchanged.
  function entityAvatarHtml(g) {
    const src = g && g.entityImagePath;
    if (typeof src !== 'string' || !src || /^[a-z][a-z0-9+.-]*:|^\/|\.\.|\\/i.test(src)) return '';
    const parts = [];
    if (g.entityImageCredit) parts.push(drawerEscapeHtml(g.entityImageCredit));
    const url = g.entityImageLicenseUrl;
    // Link only to an https licence text (CC BY / CC BY-SA need one); navigation, never fetched by the page.
    if (typeof url === 'string' && /^https:\/\//i.test(url)) {
      parts.push(`<a href="${drawerEscapeHtml(url)}" target="_blank" rel="noopener noreferrer">licence</a>`);
    }
    if (g.entityImageNote) parts.push(drawerEscapeHtml(g.entityImageNote));
    const credit = parts.length
      ? `<span class="entity-avatar-credit font-mono">${parts.join(' · ')}</span>` : '';
    return `<span class="entity-avatar"><img class="entity-avatar-img" src="${drawerEscapeHtml(src)}" alt="" width="40" height="40" loading="lazy">${credit}</span>`;
  }

  // Entity name key shared by the media manifest lookup and its test.
  function entityNameKey(name) {
    return String(name == null ? '' : name).normalize('NFKC').trim().replace(/\s+/g, ' ').toLowerCase();
  }

  const TRADEMARK_NOTE = 'Logo is a trademark of its owner';

  // docs/media/manifest.json -> Map(entityNameKey -> avatar fields). Used when an
  // exported record lacks entity_image_path, so avatars show without a data.json export.
  function entityMediaFromManifest(manifest) {
    const map = new Map();
    ((manifest && manifest.entities) || []).forEach(e => {
      if (!e || !e.entity_name || typeof e.path !== 'string' || !e.path) return;
      const isCcBy = /^cc[ -]by/i.test(String(e.license || ''));
      map.set(entityNameKey(e.entity_name), {
        path: 'media/' + e.path,
        credit: `${e.credit || ''} / ${e.license || ''}`.replace(/^ \/ | \/ $/g, ''),
        licenseUrl: isCcBy ? (e.license_url || '') : '',
        note: (e.logo || /trademark/i.test(String(e.restrictions || ''))) ? TRADEMARK_NOTE : ''
      });
    });
    return map;
  }

  function entityMediaFor(map, name) {
    return (map && map.get(entityNameKey(name))) || null;
  }

  // One short line for the basis of a v2 verdict decided under the outcome
  // rules (record.outcome_basis); '' when the record carries none.
  function outcomeBasisText(p) {
    const b = p && p.outcome_basis;
    if (!b || typeof b !== 'object') return '';
    const parts = [];
    if (b.open_ended) parts.push('Open-ended commitment');
    else if (Array.isArray(b.rules) && b.rules.includes('R2')) parts.push('One-off dated commitment');
    const reason = String(b.reason || '').trim();
    if (b.status_not_checked) parts.push('current status not checked');
    else if (reason) parts.push(reason);
    if (!parts.length) return '';
    const line = parts.join(' \u00b7 ');
    return line.charAt(0).toUpperCase() + line.slice(1);
  }

  const SFPDrawer = {
    verdictTimelineHtml, checkProvenanceHtml, formatHistoryMonth, entityAvatarHtml,
    entityNameKey, entityMediaFromManifest, entityMediaFor,
    drawerCheckOutcomes, drawerChecksSummary, drawerChecksSummaryView, drawerContradictionView, outcomeBasisText
  };
  window.SFPDrawer = SFPDrawer;
  /* SFPDRAWER_PURE_END */

  // -------------------------------------------------------------------------
  // 4-Part Detail Drawer (1.4)
  // -------------------------------------------------------------------------
  function openInspectDrawer(promiseId) {
    if (!demoData) return;
    const p = (demoData.promises || []).find(x => x.promise_id === promiseId) || demoData.p02;
    if (!p) return;

    lastActiveElement = document.activeElement;
    if (p.promise_id && permalinkId() !== p.promise_id && window.history && window.history.replaceState) {
      window.history.replaceState(null, '', `#promise-${p.promise_id}`);
    }

    const backdrop = document.getElementById('inspect-drawer-backdrop');
    const drawer = document.getElementById('inspect-drawer');
    if (!backdrop || !drawer) return;

    // Header
    const subtitleEl = document.getElementById('drawer-subtitle');
    const titleEl = document.getElementById('drawer-title');
    const chipEl = document.getElementById('drawer-verdict-chip');
    const horizonBadge = document.getElementById('drawer-horizon-badge');
    const idBadge = document.getElementById('drawer-id-badge');

    const rank = String(p.impact_rank || p.display_no || '01').padStart(2, '0');
    if (idBadge) idBadge.textContent = `#${rank}`;

    const isCorporate = /visa|pg&e|pacific gas|comcast|waymo|zoox|at&t/i.test(p.entity || '') || /corporate/i.test(p.role || '');
    const scopeRaw = p.geographic_scope ? p.geographic_scope.replace(/_/g, ' ') : 'citywide';
    const geoType = p.is_centroid === false ? 'Exact address' : 'Display centroid';
    const locationNotStated = p.location_status === 'not_stated';
    const geoPinLabel = locationNotStated ? 'Location not stated'
      : (scopeRaw.toLowerCase() === geoType.toLowerCase() ? geoType : `${geoType} (${scopeRaw})`);
    if (subtitleEl) {
      if (isCorporate) {
        subtitleEl.textContent = `${p.entity} · Corporate Entity · ${geoPinLabel}`;
      } else {
        const loc = (p.neighborhood && p.neighborhood !== 'Citywide') ? p.neighborhood : (p.role || 'San Francisco');
        subtitleEl.textContent = `${p.entity} · ${loc} · ${geoPinLabel}`;
      }
    }
    if (titleEl) {
      // Titles come from the export (PROMISE_TITLES is baked per record);
      // the entity-name fallback is the exporter's own default shape.
      let t = p.document_title || p.title || '';
      if (!t || t.toLowerCase() === `${p.entity.toLowerCase()} commitment`) {
        t = `${p.entity} Commitment`;
      }
      titleEl.textContent = t;
    }
    const verdClass = (p.verdict || 'undecided').toLowerCase().replace(/[\s-]+/g, '_');
    // When the export carries more than one verdict, the static chip is
    // replaced by the history timeline; single-verdict records keep the chip.
    const timelineHtml = window.SFPDrawer
      ? window.SFPDrawer.verdictTimelineHtml(p.verdict_history)
      : null;
    const timelineWrap = document.getElementById('drawer-verdict-timeline');
    if (chipEl) {
      chipEl.className = `verdict-chip ${verdClass}`;
      chipEl.textContent = formatVerdictLabel(p.verdict);
      chipEl.classList.toggle('hidden', Boolean(timelineHtml));
    }
    if (timelineWrap) {
      timelineWrap.innerHTML = timelineHtml || '';
      timelineWrap.classList.toggle('hidden', !timelineHtml);
    }
    if (horizonBadge) {
      horizonBadge.classList.toggle('hidden', !p.long_horizon);
    }

    // Part 1: Promise & Source
    const promiseQuote = document.getElementById('drawer-promise-quote');
    const spkVal = document.getElementById('drawer-speaker-val');
    const saidVal = document.getElementById('drawer-said-date-val');
    const dueVal = document.getElementById('drawer-due-date-val');
    const tierVal = document.getElementById('drawer-tier-val');
    const srcUrl = document.getElementById('drawer-source-url');
    const hashEl = document.getElementById('drawer-hash');
    const btnCopy = document.getElementById('btn-drawer-copy-hash');
    const retVal = document.getElementById('drawer-retrieved-date');

    const tier = getSourceTier(p.source_url);
    if (promiseQuote) promiseQuote.textContent = `“${cleanQuoteText(p.promise_text || '')}”`;
    if (spkVal) spkVal.textContent = isCorporate ? `${p.entity} (Corporate / Commercial Entity)` : `${p.entity} (${p.role || 'Public Official'})`;
    const saidDateFormatted = formatPrecisionDate(p.promised_date, p.promise_date_precision);
    if (saidVal) saidVal.textContent = saidDateFormatted + (p.promise_date_precision && p.promise_date_precision !== 'day' ? ` (${p.promise_date_precision})` : '');
    if (saidVal && p.promise_date_derived === true) {
      // v2 records whose commitment date was derived, not stated, say so.
      saidVal.textContent += ' (derived)';
      saidVal.title = p.promised_date_note || 'Derived from the source, not stated in it';
    }
    const dueStatusLabels = {
      not_applicable: 'No deadline (not applicable)',
      not_yet_known: 'Pending (not yet known)',
      not_captured: 'Not captured in source'
    };
    const dueDateFormatted = p.due_date
      ? formatPrecisionDate(p.due_date, p.due_date_precision)
      : (dueStatusLabels[p.due_date_status] || 'No deadline');
    if (dueVal) dueVal.textContent = dueDateFormatted + (p.due_date && p.due_date_precision && p.due_date_precision !== 'day' ? ` (${p.due_date_precision})` : '');
    if (tierVal) tierVal.textContent = tier;
    if (srcUrl) {
      srcUrl.href = p.source_url || '#';
      srcUrl.textContent = p.source_url || 'source link not recorded';
    }
    const hash = p.source_hash || '';
    const cleanFile = (p.source_file_path || '').split('/').pop() || (hash ? `${hash.slice(0, 16)}.md` : 'source.md');
    if (hashEl) {
      hashEl.textContent = hash ? `${hash.slice(0, 16)}…${hash.slice(-8)} (${cleanFile})` : 'not recorded';
    }
    if (btnCopy) btnCopy.setAttribute('data-hash', hash);
    if (retVal) retVal.textContent = p.fetched_at ? p.fetched_at.split('T')[0] : 'Nov 10, 2026';

    // Media
    const mediaBox = document.getElementById('drawer-media-box');
    const mediaImg = document.getElementById('drawer-media-img');
    const mediaCaption = document.getElementById('drawer-media-caption');
    const imgUrl = p.media_path || p.media_image_url || p.image_url;
    const mediaFallback = document.getElementById('drawer-media-fallback');
    const mediaIllo = document.getElementById('drawer-media-illustration');
    const mediaHeader = mediaBox && mediaBox.querySelector('.drawer-media-header');
    // Category illustration stands in whenever the record has no image, or
    // the hotlinked image fails to load, so no drawer is text-only.
    const showIllustration = (on) => {
      if (!mediaIllo) return;
      mediaIllo.hidden = !on;
      mediaIllo.innerHTML = on ? categoryThumbHtml(p, 'cat-thumb-lg') : '';
      if (mediaHeader) mediaHeader.hidden = on;
      if (mediaCaption) mediaCaption.hidden = on;
    };
    if (imgUrl && mediaBox && mediaImg) {
      mediaBox.style.display = 'block';
      showIllustration(false);
      // A hotlinked image that fails to load shows the styled fallback, never
      // the browser's broken-image glyph or alt text.
      if (mediaFallback) mediaFallback.hidden = true;
      mediaImg.style.display = '';
      mediaImg.onerror = () => {
        mediaImg.style.display = 'none';
        if (mediaFallback) mediaFallback.hidden = false;
        showIllustration(true);
      };
      mediaImg.onload = () => {
        if (mediaFallback) mediaFallback.hidden = true;
      };
      if (mediaImg.getAttribute('src') === imgUrl) {
        mediaImg.removeAttribute('src');
      }
      mediaImg.src = imgUrl;
      mediaImg.alt = p.media_caption || (titleEl ? titleEl.textContent : '') || 'Source media photo';
      if (mediaCaption) {
        mediaCaption.textContent = p.media_path
          ? `Photo: ${p.media_credit || 'Unknown'} / ${p.media_license || 'license unknown'}`
          : (p.media_caption || 'Verified source photographic archive');
      }
    } else if (mediaBox) {
      mediaBox.style.display = 'block';
      mediaImg.style.display = 'none';
      mediaImg.removeAttribute('src');
      if (mediaFallback) mediaFallback.hidden = true;
      showIllustration(true);
    }

    // Part 2: Verdict & Plain Reason
    const plainReasonEl = document.getElementById('drawer-plain-reason');
    const decidedAtEl = document.getElementById('drawer-decided-at');

    if (plainReasonEl) plainReasonEl.textContent = p.factual_outcome || formatPlainVerdictReason(p.verdict_reason, p.verdict, p.promise_id);
    const basisEl = document.getElementById('drawer-outcome-basis');
    if (basisEl) {
      const basisText = window.SFPDrawer.outcomeBasisText(p);
      basisEl.textContent = basisText;
      basisEl.hidden = !basisText;
    }
    if (decidedAtEl) decidedAtEl.textContent = p.decided_at ? p.decided_at.split('T')[0] : (p.opened_date || 'Nov 10, 2026');

    // Part 3: Advocates
    const keptBody = document.getElementById('drawer-adv-kept-body');
    const brokenBody = document.getElementById('drawer-adv-broken-body');
    const colKept = document.getElementById('drawer-adv-col-kept');
    const colBroken = document.getElementById('drawer-adv-col-broken');
    const bundles = p.advocate_bundles || {};
    const kClaims = (bundles.kept && bundles.kept.claims) || [];
    const bClaims = (bundles.broken && bundles.broken.claims) || [];

    // Contradiction banner
    const contradictionBanner = document.getElementById('drawer-contradiction-banner');
    if (contradictionBanner) {
      const contra = window.SFPDrawer.drawerContradictionView(p);
      const hasContra = contra !== null;
      if (hasContra) {
        const supCount = contra.supporting;
        const conCount = contra.contradicting;
        const supSum = p.supporting_evidence_summary || '';
        const conSum = p.contradicting_evidence_summary || '';
        const arbRule = p.arbitration_rule_explanation || (p.factual_outcome || formatPlainVerdictReason(p.verdict_reason, p.verdict, p.promise_id));
        contradictionBanner.innerHTML = `
          <div class="contradiction-adjudication-box font-mono">
            <h4>&#9878; Contradictory Evidence Adjudicated (${supCount} supporting vs ${conCount} contradicting)</h4>
            ${supSum ? `<p><strong>Supporting case:</strong> ${escapeHtml(supSum)}</p>` : ''}
            ${conSum ? `<p><strong>Contradicting case:</strong> ${escapeHtml(conSum)}</p>` : ''}
            <p><strong>Arbitration ruling:</strong> ${escapeHtml(arbRule)}</p>
          </div>
        `;
        contradictionBanner.style.display = 'block';
      } else {
        contradictionBanner.innerHTML = '';
        contradictionBanner.style.display = 'none';
      }
    }

    const verdictLower = (p.verdict || '').toLowerCase();
    if (colKept && colBroken) {
      if (verdictLower === 'kept') {
        colKept.style.borderTop = '3px solid #10B981';
        colBroken.style.borderTop = '1px solid var(--border, rgba(255,255,255,0.1))';
      } else if (verdictLower === 'broken') {
        colBroken.style.borderTop = '3px solid #EF4444';
        colKept.style.borderTop = '1px solid var(--border, rgba(255,255,255,0.1))';
      } else {
        colKept.style.borderTop = '1px solid var(--border, rgba(255,255,255,0.1))';
        colBroken.style.borderTop = '1px solid var(--border, rgba(255,255,255,0.1))';
      }
    }

    function formatAdvClaims(claims, fallbackNote) {
      if (!claims || claims.length === 0) {
        return `<p style="font-style: italic; color: var(--muted); margin: 0;">${escapeHtml(fallbackNote)}</p>`;
      }
      const seenQuotes = new Set();
      const uniqueList = [];
      for (const c of claims) {
        const raw = (c.quote || c.statement || '').trim();
        if (!raw) continue;
        const norm = raw.toLowerCase();
        if (seenQuotes.has(norm)) continue;
        seenQuotes.add(norm);
        uniqueList.push(c);
      }
      if (uniqueList.length === 0) {
        return `<p style="font-style: italic; color: var(--muted); margin: 0;">${escapeHtml(fallbackNote)}</p>`;
      }

      return uniqueList.map(c => {
        let qText = cleanQuoteText(c.quote || c.statement || '').trim();
        if (/^[a-z]/.test(qText)) {
          qText = '…' + qText;
        }
        const rawUrl = c.source_url || p.source_url || '';
        let domainStr = '';
        if (rawUrl) {
          try {
            domainStr = new URL(rawUrl).hostname.replace(/^www\./, '');
          } catch (e) {
            domainStr = rawUrl;
          }
        }
        const domainLink = domainStr
          ? `<a href="${escapeHtml(rawUrl)}" target="_blank" rel="noopener noreferrer" class="drawer-evidence-domain-link font-mono">Source: ${escapeHtml(domainStr)} &nearr;</a>`
          : `<span class="drawer-evidence-domain-link font-mono">Source: Verified disk archive</span>`;

        return `
          <div class="drawer-evidence-item">
            <blockquote class="drawer-evidence-quote font-serif">&ldquo;${escapeHtml(qText)}&rdquo;</blockquote>
            <div class="drawer-evidence-source">${domainLink}</div>
          </div>
        `;
      }).join('');
    }

    if (keptBody) {
      keptBody.innerHTML = formatAdvClaims(kClaims, 'No affirmative progress records filed during review cycle.');
    }
    if (brokenBody) {
      const note = (bundles.broken && bundles.broken.note) || 'No contradicting evidence or cancellation records found in saved sources.';
      brokenBody.innerHTML = formatAdvClaims(bClaims, note);
    }

    // Part 4: Arbitrator 7 Checks & Relevance Gate
    const checksList = document.getElementById('drawer-checks-list');

    // Dynamic allowlist description
    let domain = '';
    try {
      domain = new URL(p.source_url).hostname.replace(/^www\./, '');
    } catch (e) {
      domain = p.source_url || '';
    }
    const isMunicipal = /(sf\.gov|sfmta\.com|flysfo\.com|legistar|sfcontroller|sfgov\.org)/i.test(domain);
    let domainDesc = '';
    if (isMunicipal) {
      domainDesc = `Domain verified on municipal whitelist (${domain || 'sf.gov'}).`;
    } else if (tier === 'News' || /thefrisc|sfchronicle|sfstandard|missionlocal|sfexaminer/i.test(domain)) {
      domainDesc = `Approved local journalism source domain (${domain}).`;
    } else if (isCorporate || /bisnow|businesswire|prnewswire/i.test(domain)) {
      domainDesc = `Approved corporate / commercial publication domain (${domain}).`;
    } else {
      domainDesc = `Domain verified on approved domain whitelist (${domain}).`;
    }

    // Relevance is shown only when the export records it; no default score.
    const rel = p.relevance || {};
    const relRecorded = typeof rel.score === 'number' && isFinite(rel.score);
    const relScore = relRecorded ? rel.score : null;
    const outcomes = window.SFPDrawer.drawerCheckOutcomes(p);
    const recordedSummary = window.SFPDrawer.drawerChecksSummary(outcomes, p);
    const summaryLabel = document.querySelector('#inspect-drawer-backdrop .checks-summary-label');
    const summaryIcon = document.querySelector('#inspect-drawer-backdrop .checks-summary-icon');
    const summaryView = window.SFPDrawer.drawerChecksSummaryView(recordedSummary);
    if (summaryLabel) summaryLabel.textContent = summaryView.label;
    if (summaryIcon) {
      summaryIcon.textContent = summaryView.icon;
      summaryIcon.dataset.kind = summaryView.kind;
    }


    const rawChecks = p.checks || [];
    const checkMap = {};
    rawChecks.forEach(c => {
      checkMap[c.check] = c;
    });

    const checkDefinitions = [
      { id: 'authenticity_domain', title: 'Domain Allowlist Enforcement', defaultDesc: domainDesc },
      { id: 'authenticity_hash', title: 'SHA-256 Byte-Level Integrity', defaultDesc: 'Computed hash matches disk fingerprint byte-for-byte.' },
      { id: 'accuracy_quote', title: 'Verbatim Quote Substring Check', defaultDesc: 'Extracted commitment found verbatim in saved source bytes.' },
      { id: 'authenticity_speaker', title: 'Speaker & Role Call Verification', defaultDesc: isCorporate ? 'Corporate entity attribution verified against corporate registry.' : 'Municipal speaker attribution verified against public roster.' },
      { id: 'accuracy_date', title: 'Temporal Window & Horizon Bounds', defaultDesc: 'Said, due, and outcome dates conform to strict temporal order.' },
      { id: 'verdict_rubric', title: 'Deterministic Rubric Application', defaultDesc: 'Binary decision logic evaluates passing claims directly to verdict.' },
      { id: 'relevance_gate', title: 'Relevance Gate Score >= 5.0', defaultDesc: relRecorded ? `Scored ${relScore}/8 for public impact and measurable outcomes.` : '' }
    ];

    // Per-review provenance (model/reviewer/run) indexed by check id; only
    // rows the export carries provenance for render a provenance line.
    const verifByCheck = {};
    (Array.isArray(p.verification_history) ? p.verification_history : []).forEach(v => {
      if (v && v.check) verifByCheck[v.check] = v;
    });
    const provFor = id => (window.SFPDrawer ? window.SFPDrawer.checkProvenanceHtml(verifByCheck[id]) : '');
    const resolvedChecks = checkDefinitions.map(def => {
      const o = outcomes[def.id];
      let desc;
      if (o.status === 'unrecorded') {
        desc = 'Not recorded in this snapshot.';
      } else if (o.reason) {
        desc = o.reason;
      } else if (def.id === 'relevance_gate') {
        desc = def.defaultDesc;
      } else {
        desc = o.status === 'pass' ? 'Check passed.' : 'Verification check failed.';
      }
      return { title: def.title, status: o.status, desc, provenance: provFor(def.id) };
    });

    if (checksList) {
      const sum = window.SFPDrawer.drawerChecksSummary(outcomes, p);
      let bannerHtml = '';
      if (sum.kind === 'fail') {
        bannerHtml = `<div class="checks-summary-banner fail font-mono">&#9888; ${sum.failures} Verification Exception${sum.failures > 1 ? 's' : ''} Flagged (${sum.passed}/7 passed)</div>`;
      } else if (sum.kind === 'partial') {
        bannerHtml = `<div class="checks-summary-banner unrecorded font-mono">${sum.passed} of 7 Checks Recorded as Passed &middot; ${sum.unrecorded} Not Recorded</div>`;
      } else {
        bannerHtml = `<div class="checks-summary-banner pass font-mono">&#10003; All 7 Deterministic Checks Passed (${relScore}/8 Relevance)</div>`;
      }
      const badgeText = { pass: 'PASS', fail: 'FAIL', unrecorded: 'NOT RECORDED' };

      checksList.innerHTML = bannerHtml + resolvedChecks.map(c => `
        <div class="drawer-check-row">
          <span class="drawer-check-badge ${c.status} font-mono">${badgeText[c.status]}</span>
          <div class="drawer-check-desc">
            <strong>${escapeHtml(c.title)}</strong>
            <div style="font-size: 0.76rem; color: var(--muted); margin-top: 2px;">${escapeHtml(c.desc)}</div>
            ${c.provenance || ''}
          </div>
        </div>
      `).join('');
    }

    const rTot = document.getElementById('drawer-rel-total');
    const rReal = document.getElementById('drawer-rel-real');
    const rMeas = document.getElementById('drawer-rel-meas');
    const rSf = document.getElementById('drawer-rel-sf');
    const rInt = document.getElementById('drawer-rel-int');

    const relCell = v => (typeof v === 'number' && isFinite(v)) ? `${v} / 2` : 'Not recorded';
    if (rTot) rTot.textContent = relRecorded ? `${relScore} / 8` : 'Not recorded';
    if (rReal) rReal.textContent = relCell(rel.real);
    if (rMeas) rMeas.textContent = relCell(rel.measurable);
    if (rSf) rSf.textContent = relCell(rel.sf);
    if (rInt) rInt.textContent = relCell(rel.interesting);

    const changelogEl = document.getElementById('drawer-changelog-entry');
    const copyReceiptBtn = document.getElementById('btn-copy-receipt');
    // Receipt is built from exported fields; the run id comes from the
    // snapshot's recorded integration run, never a hardcoded literal.
    const runId = p.review_id || (demoData && demoData.database_status &&
      ((demoData.database_status.latest_run || {}).run_id ||
       (demoData.database_status.integration_run || {}).run_id)) || 'RUN_UNRECORDED';
    const receiptText = `COMMITMENT #${rank} (${p.promise_id}) · VERDICT=${(p.verdict || 'undecided').toUpperCase()} · HASH=${(p.source_hash || '').slice(0, 16)}… · RUN=${runId}`;
    if (changelogEl) {
      changelogEl.textContent = receiptText;
    }
    if (copyReceiptBtn) {
      copyReceiptBtn.setAttribute('data-hash', receiptText);
    }

    backdrop.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    drawer.focus();
  }

  window.openInspectDrawer = openInspectDrawer;

  function closeInspectDrawer() {
    const backdrop = document.getElementById('inspect-drawer-backdrop');
    if (backdrop) backdrop.classList.add('hidden');
    document.body.style.overflow = '';
    if (permalinkId() && window.history && window.history.replaceState) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
    if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
      lastActiveElement.focus();
    }
  }

  // -------------------------------------------------------------------------
  // Story-card media pure helpers (SFPSTORY_PURE_START .. END)
  //
  // Self-contained (no closure over outer state) so
  // tests/test_story_card_media.py can execute this marked block with node
  // against docs/data.json and assert the cards surface exactly the media
  // the export carries.
  // -------------------------------------------------------------------------
  /* SFPSTORY_PURE_START */
  function storyEscapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  // Show available source photos inline; missing images leave no media block.
  function storyCardMediaHtml(promise) {
    if (!promise) return '';
    // Self-hosted image (same origin, issues #82/#83): shown by default with a
    // visible credit/license line; no opt-in button and no third-party request.
    if (promise.media_path) {
      const t = promise.title || 'this promise';
      const alt = promise.media_caption || t;
      const thumb = promise.media_thumb_path || promise.media_path;
      const credit = `Photo: ${promise.media_credit || 'Unknown'} / ${promise.media_license || 'license unknown'}`;
      return `<figure class="story-card-media story-card-media-hosted"><img src="${storyEscapeHtml(promise.media_path)}" srcset="${storyEscapeHtml(thumb)} 320w, ${storyEscapeHtml(promise.media_path)} 800w" sizes="(max-width: 600px) 100vw, 400px" alt="${storyEscapeHtml(alt)}" loading="lazy"><figcaption class="story-card-media-caption font-mono">${storyEscapeHtml(credit)}</figcaption></figure>`;
    }
    const url = promise.media_image_url || promise.image_url;
    if (!url) return '';
    // Inline source image: no tap-to-load step.
    // No URL means no block at all; a URL that fails to load removes the block
    // (see setupFeaturedStories), so there is never an empty frame.
    return `<figure class="story-card-media">${storyCardMediaLoadedHtml(url, promise.media_caption || '', promise.title || 'this promise')}</figure>`;
  }

  // Photo markup: the photo plus its exported caption line (when the export
  // records one).
  function storyCardMediaLoadedHtml(url, caption, title) {
    const alt = caption || title || 'Source media photo';
    const capHtml = caption
      ? `<figcaption class="story-card-media-caption font-mono">${storyEscapeHtml(caption)}</figcaption>`
      : '';
    return `<img src="${storyEscapeHtml(url)}" alt="${storyEscapeHtml(alt)}" loading="lazy" decoding="async" referrerpolicy="no-referrer">${capHtml}`;
  }

  const SFPStory = { storyCardMediaHtml, storyCardMediaLoadedHtml };
  window.SFPStory = SFPStory;
  /* SFPSTORY_PURE_END */

  // -------------------------------------------------------------------------
  // Featured Stories (0.2)
  // -------------------------------------------------------------------------
  function setupFeaturedStories() {
    // Surface the export's source media on cards whose record carries an
    // image (issue #44) inline: no tap needed. Imageless records keep the
    // text-only card with no empty space, and an image that fails to load
    // removes its block, never showing the browser's broken-image glyph.
    document.querySelectorAll('.story-card[data-story-pid]').forEach(card => {
      const pid = card.getAttribute('data-story-pid');
      const record = demoData && (demoData.promises || []).find(x => x.promise_id === pid);
      addStoryThumb(card, record);
      const html = record ? SFPStory.storyCardMediaHtml(record) : '';
      if (!html) return;
      const tpl = document.createElement('template');
      tpl.innerHTML = html;
      const media = tpl.content.firstElementChild;
      const img = media.querySelector('img');
      if (img) {
        img.addEventListener('error', () => media.remove());
        // A cached broken image may already have failed before the listener.
        if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) media.remove();
      }
      const top = card.querySelector('.story-card-top');
      if (top && top.nextSibling) {
        card.insertBefore(media, top.nextSibling);
      } else {
        card.appendChild(media);
      }
    });
    document.querySelectorAll('.btn-story-evidence').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const pid = btn.getAttribute('data-pid');
        const qid = btn.getAttribute('data-qid');
        if (qid) {
          switchToQuarantineAndHighlight(qid);
        } else if (pid) {
          openInspectDrawer(pid);
        }
      });
    });
  }

  // -------------------------------------------------------------------------
  // Glanceable registry (issue #81): category illustrations, one-line
  // timeline strips, outcome expanders and the card layout. All of it is
  // built client-side from the export record on top of the baked rows, so the
  // exporter's markup stays the single source of the row text. Illustrations
  // are inline SVG: no image request of any kind.
  // -------------------------------------------------------------------------
  const CATEGORY_ICONS = {
    'Civic Governance': '<path d="M3 10l9-6 9 6"/><path d="M5 10v8M10 10v8M14 10v8M19 10v8"/><path d="M3 20h18"/>',
    'Housing & Neighborhoods': '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    'Transit & Streets': '<rect x="5" y="3" width="14" height="14" rx="2"/><path d="M5 11h14"/><circle cx="9" cy="14" r="0.8"/><circle cx="15" cy="14" r="0.8"/><path d="M7 17v3M17 17v3"/>',
    'Bay Area & Regional': '<path d="M2 19h20"/><path d="M7 5v14M17 5v14"/><path d="M2 15c3 0 4-10 5-10M7 5c1 0 2 10 5 10s4-10 5-10M17 5c1 0 2 10 5 10"/>',
    'Airport & Airlines': '<path d="M21 15l-8-4V5a1.5 1.5 0 0 0-3 0v6l-8 4v2l8-2v4l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-4l8 2z"/>',
    'Sports': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c3.5 3.5 3.5 14.5 0 18M12 3c-3.5 3.5-3.5 14.5 0 18"/>',
    'Environment & Energy': '<path d="M5 19c0-9 5-14 15-14 0 10-5 15-14 15"/><path d="M5 19l8-8"/>',
    'Infrastructure & Tech': '<rect x="7" y="7" width="10" height="10" rx="1"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/>',
    'Culture & Music': '<path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/>'
  };
  const CATEGORY_ICON_DEFAULT = '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h7"/>';

  // Self-hosted media written by the media pipeline (record.media_path). A
  // plain relative path only: no scheme, no host, no parent segments. Absent
  // on most records, in which case the illustration is the whole thumbnail.
  function safeLocalPath(m) {
    if (typeof m !== 'string' || !m) return '';
    if (/^[a-z][a-z0-9+.-]*:|^\/|\.\.|\\/i.test(m)) return '';
    return m;
  }

  function localMediaPath(p) {
    return safeLocalPath(p && p.media_path);
  }

  // Category illustration tinted with the verdict colour. Always built, so a
  // record is never text-only; a local image, when the record has one, is
  // layered on top and removed again if it fails to load.
  function categoryThumbHtml(p, extraClass) {
    const category = (p && p.category) || '';
    const icon = CATEGORY_ICONS[category] || CATEGORY_ICON_DEFAULT;
    const verdict = normalizeVerdict(p && p.verdict);
    const local = localMediaPath(p);
    const img = local ? `<img class="cat-thumb-img" src="${escapeHtml(local)}" alt="" loading="lazy">` : '';
    return `<span class="cat-thumb v-${escapeHtml(verdict)}${extraClass ? ' ' + extraClass : ''}" role="img" aria-label="${escapeHtml(category || 'Commitment')} illustration"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${icon}</svg>${img}</span>`;
  }

  document.addEventListener('error', (e) => {
    const t = e.target;
    if (t && t.classList && t.classList.contains('cat-thumb-img')) t.remove();
    if (t && t.classList && t.classList.contains('entity-avatar-img')) {
      const box = t.closest('.entity-avatar');
      if (box) box.remove();
    }
  }, true);

  function timelineStripHtml(p) {
    const verdict = normalizeVerdict(p.verdict);
    // Compact form so the strip fits one line on a phone: YYYY-MM, or YYYY
    // when the export only knows the year; the em dash marks an absent date.
    const compact = (iso, precision) => {
      const m = String(iso || '').trim().match(/^(\d{4})(?:-(\d{2}))?/);
      if (!m) return '\u2014';
      return (precision === 'year' || !m[2]) ? m[1] : `${m[1]}-${m[2]}`;
    };
    const said = compact(p.promise_made_date || p.promised_date, p.promise_date_precision);
    const due = compact(p.deadline_date || p.due_date, p.due_date_precision);
    const delivered = outcomePhases(p).find(x => x.phase === 'delivered');
    const done = compact(p.completion_date || (delivered && delivered.date), p.completion_date_precision);
    const chip = (cls, label, val) => `<span class="viz-phase-chip ${cls}"><span class="strip-label">${label}</span> ${escapeHtml(val)}</span>`;
    const arrow = '<span class="viz-phase-arrow" aria-hidden="true">\u2192</span>';
    const reversed = verdict === 'kept_then_reversed';
    // A reversed record carries a fourth step; its empty Due is left out so
    // the strip still fits one line on a phone.
    let html = chip('made', 'Said', said) + arrow;
    if (!(reversed && due === '\u2014')) html += chip('due', 'Due', due) + arrow;
    html += chip(done === '\u2014' ? 'pending' : 'delivered', 'Done', done);
    if (reversed) html += arrow + chip('reversed', 'Reversed', compact(reversalDate(p), 'day'));
    return `<div class="row-timeline-strip font-mono" role="group" aria-label="Timeline: said ${escapeHtml(said)}, due ${escapeHtml(due)}, done ${escapeHtml(done)}">${html}</div>`;
  }

  function enhanceRegistryRows() {
    const byId = {};
    ((demoData && demoData.promises) || []).forEach(p => { byId[p.promise_id] = p; });
    document.querySelectorAll('#promises-table-body tr.promise-row').forEach(tr => {
      if (tr.getAttribute('data-glance')) return;
      const pid = tr.getAttribute('data-promise-id');
      const p = byId[pid];
      if (!p) return;
      tr.setAttribute('data-glance', '1');
      const ent = tr.querySelector('.table-entity-cell');
      if (ent) ent.insertAdjacentHTML('afterbegin', categoryThumbHtml(p));
      const quoteCell = tr.querySelector('.table-quote-cell');
      if (quoteCell) {
        if (p.title) quoteCell.insertAdjacentHTML('afterbegin', `<div class="row-title">${escapeHtml(p.title)}</div>`);
        const outcome = quoteCell.querySelector('.table-outcome-block');
        if (outcome) outcome.id = `row-outcome-${pid}`;
      }
      const tl = tr.querySelector('.table-timeline-cell');
      if (tl) {
        tl.innerHTML = timelineStripHtml(p) +
          `<div class="row-actions"><button type="button" class="btn-row-outcome" aria-expanded="false" aria-controls="row-outcome-${escapeHtml(pid)}">Show outcome</button><span class="table-card-action">Inspect &rarr;</span></div>`;
        const btn = tl.querySelector('.btn-row-outcome');
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const open = !tr.classList.contains('outcome-open');
          tr.classList.toggle('outcome-open', open);
          btn.setAttribute('aria-expanded', open ? 'true' : 'false');
          btn.textContent = open ? 'Hide outcome' : 'Show outcome';
        });
        btn.addEventListener('keydown', (e) => e.stopPropagation());
      }
    });
  }

  // Card layout: phones always, and desktop when the Cards view is chosen.
  // The class is what the stylesheet keys on, so the table markup is the same
  // in both layouts.
  const phoneQuery = window.matchMedia ? window.matchMedia('(max-width: 768px)') : null;
  function syncCardsLayout() {
    const container = document.getElementById('promises-table-container');
    if (!container) return;
    const cards = activeViewMode === 'grid' || Boolean(phoneQuery && phoneQuery.matches);
    container.classList.toggle('cards-layout', cards);
    container.classList.toggle('cards-grid', activeViewMode === 'grid');
  }
  if (phoneQuery && phoneQuery.addEventListener) phoneQuery.addEventListener('change', syncCardsLayout);

  // Thumbnail slot on a featured card: the category illustration sits beside
  // the entity name. The inline photo below it is unchanged.
  function addStoryThumb(card, record) {
    if (card.querySelector('.cat-thumb')) return;
    const top = card.querySelector('.story-card-top');
    if (!top) return;
    const chip = top.querySelector('.verdict-chip');
    const verdict = chip ? ((chip.className.match(/\b(kept_then_reversed|in_progress|kept|broken|undecided)\b/) || [])[1] || 'undecided') : 'undecided';
    top.insertAdjacentHTML('afterbegin', categoryThumbHtml(record || { verdict }));
  }

  // -------------------------------------------------------------------------
  // Event Listeners & Wiring
  // -------------------------------------------------------------------------
  function setupEventListeners() {
    // Replay controls (Auto-play, Pause/Resume toggle, Reset, Direct clicking)
    const runSelect = document.getElementById('run-select');
    if (runSelect) {
      runSelect.addEventListener('change', () => {
        currentRunType = runSelect.value;
        currentStage = 1;
        isAutoPlaying = true;
        renderActiveStage(currentRunType, 1);
        scheduleNextAutoStage();
      });
    }

    const btnNext = document.getElementById('btn-step-next');
    if (btnNext) btnNext.addEventListener('click', togglePlayPause);

    const btnReset = document.getElementById('btn-pipeline-reset');
    if (btnReset) btnReset.addEventListener('click', resetPipeline);

    // Milestone node click listeners (circle + label)
    for (let i = 1; i <= 6; i++) {
      const ms = document.getElementById(`ms-circle-${i}`);
      if (ms) {
        ms.parentElement.addEventListener('click', () => jumpToStage(i));
      }
    }
    document.querySelectorAll('.milestone-label-clickable').forEach(lbl => {
      lbl.addEventListener('click', () => {
        const stage = parseInt(lbl.getAttribute('data-stage'), 10);
        if (stage) jumpToStage(stage);
      });
    });

    // Tabs switching
    const tabPromises = document.getElementById('tab-btn-promises');
    const tabQuarantine = document.getElementById('tab-btn-quarantine');
    if (tabPromises) tabPromises.addEventListener('click', () => setTab('promises'));
    if (tabQuarantine) tabQuarantine.addEventListener('click', () => setTab('quarantine'));

    // Segmented verdict filters
    document.querySelectorAll('.btn-seg-verdict').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.btn-seg-verdict').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filterVerdict = btn.getAttribute('data-verdict') || 'all';
        visibleRowsCount = 10;
        renderExplore();
      });
    });

    // Stacked Hero Bar segments click
    document.querySelectorAll('.bar-segment, .legend-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const verd = btn.getAttribute('data-verdict');
        if (verd) {
          filterVerdict = verd;
          document.querySelectorAll('.btn-seg-verdict').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-verdict') === verd);
          });
          visibleRowsCount = 10;
          renderExplore();
          const exp = document.getElementById('explore');
          if (exp) exp.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });

    // Search Input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        searchTerm = searchInput.value;
        visibleRowsCount = 10;
        renderExplore();
      });
    }

    // More Filters button & panel
    const btnMoreFilters = document.getElementById('btn-more-filters');
    const moreFiltersPanel = document.getElementById('more-filters-panel');
    if (btnMoreFilters && moreFiltersPanel) {
      btnMoreFilters.addEventListener('click', () => {
        const isHidden = moreFiltersPanel.classList.toggle('hidden');
        btnMoreFilters.setAttribute('aria-expanded', isHidden ? 'false' : 'true');
      });
    }

    // Filter selects
    const fCat = document.getElementById('filter-category');
    if (fCat) {
      fCat.addEventListener('change', () => {
        filterCategory = fCat.value;
        visibleRowsCount = 10;
        renderExplore();
      });
    }

    const fEnt = document.getElementById('filter-entity');
    if (fEnt) {
      fEnt.addEventListener('change', () => {
        filterEntity = fEnt.value;
        visibleRowsCount = 10;
        renderExplore();
      });
    }

    // View mode switcher buttons (Table | Map & Districts | Entity Profiles | Data Quality)
    document.querySelectorAll('.btn-view-mode').forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.getAttribute('data-view') || 'table';
        if (activeTab !== 'promises') {
          setTab('promises');
        }
        setViewMode(view, true);
      });
    });

    const fTier = document.getElementById('filter-tier');
    if (fTier) {
      fTier.addEventListener('change', () => {
        filterTier = fTier.value;
        visibleRowsCount = 10;
        renderExplore();
      });
    }

    const fPillar = document.getElementById('filter-pillar');
    if (fPillar) {
      fPillar.addEventListener('change', () => {
        filterPillar = fPillar.value;
        visibleRowsCount = 10;
        renderExplore();
      });
    }

    const fAuditFlag = document.getElementById('filter-audit-flag');
    if (fAuditFlag) {
      fAuditFlag.addEventListener('change', () => {
        filterAuditFlag = fAuditFlag.value;
        visibleRowsCount = 10;
        renderExplore();
      });
    }

    const fSort = document.getElementById('filter-sort');
    if (fSort) {
      fSort.addEventListener('change', () => {
        filterSort = fSort.value;
        const sortTextEl = document.getElementById('table-sort-text');
        if (sortTextEl) {
          const opt = fSort.options[fSort.selectedIndex];
          sortTextEl.textContent = `Sorted by ${opt ? opt.text.toLowerCase() : 'most significant'}`;
        }
        visibleRowsCount = 10;
        renderExplore();
      });
    }

    // Shared reset used by both clear-filters buttons (status line and the
    // zero-match empty state).
    function clearAllFilters() {
      searchTerm = '';
      filterVerdict = 'all';
      filterCategory = 'all';
      filterEntity = 'all';
      filterTier = 'all';
      filterPillar = 'all';
      filterAuditFlag = 'all';
      filterSort = 'rank';
      visibleRowsCount = 10;
      if (searchInput) searchInput.value = '';
      if (fCat) fCat.value = 'all';
      if (fEnt) fEnt.value = 'all';
      if (fTier) fTier.value = 'all';
      if (fPillar) fPillar.value = 'all';
      if (fAuditFlag) fAuditFlag.value = 'all';
      if (fSort) fSort.value = 'rank';
      document.querySelectorAll('.btn-seg-verdict').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-verdict') === 'all');
      });
      renderExplore();
    }

    // Clear filters button
    const btnClear = document.getElementById('btn-clear-filters');
    if (btnClear) {
      btnClear.addEventListener('click', clearAllFilters);
    }

    // Zero-match empty state: its clear-filters button reuses the same reset.
    const emptyState = document.getElementById('promises-empty-state');
    if (emptyState) {
      emptyState.addEventListener('click', (e) => {
        if (e.target.closest('.btn-clear-filters-empty')) clearAllFilters();
      });
    }

    // Pagination
    const btnShowMore = document.getElementById('btn-show-more');
    if (btnShowMore) {
      btnShowMore.addEventListener('click', () => {
        visibleRowsCount += 10;
        renderExplore();
      });
    }

    const btnShowAll = document.getElementById('btn-show-all');
    if (btnShowAll) {
      btnShowAll.addEventListener('click', () => {
        visibleRowsCount = 9999;
        renderExplore();
      });
    }

    // Table & Mobile card click listeners
    const tbody = document.getElementById('promises-table-body');
    if (tbody) {
      tbody.addEventListener('click', (e) => {
        const tr = e.target.closest('.promise-row');
        if (tr) {
          const pid = tr.getAttribute('data-promise-id');
          if (pid) openInspectDrawer(pid);
        }
      });
      tbody.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          const tr = e.target.closest('.promise-row');
          if (tr) {
            e.preventDefault();
            const pid = tr.getAttribute('data-promise-id');
            if (pid) openInspectDrawer(pid);
          }
        }
      });
    }

    // Drawer close buttons
    const btnCloseDrawer = document.getElementById('btn-close-drawer');
    if (btnCloseDrawer) btnCloseDrawer.addEventListener('click', closeInspectDrawer);

    const drawerBackdrop = document.getElementById('inspect-drawer-backdrop');
    if (drawerBackdrop) {
      drawerBackdrop.addEventListener('click', (e) => {
        if (e.target === drawerBackdrop) closeInspectDrawer();
      });
    }

    // Escape closes the drawer; Tab is trapped inside it while it is open.
    document.addEventListener('keydown', (e) => {
      const backdrop = document.getElementById('inspect-drawer-backdrop');
      const drawerOpen = !!(backdrop && !backdrop.classList.contains('hidden'));
      if (e.key === 'Escape' && drawerOpen) {
        closeInspectDrawer();
      } else if (e.key === 'Tab' && drawerOpen) {
        const drawer = document.getElementById('inspect-drawer');
        if (!drawer) return;
        const focusables = Array.prototype.filter.call(
          drawer.querySelectorAll(
            'a[href], button:not([disabled]), input:not([disabled]), ' +
            'select:not([disabled]), textarea:not([disabled]), ' +
            '[tabindex]:not([tabindex="-1"])'
          ),
          el => el.getClientRects().length > 0
        );
        if (!focusables.length) return;
        const next = SFPUX.nextFocusableIndex(
          focusables.length,
          focusables.indexOf(document.activeElement),
          e.shiftKey
        );
        e.preventDefault();
        focusables[next].focus();
      }
    });

    // Copy hash buttons everywhere
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-copy-hash');
      if (btn) {
        const hash = btn.getAttribute('data-hash');
        if (hash) {
          navigator.clipboard.writeText(hash).then(() => {
            const orig = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => { btn.textContent = orig; }, 1500);
          }).catch(() => {
            btn.textContent = 'Copied!';
            setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
          });
        }
      }
    });

    // Mobile Navigation Menu Drawer
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const navDrawer = document.getElementById('mobile-nav-drawer');
    if (menuToggle && navDrawer) {
      const iconHam = menuToggle.querySelector('.icon-hamburger');
      const iconClose = menuToggle.querySelector('.icon-close');

      const setDrawerState = (open) => {
        if (open) {
          navDrawer.classList.remove('hidden');
          menuToggle.setAttribute('aria-expanded', 'true');
          if (iconHam) iconHam.classList.add('hidden');
          if (iconClose) iconClose.classList.remove('hidden');
        } else {
          navDrawer.classList.add('hidden');
          menuToggle.setAttribute('aria-expanded', 'false');
          if (iconHam) iconHam.classList.remove('hidden');
          if (iconClose) iconClose.classList.add('hidden');
        }
      };

      menuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const willOpen = navDrawer.classList.contains('hidden');
        setDrawerState(willOpen);
      });

      // Close on link click
      navDrawer.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => setDrawerState(false));
      });

      // Close on outside click
      document.addEventListener('click', (e) => {
        if (!menuToggle.contains(e.target) && !navDrawer.contains(e.target) && !navDrawer.classList.contains('hidden')) {
          setDrawerState(false);
        }
      });

      // Close on Escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !navDrawer.classList.contains('hidden')) {
          setDrawerState(false);
        }
      });
    }

    // Featured Stories Carousel Indicator Controls
    const storiesContainer = document.getElementById('featured-stories-container');
    const carouselCounter = document.getElementById('carousel-counter');
    const btnCarouselPrev = document.getElementById('btn-carousel-prev');
    const btnCarouselNext = document.getElementById('btn-carousel-next');
    const dots = document.querySelectorAll('.carousel-dot');

    if (storiesContainer && dots.length > 0) {
      const storyCards = storiesContainer.querySelectorAll('.story-card');
      const totalStories = storyCards.length;

      const updateActiveDot = (idx) => {
        dots.forEach((d, i) => {
          if (i === idx) {
            d.classList.add('active');
            d.setAttribute('aria-selected', 'true');
          } else {
            d.classList.remove('active');
            d.setAttribute('aria-selected', 'false');
          }
        });
        if (carouselCounter) {
          carouselCounter.textContent = `${idx + 1} / ${totalStories} · Swipe →`;
        }
      };

      const scrollToIndex = (idx) => {
        if (idx >= 0 && idx < totalStories && storyCards[idx]) {
          storyCards[idx].scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' });
          updateActiveDot(idx);
        }
      };

      dots.forEach((dot, idx) => {
        dot.addEventListener('click', () => scrollToIndex(idx));
      });

      if (btnCarouselPrev) {
        btnCarouselPrev.addEventListener('click', () => {
          let cur = 0;
          dots.forEach((d, i) => { if (d.classList.contains('active')) cur = i; });
          scrollToIndex(Math.max(0, cur - 1));
        });
      }

      if (btnCarouselNext) {
        btnCarouselNext.addEventListener('click', () => {
          let cur = 0;
          dots.forEach((d, i) => { if (d.classList.contains('active')) cur = i; });
          scrollToIndex(Math.min(totalStories - 1, cur + 1));
        });
      }

      // Track scroll position to update active dot
      let scrollTimer = null;
      storiesContainer.addEventListener('scroll', () => {
        if (scrollTimer) clearTimeout(scrollTimer);
        scrollTimer = setTimeout(() => {
          const scrollLeft = storiesContainer.scrollLeft;
          let closestIdx = 0;
          let minDiff = Infinity;
          storyCards.forEach((c, idx) => {
            const diff = Math.abs(c.offsetLeft - storiesContainer.offsetLeft - scrollLeft);
            if (diff < minDiff) {
              minDiff = diff;
              closestIdx = idx;
            }
          });
          updateActiveDot(closestIdx);
        }, 60);
      });
    }

    // Keep active stepper indicator centered on resize
    window.addEventListener('resize', () => {
      renderActiveStage(currentRunType, currentStage);
    });
  }

  // -------------------------------------------------------------------------
  // Start
  // -------------------------------------------------------------------------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

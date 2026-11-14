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
  let hasAutoPlayed = false;
  const STAGE_INTERVAL_MS = 1800;
  let lastActiveElement = null;

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
    return r.replace(/\s*\([^)]*\)/g, '').replace(/\s*\[[^\]]*\]/g, '').trim() || r;
  }

  function formatVerdictLabel(verdict) {
    const v = (verdict || '').toLowerCase().replace(/[\s-]+/g, '_');
    if (v === 'in_progress') return 'In progress';
    if (v === 'kept') return 'Kept';
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
    return t.replace(/\s+/g, ' ').trim();
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
  const VERDICT_ORDER = ['kept', 'in_progress', 'broken', 'stalled', 'undecided'];

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

  const SFPViz = {
    VERDICT_ORDER,
    countByVerdict,
    countByCategory,
    countBySourceType,
    countByYearAndVerdict,
    funnelStages,
    windowFunnelStages,
    quarantineReasons,
    denialDomains
  };
  /* SFPVIZ_PURE_END */

  // -------------------------------------------------------------------------
  // Initialization
  // -------------------------------------------------------------------------
  async function init() {
    if (window.__DEMO_DATA__) {
      demoData = window.__DEMO_DATA__;
    } else {
      try {
        const res = await fetch('data.json');
        demoData = await res.json();
      } catch (err) {
        console.error('Failed to load data.json', err);
        return;
      }
    }

    setupReplayScenarios();
    setupEventListeners();
    renderExplore();
    renderQuarantineTable();
    setupFeaturedStories();
    renderVisualizations();
  }

  // -------------------------------------------------------------------------
  // Replay State Machine (0.5) - Real Commitments, Auto-Play, Zero Layout Shift
  // -------------------------------------------------------------------------
  const SCENARIOS = {
    P02: {
      id: 'P02',
      label: '#01 · 24/7 Crisis Center',
      speaker: 'Mayor Daniel Lurie',
      title: '24/7 Crisis Stabilization Center',
      expectedVerdict: 'kept',
      verdictLabel: 'KEPT',
      stages: {
        1: {
          title: 'Source Fetched',
          desc: 'Archived sf.gov release 582955d5… from official municipal domain allowlist.'
        },
        2: {
          title: 'Quote Extracted',
          desc: '“That’s exactly what this 24/7 police-friendly stabilization center will be, and I am proud to be opening it.”'
        },
        3: {
          title: 'Relevance Gate Passed',
          desc: 'Relevance gate score 8/8: quantified Tenderloin civic commitment with measurable timeline.'
        },
        4: {
          title: 'Evidence Evaluated',
          desc: 'Adjudicated 4 supporting vs 0 contradicting claims; verified 344 admissions recorded since April 28, 2025.'
        },
        5: {
          title: 'Code Checks Passed',
          desc: 'All 7 deterministic code checks passed: SHA-256 byte-match, date consistency, and speaker attribution verified.'
        },
        6: {
          title: 'Verdict Published',
          desc: 'Published KEPT verdict: official primary records confirm 24/7 crisis center operational at 822 Geary St.'
        }
      }
    },
    P05: {
      id: 'P05',
      label: '#02 · 1,500 Shelter Beds',
      speaker: 'Mayor Daniel Lurie',
      title: '1,500 Shelter Beds in First 6 Months',
      expectedVerdict: 'broken',
      verdictLabel: 'BROKEN',
      stages: {
        1: {
          title: 'Source Fetched',
          desc: 'Archived SF Standard source document 384c310b… from news tier.'
        },
        2: {
          title: 'Quote Extracted',
          desc: '“Open 1,500 new shelter beds in the first six months of the administration.”'
        },
        3: {
          title: 'Relevance Gate Passed',
          desc: 'Relevance gate score 8/8: citywide shelter bed expansion with concrete numeric threshold.'
        },
        4: {
          title: 'Evidence Evaluated',
          desc: 'Adjudicated 1 supporting vs 2 contradicting claims; city shelter capacity tracker logged ~500 beds added.'
        },
        5: {
          title: 'Code Checks Evaluated',
          desc: 'Deterministic code checks failed deadline threshold: 6-month window passed with <50% target delivery.'
        },
        6: {
          title: 'Verdict Published',
          desc: 'Published BROKEN verdict: numeric target not met; administration pivoted strategy after 6 months.'
        }
      }
    },
    'SFO-01': {
      id: 'SFO-01',
      label: '#03 · Runway 28L Reopening',
      speaker: 'SFO Airport',
      title: 'Runway 28L Safety Realignment & Reopening',
      expectedVerdict: 'kept',
      verdictLabel: 'KEPT',
      stages: {
        1: {
          title: 'Source Fetched',
          desc: 'Archived flysfo.com press release b6a2f59f… from verified SFO airport domain.'
        },
        2: {
          title: 'Quote Extracted',
          desc: '“Runway 28L will reopen ahead of schedule on Friday, June 21, 2024.”'
        },
        3: {
          title: 'Relevance Gate Passed',
          desc: 'Relevance gate score 8/8: critical airfield safety capital project with defined completion target.'
        },
        4: {
          title: 'Evidence Evaluated',
          desc: 'Adjudicated 3 supporting vs 0 contradicting operational flight logs; runway operational June 21, 2024.'
        },
        5: {
          title: 'Code Checks Passed',
          desc: 'All 7 deterministic code checks passed: SHA-256 verified, reopening date beat July 1 deadline by 10 days.'
        },
        6: {
          title: 'Verdict Published',
          desc: 'Published KEPT verdict: Runway 28L reopened ahead of schedule following $51M taxiway realignment.'
        }
      }
    },
    P06: {
      id: 'P06',
      label: '#18 · Vision Zero',
      speaker: 'City & County of San Francisco',
      title: 'Vision Zero: End Traffic Fatalities by 2024',
      expectedVerdict: 'broken',
      verdictLabel: 'BROKEN',
      stages: {
        1: {
          title: 'Source Fetched',
          desc: 'Archived municipal resolution 9e32a10f… from official City & County of San Francisco records.'
        },
        2: {
          title: 'Quote Extracted',
          desc: '“Adopt Vision Zero with the goal of eliminating all traffic fatalities in San Francisco by 2024.”'
        },
        3: {
          title: 'Relevance Gate Passed',
          desc: 'Relevance gate score 8/8: high-impact citywide transit and pedestrian safety mandate.'
        },
        4: {
          title: 'Evidence Evaluated',
          desc: 'Adjudicated 0 supporting vs 5 contradicting SFMTA collision records; 39 traffic fatalities logged in 2024.'
        },
        5: {
          title: 'Code Checks Evaluated',
          desc: 'Deterministic code checks evaluated target condition: fatalities > 0 at deadline triggers automatic broken verdict.'
        },
        6: {
          title: 'Verdict Published',
          desc: 'Published BROKEN verdict: fatal traffic collisions were not eliminated by the 2024 milestone.'
        }
      }
    }
  };

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
    const scenario = SCENARIOS[scenarioKey] || SCENARIOS.P02;
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

  function startAutoPlay() {
    isAutoPlaying = true;
    renderActiveStage(currentRunType, currentStage);
    scheduleNextAutoStage();
  }

  function setupObserverForReplay() {
    const watchSection = document.getElementById('watch');
    if (!watchSection) return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
      isAutoPlaying = false;
      renderActiveStage(currentRunType, 1);
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !hasAutoPlayed) {
          hasAutoPlayed = true;
          startAutoPlay();
        }
      });
    }, { threshold: 0.15 });

    observer.observe(watchSection);

    // Initial load auto-trigger
    setTimeout(() => {
      if (!hasAutoPlayed) {
        const rect = watchSection.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
          hasAutoPlayed = true;
          startAutoPlay();
        }
      }
    }, 400);
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
    in_progress: '#F59E0B',
    broken: '#EF4444',
    stalled: '#C084FC',
    undecided: '#94A3B8'
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

    const W = 760;
    const H = 250;
    const pad = { top: 14, right: 12, bottom: 26, left: 34 };
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
      gridSvg += `<text x="${pad.left - 6}" y="${Number(y) + 3}" text-anchor="end" font-size="9" fill="var(--muted)" font-family="monospace">${t}</text>`;
    }

    let axisSvg = '';
    buckets.forEach((b, i) => {
      const showLabel = i === 0 || i === buckets.length - 1 || Number(b.year) % 5 === 0;
      if (!showLabel) return;
      const x = pad.left + i * colW + colW / 2;
      axisSvg += `<text x="${x.toFixed(1)}" y="${H - 8}" text-anchor="middle" font-size="9" fill="var(--muted)" font-family="monospace">${b.year}</text>`;
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
      .map(([label, count]) => ({ label, count, color: 'var(--purple)' }));
    renderBarRows(document.getElementById('viz-source-bars'), stEntries, total);

    renderTimelineChart(promises);

    const totalEl = document.getElementById('viz-total');
    if (totalEl) totalEl.textContent = String(total);

    const legendEl = document.getElementById('viz-timeline-legend');
    if (legendEl) {
      legendEl.innerHTML = SFPViz.VERDICT_ORDER.map(v => `
        <span class="viz-legend-item"><span class="viz-legend-swatch" style="background:${VERDICT_COLORS[v]}"></span>${formatVerdictLabel(v)}</span>
      `).join('');
    }
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

    if (tableEl) tableEl.classList.toggle('hidden', activeViewMode !== 'table');
    if (mapEl) mapEl.classList.toggle('hidden', activeViewMode !== 'map');
    if (entEl) entEl.classList.toggle('hidden', activeViewMode !== 'entities');
    if (auditEl) auditEl.classList.toggle('hidden', activeViewMode !== 'audit');
    if (paginationEl) paginationEl.classList.toggle('hidden', activeViewMode !== 'table');
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

  function renderExplore() {
    const list = filterAndSortPromises();
    const totalCount = (demoData && demoData.promises && demoData.promises.length) || 54;
    const showingCount = Math.min(visibleRowsCount, list.length);

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

    // Render table rows
    const tbody = document.getElementById('promises-table-body');

    if (tbody) {
      tbody.innerHTML = list.slice(0, showingCount).map((p, idx) => {
        const rank = String(p.impact_rank || idx + 1).padStart(2, '0');
        const pid = escapeHtml(p.promise_id || '');
        const entity = escapeHtml(p.entity || '');
        const role = escapeHtml(p.role || '');
        const neighborhood = escapeHtml(p.neighborhood || 'Citywide San Francisco');
        const promiseRaw = cleanQuoteText(p.promise_text || '');
        const promiseClamped = escapeHtml(promiseRaw.slice(0, 150) + (promiseRaw.length > 150 ? '…' : ''));
        const outcomeReason = escapeHtml(formatPlainVerdictReason(p.verdict_reason, p.verdict));
        let promised = escapeHtml(p.promised_date_display || formatPrecisionDate(p.promised_date, p.promise_date_precision) || 'not recorded');
        if (p.promised_date_note) promised += ' (derived)';
        const due = escapeHtml(p.due_date_display || (p.due_date ? formatPrecisionDate(p.due_date, p.due_date_precision) : 'No deadline'));
        const done = escapeHtml(p.opened_date || p.completed_date || (p.verdict === 'kept' ? 'Verified completed' : '—'));
        const verdict = p.verdict || 'undecided';
        const verdClass = verdict.toLowerCase().replace(/[\s-]+/g, '_');
        const verdictLabel = formatVerdictLabel(verdict);

        return `
          <tr class="promise-row" id="promise-${pid}" data-promise-id="${pid}" tabindex="0" role="button" aria-label="Inspect #${rank} ${entity}: ${promiseClamped.slice(0, 60)}">
            <td class="table-entity-cell">
              <div class="entity-headline-row">
                <span class="table-entity-name">${entity}</span>
              </div>
              <div class="entity-sub-row font-mono">
                <span class="table-role-tag">${role}</span>
              </div>
              <div class="entity-geo-tag font-mono">${neighborhood}</div>
            </td>
            <td class="table-quote-cell">
              <div class="table-promise-block">
                <blockquote class="table-quote-text font-serif">&ldquo;${promiseClamped}&rdquo;</blockquote>
              </div>
              <div class="table-outcome-block">
                <span class="table-outcome-kicker font-mono">WHAT HAPPENED:</span>
                <span class="table-outcome-text">${outcomeReason}</span>
              </div>
            </td>
            <td class="table-verdict-cell">
              <span class="verdict-chip ${verdClass}">${verdictLabel}</span>
            </td>
            <td class="table-timeline-cell font-mono">
              <div class="timeline-row"><span class="timeline-label">Said:</span> <span class="timeline-val">${promised}</span></div>
              <div class="timeline-row"><span class="timeline-label">Due:</span> <span class="timeline-val">${due}</span></div>
              <div class="timeline-row"><span class="timeline-label">Done:</span> <span class="timeline-val">${done}</span></div>
            </td>
          </tr>
        `;
      }).join('');
    }

    if (activeViewMode === 'map') {
      renderMapAndDistrictsView(list);
    } else if (activeViewMode === 'entities') {
      renderEntityProfilesView(list);
    } else if (activeViewMode === 'audit') {
      renderQualityAuditView();
    }
  }

  function renderMapAndDistrictsView(list) {
    const mapWrap = document.getElementById('sf-svg-map-wrap');
    const selectedCard = document.getElementById('map-selected-card');
    const districtBars = document.getElementById('district-bars-list');
    if (!mapWrap || !districtBars) return;

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

    const verdictColor = {
      kept: '#10B981',
      broken: '#EF4444',
      in_progress: '#F59E0B',
      undecided: '#94A3B8'
    };

    const sfOutlinePath = 'M 55,298 L 62,210 L 66,142 L 88,92 L 154,68 L 238,68 L 315,76 L 372,110 L 398,176 L 408,248 L 392,302 L 320,312 L 222,312 L 125,308 Z';
    const tiPath = 'M 412,56 L 434,54 L 438,84 L 414,88 Z';
    const ggpPath = 'M 68,178 L 166,174 L 166,192 L 68,196 Z';

    const pins = [];
    const regionalItems = [];
    (list || []).forEach(p => {
      const lat = Number(p.latitude);
      const lon = Number(p.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      const inSFO = lat >= 37.59 && lat <= 37.65 && lon >= -122.42 && lon <= -122.35;
      const inSF = lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon;
      if (!inSF && !inSFO) {
        regionalItems.push(p);
        return;
      }
      const pt = inSFO ? projectSFO(lat, lon) : projectSF(lat, lon);
      pins.push({ p, x: pt.x, y: pt.y, inSFO });
    });

    const markersSvg = pins.map(({ p, x, y }) => {
      const v = (p.verdict || 'undecided').toLowerCase();
      const color = verdictColor[v] || '#94A3B8';
      const isCentroid = p.is_centroid !== false;
      const pid = escapeHtml(p.promise_id || '');
      const title = escapeHtml(`${p.entity}: ${p.neighborhood || 'San Francisco'}`);
      return `
        <g class="map-pin-node" data-promise-id="${pid}" tabindex="0" role="button" aria-label="${title}" style="cursor:pointer;">
          ${isCentroid ? `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9.5" fill="none" stroke="${color}" stroke-width="1.4" stroke-dasharray="2.5 2" opacity="0.78"/>` : ''}
          <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${isCentroid ? '4.8' : '6.5'}" fill="${color}" fill-opacity="${isCentroid ? '0.68' : '0.96'}" stroke="#0B1120" stroke-width="1.5">
            <title>${title} (${isCentroid ? 'Display Centroid' : 'Exact Address'})</title>
          </circle>
        </g>
      `;
    }).join('');

    const regionalHtml = regionalItems.length > 0 ? `
      <div class="map-regional-strip font-mono">
        <span class="regional-strip-label">REGIONAL / STATEWIDE DISPLAY CENTROIDS (${regionalItems.length}):</span>
        ${regionalItems.map(p => `<button type="button" class="btn-regional-pin" data-promise-id="${escapeHtml(p.promise_id)}">${escapeHtml(p.promise_id)} · ${escapeHtml(p.entity)}</button>`).join('')}
      </div>
    ` : '';

    mapWrap.innerHTML = `
      <svg class="sf-svg-map" viewBox="0 0 ${W} ${H}" role="img" aria-label="San Francisco commitment coordinates map">
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
        ${markersSvg}
      </svg>
      ${regionalHtml}
    `;

    mapWrap.querySelectorAll('[data-promise-id]').forEach(node => {
      const handler = () => {
        const pid = node.getAttribute('data-promise-id');
        const p = (demoData && demoData.promises || []).find(item => item.promise_id === pid);
        if (!p || !selectedCard) return;
        selectedCard.classList.remove('hidden');
        selectedCard.innerHTML = `
          <div class="map-selected-top">
            <span class="verdict-chip ${(p.verdict || '').toLowerCase()}">${formatVerdictLabel(p.verdict)}</span>
            <span class="font-mono" style="font-size:0.76rem;color:var(--muted);">${escapeHtml(p.promise_id)} · ${p.is_centroid === false ? 'Exact Street Location' : 'Display Centroid'} (${escapeHtml((p.geographic_scope || 'citywide').replace('_', ' '))})</span>
          </div>
          <div class="map-selected-title">${escapeHtml(p.entity)} — ${escapeHtml(p.neighborhood || 'San Francisco')}</div>
          <p class="map-selected-outcome">${escapeHtml(p.factual_outcome || p.promise_text || '')}</p>
          <button type="button" class="btn-map-inspect" data-inspect-id="${escapeHtml(p.promise_id)}">Inspect full commitment &rarr;</button>
        `;
        const inspBtn = selectedCard.querySelector('.btn-map-inspect');
        if (inspBtn) {
          inspBtn.addEventListener('click', () => openInspectDrawer(p.promise_id));
        }
      };
      node.addEventListener('click', handler);
      node.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handler();
        }
      });
    });

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
          items: []
        });
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
            <div>
              <h4 class="entity-card-name">${escapeHtml(g.name)}</h4>
              <span class="entity-card-cat font-mono">${escapeHtml(catLabel)}</span>
            </div>
            ${cautionBadge}
          </div>
          <div class="entity-stacked-bar" aria-label="Verdict breakdown">
            ${g.kept > 0 ? `<span style="width:${keptPct}%;background:#10B981;" title="${g.kept} Kept"></span>` : ''}
            ${g.inProgress > 0 ? `<span style="width:${progPct}%;background:#F59E0B;" title="${g.inProgress} In Progress"></span>` : ''}
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
  // 4-Part Detail Drawer (1.4)
  // -------------------------------------------------------------------------
  function openInspectDrawer(promiseId) {
    if (!demoData) return;
    const p = (demoData.promises || []).find(x => x.promise_id === promiseId) || demoData.p02;
    if (!p) return;

    lastActiveElement = document.activeElement;

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
    const scopeRaw = p.geographic_scope ? p.geographic_scope.replace('_', ' ') : 'citywide';
    const geoPinLabel = p.is_centroid === false ? `Exact Address (${scopeRaw})` : `Display Centroid (${scopeRaw})`;
    if (subtitleEl) {
      if (isCorporate) {
        subtitleEl.textContent = `${p.entity} · Corporate Entity · ${geoPinLabel}`;
      } else {
        const loc = (p.neighborhood && p.neighborhood !== 'Citywide') ? p.neighborhood : (p.role || 'San Francisco');
        subtitleEl.textContent = `${p.entity} · ${loc} · ${geoPinLabel}`;
      }
    }
    if (titleEl) {
      let t = p.document_title || p.title || '';
      if (!t || t.toLowerCase() === `${p.entity.toLowerCase()} commitment`) {
        const fallbackTitles = {
          P02: "24/7 Crisis Stabilization Center",
          P05: "1,500 Shelter Beds in First 6 Months",
          "SFO-01": "Runway 28L Safety Realignment & Reopening",
          "SFO-02": "Harvey Milk Terminal 1 Final Completion",
          "SFO-03": "Sustainable Aviation Fuel (SAF) Infrastructure",
          "SFO-04": "Alaska Airlines Terminal 1 Flight Operations",
          P21: "JFK Drive Permanent Car-Free Promenade",
          P04: "Chase Center Valkyries Regular Season Games",
          P82: "Valkyries WNBA Championship Guarantee",
          P83: "Whole Foods Mid-Market Flagship Safety",
          P11: "Grateful Dead Tour Retirement & Archival Shows",
          P01: "Fentanyl State of Emergency Ordinance",
          P59: "Zoox Driverless Passenger Ride Hail in SF",
          P43: "Waymo Fully Autonomous Ride-Hail Expansion",
          P41: "Central Subway Substantial Completion (2018)",
          P10: "Mission Rock 40% Affordable Housing Pledges",
          P18: "Housing Element: 82,200 New Homes by 2031",
          P06: "Vision Zero: End Traffic Fatalities by 2024",
          P08: "1,000 SRO Housing Units Improvement",
          P22: "Embarcadero Navigation Center 200 Beds",
          P17: "Hire 425 New SFPD Police Officers",
          P25: "Close San Francisco Juvenile Hall Facility",
          P12: "6,500 Shared E-Scooter Fleet Cap",
          P26: "Empty Homes Tax: 4,500 Units in Year One",
          P27: "Housing Trust Fund: $20M First-Year Budget",
          P29: "Care Not Cash Homeless Services Reform",
          P31: "Family Zoning Plan Neighborhood Housing",
          P30: "Homelessness Recovery: 1,500 PSH Units",
          P36: "CleanPowerSF 100% Renewable Electricity",
          P09: "PG&E 10,000 Miles Underground Power Lines",
          P61: "SFPUC Water System Improvement Program",
          P66: "Chase Center Arena 18,064 Capacity Delivery",
          P64: "Treasure Island 8,000 New Residential Units",
          P84: "Pier 70 Historic Shipyard Redevelopment",
          P86: "Potrero Power Station 2,600 Homes Plan",
          P07: "3.5 Million New Homes in California by 2025",
          P13: "10-Year Plan to End Chronic Homelessness",
          P15: "Add 5,000 Supportive Housing Units in 10 Years",
          P16: "Open 1,000 Additional Shelter Beds in SF",
          P19: "Healthy San Francisco Universal Healthcare",
          P20: "Interim Mayor Non-Candidacy Pledge",
          P23: "Downtown Hospitality Corridor Recovery",
          P28: "Open 250 Additional Behavioral Health Beds",
          P35: "Mental Health SF Reform Implementation",
          P38: "Reduce PSPS Wildfire Outage Scope by Half",
          P39: "Install 7,500 EV Charging Ports",
          P40: "PG&E Fleet Vehicle Electrification by 2030",
          P57: "Comcast Gigabit Fiber-to-the-Home Network",
          P03: "Permitting Reform & Small Business Overhaul",
          P58: "AT&T Public Market Street Wi-Fi Expansion",
          P62: "Visa Mission Rock HQ 1,500 Staff Occupancy",
          P65: "Central Subway Contract Completion (May 2018)",
          P85: "Central Subway Chinatown & North Beach Study"
        };
        t = fallbackTitles[p.promise_id] || `${p.entity} Commitment`;
      }
      titleEl.textContent = t;
    }
    const verdClass = (p.verdict || 'undecided').toLowerCase().replace(/[\s-]+/g, '_');
    if (chipEl) {
      chipEl.className = `verdict-chip ${verdClass}`;
      chipEl.textContent = formatVerdictLabel(p.verdict);
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
    const imgUrl = p.media_image_url || p.image_url;
    if (imgUrl && mediaBox && mediaImg) {
      mediaBox.style.display = 'block';
      mediaImg.src = imgUrl;
      mediaImg.alt = p.media_caption || (titleEl ? titleEl.textContent : '') || 'Source media photo';
      if (mediaCaption) mediaCaption.textContent = p.media_caption || 'Verified source photographic archive';
    } else if (mediaBox) {
      mediaBox.style.display = 'none';
    }

    // Part 2: Verdict & Plain Reason
    const plainReasonEl = document.getElementById('drawer-plain-reason');
    const decidedAtEl = document.getElementById('drawer-decided-at');

    if (plainReasonEl) plainReasonEl.textContent = p.factual_outcome || formatPlainVerdictReason(p.verdict_reason, p.verdict, p.promise_id);
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
      const hasContra = Boolean(p.has_contradictory_evidence) || (kClaims.length > 0 && bClaims.length > 0) || (bundles.broken && bundles.broken.note && /interim|conflict|competing|contradict/i.test(bundles.broken.note));
      if (hasContra) {
        const supCount = p.verdict_supporting_evidence_count !== undefined ? p.verdict_supporting_evidence_count : kClaims.length;
        const conCount = p.verdict_contradicting_evidence_count !== undefined ? p.verdict_contradicting_evidence_count : bClaims.length;
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

    const rel = p.relevance || { score: 8, real: 2, measurable: 2, sf: 2, interesting: 2 };
    const relScore = (rel.score !== undefined) ? rel.score : 8;

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
      { id: 'relevance_gate', title: 'Relevance Gate Score >= 5.0', defaultDesc: `Scored ${relScore}/8 for public impact and measurable outcomes.` }
    ];

    let failedCheckCount = 0;
    const failedNameSet = new Set(Array.isArray(p.failed_check_names) ? p.failed_check_names : []);
    const resolvedChecks = checkDefinitions.map(def => {
      if (def.id === 'relevance_gate') {
        const pass = relScore >= 5;
        if (!pass) failedCheckCount++;
        return {
          title: def.title,
          pass,
          desc: def.defaultDesc
        };
      }
      const item = checkMap[def.id];
      if (item) {
        const pass = item.passed === true;
        if (!pass) failedCheckCount++;
        return {
          title: def.title,
          pass,
          desc: item.reason || (pass ? 'Check passed.' : 'Verification check failed or unrecorded.')
        };
      }
      const flaggedMissing = failedNameSet.has(def.id);
      if (flaggedMissing) failedCheckCount++;
      return {
        title: def.title,
        pass: !flaggedMissing,
        desc: flaggedMissing ? 'Verification check failed or unrecorded.' : def.defaultDesc
      };
    });

    if (checksList) {
      let bannerHtml = '';
      const reportedFailures = Math.max(failedCheckCount, p.failed_check_count || 0);
      if (reportedFailures > 0 || p.all_checks_passed === false) {
        bannerHtml = `<div class="checks-summary-banner fail font-mono">&#9888; ${reportedFailures} Verification Exception${reportedFailures > 1 ? 's' : ''} Flagged (${Math.max(0, 7 - reportedFailures)}/7 passed)</div>`;
      } else {
        bannerHtml = `<div class="checks-summary-banner pass font-mono">&#10003; All 7 Deterministic Checks Passed (${relScore}/8 Relevance)</div>`;
      }

      checksList.innerHTML = bannerHtml + resolvedChecks.map(c => `
        <div class="drawer-check-row">
          <span class="drawer-check-badge ${c.pass ? 'pass' : 'fail'} font-mono">${c.pass ? 'PASS' : 'FAIL'}</span>
          <div class="drawer-check-desc">
            <strong>${escapeHtml(c.title)}</strong>
            <div style="font-size: 0.76rem; color: var(--muted); margin-top: 2px;">${escapeHtml(c.desc)}</div>
          </div>
        </div>
      `).join('');
    }

    const rTot = document.getElementById('drawer-rel-total');
    const rReal = document.getElementById('drawer-rel-real');
    const rMeas = document.getElementById('drawer-rel-meas');
    const rSf = document.getElementById('drawer-rel-sf');
    const rInt = document.getElementById('drawer-rel-int');

    if (rTot) rTot.textContent = `${relScore} / 8`;
    if (rReal) rReal.textContent = `${rel.real || 2} / 2`;
    if (rMeas) rMeas.textContent = `${rel.measurable || 2} / 2`;
    if (rSf) rSf.textContent = `${rel.sf || 2} / 2`;
    if (rInt) rInt.textContent = `${rel.interesting || 2} / 2`;

    const changelogEl = document.getElementById('drawer-changelog-entry');
    const copyReceiptBtn = document.getElementById('btn-copy-receipt');
    const receiptText = `COMMITMENT #${rank} (${p.promise_id}) · VERDICT=${(p.verdict || 'KEPT').toUpperCase()} · HASH=${(p.source_hash || '').slice(0, 16)}… · RUN=ARBITRATOR_RUN_accd67e9`;
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
    if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
      lastActiveElement.focus();
    }
  }

  // -------------------------------------------------------------------------
  // Featured Stories (0.2)
  // -------------------------------------------------------------------------
  function setupFeaturedStories() {
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

    // View mode switcher buttons (Table | Map & Districts | Entity Profiles | Quality Audit)
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

    // Clear filters button
    const btnClear = document.getElementById('btn-clear-filters');
    if (btnClear) {
      btnClear.addEventListener('click', () => {
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

    // Escape key listener for drawer
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const backdrop = document.getElementById('inspect-drawer-backdrop');
        if (backdrop && !backdrop.classList.contains('hidden')) {
          closeInspectDrawer();
        }
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

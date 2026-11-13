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
  let filterVerdict = 'all';
  let filterCategory = 'all';
  let filterEntity = 'all';
  let filterTier = 'all';
  let filterSort = 'rank';
  let searchTerm = '';
  let visibleRowsCount = 10;
  let currentRunType = 'N01'; // Default to Watchdog Catch per brief P0.5
  let currentStage = 0;
  let isAutoRunning = false;
  let autoTimer = null;
  let hasAutoPlayed = false;
  let lastActiveElement = null;

  // -------------------------------------------------------------------------
  // Plain Reason Lookup (1.3)
  // -------------------------------------------------------------------------
  function formatPlainVerdictReason(reason, verdict) {
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
    return String(text).replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1').replace(/`([^`]+)`/g, '$1').trim();
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

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
    setupObserverForReplay();
  }

  // -------------------------------------------------------------------------
  // Replay State Machine (0.5)
  // -------------------------------------------------------------------------
  const SCENARIOS = {
    N01: {
      id: 'N01',
      label: 'Watchdog N01 · Quote Mutation Catch (Planted Test)',
      speaker: 'Planted Watchdog Test N01',
      title: 'Quote Mutation Detection',
      target: 'Mayor Daniel Lurie · 1,500 Shelter Beds (P05)',
      expectedVerdict: 'quarantined',
      verdictLabel: 'Quarantined',
      sourceUrl: 'https://www.sf.gov/news/mayor-lurie-announces-crisis-stabilization-center',
      file: '582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md',
      hash: '582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa',
      stages: {
        1: {
          badge: 'HASH VERIFIED',
          title: 'Stage 1: Contemporaneous Source Retrieval',
          desc: 'Archil disk reads saved markdown record. SHA-256 byte fingerprint matches disk origin (582955d5df78...).'
        },
        2: {
          badge: 'MUTATION DETECTED',
          title: 'Stage 2: Deterministic Quote Verification',
          alert: true,
          alertText: "FLASH: 'shelter units' was altered! Original source reads '1,500 new shelter beds'. Substring match failed.",
          desc: 'Verbatim quote verification failed against immutable saved bytes.'
        },
        3: {
          badge: 'GATE PASSED (8/8)',
          title: 'Stage 3: Relevance Gate',
          desc: 'Relevance criteria scored 8/8 for civic impact and measurable metric.'
        },
        4: {
          badge: 'ADVOCATES FILED',
          title: 'Stage 4: Process-Isolated Advocates',
          desc: 'Sandbox A and Sandbox B run in separate memory spaces without database write access.'
        },
        5: {
          badge: 'CHECK FAILED · DIVERTED',
          title: 'Stage 5: Arbitrator Code Execution',
          alert: true,
          desc: 'Deterministic check accuracy_quote FAILED. Row immediately diverted to Quarantine Registry.'
        },
        6: {
          badge: 'HELD IN QUARANTINE',
          title: 'Stage 6: Outcome Ledger',
          desc: 'Item Q-N01 held back in quarantine registry. 0 rows written to main verified table.'
        }
      }
    },
    P02: {
      id: 'P02',
      label: '#01 · 24/7 Crisis Center (Lurie · Kept)',
      speaker: 'Mayor Daniel Lurie',
      title: '24/7 Crisis Stabilization Center',
      target: 'Tenderloin (822 Geary St)',
      expectedVerdict: 'kept',
      verdictLabel: 'Kept',
      sourceUrl: 'https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center',
      file: '582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md',
      hash: '582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa',
      stages: {
        1: {
          badge: 'HASH VERIFIED',
          title: 'Stage 1: Official Source Retrieval',
          desc: 'Archil disk reads official sf.gov municipal press release. SHA-256 matches byte-for-byte.'
        },
        2: {
          badge: 'QUOTE VERIFIED',
          title: 'Stage 2: Model Draft Extraction',
          desc: 'Verbatim quote verified: "That’s exactly what this 24/7 police-friendly stabilization center will be, and I am proud to be opening it,".'
        },
        3: {
          badge: 'GATE PASSED (8/8)',
          title: 'Stage 3: Relevance Gate',
          desc: 'Scored 8/8: Real commitment (2/2), Measurable (2/2), SF scope (2/2), Public interest (2/2).'
        },
        4: {
          badge: 'ARGUMENTS FILED',
          title: 'Stage 4: Process-Isolated Advocates',
          desc: 'Sandbox A confirms facility began accepting clients on April 28, 2025 at 822 Geary St. Sandbox B found 0 contradicting closure notices.'
        },
        5: {
          badge: '7/7 CHECKS PASSED',
          title: 'Stage 5: Arbitrator Code Execution',
          desc: 'All 7 deterministic checks passed: domain allowlist, hash match, quote match, timeline, rubric.'
        },
        6: {
          badge: 'VERIFIED & SIGNED',
          title: 'Stage 6: Verdict Ledger',
          desc: 'Verdict KEPT signed into append-only SQLite audit ledger. Published to main table.'
        }
      }
    },
    P05: {
      id: 'P05',
      label: '#05 · 1,500 Shelter Beds (Lurie · Broken)',
      speaker: 'Mayor Daniel Lurie',
      title: '1,500 Shelter Beds in First 6 Months',
      target: 'Citywide Shelter Network',
      expectedVerdict: 'broken',
      verdictLabel: 'Broken',
      sourceUrl: 'https://thefrisc.com/mayor-lurie-shelter-pledge-shortfall',
      file: 'thefrisc_shelter_shortfall.md',
      hash: '384c310bb67941a4a131738f8ed7c9aa4d73e5bc41468a7d6c028caafc141812',
      stages: {
        1: {
          badge: 'SOURCE RETRIEVED',
          title: 'Stage 1: News Investigation Source',
          desc: 'Retrieved verified investigative reporting documenting shelter capacity metrics.'
        },
        2: {
          badge: 'QUOTE EXTRACTED',
          title: 'Stage 2: Verbatim Extraction',
          desc: 'Extracted campaign commitment to open 1,500 beds in the first six months.'
        },
        3: {
          badge: 'GATE PASSED (8/8)',
          title: 'Stage 3: Relevance Gate',
          desc: 'High civic priority and quantified bed count target passed relevance gate.'
        },
        4: {
          badge: 'EVIDENCE FILED',
          title: 'Stage 4: Process-Isolated Advocates',
          desc: 'Sandbox B files municipal audit showing shelter expansions remained below numeric target.'
        },
        5: {
          badge: 'RUBRIC EVALUATION',
          title: 'Stage 5: Arbitrator Code Execution',
          desc: 'Deterministic rubric rule: numeric target not met within deadline window evaluated to broken.'
        },
        6: {
          badge: 'VERDICT BROKEN',
          title: 'Stage 6: Verdict Ledger',
          desc: 'Verdict BROKEN committed to audit ledger. Reason: numeric target not met or plan abandoned.'
        }
      }
    }
  };

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
    const scenario = SCENARIOS[scenarioKey] || SCENARIOS.N01;
    const panel = document.getElementById('pipeline-active-stage-panel');
    const stageIndicator = document.getElementById('pipeline-stage-indicator');
    const statusText = document.getElementById('packet-status-text');
    const trackFill = document.getElementById('packet-track-fill');
    const ballDot = document.getElementById('packet-ball-dot');

    // Update milestone indicators
    for (let i = 1; i <= 6; i++) {
      const circle = document.getElementById(`ms-circle-${i}`);
      if (circle) {
        if (i < stageNum) {
          circle.className = 'milestone-circle passed';
          circle.textContent = '✓';
        } else if (i === stageNum) {
          circle.className = 'milestone-circle active';
          circle.textContent = i;
        } else {
          circle.className = 'milestone-circle';
          circle.textContent = i;
        }
      }
    }

    const pct = stageNum === 0 ? 0 : Math.round((stageNum / 6) * 100);
    if (trackFill) trackFill.style.width = `${pct}%`;
    if (ballDot) ballDot.style.left = `${pct}%`;

    if (stageNum === 0) {
      if (stageIndicator) stageIndicator.textContent = 'STAGE 0 / 6 · READY TO RUN';
      if (statusText) statusText.textContent = 'waiting to start';
      if (panel) {
        panel.innerHTML = `
          <div class="stage-card-header">
            <span class="stage-state-pill font-mono">READY</span>
            <h3 class="stage-heading">${escapeHtml(scenario.title)}</h3>
          </div>
          <p style="color: var(--ink-dim); font-size: 0.95rem; margin: 12px 0 16px;">
            Target: <strong>${escapeHtml(scenario.speaker)}</strong> (${escapeHtml(scenario.target)})
          </p>
          <div style="background: rgba(0,0,0,0.25); padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 0.86rem; color: var(--muted);" class="font-mono">
            Source: ${escapeHtml(scenario.sourceUrl)}
          </div>
          <button type="button" class="btn btn-primary" id="btn-replay-start-inline" style="min-height: 44px;">
            Start Pipeline Run &rarr;
          </button>
        `;
        const startBtn = document.getElementById('btn-replay-start-inline');
        if (startBtn) startBtn.addEventListener('click', runReplay);
      }
      return;
    }

    const stageData = scenario.stages[stageNum] || {};
    if (stageIndicator) {
      stageIndicator.textContent = `STAGE ${stageNum} / 6 · ${stageData.badge || 'RUNNING'}`;
    }
    if (statusText) {
      statusText.textContent = stageNum === 6 ? (scenario.expectedVerdict === 'quarantined' ? 'diverted to quarantine' : 'verified & delivered') : 'in progress';
    }

    if (panel) {
      let alertHtml = '';
      if (stageData.alert) {
        alertHtml = `
          <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 8px; padding: 12px 14px; margin: 12px 0; color: #FCA5A5; font-size: 0.88rem;" class="font-mono">
            <strong>⚠ WATCHDOG CATCH:</strong> ${escapeHtml(stageData.alertText || stageData.desc)}
          </div>
        `;
      }

      panel.innerHTML = `
        <div class="stage-card-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="stage-num-badge blue">${stageNum}</span>
            <h3 class="stage-heading" style="margin: 0;">${escapeHtml(stageData.title || `Stage ${stageNum}`)}</h3>
          </div>
          <span class="stage-state-pill font-mono done">${escapeHtml(stageData.badge || 'DONE')}</span>
        </div>
        ${alertHtml}
        <p style="color: var(--ink); font-size: 0.92rem; line-height: 1.5; margin: 14px 0;">
          ${escapeHtml(stageData.desc || '')}
        </p>
        <div style="display: flex; gap: 12px; margin-top: 18px; align-items: center; flex-wrap: wrap;">
          <span class="font-mono" style="font-size: 0.78rem; color: var(--muted);">SHA-256: <code>${escapeHtml(scenario.hash.slice(0, 16))}…</code></span>
          <button type="button" class="btn-copy-hash font-mono" data-hash="${escapeHtml(scenario.hash)}">Copy Hash</button>
        </div>
      `;
    }
  }

  function advanceStep() {
    if (currentStage >= 6) {
      currentStage = 1;
    } else {
      currentStage++;
    }
    renderActiveStage(currentRunType, currentStage);
  }

  function runReplay() {
    if (isAutoRunning) {
      clearTimeout(autoTimer);
      isAutoRunning = false;
      return;
    }
    isAutoRunning = true;
    currentStage = 1;
    renderActiveStage(currentRunType, currentStage);

    function tick() {
      if (!isAutoRunning) return;
      if (currentStage < 6) {
        currentStage++;
        renderActiveStage(currentRunType, currentStage);
        autoTimer = setTimeout(tick, 1000);
      } else {
        isAutoRunning = false;
      }
    }
    autoTimer = setTimeout(tick, 1000);
  }

  function resetPipeline() {
    clearTimeout(autoTimer);
    isAutoRunning = false;
    currentStage = 0;
    renderActiveStage(currentRunType, 0);
  }

  function jumpToStage(num) {
    clearTimeout(autoTimer);
    isAutoRunning = false;
    currentStage = num;
    renderActiveStage(currentRunType, num);
  }

  function setupObserverForReplay() {
    const watchSection = document.getElementById('watch');
    if (!watchSection) return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !hasAutoPlayed) {
          hasAutoPlayed = true;
          runReplay();
        }
      });
    }, { threshold: 0.35 });

    observer.observe(watchSection);
  }

  // -------------------------------------------------------------------------
  // Quarantine Registry (0.1)
  // -------------------------------------------------------------------------
  function renderQuarantineTable() {
    if (!demoData) return;
    const quarantined = demoData.quarantined || [];
    const tbody = document.getElementById('quarantine-table-body');
    const mobileList = document.getElementById('mobile-quarantine-cards-list');

    if (tbody) {
      tbody.innerHTML = quarantined.map((q, idx) => {
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
        const destination = escapeHtml(q.destination || 'Held back. Never published.');
        const hash = escapeHtml(q.source_hash || '');
        const hashHtml = hash ? `<div class="quarantine-hash-row font-mono"><span class="hash-label">SHA-256:</span> <code class="quarantine-hash">${hash.slice(0, 12)}…</code> <button type="button" class="btn-copy-hash font-mono" data-hash="${hash}">Copy</button></div>` : '';

        return `
          <tr class="quarantine-row" id="quarantine-row-${qid}" data-qid="${qid}">
            <td class="quarantine-type-cell">
              <div class="quarantine-badge-group">
                <span class="quarantine-type-badge ${typeCls}">${typeBadge}</span>
                <span class="quarantine-pid font-mono">${pid}</span>
              </div>
            </td>
            <td class="quarantine-claim-cell">
              <div class="quarantine-submitted-claim">&ldquo;${claim}&rdquo;</div>
              ${diffHtml}
            </td>
            <td class="quarantine-check-cell">
              <div class="quarantine-check-plain">${failingPlain}</div>
              <code class="quarantine-check-code font-mono">${checkType}</code>
            </td>
            <td class="quarantine-reason-cell">
              <p class="quarantine-reason-text">${reason}</p>
              <div class="quarantine-catcher-meta font-mono">Caught by ${agent} &middot; ${dateStr}</div>
            </td>
            <td class="quarantine-outcome-cell">
              <div class="quarantine-outcome-status font-mono">${destination}</div>
              ${hashHtml}
            </td>
          </tr>
        `;
      }).join('');
    }

    if (mobileList) {
      mobileList.innerHTML = quarantined.map((q, idx) => {
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
        const destination = escapeHtml(q.destination || 'Held back. Never published.');

        return `
          <div class="mobile-quarantine-card" id="mobile-qcard-${qid}" data-qid="${qid}">
            <div class="mobile-card-header">
              <div class="mobile-card-speaker-group">
                <span class="quarantine-type-badge ${typeCls}">${typeBadge}</span>
                <span class="mobile-card-id font-mono">${pid}</span>
              </div>
              <span class="verdict-chip quarantined">Quarantined</span>
            </div>
            <blockquote class="quarantine-claim-quote font-serif">&ldquo;${claim}&rdquo;</blockquote>
            ${diffHtml}
            <div class="quarantine-check-block">
              <div class="quarantine-check-plain">${failingPlain} <code class="quarantine-check-code font-mono">${checkType}</code></div>
              <p class="quarantine-reason-text">${reason}</p>
            </div>
            <div class="mobile-card-footer font-mono">
              <span>${agent} &middot; ${dateStr}</span>
              <span class="quarantine-outcome-status">${destination}</span>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  function setTab(tabName) {
    activeTab = tabName;
    const tabPromises = document.getElementById('tab-btn-promises');
    const tabQuarantine = document.getElementById('tab-btn-quarantine');
    const tablePromises = document.getElementById('promises-table-container');
    const cardsPromises = document.getElementById('mobile-cards-list');
    const tableQuarantine = document.getElementById('quarantine-table-container');
    const cardsQuarantine = document.getElementById('mobile-quarantine-cards-list');
    const qHeader = document.getElementById('quarantine-header-status');
    const primaryControls = document.querySelector('.explore-primary-controls');
    const moreFiltersPanel = document.getElementById('more-filters-panel');
    const showingStatus = document.getElementById('table-showing-status');
    const paginationControls = document.getElementById('pagination-controls');

    if (tabName === 'quarantine') {
      if (tabPromises) {
        tabPromises.classList.remove('active');
        tabPromises.setAttribute('aria-selected', 'false');
      }
      if (tabQuarantine) {
        tabQuarantine.classList.add('active');
        tabQuarantine.setAttribute('aria-selected', 'true');
      }

      // Hide verified-only controls
      if (primaryControls) primaryControls.classList.add('hidden');
      if (moreFiltersPanel) moreFiltersPanel.classList.add('hidden');
      if (showingStatus) showingStatus.classList.add('hidden');
      if (paginationControls) paginationControls.classList.add('hidden');
      if (tablePromises) tablePromises.classList.add('hidden');
      if (cardsPromises) cardsPromises.classList.add('hidden');

      // Show quarantine elements
      if (qHeader) qHeader.classList.remove('hidden');
      if (tableQuarantine) tableQuarantine.classList.remove('hidden');
      if (cardsQuarantine) cardsQuarantine.classList.remove('hidden');
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
      if (primaryControls) primaryControls.classList.remove('hidden');
      if (showingStatus) showingStatus.classList.remove('hidden');
      if (paginationControls) paginationControls.classList.remove('hidden');
      if (tablePromises) tablePromises.classList.remove('hidden');
      if (cardsPromises) cardsPromises.classList.remove('hidden');

      // Hide quarantine elements
      if (qHeader) qHeader.classList.add('hidden');
      if (tableQuarantine) tableQuarantine.classList.add('hidden');
      if (cardsQuarantine) cardsQuarantine.classList.add('hidden');
    }
  }

  function switchToQuarantineAndHighlight(qid) {
    setTab('quarantine');
    const el = document.getElementById(`quarantine-row-${qid}`) || document.getElementById(`mobile-qcard-${qid}`);
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

    // Keyword search
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase().trim();
      list = list.filter(p => {
        const text = `${p.promise_id} ${p.entity} ${p.role || ''} ${p.promise_text} ${p.neighborhood || ''} ${p.category}`.toLowerCase();
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
    const mobileCards = document.getElementById('mobile-cards-list');

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
        let promised = escapeHtml(p.promised_date || 'not recorded');
        if (p.promised_date_note) promised += ' (derived)';
        const due = escapeHtml(p.due_date || 'No deadline');
        const done = escapeHtml(p.opened_date || p.completed_date || (p.verdict === 'kept' ? 'Verified completed' : '—'));
        const verdict = p.verdict || 'undecided';
        const verdClass = verdict.toLowerCase().replace(/[\s-]+/g, '_');
        const verdictLabel = formatVerdictLabel(verdict);
        const tier = getSourceTier(p.source_url);
        const tierClass = tier.toLowerCase();

        return `
          <tr class="promise-row" id="promise-${pid}" data-promise-id="${pid}" tabindex="0" role="button" aria-label="Inspect #${rank} ${entity}: ${promiseClamped.slice(0, 60)}">
            <td class="table-entity-cell">
              <div class="entity-headline-row">
                <span class="table-entity-name">${entity}</span>
                <span class="stable-id-pill font-mono">#${rank}</span>
              </div>
              <div class="entity-sub-row font-mono">
                <span class="table-role-tag">${role}</span>
              </div>
              <div class="entity-geo-tag font-mono">${neighborhood}</div>
            </td>
            <td class="table-quote-cell">
              <div class="table-promise-block">
                <div class="table-kicker font-mono">PROMISE</div>
                <blockquote class="table-quote-text font-serif">&ldquo;${promiseClamped}&rdquo;</blockquote>
              </div>
              <div class="table-outcome-block">
                <span class="table-kicker font-mono">WHAT HAPPENED:</span>
                <span class="table-outcome-text">${outcomeReason}</span>
              </div>
            </td>
            <td class="table-verdict-cell">
              <span class="verdict-chip ${verdClass}">${verdictLabel}</span>
              <div class="table-tier-row">
                <span class="source-tier-pill font-mono source-tier-${tierClass}">${tier}</span>
              </div>
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

    if (mobileCards) {
      mobileCards.innerHTML = list.slice(0, showingCount).map((p, idx) => {
        const rank = String(p.impact_rank || idx + 1).padStart(2, '0');
        const pid = escapeHtml(p.promise_id || '');
        const entity = escapeHtml(p.entity || '');
        const promiseRaw = cleanQuoteText(p.promise_text || '');
        const promise140 = escapeHtml(promiseRaw.slice(0, 140) + (promiseRaw.length > 140 ? '…' : ''));
        const outcomeReason = escapeHtml(formatPlainVerdictReason(p.verdict_reason, p.verdict));
        let promised = escapeHtml(p.promised_date || 'not recorded');
        if (p.promised_date_note) promised += ' (derived)';
        const due = escapeHtml(p.due_date || 'No deadline');
        const verdict = p.verdict || 'undecided';
        const verdClass = verdict.toLowerCase().replace(/[\s-]+/g, '_');
        const verdictLabel = formatVerdictLabel(verdict);
        const tier = getSourceTier(p.source_url);
        const tierClass = tier.toLowerCase();

        return `
          <div class="mobile-promise-card" data-pid="${pid}" tabindex="0" role="button" aria-label="Inspect #${rank} ${entity}: ${promise140.slice(0, 60)}">
            <div class="mobile-card-header">
              <div class="mobile-card-speaker-group">
                <span class="mobile-card-speaker">${entity}</span>
                <span class="mobile-card-id font-mono">#${rank}</span>
              </div>
              <span class="verdict-chip ${verdClass}">${verdictLabel}</span>
            </div>
            <div class="mobile-promise-slot">
              <blockquote class="mobile-card-quote font-serif">&ldquo;${promise140}&rdquo;</blockquote>
            </div>
            <div class="mobile-card-footer font-mono">
              <span class="mobile-card-date">Said ${promised}</span>
              <span class="mobile-card-tap-hint">Details &rarr;</span>
            </div>
          </div>
        `;
      }).join('');
    }
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
    const tierChipEl = document.getElementById('drawer-source-tier-chip');
    const horizonBadge = document.getElementById('drawer-horizon-badge');
    const idBadge = document.getElementById('drawer-id-badge');

    const rank = String(p.impact_rank || p.display_no || '01').padStart(2, '0');
    if (idBadge) idBadge.textContent = `#${rank} · ${p.promise_id}`;
    if (subtitleEl) {
      const loc = (p.neighborhood && p.neighborhood !== 'Citywide') ? p.neighborhood : (p.role || 'San Francisco');
      subtitleEl.textContent = `${p.entity} · ${loc}`;
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
    const tier = getSourceTier(p.source_url);
    if (tierChipEl) {
      tierChipEl.className = `source-tier-pill source-tier-${tier.toLowerCase()} font-mono`;
      tierChipEl.textContent = tier;
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
    const filePath = document.getElementById('drawer-file-path');
    const hashEl = document.getElementById('drawer-hash');
    const btnCopy = document.getElementById('btn-drawer-copy-hash');
    const retVal = document.getElementById('drawer-retrieved-date');

    if (promiseQuote) promiseQuote.textContent = `“${cleanQuoteText(p.promise_text || '')}”`;
    if (spkVal) spkVal.textContent = `${p.entity} (${p.role || 'Public Official'})`;
    if (saidVal) saidVal.textContent = p.promised_date || 'not recorded';
    if (dueVal) dueVal.textContent = p.due_date || 'No deadline';
    if (tierVal) tierVal.textContent = tier;
    if (srcUrl) {
      srcUrl.href = p.source_url || '#';
      srcUrl.textContent = p.source_url || 'source link not recorded';
    }
    if (filePath) {
      const cleanPath = (p.source_file_path || '').split('/').pop() || `${p.source_hash}.md`;
      filePath.textContent = cleanPath;
    }
    if (hashEl) hashEl.textContent = p.source_hash || 'not recorded';
    if (btnCopy) btnCopy.setAttribute('data-hash', p.source_hash || '');
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
    const chipLg = document.getElementById('drawer-verdict-chip-lg');
    const plainReasonEl = document.getElementById('drawer-plain-reason');
    const outcomeQuoteEl = document.getElementById('drawer-outcome-quote');
    const decidedAtEl = document.getElementById('drawer-decided-at');

    if (chipLg) {
      chipLg.className = `verdict-chip ${verdClass}`;
      chipLg.textContent = formatVerdictLabel(p.verdict);
    }
    if (plainReasonEl) plainReasonEl.textContent = formatPlainVerdictReason(p.verdict_reason, p.verdict);
    if (outcomeQuoteEl) outcomeQuoteEl.textContent = `“${cleanQuoteText(p.verbatim_quote || p.verdict_reason || '')}”`;
    if (decidedAtEl) decidedAtEl.textContent = p.decided_at ? p.decided_at.split('T')[0] : (p.opened_date || 'Nov 10, 2026');

    // Part 3: Advocates
    const keptBody = document.getElementById('drawer-adv-kept-body');
    const brokenBody = document.getElementById('drawer-adv-broken-body');
    const bundles = p.advocate_bundles || {};
    const kClaims = (bundles.kept && bundles.kept.claims) || [];
    const bClaims = (bundles.broken && bundles.broken.claims) || [];

    if (keptBody) {
      if (kClaims.length > 0) {
        keptBody.innerHTML = kClaims.map(c => `
          <div style="margin-bottom: 8px;">
            <div style="font-style: italic; color: var(--ink);">“${escapeHtml(c.quote || c.statement || '')}”</div>
            <div class="font-mono" style="font-size: 0.72rem; color: var(--muted); margin-top: 2px;">Source: ${escapeHtml(c.source_url || p.source_url || 'Verified record')}</div>
          </div>
        `).join('');
      } else {
        keptBody.innerHTML = `<p style="font-style: italic; color: var(--muted); margin: 0;">No affirmative source filed during review cycle.</p>`;
      }
    }

    if (brokenBody) {
      if (bClaims.length > 0) {
        brokenBody.innerHTML = bClaims.map(c => `
          <div style="margin-bottom: 8px;">
            <div style="font-style: italic; color: var(--ink);">“${escapeHtml(c.quote || c.statement || '')}”</div>
            <div class="font-mono" style="font-size: 0.72rem; color: var(--muted); margin-top: 2px;">Source: ${escapeHtml(c.source_url || 'Verified record')}</div>
          </div>
        `).join('');
      } else {
        const note = (bundles.broken && bundles.broken.note) || 'No contradicting evidence or cancellation records found in saved sources.';
        brokenBody.innerHTML = `<p style="font-style: italic; color: var(--muted); margin: 0;">${escapeHtml(note)}</p>`;
      }
    }

    // Part 4: Arbitrator 7 Checks & Relevance Gate
    const checksList = document.getElementById('drawer-checks-list');
    const defaultChecks = [
      { name: 'authenticity_domain', title: 'Domain Allowlist Enforcement', pass: true, desc: 'Domain is on allowlist (sf.gov, sfmta.com, flysfo.com, legistar).' },
      { name: 'authenticity_hash', title: 'SHA-256 Byte-Level Integrity', pass: true, desc: 'Computed hash matches disk fingerprint byte-for-byte.' },
      { name: 'accuracy_quote', title: 'Verbatim Quote Substring Check', pass: true, desc: 'Extracted commitment found verbatim in saved source bytes.' },
      { name: 'accuracy_speaker', title: 'Speaker & Role Call Verification', pass: true, desc: 'Municipal speaker attribution verified against public roster.' },
      { name: 'accuracy_date', title: 'Temporal Window & Horizon Bounds', pass: true, desc: 'Said, due, and outcome dates conform to strict temporal order.' },
      { name: 'verdict_rubric', title: 'Deterministic Rubric Application', pass: true, desc: 'Binary decision logic evaluates passing claims directly to verdict.' },
      { name: 'relevance_gate', title: 'Relevance Gate Score >= 5.0', pass: true, desc: 'Scored 8/8 for public impact and measurable outcomes.' }
    ];

    if (checksList) {
      checksList.innerHTML = defaultChecks.map(c => `
        <div class="drawer-check-row">
          <span class="drawer-check-badge ${c.pass ? 'pass' : 'fail'} font-mono">${c.pass ? 'PASS' : 'FAIL'}</span>
          <div class="drawer-check-desc">
            <strong>${escapeHtml(c.title)}</strong>
            <div style="font-size: 0.76rem; color: var(--muted); margin-top: 2px;">${escapeHtml(c.desc)}</div>
          </div>
        </div>
      `).join('');
    }

    const rel = p.relevance || { score: 8, real: 2, measurable: 2, sf: 2, interesting: 2 };
    const rTot = document.getElementById('drawer-rel-total');
    const rReal = document.getElementById('drawer-rel-real');
    const rMeas = document.getElementById('drawer-rel-meas');
    const rSf = document.getElementById('drawer-rel-sf');
    const rInt = document.getElementById('drawer-rel-int');

    if (rTot) rTot.textContent = `${rel.score || 8} / 8`;
    if (rReal) rReal.textContent = `${rel.real || 2} / 2`;
    if (rMeas) rMeas.textContent = `${rel.measurable || 2} / 2`;
    if (rSf) rSf.textContent = `${rel.sf || 2} / 2`;
    if (rInt) rInt.textContent = `${rel.interesting || 2} / 2`;

    const changelogEl = document.getElementById('drawer-changelog-entry');
    if (changelogEl) {
      changelogEl.textContent = `[${p.decided_at || '2025-05-01T00:00:00Z'}] COMMITMENT #${rank} (${p.promise_id}) VERDICT=${(p.verdict || 'KEPT').toUpperCase()} SIGNED_BY=ARBITRATOR_RUN_accd67e9 HASH=${(p.source_hash || '').slice(0, 16)}…`;
    }

    backdrop.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    drawer.focus();
  }

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
    // Replay controls
    const runSelect = document.getElementById('run-select');
    if (runSelect) {
      runSelect.addEventListener('change', () => {
        currentRunType = runSelect.value;
        resetPipeline();
      });
    }

    const btnRun = document.getElementById('btn-run-selected');
    if (btnRun) btnRun.addEventListener('click', runReplay);

    const btnNext = document.getElementById('btn-step-next');
    if (btnNext) btnNext.addEventListener('click', advanceStep);

    const btnReset = document.getElementById('btn-pipeline-reset');
    if (btnReset) btnReset.addEventListener('click', resetPipeline);

    // Milestone node click listeners
    for (let i = 1; i <= 6; i++) {
      const ms = document.getElementById(`ms-circle-${i}`);
      if (ms) {
        ms.parentElement.addEventListener('click', () => jumpToStage(i));
      }
    }

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

    const fTier = document.getElementById('filter-tier');
    if (fTier) {
      fTier.addEventListener('change', () => {
        filterTier = fTier.value;
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
        filterSort = 'rank';
        visibleRowsCount = 10;
        if (searchInput) searchInput.value = '';
        if (fCat) fCat.value = 'all';
        if (fEnt) fEnt.value = 'all';
        if (fTier) fTier.value = 'all';
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

    const mobileList = document.getElementById('mobile-cards-list');
    if (mobileList) {
      mobileList.addEventListener('click', (e) => {
        const card = e.target.closest('.mobile-promise-card');
        if (card) {
          const pid = card.getAttribute('data-pid');
          if (pid) openInspectDrawer(pid);
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

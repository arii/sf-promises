#!/usr/bin/env python3
"""
Rebuild docs/index.html with the new 7-section flow:
1. What is this? (Hero)
2. How are promises doing? (Stacked verdict bar)
3. Watch one promise get checked (Centerpiece pipeline replay at #watch)
4. Featured stories (6 cards at #stories)
5. Explore all promises (Mobile cards list + Desktop 4-col table at #explore)
6. How it's built (3 steps + 3 tech blocks at #how-it-works)
7. Limits (What this can't tell you at #limits)
"""

import re
from pathlib import Path

index_path = Path("docs/index.html")
html = index_path.read_text(encoding="utf-8")

# 1. Extract the 6 stages grid from pipeline-interactive-section
grid_match = re.search(r'(<div class="pipeline-6stages-grid">.*?</div>\s*<!-- Why This Design Architecture Card -->.*?</div>\s*</div>)', html, re.DOTALL)
if not grid_match:
    # try matching until </section>
    grid_match = re.search(r'(<div class="pipeline-6stages-grid">.*?)(\s*<!-- Why This Design Architecture Card -->.*?)?\s*</section>', html, re.DOTALL)
assert grid_match, "Could not find pipeline-6stages-grid in html"
stages_grid_html = grid_match.group(1).strip()

# 2. Extract inspect modal
modal_match = re.search(r'(<!-- 4-PART PROVENANCE & VERIFICATION INSPECTION MODAL -->\s*<div class="modal-backdrop[^>]*id="inspect-modal".*?</div>\s*</div>\s*</div>)', html, re.DOTALL)
assert modal_match, "Could not find inspect-modal in html"
modal_html = modal_match.group(1).strip()

# Assemble the new index.html template
new_html = f"""<!DOCTYPE html>
<html lang="en" style="color-scheme: dark;">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0f1a26">
  <title>SF Promises — Sourced Record of San Francisco Public Commitments</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
  <div class="shell">
    <!-- Sticky Topbar with Brand and 4 Navigation Links -->
    <header class="topbar sticky-nav" id="top">
      <div class="topbar-left">
        <a href="#top" class="brand" aria-label="SF Promises · top">
          <span class="brand-mark">SF</span>
          <span class="brand-text">SF Promises</span>
        </a>
        <nav class="topbar-nav" aria-label="Primary Navigation">
          <a href="#watch" class="nav-link">Watch</a>
          <a href="#stories" class="nav-link">Stories</a>
          <a href="#explore" class="nav-link">Explore</a>
          <a href="#how-it-works" class="nav-link">How it's built</a>
        </nav>
      </div>
      <div class="topbar-right">
        <a href="https://github.com/arii/sf-promises" target="_blank" rel="noopener noreferrer" class="github-icon-btn" aria-label="GitHub Repository">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        </a>
      </div>
    </header>

    <main class="wrap">
      <!-- SECTION 1: WHAT IS THIS? (Hero) -->
      <section class="hero-section" id="hero" aria-label="Overview">
        <h1 class="hero-headline">A sourced record of what San Francisco's leaders promised, and what happened.</h1>
        <p class="hero-subline">Tracking 54 public commitments across City Hall, SFO Airport, transit, and sports against saved, hashed documents.</p>
        <div class="hero-actions-row">
          <a href="#watch" class="btn btn-primary" id="btn-hero-watch">Watch one get checked &darr;</a>
          <a href="#explore" class="btn btn-secondary" id="btn-hero-browse">Browse promises &darr;</a>
        </div>
      </section>

      <!-- SECTION 2: HOW ARE PROMISES DOING? (Interactive Stacked Verdict Bar) -->
      <section class="verdict-bar-section" id="status-bar" aria-label="Outcome Distribution">
        <div class="stacked-bar-header">
          <span class="bar-header-title">Outcome Distribution</span>
          <span class="bar-header-count" id="outcome-dist-verified">54 VERIFIED</span>
        </div>
        <div class="proportional-stacked-bar interactive-bar" id="hero-stacked-bar" role="group" aria-label="Outcome breakdown: tap a segment to filter promises">
          <button type="button" class="bar-segment seg-kept" id="bar-seg-kept" data-verdict="kept" style="width: 46.3%;" title="Filter Kept (25)" aria-label="Filter Kept (25)"></button>
          <button type="button" class="bar-segment seg-progress" id="bar-seg-progress" data-verdict="in_progress" style="width: 18.5%;" title="Filter In Progress (10)" aria-label="Filter In Progress (10)"></button>
          <button type="button" class="bar-segment seg-broken" id="bar-seg-broken" data-verdict="broken" style="width: 31.5%;" title="Filter Broken (17)" aria-label="Filter Broken (17)"></button>
          <button type="button" class="bar-segment seg-undecided" id="bar-seg-undecided" data-verdict="undecided" style="width: 3.7%;" title="Filter Undecided (2)" aria-label="Filter Undecided (2)"></button>
        </div>
        <div class="stacked-legend-grid">
          <button type="button" class="legend-btn" data-verdict="kept"><span class="legend-swatch seg-kept"></span> <span id="legend-text-kept">25 Kept (46%)</span></button>
          <button type="button" class="legend-btn" data-verdict="in_progress"><span class="legend-swatch seg-progress"></span> <span id="legend-text-progress">10 In Progress (19%)</span></button>
          <button type="button" class="legend-btn" data-verdict="broken"><span class="legend-swatch seg-broken"></span> <span id="legend-text-broken">17 Broken (31%)</span></button>
          <button type="button" class="legend-btn" data-verdict="undecided"><span class="legend-swatch seg-undecided"></span> <span id="legend-text-undecided">2 Undecided (4%)</span></button>
        </div>
        <div class="tally-hero-line font-mono" id="tally-hero-line" style="display: none;">
          <strong id="tally-total">54</strong>
          <strong id="tally-kept">25</strong>
          <strong id="tally-progress">10</strong>
          <strong id="tally-broken">17</strong>
          <strong id="tally-undecided">2</strong>
        </div>
      </section>

      <!-- SECTION 3: WATCH ONE PROMISE GET CHECKED (Centerpiece Pipeline Replay) -->
      <section class="watch-section pipeline-interactive-section" id="watch" aria-label="Watch one promise get checked">
        <div class="section-heading-group">
          <h2>Watch one promise get checked</h2>
          <p class="section-lead">Follow the record from a public document to a decision across four sandboxes running as separated processes. Models draft in parallel; only Arbitrator code can write to the verified database.</p>
          <div class="saved-run-banner" role="note">SAVED RUN: Replay of verified pipeline run, not live execution</div>
        </div>

        <!-- Pipeline Controls Bar -->
        <div class="pipeline-actions-row">
          <label class="run-select-label font-mono" for="run-select">REPLAY</label>
          <select id="run-select" class="run-select" aria-label="Choose a promise to replay through the pipeline"></select>
          <button type="button" class="btn-play-action btn-primary-filled" id="btn-run-selected" title="Replay the selected run through all 6 stages">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            <span>Replay Walkthrough</span>
          </button>
          <button type="button" class="btn-play-action btn-step-advance" id="btn-step-next">
            <span>Next Stage &rarr;</span>
          </button>
          <button type="button" class="btn-play-action btn-pipeline-reset-pill" id="btn-pipeline-reset">
            <span>Reset ↺</span>
          </button>
        </div>

        <!-- Packet Transit Card with 6 Short Milestones -->
        <div class="packet-transit-card">
          <div class="packet-transit-header font-mono">
            <span class="packet-label" id="pipeline-stage-indicator">STAGE 0 / 6 &nbsp;·&nbsp; READY TO RUN</span>
            <span class="packet-status-text" id="packet-status-text">waiting to start</span>
          </div>

          <div class="packet-track-container">
            <div class="packet-track-bg-line"></div>
            <div class="packet-track-fill-line" id="packet-track-fill" style="width: 0%;"></div>
            
            <div class="packet-milestones-row">
              <div class="milestone-node"><div class="milestone-circle" id="ms-circle-1">1</div></div>
              <div class="milestone-node"><div class="milestone-circle" id="ms-circle-2">2</div></div>
              <div class="milestone-node"><div class="milestone-circle" id="ms-circle-3">3</div></div>
              <div class="milestone-node"><div class="milestone-circle" id="ms-circle-4">4</div></div>
              <div class="milestone-node"><div class="milestone-circle" id="ms-circle-5">5</div></div>
              <div class="milestone-node"><div class="milestone-circle" id="ms-circle-6">6</div></div>
            </div>

            <div class="packet-ball-dot" id="packet-ball-dot" style="left: 0%;">
              <div class="packet-ball-inner" id="packet-ball-inner"></div>
            </div>
          </div>

          <div class="milestone-labels-row font-mono">
            <span>Fetch</span>
            <span>Extract</span>
            <span>Gate</span>
            <span>Argue</span>
            <span>Decide</span>
            <span>Publish</span>
          </div>
        </div>

        <!-- 6 Stage Cards Grid -->
        {stages_grid_html}
      </section>

      <!-- SECTION 4: FEATURED STORIES -->
      <section class="stories-section" id="stories" aria-label="Featured Stories">
        <div class="section-heading-group">
          <h2>Featured stories</h2>
          <p class="section-lead">Six key commitments across City Hall, SFO Airport, transit, and public safety.</p>
        </div>
        <div class="featured-stories-grid" id="featured-stories-container">
          <!-- Pre-rendered by export_data.py -->
        </div><!-- end featured stories -->
      </section>

      <!-- SECTION 5: EXPLORE ALL PROMISES -->
      <section class="explore-section table-section" id="explore" aria-label="Explore all promises">
        <div class="section-heading-group">
          <h2>Explore all promises</h2>
          <p class="section-lead">Search and filter all 54 verified commitments and the quarantine registry.</p>
        </div>

        <div class="tabs-container">
          <div class="tab-buttons-group">
            <button type="button" class="tab-nav-btn active" id="tab-btn-promises">
              Verified Commitments <span class="tab-badge font-mono" id="tab-count-promises">54</span>
            </button>
            <button type="button" class="tab-nav-btn" id="tab-btn-quarantine">
              Quarantine Registry <span class="tab-badge font-mono" id="tab-count-quarantine">13</span>
            </button>
          </div>
        </div>

        <!-- Full-width Search & Mobile Filter Bar -->
        <div class="explore-controls-wrapper">
          <div class="search-row-full">
            <input type="text" id="search-input" class="search-input" placeholder="Search by speaker, keyword, or neighborhood..." aria-label="Search promises">
            <button type="button" class="btn-mobile-filter" id="btn-mobile-filter" aria-haspopup="dialog" aria-expanded="false">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              <span>Filter</span>
              <span class="mobile-filter-badge" id="mobile-filter-badge" style="display:none;">0</span>
            </button>
          </div>

          <!-- Desktop-only filters panel -->
          <div class="desktop-filters-panel" id="desktop-filters-panel">
            <div class="domain-filter-pills-bar" id="domain-pills-bar">
              <button type="button" class="btn-domain-pill active" data-category="all" id="btn-domain-all">All of SF</button>
              <button type="button" class="btn-domain-pill" data-category="Transit &amp; Streets">Transit &amp; Streets (8)</button>
              <button type="button" class="btn-domain-pill" data-category="Housing &amp; Neighborhoods">Housing &amp; Neighborhoods (13)</button>
              <button type="button" class="btn-domain-pill" data-category="Civic Governance">Civic Governance (15)</button>
              <button type="button" class="btn-domain-pill" data-category="Airport &amp; Airlines">Airport &amp; Airlines (4)</button>
              <button type="button" class="btn-domain-pill" data-category="Sports">Sports (3)</button>
              <button type="button" class="btn-domain-pill" data-category="Culture &amp; Music">Culture &amp; Music (1)</button>
              <button type="button" class="btn-domain-pill" data-category="Environment &amp; Energy">Environment &amp; Energy (2)</button>
              <button type="button" class="btn-domain-pill" data-category="Infrastructure &amp; Tech">Infrastructure &amp; Tech (2)</button>
              <button type="button" class="btn-domain-pill" data-category="Bay Area &amp; Regional">Bay Area &amp; Regional (6)</button>
            </div>

            <div class="filters-dropdowns-row">
              <div class="filter-group">
                <label for="filter-entity">Entity</label>
                <select id="filter-entity" class="filter-select">
                  <option value="all">All Entities</option>
                  <option value="politicians">Politicians</option>
                  <option value="city_government">City Government &amp; Airport</option>
                  <option value="sports">Sports</option>
                  <option value="companies">Companies &amp; Airlines</option>
                  <option value="culture">Culture</option>
                </select>
              </div>

              <div class="filter-group">
                <label for="filter-verdict">Verdict</label>
                <select id="filter-verdict" class="filter-select">
                  <option value="all">All Verdicts</option>
                  <option value="kept">Kept</option>
                  <option value="in_progress">In Progress</option>
                  <option value="broken">Broken</option>
                  <option value="stalled">Stalled</option>
                  <option value="undecided">Undecided</option>
                </select>
              </div>

              <div class="filter-group">
                <label for="filter-category">Category</label>
                <select id="filter-category" class="filter-select">
                  <option value="all">All Categories</option>
                  <option value="Airport &amp; Airlines">Airport &amp; Airlines</option>
                  <option value="Transit &amp; Streets">Transit &amp; Streets</option>
                  <option value="Housing &amp; Neighborhoods">Housing &amp; Neighborhoods</option>
                  <option value="Civic Governance">Civic Governance</option>
                  <option value="Sports">Sports</option>
                  <option value="Culture &amp; Music">Culture &amp; Music</option>
                  <option value="Environment &amp; Energy">Environment &amp; Energy</option>
                  <option value="Infrastructure &amp; Tech">Infrastructure &amp; Tech</option>
                  <option value="Bay Area &amp; Regional">Bay Area &amp; Regional</option>
                </select>
              </div>

              <div class="filter-group">
                <label for="filter-sort">Sort</label>
                <select id="filter-sort" class="filter-select font-mono">
                  <option value="rank">Impact &amp; Debate Rank</option>
                  <option value="default">Promised Date (Newest first)</option>
                  <option value="date_asc">Promised Date (Oldest first)</option>
                  <option value="verdict">Verdict</option>
                  <option value="entity">Entity (A &rarr; Z)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Active Removable Filter Chips Tray -->
        <div class="active-chips-tray font-mono" id="active-chips-tray" style="display: none;">
          <span class="chips-label">ACTIVE FILTERS:</span>
          <div class="chips-container" id="chips-container"></div>
          <button type="button" class="btn-clear-all" id="btn-clear-all-chips">Clear all &times;</button>
        </div>

        <div class="table-results-status-bar font-mono">
          <div class="status-count-info">
            <span>Showing <strong id="table-showing-count">10</strong> of <span id="table-total-count">54</span> commitments</span>
            <span class="active-filter-indicator font-mono" id="active-filter-indicator">&middot; Active: All commitments</span>
          </div>
        </div>

        <!-- MOBILE CARDS LIST (<768px) -->
        <div class="mobile-promise-cards-list" id="mobile-cards-list">
          <!-- Pre-rendered by export_data.py -->
        </div><!-- end mobile cards -->

        <!-- DESKTOP 4-COLUMN TABLE (>=768px) -->
        <div class="data-table-container" id="promises-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 26%;" class="sortable-th" data-sort="entity" role="columnheader" aria-sort="none" tabindex="0">
                  <div class="th-content">
                    <span>Speaker</span>
                    <span class="sort-icon font-mono">&updownarrow;</span>
                  </div>
                </th>
                <th style="width: 44%;" class="sortable-th" data-sort="quote" role="columnheader" aria-sort="none" tabindex="0">
                  <div class="th-content">
                    <span>Promise</span>
                    <span class="sort-icon font-mono">&updownarrow;</span>
                  </div>
                </th>
                <th style="width: 15%;" class="sortable-th" data-sort="verdict" role="columnheader" aria-sort="none" tabindex="0">
                  <div class="th-content">
                    <span>Verdict</span>
                    <span class="sort-icon font-mono">&updownarrow;</span>
                  </div>
                </th>
                <th style="width: 15%;" class="sortable-th" data-sort="timeline" role="columnheader" aria-sort="none" tabindex="0">
                  <div class="th-content">
                    <span>Date</span>
                    <span class="sort-icon font-mono">&updownarrow;</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody id="promises-table-body" class="list">
              <!-- Pre-rendered by export_data.py -->
            </tbody>
          </table>
        </div>

        <!-- Quarantine Registry Table -->
        <div class="data-table-container" id="quarantine-table-container" style="display: none;">
          <table class="data-table quarantine-table">
            <thead>
              <tr>
                <th style="width: 10%;">Test ID</th>
                <th style="width: 32%;">Target / Planted Claim</th>
                <th style="width: 22%;">Failure Reason</th>
                <th style="width: 24%;">Arbitrator Finding</th>
                <th style="width: 12%;">Storage State</th>
              </tr>
            </thead>
            <tbody id="quarantine-table-body">
              <!-- Pre-rendered by export_data.py -->
            </tbody>
          </table>
        </div>

        <!-- Pagination Controls -->
        <div class="pagination-controls" id="pagination-controls">
          <button type="button" class="btn-pagination" id="btn-show-more">
            Show 10 More Commitments (showing 10 of 54)
          </button>
          <button type="button" class="btn-pagination-secondary" id="btn-show-all">
            Show All 54
          </button>
        </div>

        <!-- Back to Top Button -->
        <div class="back-to-top-row">
          <a href="#top" class="btn-back-to-top font-mono" id="btn-back-to-top">
            <span>Back to top &uarr;</span>
          </a>
        </div>
      </section>

      <!-- SECTION 6: HOW IT'S BUILT -->
      <section class="how-it-works-section" id="how-it-works" aria-label="How it is built">
        <div class="section-heading-group">
          <h2>How it's built</h2>
          <p class="section-lead">A verification pipeline designed to ground public accountability in cryptographic proof.</p>
        </div>

        <!-- 3 One-Line Steps with Icons -->
        <div class="steps-3-grid">
          <div class="step-card">
            <div class="step-icon" aria-hidden="true">📄</div>
            <div class="step-title">Find the source</div>
            <p class="step-desc">Saved and cryptographically hashed from municipal records and local news archives.</p>
          </div>
          <div class="step-card">
            <div class="step-icon" aria-hidden="true">⚖️</div>
            <div class="step-title">Argue both sides</div>
            <p class="step-desc">Two model advocates debate kept vs. broken outcomes from isolated sandboxes.</p>
          </div>
          <div class="step-card">
            <div class="step-icon" aria-hidden="true">🔒</div>
            <div class="step-title">Check with code</div>
            <p class="step-desc">Deterministic code checks dates, hashes, and quotes. Zero model calls decide verdicts.</p>
          </div>
        </div>

        <!-- 3 Architecture Blocks -->
        <div class="tech-blocks-row">
          <div class="tech-block">
            <div class="tech-kicker">Persistent sandboxes</div>
            <h3>Archil sandboxes</h3>
            <p>Isolated microVM workers run checks without direct access to production databases.</p>
          </div>
          <div class="tech-block">
            <div class="tech-kicker">Temporal retrieval</div>
            <h3>Keenable search</h3>
            <p>Strict time-window searches find verbatim public commitments and realized outcomes.</p>
          </div>
          <div class="tech-block">
            <div class="tech-kicker">Deterministic code</div>
            <h3>Arbitrator ledger</h3>
            <p>Seven deterministic checks sign verdicts directly into an immutable audit trail.</p>
          </div>
        </div>

        <!-- Built With Heritage -->
        <div class="built-heritage-card">
          <div class="built-heritage-grid">
            <div>
              <h4>Built With</h4>
              <ul class="plain-credits-list">
                <li><strong>Archil Cloud Disks:</strong> Isolated microVM forks and persistent verification filesystem (<span class="font-mono">/mnt/archil</span>).</li>
                <li><strong>Keenable API:</strong> Strict temporal retrieval across allowlisted contemporaneous SF domains.</li>
                <li><strong>SF Legistar &amp; DataSF:</strong> Official Board of Supervisors agendas, resolutions, and 311 operational signals.</li>
                <li><strong>Granicus Transcripts:</strong> Verbatim City Hall hearing records.</li>
                <li><a href="https://huggingface.co/datasets/onasafari/sf-promises" target="_blank" rel="noopener"><strong>Hugging Face Dataset:</strong></a> Open public SQLite database and 51-column dataset release.</li>
              </ul>
            </div>
            <div>
              <h4>Inspired By</h4>
              <ul class="plain-credits-list">
                <li><a href="https://github.com/xternal/openpromises" target="_blank" rel="noopener"><strong>OpenPromises:</strong></a> Open commitment verification principles.</li>
                <li><a href="https://github.com/cluster2600/kept.vote" target="_blank" rel="noopener"><strong>kept.vote:</strong></a> Civic promise accountability.</li>
                <li><a href="https://councilhound.net" target="_blank" rel="noopener"><strong>CouncilHound:</strong></a> Municipal council tracking.</li>
                <li><a href="https://ken.promisetracker-v2.dev.codeforafrica.org" target="_blank" rel="noopener"><strong>PromiseTracker:</strong></a> Citizen accountability.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- SECTION 7: LIMITS (Collapsible by default) -->
      <section class="limits-section" id="limits" aria-label="System Limits">
        <details class="limits-accordion" id="limits-accordion">
          <summary class="limits-heading">
            <span class="limits-title">What this can't tell you</span>
            <span class="limits-chevron font-mono" aria-hidden="true">&darr;</span>
          </summary>
          <div class="limits-body">
            <p>SF Promises verifies whether specific public commitments were fulfilled as written in verifiable municipal documents. Here is what deterministic checks cannot capture:</p>
            <ul>
              <li><strong>Private negotiations:</strong> Verbal agreements, closed-door council negotiations, or undocumented promises made without public record.</li>
              <li><strong>Intent &amp; motivation:</strong> We track outcomes (did the beds open?), not whether an official tried hard or faced unexpected political resistance.</li>
              <li><strong>Nuanced capital delays:</strong> Major infrastructure projects face complex supply-chain or legal delays that binary checks record strictly as delayed.</li>
              <li><strong>Append-only corrections:</strong> When ground truth changes (like a store closing after opening), the ledger re-checks every 90 days and appends corrections rather than erasing history.</li>
            </ul>
          </div>
        </details>
      </section>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <div class="footer-left">
        <span class="footer-brand-title">SF Promises &middot; arii/sf-promises</span>
        <span>Built by Ariel Anders &middot; Archil Hackathon (Nov 10, 2026 &middot; Best Use of Keenable)</span>
      </div>
      <div class="footer-links-group">
        <a href="#watch" class="btn-footer-link">Watch &uarr;</a>
        <a href="https://huggingface.co/datasets/onasafari/sf-promises" target="_blank" rel="noopener noreferrer" style="color: #FCD34D;">Hugging Face 🤗</a>
        <a href="https://github.com/arii/sf-promises" target="_blank" rel="noopener noreferrer" style="color: var(--blue);">GitHub &nearr;</a>
      </div>
    </footer>
  </div>

  <!-- Mobile Filter Sheet / Bottom Drawer (<768px) -->
  <div class="mobile-filter-sheet-backdrop" id="mobile-filter-backdrop" style="display: none;" aria-hidden="true">
    <div class="mobile-filter-sheet" id="mobile-filter-sheet" role="dialog" aria-modal="true" aria-label="Filter Commitments">
      <div class="sheet-header">
        <h3>Filter Commitments</h3>
        <button type="button" class="btn-close-sheet" id="btn-close-filter-sheet" aria-label="Close filters">&times;</button>
      </div>
      <div class="sheet-body">
        <div class="sheet-filter-group">
          <label for="mobile-filter-entity">Entity</label>
          <select id="mobile-filter-entity" class="sheet-select">
            <option value="all">All Entities</option>
            <option value="politicians">Politicians</option>
            <option value="city_government">City Government &amp; Airport</option>
            <option value="sports">Sports</option>
            <option value="companies">Companies &amp; Airlines</option>
            <option value="culture">Culture</option>
          </select>
        </div>

        <div class="sheet-filter-group">
          <label for="mobile-filter-verdict">Verdict</label>
          <select id="mobile-filter-verdict" class="sheet-select">
            <option value="all">All Verdicts</option>
            <option value="kept">Kept</option>
            <option value="in_progress">In Progress</option>
            <option value="broken">Broken</option>
            <option value="stalled">Stalled</option>
            <option value="undecided">Undecided</option>
          </select>
        </div>

        <div class="sheet-filter-group">
          <label for="mobile-filter-category">Category</label>
          <select id="mobile-filter-category" class="sheet-select">
            <option value="all">All Categories</option>
            <option value="Airport &amp; Airlines">Airport &amp; Airlines</option>
            <option value="Transit &amp; Streets">Transit &amp; Streets</option>
            <option value="Housing &amp; Neighborhoods">Housing &amp; Neighborhoods</option>
            <option value="Civic Governance">Civic Governance</option>
            <option value="Sports">Sports</option>
            <option value="Culture &amp; Music">Culture &amp; Music</option>
            <option value="Environment &amp; Energy">Environment &amp; Energy</option>
            <option value="Infrastructure &amp; Tech">Infrastructure &amp; Tech</option>
            <option value="Bay Area &amp; Regional">Bay Area &amp; Regional</option>
          </select>
        </div>

        <div class="sheet-filter-group">
          <label for="mobile-filter-sort">Sort</label>
          <select id="mobile-filter-sort" class="sheet-select font-mono">
            <option value="rank">Impact &amp; Debate Rank</option>
            <option value="default">Promised Date (Newest first)</option>
            <option value="date_asc">Promised Date (Oldest first)</option>
            <option value="verdict">Verdict</option>
            <option value="entity">Entity (A &rarr; Z)</option>
          </select>
        </div>
      </div>
      <div class="sheet-footer">
        <button type="button" class="btn-sheet-reset" id="btn-sheet-reset">Reset</button>
        <button type="button" class="btn-sheet-apply" id="btn-sheet-apply">Apply Filters</button>
      </div>
    </div>
  </div>

  {modal_html}

  <!-- Scripts -->
  <script src="data.js"></script>
  <script src="list.min.js"></script>
  <script src="app.js"></script>
</body>
</html>
"""

index_path.write_text(new_html, encoding="utf-8")
print("Rebuilt docs/index.html with new 7-section layout structure.")

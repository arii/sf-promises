(() => {
  'use strict';
  const labels = {
    KEPT: 'Kept', KEPT_THEN_REVERSED: 'Kept then reversed',
    DELAYED_OR_PARTIAL: 'Delayed or partial', BROKEN: 'Broken', IN_PROGRESS: 'In progress',
  };
  const fileInput = document.getElementById('snapshot-file');
  const status = document.getElementById('status');
  const time = document.getElementById('snapshot-time');
  const list = document.getElementById('promise-list');
  const tallies = document.getElementById('tallies');
  const filters = {
    verdict: document.getElementById('verdict-filter'),
    entity_type: document.getElementById('entity-filter'),
    sector: document.getElementById('sector-filter'),
  };
  let promises = [];
  let generation = 0;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  function setOptions(select, values, names = {}) {
    select.replaceChildren(select.options[0]);
    select.value = 'all';
    values.forEach(value => select.add(new Option(names[value] || value, value)));
  }

  function valid(snapshot) {
    return snapshot && snapshot.snapshot_kind === 'candidate_not_published'
      && typeof snapshot.as_of === 'string' && Array.isArray(snapshot.promises)
      && snapshot.promises.length <= 10000 && snapshot.promises.every(p =>
        p && ['promise_id', 'promise_text', 'entity_name', 'entity_type', 'sector',
          'neighborhood', 'date_promised', 'date_deadline', 'verdict_reason', 'decided_at']
          .every(key => typeof p[key] === 'string')
        && Object.hasOwn(labels, p.verdict) && Array.isArray(p.evidence)
        && p.evidence.every(e => e && ['phase', 'url', 'source_tier', 'published_date',
          'local_source_path', 'content_sha256', 'verbatim_quote'].every(key => typeof e[key] === 'string'))
        && p.relevance && Number.isInteger(p.relevance.total)
      );
  }

  function detailFor(promise) {
    const details = node('details');
    const summary = node('summary');
    summary.append(node('strong', promise.promise_text));
    const meta = node('span', undefined, 'summary-meta');
    meta.append(node('span', labels[promise.verdict], 'badge'),
      node('span', `${promise.promise_id} · ${promise.entity_name} · ${promise.neighborhood}`));
    summary.append(meta);
    const detail = node('div', undefined, 'detail');
    detail.append(node('p', `${promise.entity_type} · ${promise.sector}`),
      node('p', `Promised: ${promise.date_promised} · Deadline: ${promise.date_deadline}`),
      node('h3', 'Recorded verdict'),
      node('p', `${labels[promise.verdict]} — ${promise.verdict_reason}`),
      node('p', `Decided: ${promise.decided_at} · Relevance: ${promise.relevance.total}/8`),
      node('h3', 'Evidence'));
    promise.evidence.forEach(evidence => {
      const section = node('div', undefined, 'evidence');
      section.append(node('p', `${evidence.phase} · ${evidence.source_tier} · ${evidence.published_date}`),
        node('blockquote', evidence.verbatim_quote));
      try {
        const url = new URL(evidence.url);
        if (url.protocol === 'https:' && !url.username && !url.password) {
          const link = node('a', evidence.url);
          link.href = url.href;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          section.append(link);
        } else {
          section.append(node('p', 'Source URL unavailable'));
        }
      } catch {
        section.append(node('p', 'Source URL unavailable'));
      }
      section.append(node('p', `Saved file: ${evidence.local_source_path}`),
        node('p', `SHA-256: ${evidence.content_sha256}`, 'hash'));
      detail.append(section);
    });
    if (!promise.evidence.length) detail.append(node('p', 'No evidence recorded.'));
    details.append(summary, detail);
    return details;
  }

  function render() {
    const selected = Object.entries(filters);
    const filtered = promises.filter(p => selected.every(([key, select]) =>
      select.value === 'all' || p[key] === select.value));
    list.replaceChildren(...filtered.map(detailFor));
    status.textContent = `Showing ${filtered.length} of ${promises.length} promise${promises.length === 1 ? '' : 's'}.`;
    if (!filtered.length) list.append(node('p', 'No matching promises.', 'muted'));
  }

  Object.values(filters).forEach(select => select.addEventListener('change', render));
  fileInput.addEventListener('change', async () => {
    const current = ++generation;
    promises = [];
    list.replaceChildren();
    tallies.replaceChildren();
    time.textContent = '';
    Object.values(filters).forEach(select => setOptions(select, []));
    const file = fileInput.files[0];
    if (!file) {
      status.textContent = 'Choose a candidate snapshot to begin.';
      return;
    }
    try {
      if (file.size > 5 * 1024 * 1024) throw new Error('size');
      const snapshot = JSON.parse(await file.text());
      if (current !== generation) return;
      if (!valid(snapshot)) throw new Error('invalid');
      promises = snapshot.promises;
      time.textContent = `Snapshot cutoff: ${snapshot.as_of} · Candidate, not published`;
      const counts = Object.fromEntries(Object.keys(labels).map(key => [key, 0]));
      promises.forEach(p => counts[p.verdict]++);
      Object.keys(labels).filter(key => counts[key]).forEach(key =>
        tallies.append(node('span', `${labels[key]}: ${counts[key]}`, 'tally')));
      setOptions(filters.verdict, Object.keys(labels), labels);
      setOptions(filters.entity_type, [...new Set(promises.map(p => p.entity_type))].sort());
      setOptions(filters.sector, [...new Set(promises.map(p => p.sector))].sort());
      render();
    } catch {
      if (current === generation) status.textContent = 'Invalid or unreadable candidate snapshot.';
    }
  });
})();

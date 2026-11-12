---
name: keenable-temporal-audit
description: Use when discovering or verifying evidence for SF Promises origin, delivery, or survival claims with Keenable.
---

# Temporal research and evidence

The official `keenable` Python SDK documents `AsyncKeenable.search`, `fetch`,
`published_after`, `published_before`, and `max_results`:
https://pypi.org/project/keenable/

- Use `src.v2_discovery.discover_timeline` for bounded origin, delivery and
  survival lead searches; dates are inputs, not facts inferred from snippets.
- Origin news/press sources must be published within 30 days of the promise.
  A later Tier 1 official source may establish historical origin only after
  its identity, original date and commitment text are independently verified.
  Missing dates remain blocked. Deadline horizon must be at least 60 days.
- Search results and Tier 3 canaries are leads, never evidence. Fetch and save
  complete source material first; verify the allowlisted URL, saved bytes,
  SHA-256 and verbatim quote. An empty, truncated or unsupported source is
  blocked. Never represent a source tier or extracted fact as verified solely
  because a model asserted it.
- Use `src.v2_keenable.RetryingKeenable` for bounded 429 retries with
  `Retry-After`. Payment errors, exhausted retry budgets and missing or
  excessive retry delays must stop as blocked rather than yield empty results.
- If an origin check fails, perform bounded rediscovery before quarantine.
  Kept and broken advocates use separate staging bundles; only the
  deterministic Verdict coordinator may publish or quarantine.

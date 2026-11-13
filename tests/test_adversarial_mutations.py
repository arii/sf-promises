"""Test automated adversarial mutations against the arbitrator's verification suite."""

import hashlib
from src.checks import (
    check_quote,
    check_hash,
    check_domain,
)
from src.arbitrator import compute_deterministic_verdict
from datetime import date, timedelta


def test_adversarial_mutations_false_accept_rate():
    """Generate 50 adversarial mutations across quote, hash, domain, and temporal checks.
    Verify that 0% are falsely accepted (100% catch rate).
    """
    total_mutations = 50
    catches = 0

    real_quote = "The stabilization unit, staffed by nurses, doctors, and behavioral health specialists, will begin accepting clients on April 28."
    real_text = f"San Francisco Department of Public Health announced: {real_quote}"
    real_hash = hashlib.sha256(real_text.encode("utf-8")).hexdigest()

    # Category 1: Altered quote mutations (15 tests)
    quote_mutations = [
        real_quote.replace("April 28", "May 15"),
        real_quote.replace("nurses", "paramedics"),
        real_quote.replace("doctors", "interns"),
        real_quote.replace("stabilization", "triage"),
        real_quote.replace("behavioral", "mental"),
        real_quote + " guaranteed.",
        "Mayor Lurie announced: " + real_quote,
        real_quote.lower(),
        real_quote.replace("will begin", "began"),
        real_quote.replace("specialists", "officers"),
        real_quote.replace("clients", "patients"),
        real_quote.replace("staffed", "managed"),
        "Completely fabricated quote about homeless services in SF",
        real_quote.replace("28", "29"),
        "“" + real_quote + "”",
    ]
    for q in quote_mutations:
        passed, reason = check_quote(real_text, q)
        if not passed:
            catches += 1

    # Category 2: Hash corruption mutations (15 tests)
    hash_mutations = [
        real_hash[:-1] + ("0" if real_hash[-1] != "0" else "1"),
        "0" * 64,
        "a" * 64,
        real_hash[:32],  # truncated
        real_hash + "ab",  # too long
        "not-a-hex-digest",
        real_hash.upper(),  # case mismatch
        hashlib.sha256(b"different text").hexdigest(),
        hashlib.sha256(real_text.replace("April", "May").encode("utf-8")).hexdigest(),
        real_hash[::-1],  # reversed
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # empty hash
        real_hash[:-4] + "dead",
        "deadbeef" * 8,
        real_hash.replace(real_hash[0], "f" if real_hash[0] != "f" else "0"),
        real_hash[:63] + ("x"),  # non-hex
    ]
    for h in hash_mutations:
        passed, reason = check_hash(real_text.encode("utf-8"), h)
        if not passed:
            catches += 1

    # Category 3: Domain allowlist mutations (10 tests)
    domain_mutations = [
        "https://evil-spoof-sf.gov.attacker.com/news",
        "https://sf-gov.com/press",
        "https://untrusted-blog.org/sf-promises",
        "https://sfgov.fake/announcement",
        "https://russia-today.ru/sf",
        "https://reddit.com/r/sanfrancisco",
        "https://x.com/MayorLurie/status/123456",
        "https://medium.com/@user/sf-crisis",
        "https://substack.com/post/sf-audit",
        "https://sfmta.phishing.io/updates",
    ]
    for d in domain_mutations:
        passed, reason = check_domain(d)
        if not passed:
            catches += 1

    # Category 4: Temporal arithmetic mutations (10 tests)
    # A future deadline claiming completed when it is not delivered or contradictory
    today = date.today()
    temporal_mutations = [
        # Future deadline with no delivery claiming KEPT
        {"deadline": today + timedelta(days=60), "delivery": "NOT_DELIVERED", "survival": "NOT_YET_OPEN"},
        {"deadline": today + timedelta(days=120), "delivery": "PENDING_FUTURE_DEADLINE", "survival": "NOT_YET_OPEN"},
        {"deadline": today + timedelta(days=365), "delivery": "NOT_DELIVERED", "survival": "NOT_YET_OPEN"},
        {"deadline": today + timedelta(days=1), "delivery": "NOT_DELIVERED", "survival": "NOT_YET_OPEN"},
        {"deadline": today + timedelta(days=30), "delivery": "NOT_DELIVERED", "survival": "SHUTTERED_OR_CLOSED"},
        # Past deadline with no delivery claiming KEPT
        {"deadline": today - timedelta(days=60), "delivery": "NOT_DELIVERED", "survival": "NOT_YET_OPEN"},
        {"deadline": today - timedelta(days=120), "delivery": "NOT_DELIVERED", "survival": "SHUTTERED_OR_CLOSED"},
        {"deadline": today - timedelta(days=365), "delivery": "NOT_DELIVERED", "survival": "REVOKED_OR_HALTED"},
        {"deadline": today - timedelta(days=10), "delivery": "NOT_DELIVERED", "survival": "NOT_YET_OPEN"},
        {"deadline": today - timedelta(days=500), "delivery": "NOT_DELIVERED", "survival": "NOT_YET_OPEN"},
    ]
    for m in temporal_mutations:
        verdict = compute_deterministic_verdict(
            date_deadline=m["deadline"],
            initial_delivery=m["delivery"],
            current_survival=m["survival"],
            as_of=today,
        )
        # None of these mutations may be computed as "KEPT"
        if verdict != "KEPT":
            catches += 1

    false_accepts = total_mutations - catches
    false_accept_rate = false_accepts / total_mutations

    print(f"\nAdversarial Mutations: {catches}/{total_mutations} caught ({catches / total_mutations * 100:.1f}%)")
    print(f"False-accept rate: {false_accept_rate * 100:.2f}%")

    assert catches == total_mutations, f"{false_accepts} mutations were falsely accepted!"
    assert false_accept_rate == 0.0, f"False-accept rate must be 0.0, got {false_accept_rate}"

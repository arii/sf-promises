"""Lane F case definitions: P01-P12 ground truth + N01-N12 planted specs.

Source of truth: Archil Hackathon Nov 10 - SF Promises Export/03-validation-and-tests.md
Do NOT rename with a test_ prefix: this module is data, not a pytest file.
"""

# promise_id -> ground truth. expected_verdict may use "a|b" for either-or cases.
P01_P12 = {
    "P01": {
        "promise_text": "Fentanyl State of Emergency Ordinance",
        "speaker": "Mayor Daniel Lurie",
        "expected_verdict": "kept",
        "expected_evidence": "Board vote 10 to 1, February 2025",
        "difficulty": "easy",
        "tests_what": "vote as evidence",
    },
    "P02": {
        "promise_text": "24/7 crisis stabilization center at 822 Geary St",
        "speaker": "Mayor Daniel Lurie",
        "expected_verdict": "kept",
        "expected_evidence": "opened April 28, 2025, 16 beds, 24/7, 822 Geary St",
        "difficulty": "easy",
        "tests_what": "opening date and address as evidence",
    },
    "P03": {
        "promise_text": "PermitSF reforms",
        "speaker": "Mayor Daniel Lurie",
        "expected_verdict": "kept",
        "expected_evidence": "first reforms delivered May 20, 2025, legislative package",
        "difficulty": "easy",
        "tests_what": "legislative package as evidence",
    },
    "P04": {
        "promise_text": "Golden State Valkyries sellouts",
        "speaker": "Golden State Valkyries",
        "expected_verdict": "kept",
        "expected_evidence": "10,000 season tickets by Mar 26 2025, 22 home sellouts, avg 18,064",
        "difficulty": "easy",
        "tests_what": "count as evidence, easy case",
    },
    "P05": {
        "promise_text": "1,500 new shelter beds in six months",
        "speaker": "Mayor Daniel Lurie",
        "expected_verdict": "broken",
        "expected_evidence": "plan abandoned Jul 2025, 863 beds opened by Apr 2026, net gain 403",
        "difficulty": "hard",
        "tests_what": "partial progress trap, deadline plus number must both hold",
    },
    "P06": {
        "promise_text": "Vision Zero, eliminate traffic deaths by 2024",
        "speaker": "Mayor Ed Lee",
        "expected_verdict": "broken",
        "expected_evidence": "43 traffic deaths in 2024, highest since 2005",
        "difficulty": "medium",
        "tests_what": "deadline plus count, over-reported case",
    },
    "P07": {
        "promise_text": "3.5 million new homes by 2025",
        "speaker": "Governor Gavin Newsom",
        "expected_verdict": "broken",
        "expected_evidence": "678,000+ units built from 2019, about 20 percent of goal",
        "difficulty": "medium",
        "tests_what": "large number, stretch goal language, over-reported case",
    },
    "P08": {
        "promise_text": "5 million dollars to repair homeless SRO housing",
        "speaker": "Mayor London Breed",
        "expected_verdict": "broken|stalled",
        "expected_evidence": "none spent 6+ months after money available",
        "difficulty": "medium",
        "tests_what": "money unspent, stalled when no action in 90 days",
    },
    "P09": {
        "promise_text": "PG&E underground 10,000 miles of power lines",
        "speaker": "PG&E",
        "expected_verdict": "in_progress",
        "expected_evidence": "1,200+ miles energized by Dec 2025, 1,600 by end 2026",
        "difficulty": "medium",
        "tests_what": "numeric progress, never mark kept early",
    },
    "P10": {
        "promise_text": "Giants Mission Rock, 1,200 to 1,500 homes, 40 percent affordable",
        "speaker": "San Francisco Giants",
        "expected_verdict": "in_progress",
        "expected_evidence": "future delivery, no completion yet",
        "difficulty": "medium",
        "tests_what": "future promise, no kept verdict before delivery",
    },
    "P11": {
        "promise_text": "Dead and Company final tour",
        "speaker": "Dead and Company",
        "expected_verdict": "undecided|broken",
        "expected_evidence": "exact wording decides; record reading in verdicts.reading_used",
        "difficulty": "hard",
        "tests_what": "exact wording decides the case",
    },
    "P12": {
        "promise_text": "Lime SFMTA permit",
        "speaker": "Lime",
        # Corrected 19:45 (parent): saved source contains no 2027 language;
        # extracted text (permit through Jun 30 2026, term completed) honestly
        # judges kept. Old expectation: in_progress / 2027 permit.
        "expected_verdict": "kept",
        "expected_evidence": "permit term through Jun 30 2026 completed, 3,250 fleet cap",
        "difficulty": "medium",
        "tests_what": "permit as source, permitted max vs deployment commitment",
    },
}

# N01-N12 planted specs: expected catching check + reason, per 03-validation-and-tests.md.
N01_N12 = {
    "N01": {"base": "P05", "check": "accuracy_quote", "reason": "quote none",
            "desc": "changed word in quote (beds->units), extractor output only"},
    "N02": {"base": "P05", "check": "authenticity_speaker", "reason": "speaker not in attendance",
            "desc": "wrong speaker not in roll call"},
    "N03": {"base": "P05", "check": "authenticity_hash", "reason": "hash mismatch on re-fetch",
            "desc": "changed byte in saved file after hash recorded"},
    "N04": {"base": "P05", "check": "accuracy_evidence", "reason": "missing source",
            "desc": "invented promise (5,000 beds in one month), no source file/URL/hash"},
    "N05": {"base": "P05", "check": "accuracy_quote", "reason": "quote none",
            "desc": "invented number (1,500->2,000 beds)"},
    "N06": {"base": "P05", "check": "accuracy_date", "reason": "date mismatch with source",
            "desc": "invented date (due date shifted one year)"},
    "N07": {"base": "P05", "check": "authenticity_domain", "reason": "domain not on allowlist",
            "desc": "source outside allowlist (random blog)"},
    "N08": {"base": "P05", "check": "accuracy_evidence", "reason": "news alone does not prove kept",
            "desc": "news-only source claimed as kept, capped at undecided"},
    "N09": {"base": "P05", "check": "accuracy_evidence", "reason": "press release alone does not prove kept",
            "desc": "press release claimed as kept, capped at undecided"},
    "N10": {"base": "P05", "check": "accuracy_quote", "reason": "quote none",
            "desc": "kept advocate inventing a quote, evidence row dropped"},
    "N11": {"base": "P05", "check": "accuracy_evidence", "reason": "evidence does not match promise_id",
            "desc": "broken advocate citing P06 evidence in P05 bundle, row dropped"},
    "N12": {"base": "P05", "check": "relevance_low", "reason": "restated vote is not a new promise",
            "desc": "restated vote (Board passed Fentanyl ordinance 10-1) as new promise"},
}

CLEAN_EXTRA = ["P21", "P22", "P23", "P43", "P66", "P67", "P83"]
HARD_EXTRA = ["P24", "P30", "P49", "P79", "P97"]

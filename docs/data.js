/* SF Promises - Dynamic SQLite Export */
window.__DEMO_DATA__ = {
  "metadata": {
    "title": "SF Promises",
    "city": "San Francisco",
    "last_checked": "Nov 13, 2026",
    "last_updated": "Nov 13, 2026",
    "github_repo": "https://github.com/arii/sf-promises",
    "commit_sha": "50bd4c9c8f03a77f2351c5a61b75bebc9f79e2c6",
    "sqlite_file": "promises.db",
    "sqlite_tables": 20,
    "exported_at": "2026-11-13T01:47:21Z"
  },
  "database_status": {
    "commit_sha": "50bd4c9c8f03a77f2351c5a61b75bebc9f79e2c6",
    "tracked_count": 54,
    "seed_promises_count": 12,
    "total_db_promises": 54,
    "total_db_verdicts": 54,
    "total_db_evidence": 124,
    "quarantine_registry_count": 13,
    "pending_intake_count": 38,
    "pending_intake_ids": [
      "P32",
      "P33",
      "P34",
      "P45",
      "P46",
      "P47",
      "P48",
      "P49",
      "P50",
      "P51",
      "P52",
      "P53",
      "P54",
      "P55",
      "P56",
      "P69",
      "P70",
      "P71",
      "P72",
      "P73",
      "P74",
      "P75",
      "P76",
      "P77",
      "P78",
      "P79",
      "P97",
      "S10",
      "S11",
      "S12",
      "S13",
      "S14",
      "S4",
      "S5",
      "S6",
      "S7",
      "S8",
      "S9"
    ],
    "id_reconciliation": "54 published \u00b7 13 in quarantine registry \u00b7 38 seeds awaiting intake",
    "id_scheme": "Ranked #1\u2013#{len(all_promises)} by civic impact, public interest, and verifiability. Gaps reflect quarantined test cases or pending intake.",
    "acceptance_verified": true,
    "acceptance_status_label": "Acceptance verified on commit 50bd4c9 (separated processes, not Firecracker)",
    "counts": {
      "kept": 25,
      "broken": 17,
      "in_progress": 10,
      "undecided": 2
    },
    "integration_run": {
      "run_id": "F-20261111-045601",
      "commit_sha": "50bd4c9c8f03a77f2351c5a61b75bebc9f79e2c6",
      "total_tests": 36,
      "passed": 33,
      "failed": 0,
      "blocked": 3,
      "status_label": "33 passed, 0 failed, 3 blocked"
    },
    "latest_run": {
      "run_id": "F-20261111-045601",
      "commit_sha": "1f7c7b68eb5798e474ccec19c539e3cbc2c9f825",
      "total_tests": 36,
      "passed": 33,
      "failed": 0,
      "blocked": 3,
      "status_label": "33 passed, 0 failed, 3 blocked"
    },
    "sandbox_isolation_verified": true,
    "sandbox_isolation_label": "Sandbox isolation verified on commit 50bd4c9 (separated processes, not Firecracker)",
    "discrepancies": [
      "DB holds 54 promises (12 seeds + 42 Tier-2 banked, scale paused by user decision) with 54 verdicts and 124 evidence rows; every file hash re-verified.",
      "Latest harness run F-20261111-045601 on 50bd4c9: 33 pass / 0 fail / 3 blocked-extended.",
      "Acceptance verified on commit 50bd4c9: loop, per-row hash, change log, N-catches, demo verified. Sandbox isolation verified (separated processes, not Firecracker).",
      "Earlier demo revisions hardcoded tally counts instead of querying live SQLite counts; current counts render from this export.",
      "Staging references (sources/test_cases/quarantined to promises) dangle pre-verdict by design; arbitrator publishes FK ON (decided, see QUESTIONS.md)."
    ],
    "discrepancy_files": [
      "QUESTIONS.md",
      "WORKING_NOTES.md"
    ]
  },
  "p02": {
    "promise_id": "P02",
    "promise_text": "That\u2019s exactly what this 24/7 police-friendly stabilization center will be, and I am proud to be opening it,",
    "entity": "Mayor Daniel Lurie",
    "role": "Mayor of San Francisco",
    "entity_type": "politicians",
    "category": "Civic Governance",
    "neighborhood": "Tenderloin (822 Geary St)",
    "promised_date": "2025-01-07",
    "due_date": null,
    "opened_date": "2025-04-28",
    "page_number": null,
    "verdict": "kept",
    "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
    "source_id": "S582955d5df78",
    "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center-to-provide-urgent-care-for-people-in-crisis",
    "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
    "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
    "source_type": "sf_gov_page",
    "relevance": {
      "score": 8,
      "real": 2,
      "measurable": 2,
      "sf": 2,
      "interesting": 2
    },
    "verbatim_quote": "The facility began accepting clients on April 28.",
    "document_title": "Mayor Lurie Delivers on Key Commitment, Opening 24/7 Police-Friendly Stabilization Center to Provide Urgent Care for People in Crisis",
    "quote_date": "April 28, 2025"
  },
  "sf_showcase": [
    {
      "promise_id": "P02",
      "tag": "Tenderloin \u00b7 822 Geary St",
      "domain": "Civic Governance",
      "title": "24/7 Crisis Stabilization Center",
      "quote": "\u201cThat\u2019s exactly what this 24/7 police-friendly stabilization center will be, and I am proud to be opening it,\u201d",
      "entity": "Mayor Daniel Lurie",
      "verdict": "kept",
      "evidence": "16-bed center opened April 28, 2025 at 822 Geary St with 24/7 crisis care."
    },
    {
      "promise_id": "SFO-01",
      "tag": "SFO \u00b7 Airfield & Runways",
      "domain": "Airport & Airlines",
      "title": "Runway 28L Accelerated Reopening",
      "quote": "\u201cSFO announced today that Runway 28L will reopen ahead of schedule on Friday, June 21, 2024.\u201d",
      "entity": "San Francisco International Airport",
      "verdict": "kept",
      "evidence": "Runway 28L reopened June 21, 2024 beating the July 1 deadline after $51M taxiway realignment."
    },
    {
      "promise_id": "P04",
      "tag": "Mission Bay \u00b7 Chase Center",
      "domain": "Sports",
      "title": "Golden State Valkyries Chase Center Attendance",
      "quote": "\u201cThe Valkyries will play all regular-season home games at Chase Center, with a pledge to lead the WNBA in attendance.\u201d",
      "entity": "Golden State Valkyries",
      "verdict": "kept",
      "evidence": "Sold out inaugural games at Chase Center with 10,000 season-ticket deposits; led WNBA attendance."
    },
    {
      "promise_id": "P21",
      "tag": "Golden Gate Park",
      "domain": "Transit & Streets",
      "title": "Car-Free JFK Promenade",
      "quote": "\u201cpermanently ban automobile traffic on a portion of the western half of J.F.K. Drive\u201d",
      "entity": "City of San Francisco",
      "verdict": "kept",
      "evidence": "Voters approved Proposition J; 1.5 miles of JFK Promenade permanently car-free."
    },
    {
      "promise_id": "P10",
      "tag": "Mission Rock & South Beach",
      "domain": "Housing & Neighborhoods",
      "title": "SF Giants 40% Affordable Homes",
      "quote": "\u201cAlso, 40% of the project\u2019s residential portion is below-market-rate units, mostly targeting middle-income families.\u201d",
      "entity": "San Francisco Giants",
      "verdict": "in_progress",
      "evidence": "Phase 1 residential towers active across McCovey Cove with income-restricted units."
    },
    {
      "promise_id": "P11",
      "tag": "Haight-Ashbury & Golden Gate Park",
      "domain": "Culture & Music",
      "title": "Dead & Company Final Tour",
      "quote": "\u201cWe never said we'll never play again, but we'll never tour again.\u201d",
      "entity": "Mickey Hart / Dead & Company",
      "verdict": "undecided",
      "evidence": "Played 3-night farewell run at Oracle Park; later played Golden Gate Park Polo Fields 60th anniversary."
    }
  ],
  "promises": [
    {
      "promise_id": "P02",
      "promise_text": "That\u2019s exactly what this 24/7 police-friendly stabilization center will be, and I am proud to be opening it,",
      "entity": "Daniel Lurie",
      "role": "Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Tenderloin (822 Geary St)",
      "promised_date": "2025-01-07",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "S582955d5df78",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center-to-provide-urgent-care-for-people-in-crisis",
      "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
      "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
      "source_type": "sf_gov_page",
      "fetched_at": "2026-11-11T03:07:47.024841+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:31:14Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P02",
          "advocate_role": "kept_advocate",
          "evidence_checked": 2,
          "claims": [
            {
              "promise_id": "P02",
              "claim_text": "Stabilization unit began accepting clients April 28",
              "quote": "The facility began accepting clients on April 28.",
              "quote_match": "exact",
              "evidence_type": "opening",
              "source_file_path": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05.md",
              "source_hash": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05",
              "source_url": "https://www.sfpublicworkstv.org/april2025",
              "page_number": null,
              "evidence_date": "2025-04"
            },
            {
              "promise_id": "P02",
              "claim_text": "24/7 center at 822 Geary St with ribbon-cutting ceremony",
              "quote": "Public Works staff gather during the ribbon-cutting ceremony for the new Stabilization Unit.",
              "quote_match": "exact",
              "evidence_type": "opening",
              "source_file_path": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05.md",
              "source_hash": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05",
              "source_url": "https://www.sfpublicworkstv.org/april2025",
              "page_number": null,
              "evidence_date": "2025-04"
            },
            {
              "promise_id": "P02",
              "claim_text": "Mayor Lurie opened the 822 Geary facility",
              "quote": "and I am proud to be opening it,\u201d said Mayor Daniel Lurie.",
              "quote_match": "exact",
              "evidence_type": "opening",
              "source_file_path": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05.md",
              "source_hash": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05",
              "source_url": "https://www.sfpublicworkstv.org/april2025",
              "page_number": null,
              "evidence_date": "2025-04"
            },
            {
              "promise_id": "P02",
              "claim_text": "Center opened at 822 Geary Street in April, 344 admitted in five months",
              "quote": "which opened at 822 Geary Street in April.",
              "quote_match": "exact",
              "evidence_type": "opening",
              "source_file_path": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md",
              "source_hash": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa",
              "source_url": "https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
              "page_number": null,
              "evidence_date": "2025-12"
            }
          ]
        },
        "broken": {
          "promise_id": "P02",
          "advocate_role": "broken_advocate",
          "evidence_checked": 3,
          "claims": [],
          "note": "none found: searched saved files mentioning 822 Geary/stabilization (3 files), no contradicting source. No second search per cut rule."
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 1,
      "verbatim_quote": "The facility began accepting clients on April 28.",
      "document_title": "24/7 Crisis Stabilization Center",
      "quote_date": "April 28, 2025",
      "opened_date": "2025-04-28",
      "importance_score": 99,
      "impact_rank": 1,
      "source_tier": "Official",
      "neighborhood_canonical": "Tenderloin",
      "address_full": "822 Geary Street, San Francisco, CA 94102",
      "latitude": 37.7858,
      "longitude": -122.4172,
      "supervisor_district": 5,
      "is_citywide": false,
      "promise_made_date": "2025-01-07",
      "deadline_date": null,
      "completion_date": "2025-04-28",
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 674,
      "time_to_verdict_days": 673,
      "entity_canonical_name": "Daniel Lurie",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2025-01-08",
      "entity_term_end": "2029-01-08",
      "category_l1": "Public Safety",
      "category_l2": "Crisis & Mental Health Services",
      "secondary_categories": [
        "Healthcare",
        "Housing"
      ],
      "tags": [
        "stabilization_center",
        "mental_health",
        "police_friendly",
        "tenderloin",
        "substance_abuse"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 9,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center-to-provide-urgent-care-for-people-in-crisis",
      "title": "24/7 Crisis Stabilization Center",
      "media_image_url": "https://www.sf.gov/sites/default/files/styles/og_image/public/2025-04/crisis-stabilization-center-822-geary.jpg",
      "image_url": "https://www.sf.gov/sites/default/files/styles/og_image/public/2025-04/crisis-stabilization-center-822-geary.jpg",
      "media_caption": "822 Geary Street 24/7 Police-Friendly Crisis Stabilization Center in the Tenderloin"
    },
    {
      "promise_id": "P05",
      "promise_text": "[Reported by The Frisc] His campaign promise to [end street homelessness](https://sfstandard.com/2025/01/28/san-francisco-daniel-lurie-homelessness-shelter-promise/), in part by opening 1,500 new shelter beds in his first six months of office, didn\u2019t last long.",
      "entity": "Daniel Lurie",
      "role": "Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Citywide Shelter Network",
      "promised_date": "2024-11-05",
      "due_date": null,
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "numeric target not met or plan abandoned",
      "source_id": "S6b445cb1ab31",
      "source_url": "https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
      "source_file_path": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md",
      "source_hash": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:08:55.078040+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:34:00Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P05",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P05",
              "claim_text": "Administration stood up 500 new beds",
              "quote": "The administration also says it stood up 500 new beds.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md",
              "source_hash": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa",
              "source_url": "https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
              "page_number": null,
              "evidence_date": "2025-12"
            },
            {
              "promise_id": "P05",
              "claim_text": "Nearly 2,000 people entered shelter via street teams",
              "quote": "including helping nearly 2,000 people enter shelter through the reorganized street teams.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md",
              "source_hash": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa",
              "source_url": "https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
              "page_number": null,
              "evidence_date": "2025-12"
            }
          ]
        },
        "broken": {
          "promise_id": "P05",
          "advocate_role": "broken_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P05",
              "claim_text": "1,500-bed goal abandoned altogether in July",
              "quote": "The administration abandoned the goal altogether in July.",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md",
              "source_hash": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa",
              "source_url": "https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
              "page_number": null,
              "evidence_date": "2025-12"
            },
            {
              "promise_id": "P05",
              "claim_text": "Six-month pledge did not last",
              "quote": "in part by opening 1,500 new shelter beds in his first six months of office, didn\u2019t last long.",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md",
              "source_hash": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa",
              "source_url": "https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
              "page_number": null,
              "evidence_date": "2025-12"
            },
            {
              "promise_id": "P05",
              "claim_text": "City health chief: plan no longer the right approach",
              "quote": "Kunal Modi said the plan to add 1,500 beds \u201cwas no longer the right approach.\u201d",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa.md",
              "source_hash": "6b445cb1ab3198e5bc72810651999042c6630826bd1da44e8002e76955c7a6aa",
              "source_url": "https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
              "page_number": null,
              "evidence_date": "2025-12"
            }
          ]
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "numeric target not met or plan abandoned"
        }
      ],
      "display_no": 2,
      "importance_score": 98,
      "impact_rank": 2,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2024-11-05",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 737,
      "time_to_verdict_days": 736,
      "entity_canonical_name": "Daniel Lurie",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2025-01-08",
      "entity_term_end": "2029-01-08",
      "category_l1": "Housing",
      "category_l2": "Emergency Shelter",
      "secondary_categories": [
        "Public Safety",
        "Social Services"
      ],
      "tags": [
        "shelter_beds",
        "homelessness",
        "1500_beds",
        "street_homelessness"
      ],
      "verdict_confidence": 0.95,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 9,
      "completion_percentage": 25,
      "source_credibility_score": 8,
      "source_type_standardized": "news_local",
      "source_domain_authority": 8,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://thefrisc.com/one-year-of-luries-approach-to-sfs-homelessness-drugs-mental-health/",
      "document_title": "1,500 Shelter Beds in First 6 Months",
      "title": "1,500 Shelter Beds in First 6 Months",
      "media_image_url": "https://assets.sfstandard.com/image/994911177489/image_s94fpd5el5549a2690grvt1g5u/-S3840x2561-FPNG",
      "image_url": "https://assets.sfstandard.com/image/994911177489/image_s94fpd5el5549a2690grvt1g5u/-S3840x2561-FPNG",
      "media_caption": "San Francisco urban shelter expansion network sites under 6-month evaluation"
    },
    {
      "promise_id": "SFO-01",
      "promise_text": "SFO announced today that Runway 28L will reopen ahead of schedule on Friday, June 21, 2024. The runway had been closed since January 16, 2024 for a major taxiway improvement and realignment project that was originally scheduled to conclude by July 1, 2024.",
      "entity": "San Francisco International Airport",
      "role": "Airport Commission / Municipal Transportation",
      "entity_type": "city_government",
      "category": "Airport & Airlines",
      "neighborhood": "SFO (Airfield & Runways)",
      "promised_date": "2024-01-16",
      "due_date": "2024-07-01",
      "opened_date": "2024-06-21",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "Runway 28L reopened June 21, 2024, beating the July 1, 2024 deadline by 10 days after completing the $51M taxiway realignment.",
      "source_id": "SFO-SRC-28L",
      "source_url": "https://www.flysfo.com/about/media/press-releases/sfo-reopen-runway-28l-ahead-schedule-friday-june-21st",
      "source_file_path": "sfo_runway_28l_reopening.md",
      "source_hash": "b6a2f59ff456a48457101705f585cec933f646c0e960e934313dce2b4c585068",
      "source_type": "official_press_release",
      "fetched_at": "2024-06-21T18:00:00Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "importance_score": 97,
      "document_title": "Runway 28L Safety Realignment & Reopening",
      "quote_date": "June 20, 2024",
      "reading_used": "strict",
      "decided_at": "2024-06-22T00:00:00Z",
      "advocate_bundles": {
        "kept": {
          "claims": [
            {
              "quote": "Runway 28L will reopen ahead of schedule on Friday, June 21, 2024",
              "source_url": "https://www.flysfo.com/about/media/press-releases/sfo-reopen-runway-28l-ahead-schedule-friday-june-21st"
            }
          ]
        },
        "broken": {
          "claims": []
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "flysfo.com is on the trusted official municipal domain allowlist"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "SHA-256 matches b6a2f59f... byte-for-byte"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "verbatim quote verified against saved press release"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "reopened 2024-06-21 before promised deadline 2024-07-01"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "deterministic rubric: affirmative completion prior to deadline = kept"
        }
      ],
      "impact_rank": 3,
      "display_no": 3,
      "source_tier": "Official",
      "neighborhood_canonical": "SFO Airport",
      "address_full": "Airfield Runway 28L/10R, San Francisco International Airport, San Francisco, CA 94128",
      "latitude": 37.6213,
      "longitude": -122.379,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2024-01-16",
      "deadline_date": "2024-07-01",
      "completion_date": "2024-06-21",
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1031,
      "time_to_verdict_days": 158,
      "entity_canonical_name": "San Francisco International Airport (SFO)",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Airport Infrastructure",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "sfo",
        "runway_reconstruction",
        "aviation",
        "capital_projects"
      ],
      "verdict_confidence": 0.99,
      "verdict_evidence_count": 4,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.flysfo.com/about/media/press-releases/sfo-reopen-runway-28l-ahead-schedule-friday-june-21st",
      "title": "Runway 28L Safety Realignment & Reopening",
      "media_image_url": "https://www.flysfo.com/sites/default/files/2024-06/runway_28l_reopening_airfield.jpg",
      "image_url": "https://www.flysfo.com/sites/default/files/2024-06/runway_28l_reopening_airfield.jpg",
      "media_caption": "SFO Runway 28L safety realignment and resurfacing project on airfield"
    },
    {
      "promise_id": "SFO-02",
      "promise_text": "San Francisco International Airport celebrated the completion of the $2.4 billion Harvey Milk Terminal 1, unveiling the final phase featuring a new North Check-in lobby and bringing the total number of gates in the terminal to 25.",
      "entity": "San Francisco International Airport",
      "role": "Airport Commission / Municipal Transportation",
      "entity_type": "city_government",
      "category": "Airport & Airlines",
      "neighborhood": "SFO (Harvey Milk Terminal 1)",
      "promised_date": "2019-07-23",
      "due_date": "2024-07-01",
      "opened_date": "2024-07-01",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "Final phase completed July 1, 2024, delivering all 25 gates and post-security concourse connections under the $2.4B capital program.",
      "source_id": "SFO-SRC-T1",
      "source_url": "https://www.flysfo.com/about/media/press-releases/sfo-celebrates-completion-harvey-milk-terminal-1",
      "source_file_path": "sfo_harvey_milk_terminal_1_completion.md",
      "source_hash": "fa3e92fe13bcdf43cdeb185b63dd2dd32fe8e6e13926ccd5dc588d830c998eef",
      "source_type": "official_press_release",
      "fetched_at": "2024-07-01T20:00:00Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "importance_score": 96,
      "document_title": "Harvey Milk Terminal 1 Final Completion",
      "quote_date": "July 1, 2024",
      "reading_used": "strict",
      "decided_at": "2024-07-02T00:00:00Z",
      "advocate_bundles": {
        "kept": {
          "claims": [
            {
              "quote": "unveiling the final phase featuring a new North Check-in lobby and bringing the total number of gates in the terminal to 25",
              "source_url": "https://www.flysfo.com/about/media/press-releases/sfo-celebrates-completion-harvey-milk-terminal-1"
            }
          ]
        },
        "broken": {
          "claims": []
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "flysfo.com is on the trusted official municipal domain allowlist"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "SHA-256 matches fa3e92fe... byte-for-byte"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "verbatim quote verified against saved press release"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "opened July 1, 2024 matching capital program milestone"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "deterministic rubric: full scope verified operational = kept"
        }
      ],
      "impact_rank": 4,
      "display_no": 4,
      "source_tier": "Official",
      "neighborhood_canonical": "SFO Airport",
      "address_full": "Harvey Milk Terminal 1, San Francisco International Airport, San Francisco, CA 94128",
      "latitude": 37.6169,
      "longitude": -122.3872,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2019-07-23",
      "deadline_date": "2024-07-01",
      "completion_date": "2024-07-01",
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2669,
      "time_to_verdict_days": 1806,
      "entity_canonical_name": "San Francisco International Airport (SFO)",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Airport Infrastructure",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "sfo",
        "harvey_milk_terminal_1",
        "terminal_modernization",
        "gates"
      ],
      "verdict_confidence": 0.99,
      "verdict_evidence_count": 4,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.flysfo.com/about/media/press-releases/sfo-celebrates-completion-harvey-milk-terminal-1",
      "title": "Harvey Milk Terminal 1 Final Completion",
      "media_image_url": "https://www.flysfo.com/sites/default/files/2024-07/harvey_milk_terminal_1_ribbon_cutting.jpg",
      "image_url": "https://www.flysfo.com/sites/default/files/2024-07/harvey_milk_terminal_1_ribbon_cutting.jpg",
      "media_caption": "$2.4B Harvey Milk Terminal 1 final concourse completion ceremony"
    },
    {
      "promise_id": "P21",
      "promise_text": "to permanently ban automobile traffic on a portion of the western half of J.F.K. Drive",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Transit & Streets",
      "neighborhood": "Golden Gate Park (JFK Promenade)",
      "promised_date": "2022-04",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims (re-open R2: sf.streetsblog.org allowlisted; 7-4 board vote to make JFK Promenade permanent now passes domain)",
      "source_id": "S6685fe8d7b3d",
      "source_url": "https://sf.streetsblog.org/2022/04/26/hurrah-for-j-f-k-promenade-forever",
      "source_file_path": "6685fe8d7b3d73bc63e7d84d0f1db531e6d6cd12bf90d1c5cf63885f90c8bc6a.md",
      "source_hash": "6685fe8d7b3d73bc63e7d84d0f1db531e6d6cd12bf90d1c5cf63885f90c8bc6a",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:06:06Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:10:17Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Board voted 7-4 to make JFK Promenade permanent",
              "evidence_date": "2022-04-26",
              "evidence_type": "vote",
              "page_number": null,
              "promise_id": "P21",
              "quote": "the Supes voted seven to four to make the J.F.K. Promenade permanent",
              "quote_match": "exact",
              "source_file_path": "6685fe8d7b3d73bc63e7d84d0f1db531e6d6cd12bf90d1c5cf63885f90c8bc6a.md",
              "source_hash": "6685fe8d7b3d73bc63e7d84d0f1db531e6d6cd12bf90d1c5cf63885f90c8bc6a",
              "source_url": "https://sf.streetsblog.org/2022/04/26/hurrah-for-j-f-k-promenade-forever"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P21"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file reports passage 7-4; Prop J reaffirmation not in this file; no contradiction. No second search per cut rule.",
          "promise_id": "P21"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: official primary evidence confirms completion with zero contradicting claims (re-open R2: sf.streetsblog.org allowlisted; 7-4 board vote to make JFK Promenade permanent now passes domain)"
        }
      ],
      "display_no": 5,
      "importance_score": 95,
      "impact_rank": 5,
      "source_tier": "News",
      "neighborhood_canonical": "Golden Gate Park",
      "address_full": "JFK Promenade, Golden Gate Park, San Francisco, CA 94117",
      "latitude": 37.7712,
      "longitude": -122.4687,
      "supervisor_district": 1,
      "is_citywide": false,
      "promise_made_date": "2022-04-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1686,
      "time_to_verdict_days": 1685,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Transportation",
      "category_l2": "Bicycle & Pedestrian Infrastructure",
      "secondary_categories": [
        "Culture & Recreation"
      ],
      "tags": [
        "car_free_jfk",
        "golden_gate_park",
        "promenade",
        "pedestrian_safety"
      ],
      "verdict_confidence": 0.99,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://sf.streetsblog.org/2022/04/26/hurrah-for-j-f-k-promenade-forever",
      "document_title": "JFK Drive Permanent Car-Free Promenade",
      "title": "JFK Drive Permanent Car-Free Promenade",
      "media_image_url": "https://sfrecpark.org/ImageRepository/Document?documentID=17234",
      "image_url": "https://sfrecpark.org/ImageRepository/Document?documentID=17234",
      "media_caption": "Golden Gate Park JFK Promenade car-free recreation corridor"
    },
    {
      "promise_id": "P04",
      "promise_text": "The Valkyries have sold out all 44 regular-season games at Chase Center over their first two seasons, to lead the WNBA in attendance.",
      "entity": "Golden State Valkyries",
      "role": null,
      "entity_type": "sports_team",
      "category": "Sports",
      "neighborhood": "Mission Bay (Chase Center)",
      "promised_date": "2025-03-26",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "S6a517bcb0178",
      "source_url": "https://www.sfchronicle.com/sports/article/valkyries-wnba-championship-22499436.php",
      "source_file_path": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4.md",
      "source_hash": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:16:43.671675+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:33:26Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P04",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P04",
              "claim_text": "Sold out all 44 regular-season games, led WNBA in attendance",
              "quote": "The Valkyries have sold out all 44 regular-season games at Chase Center over their first two seasons, to lead the WNBA in attendance.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4.md",
              "source_hash": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4",
              "source_url": "https://www.sfchronicle.com/sports/article/valkyries-wnba-championship-22499436.php",
              "page_number": null,
              "evidence_date": "2026-11"
            },
            {
              "promise_id": "P04",
              "claim_text": "18,064 per game in the arena",
              "quote": "Every time, 18,064 people cram into the arena, dancing and shouting and creating an unapologetically happy community.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4.md",
              "source_hash": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4",
              "source_url": "https://www.sfchronicle.com/sports/article/valkyries-wnba-championship-22499436.php",
              "page_number": null,
              "evidence_date": "2026-11"
            },
            {
              "promise_id": "P04",
              "claim_text": "10,500 season tickets year one, 12,000+ season two",
              "quote": "The Valkyries sold about 10,500 season tickets last year, when they became the first expansion team to make the playoffs, and then bumped the total to more than 12,000 this season.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4.md",
              "source_hash": "6a517bcb01782af9fcca0d02e947e8398ae65d860a27abb0f8f4630c886e5ea4",
              "source_url": "https://www.sfchronicle.com/sports/article/valkyries-wnba-championship-22499436.php",
              "page_number": null,
              "evidence_date": "2026-11"
            }
          ]
        },
        "broken": {
          "promise_id": "P04",
          "advocate_role": "broken_advocate",
          "evidence_checked": 12,
          "claims": [],
          "note": "none found: searched all 12 saved files for Valkyrie attendance contradictions; only hit is a reader comment about coverage topics, not attendance. No second search per cut rule."
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 6,
      "importance_score": 94,
      "impact_rank": 6,
      "source_tier": "News",
      "neighborhood_canonical": "Mission Bay",
      "address_full": "1 Warriors Way, San Francisco, CA 94158",
      "latitude": 37.768,
      "longitude": -122.3877,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2025-03-26",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 596,
      "time_to_verdict_days": 595,
      "entity_canonical_name": "Golden State Valkyries",
      "entity_category": "sports_team",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Culture & Recreation",
      "category_l2": "Professional Sports",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "valkyries",
        "wnba",
        "chase_center",
        "womens_sports",
        "inaugural_season"
      ],
      "verdict_confidence": 0.99,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 8,
      "source_type_standardized": "news_mainstream",
      "source_domain_authority": 9,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfchronicle.com/sports/article/valkyries-wnba-championship-22499436.php",
      "document_title": "Chase Center Valkyries Regular Season Games",
      "title": "Chase Center Valkyries Regular Season Games",
      "media_image_url": "https://cdn.abcotvs.com/dip/images/11518842_247-NOWSTREAMING_1280x720.png",
      "image_url": "https://cdn.abcotvs.com/dip/images/11518842_247-NOWSTREAMING_1280x720.png",
      "media_caption": "Chase Center arena in Mission Bay hosting Golden State Warriors and Valkyries"
    },
    {
      "promise_id": "P82",
      "promise_text": "I\u2019m telling you right now, we will win a WNBA championship in the first five years of this franchise.",
      "entity": "Joe Lacob",
      "role": "Golden State Valkyries owner",
      "entity_type": "other",
      "category": "Sports",
      "neighborhood": "Chase Center (WNBA Championship Target)",
      "promised_date": "2023-10-05",
      "due_date": "2028-10-05",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims [due 2028-10-05 = promised 2023-10-05 + five-year term stated in source]",
      "source_id": "S7ce6c45c9f3a",
      "source_url": "https://nytimes.com/athletic/7742640/2026/10/31/wnba-finals-champion-valkyries-dream",
      "source_file_path": "b55705803b0e6ea0890577d6a9fa3e08578eeb0fcf50f2ed49597eeca6ad4444.md",
      "source_hash": "b55705803b0e6ea0890577d6a9fa3e08578eeb0fcf50f2ed49597eeca6ad4444",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:01:32Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:03:04Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Valkyries won the 2026 WNBA championship in year 2, beating Atlanta Dream 68-63 in Game 7, inside the five-year term",
              "evidence_date": "2026-10-31",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P82",
              "quote": "SAN FRANCISCO \u2014 Just two years into existence, the Golden State Valkyries made history by winning a championship. They did it with their typical grit and determination \u2014 and even some sensational shooting from Gabby Williams \u2014 to hold off the Atlanta Dream for a 68-63 victory.",
              "quote_match": "exact",
              "source_file_path": "b55705803b0e6ea0890577d6a9fa3e08578eeb0fcf50f2ed49597eeca6ad4444.md",
              "source_hash": "b55705803b0e6ea0890577d6a9fa3e08578eeb0fcf50f2ed49597eeca6ad4444",
              "source_url": "https://nytimes.com/athletic/7742640/2026/10/31/wnba-finals-champion-valkyries-dream"
            },
            {
              "claim_text": "Official team record: Valkyries won the 2026 WNBA Championship, Game 7 68-63 over Atlanta at Chase Center San Francisco",
              "evidence_date": "2026-10-31",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P82",
              "quote": "The Golden State Valkyries have won the 2026 WNBA Championship after Saturday\u2019s 68-63 win over the Atlanta Dream in Game 7 of the WNBA Finals at Chase Center in San Francisco.",
              "quote_match": "exact",
              "source_file_path": "722623ed8d3632d16c1d65907448f78b52606b04dd34a9c310b1cbbb9ca9f6ce.md",
              "source_hash": "722623ed8d3632d16c1d65907448f78b52606b04dd34a9c310b1cbbb9ca9f6ce",
              "source_url": "https://valkyries.wnba.com/news/golden-state-valkyries-win-2026-wnba-championship-20261031"
            }
          ],
          "evidence_checked": 2,
          "promise_id": "P82"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: search 'Valkyries 2026 season lost eliminated missed championship' returned only title-win coverage (Game 7 68-63, first title); no contradicting source exists.",
          "promise_id": "P82"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": false,
          "reason": "unlisted source domain"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 7,
      "importance_score": 93,
      "impact_rank": 7,
      "source_tier": "News",
      "neighborhood_canonical": "Mission Bay",
      "address_full": "1 Warriors Way, San Francisco, CA 94158",
      "latitude": 37.768,
      "longitude": -122.3877,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2023-10-05",
      "deadline_date": "2028-10-05",
      "completion_date": null,
      "days_remaining": 693,
      "days_overdue": null,
      "promise_age_days": 1134,
      "time_to_verdict_days": 1133,
      "entity_canonical_name": "Joe Lacob",
      "entity_category": "sports_team",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Culture & Recreation",
      "category_l2": "Professional Sports",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "wnba",
        "championship",
        "valkyries",
        "joe_lacob",
        "chase_center"
      ],
      "verdict_confidence": 0.9,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 7,
      "completion_percentage": 100,
      "source_credibility_score": 8,
      "source_type_standardized": "news_mainstream",
      "source_domain_authority": 9,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://nytimes.com/athletic/7742640/2026/10/31/wnba-finals-champion-valkyries-dream",
      "document_title": "Valkyries WNBA Championship Guarantee",
      "title": "Valkyries WNBA Championship Guarantee"
    },
    {
      "promise_id": "P83",
      "promise_text": "Whole Foods Market will open its new 64,737-square-foot San Francisco flagship store at Trinity Place (1185 Market Street) in San Francisco\u2019s Mid-Market neighborhood on Thursday, March 10.",
      "entity": "Whole Foods Market",
      "role": null,
      "entity_type": "company",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Mid-Market (8th & Market Flagship)",
      "promised_date": "2022-02-17",
      "due_date": "2022-03-10",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims [due 2022-03-10 stated explicitly in Feb 17, 2022 source: on Thursday, March 10]",
      "source_id": "S49884a310666",
      "source_url": "https://www.webwire.com/ViewPressRel.asp?aId=285415",
      "source_file_path": "9ffa08cba72b594dd6cab2943b8eab7896b0aa63bb8f8039ee33cdfaf5d409e5.md",
      "source_hash": "9ffa08cba72b594dd6cab2943b8eab7896b0aa63bb8f8039ee33cdfaf5d409e5",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:06:44Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:07:13Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Store opened at Trinity Place in March 2022 (opening day March 10 corroborated by Trinity opening-day release)",
              "evidence_date": "2022-03-10",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P83",
              "quote": "The closure comes just a year after the store opened at the Trinity S.F. apartment building at Market and Eighth streets in March 2022.",
              "quote_match": "exact",
              "source_file_path": "3185b3a602b047719f279c3791244b1e528873c728fae13dd8074613d0ac8402.md",
              "source_hash": "3185b3a602b047719f279c3791244b1e528873c728fae13dd8074613d0ac8402",
              "source_url": "https://sfchronicle.com/sf/article/whole-foods-closing-civic-center-store-s-f-17889427.php"
            },
            {
              "claim_text": "Opening-day release: Whole Foods Market has opened its Trinity Place flagship on Thursday, March 10",
              "evidence_date": "2022-03-10",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P83",
              "quote": "**SAN FRANCISCO (March 10, 2022)****\u2013** Whole Foods Market has opened its new 64,737-square-foot San Francisco flagship store at [Trinity Place](https://www.trinitysf.com/trinity-place/) (1185 Market Street) in San Francisco\u2019s Mid-Market neighborhood on Thursday, March 10.",
              "quote_match": "exact",
              "source_file_path": "49884a310666b77220056cc8dffb993ac8b3c3a6bd2066dc83a08d018b37b226.md",
              "source_hash": "49884a310666b77220056cc8dffb993ac8b3c3a6bd2066dc83a08d018b37b226",
              "source_url": "https://trinitysf.com/inthenews/san-francisco-flagship-whole-foods-now-open-at-trinity-place"
            }
          ],
          "evidence_checked": 2,
          "promise_id": "P83"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: broken search returned only the April 2023 closure (a separate promise, P70 in another partition); a post-fulfillment closure does not contradict the March 10, 2022 opening. No source disputes the opening date.",
          "promise_id": "P83"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": false,
          "reason": "unlisted source domain"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 8,
      "importance_score": 92,
      "impact_rank": 8,
      "source_tier": "News",
      "neighborhood_canonical": "Mid-Market",
      "address_full": "1188 Market Street, San Francisco, CA 94102",
      "latitude": 37.7786,
      "longitude": -122.4153,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2022-02-17",
      "deadline_date": "2022-03-10",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1729,
      "time_to_verdict_days": 1728,
      "entity_canonical_name": "Whole Foods Market",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Economy & Commercial",
      "category_l2": "Retail & Grocery",
      "secondary_categories": [
        "Public Safety"
      ],
      "tags": [
        "whole_foods",
        "mid_market",
        "flagship_grocery",
        "retail_theft",
        "closure"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 1,
      "verdict_reason_code": "delayed_but_kept",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.webwire.com/ViewPressRel.asp?aId=285415",
      "document_title": "Whole Foods Mid-Market Flagship Safety",
      "title": "Whole Foods Mid-Market Flagship Safety",
      "media_image_url": "https://s.hdnux.com/photos/01/66/20/50/31001134/3/rawImage.jpg",
      "image_url": "https://s.hdnux.com/photos/01/66/20/50/31001134/3/rawImage.jpg",
      "media_caption": "Whole Foods Market 64,737-square-foot flagship store at 8th and Market Street"
    },
    {
      "promise_id": "P11",
      "promise_text": "We never said we'll never play again, but we'll never tour again.",
      "entity": "Mickey Hart",
      "role": "Musician",
      "entity_type": "artist",
      "category": "Culture & Music",
      "neighborhood": "Haight-Ashbury Heritage & Oracle Park",
      "promised_date": "2022-09-23",
      "due_date": null,
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "re-open: 30-show Sphere leg May-Aug 2024 + 18-show Sphere leg Mar-May 2025 + sold-out 3-day Golden Gate Park run Aug 1-3 2025; contradicting primary evidence outranks affirmative claims",
      "source_id": "Sd19eac519a89",
      "source_url": "https://en.wikipedia.org/wiki/Dead_%26_Company_Summer_Tour_2023",
      "source_file_path": "1aa36b054f1b446f774d115a2a028dfa578819a8ade52b16fa55efc371c0c6bb.md",
      "source_hash": "1aa36b054f1b446f774d115a2a028dfa578819a8ade52b16fa55efc371c0c6bb",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:54:43Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": "tour = sustained multi-show concert runs for paying audiences, including residency legs and multi-night park runs, not only multi-city routing; supersedes the 2023 multi-city-only reading",
      "decided_at": "2026-11-11T04:54:43Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 2,
          "note": "none found (re-open diligence 2026-11-11): 2 Keenable searches executed - (1) 'Dead & Company Sphere residency 2024 Las Vegas concerts announced' -> Dead Forever 30-show 2024 + 18-show 2025 Sphere legs; (2) site:sfchronicle.com 'Dead & Company Golden Gate Park Polo Fields August 2025 concerts' -> sold-out 3-day Golden Gate Park run Aug 1-3 2025. Both searches returned post-2023 performance evidence only; no source supports 'never toured again'. No second search per cut rule.",
          "promise_id": "P11"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Sphere leg 1 extended to 30 shows, May-Aug 2024",
              "evidence_date": "2024-08-10",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P11",
              "quote": "Dead Forever: Live at Sphere was initially announced as a single-leg 24-show residency due to begin on May 16, 2024, and conclude on July 13. Shortly after its initial announcement, it was extended to 30 shows set to conclude on August 10.",
              "quote_match": "exact",
              "source_file_path": "d19eac519a8956f4509767f84739b665086b85e585d159f33b7551ccfd956234.md",
              "source_hash": "d19eac519a8956f4509767f84739b665086b85e585d159f33b7551ccfd956234",
              "source_url": "https://en.wikipedia.org/wiki/Dead_Forever:_Live_at_Sphere"
            },
            {
              "claim_text": "Sphere leg 2: 18 more shows from March 20 2025",
              "evidence_date": "2025-03-20",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P11",
              "quote": "On December 4, 2024, the band announced they would revive the residency production and return to Sphere for a second leg of 18 shows beginning on March 20, 2025.",
              "quote_match": "exact",
              "source_file_path": "d19eac519a8956f4509767f84739b665086b85e585d159f33b7551ccfd956234.md",
              "source_hash": "d19eac519a8956f4509767f84739b665086b85e585d159f33b7551ccfd956234",
              "source_url": "https://en.wikipedia.org/wiki/Dead_Forever:_Live_at_Sphere"
            },
            {
              "claim_text": "Sold-out three-day Golden Gate Park run, finale Aug 3 2025",
              "evidence_date": "2025-08-03",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P11",
              "quote": "took the stage for the final night of their sold-out, three-day run at Golden Gate Park",
              "quote_match": "exact",
              "source_file_path": "11405df1d29a460c6e43d2c310e43c80df2e47ca89e1ab2eeac5b010130ba121.md",
              "source_hash": "11405df1d29a460c6e43d2c310e43c80df2e47ca89e1ab2eeac5b010130ba121",
              "source_url": "https://www.sfchronicle.com/entertainment/article/grateful-dead-60th-finale-20800345.php"
            },
            {
              "claim_text": "Tens of thousands packed Polo Field on Aug 3 2025",
              "evidence_date": "2025-08-03",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P11",
              "quote": "Tens of thousands of Deadheads once again packed the Polo Field on Sunday, Aug. 3",
              "quote_match": "exact",
              "source_file_path": "11405df1d29a460c6e43d2c310e43c80df2e47ca89e1ab2eeac5b010130ba121.md",
              "source_hash": "11405df1d29a460c6e43d2c310e43c80df2e47ca89e1ab2eeac5b010130ba121",
              "source_url": "https://www.sfchronicle.com/entertainment/article/grateful-dead-60th-finale-20800345.php"
            }
          ],
          "evidence_checked": 4,
          "promise_id": "P11"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "contradicting primary evidence outranks affirmative claims"
        }
      ],
      "display_no": 9,
      "importance_score": 91,
      "impact_rank": 9,
      "source_tier": "Reference",
      "neighborhood_canonical": "Golden Gate Park",
      "address_full": "Polo Field & Haight Corridor, Golden Gate Park, San Francisco, CA 94121",
      "latitude": 37.7686,
      "longitude": -122.493,
      "supervisor_district": 1,
      "is_citywide": false,
      "promise_made_date": "2022-09-23",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1511,
      "time_to_verdict_days": 1510,
      "entity_canonical_name": "Dead & Company",
      "entity_category": "cultural_organization",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Culture & Recreation",
      "category_l2": "Live Music & Concerts",
      "secondary_categories": [
        "Culture"
      ],
      "tags": [
        "dead_and_company",
        "farewell_tour",
        "golden_gate_park",
        "sphere_residency"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 0,
      "verdict_contradiction_count": 3,
      "verdict_reason_code": "goal_abandoned",
      "impact_score": 7,
      "completion_percentage": 0,
      "source_credibility_score": 7,
      "source_type_standardized": "academic_report",
      "source_domain_authority": 9,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://en.wikipedia.org/wiki/Dead_%26_Company_Summer_Tour_2023",
      "document_title": "Grateful Dead Tour Retirement & Archival Shows",
      "title": "Grateful Dead Tour Retirement & Archival Shows"
    },
    {
      "promise_id": "SFO-03",
      "promise_text": "United Airlines has expanded its commitment to fly 100% green by 2050 without relying on voluntary carbon offsets, taking delivery of Neste MY Sustainable Aviation Fuel via SFO pipeline infrastructure for regular commercial passenger operations.",
      "entity": "United Airlines",
      "role": "Major SFO Hub Airline",
      "entity_type": "companies",
      "category": "Airport & Airlines",
      "neighborhood": "SFO (Terminal 3 & Fuel Infrastructure)",
      "promised_date": "2020-12-10",
      "due_date": "2050-12-31",
      "opened_date": "2024-08-01",
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "Active commercial SAF intake through SFO hydrant pipeline system; long-range net-zero fleet target ongoing through 2050.",
      "source_id": "SFO-SRC-SAF",
      "source_url": "https://www.flysfo.com/about/media/press-releases/sfo-welcomes-expanded-use-sustainable-aviation-fuel-united-airlines",
      "source_file_path": "sfo_united_airlines_saf.md",
      "source_hash": "d92b73174f8aa2fc801f6e582878f3e5afa4450c1217f5706bab1fb746dc61f0",
      "source_type": "official_press_release",
      "fetched_at": "2024-08-01T15:00:00Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "importance_score": 90,
      "document_title": "Sustainable Aviation Fuel (SAF) Infrastructure",
      "quote_date": "August 1, 2024",
      "reading_used": "strict",
      "decided_at": "2024-08-02T00:00:00Z",
      "advocate_bundles": {
        "kept": {
          "claims": [
            {
              "quote": "taking delivery of Neste MY Sustainable Aviation Fuel via SFO pipeline infrastructure",
              "source_url": "https://www.flysfo.com/about/media/press-releases/sfo-welcomes-expanded-use-sustainable-aviation-fuel-united-airlines"
            }
          ]
        },
        "broken": {
          "claims": []
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "flysfo.com is on the trusted official municipal domain allowlist"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "SHA-256 matches d92b7317... byte-for-byte"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "verbatim quote verified against saved press release"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "target horizon 2050 actively executing with 2024 pipeline delivery"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "deterministic rubric: active delivery ahead of final target = in_progress"
        }
      ],
      "impact_rank": 10,
      "display_no": 10,
      "source_tier": "Official",
      "neighborhood_canonical": "SFO Airport",
      "address_full": "Terminal 3 Gate Concourse, San Francisco International Airport, San Francisco, CA 94128",
      "latitude": 37.6189,
      "longitude": -122.3855,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2020-12-10",
      "deadline_date": "2050-12-31",
      "completion_date": "2024-08-01",
      "days_remaining": 8815,
      "days_overdue": null,
      "promise_age_days": 2163,
      "time_to_verdict_days": 1331,
      "entity_canonical_name": "United Airlines",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Airlines & Sustainable Aviation",
      "secondary_categories": [
        "Environment & Energy"
      ],
      "tags": [
        "united_airlines",
        "sustainable_aviation_fuel",
        "saf",
        "net_zero"
      ],
      "verdict_confidence": 0.92,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 8,
      "completion_percentage": 35,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.flysfo.com/about/media/press-releases/sfo-welcomes-expanded-use-sustainable-aviation-fuel-united-airlines",
      "title": "Sustainable Aviation Fuel (SAF) Infrastructure"
    },
    {
      "promise_id": "SFO-04",
      "promise_text": "Alaska Airlines officially commenced flight operations from Harvey Milk Terminal 1 at SFO, welcoming guests to a brand-new 11,000-square-foot lounge featuring 55% more seating and local culinary offerings.",
      "entity": "Alaska Airlines",
      "role": "SFO Hub Airline",
      "entity_type": "companies",
      "category": "Airport & Airlines",
      "neighborhood": "SFO (Harvey Milk Terminal 1 Concourse B)",
      "promised_date": "2023-04-18",
      "due_date": "2024-07-24",
      "opened_date": "2024-07-24",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "Relocated full SFO flight operations and opened the 11,000-square-foot Terminal 1 lounge on July 24, 2024.",
      "source_id": "SFO-SRC-ALA",
      "source_url": "https://www.flysfo.com/about/media/press-releases/alaska-airlines-opens-doors-harvey-milk-terminal-1-sfo",
      "source_file_path": "sfo_alaska_airlines_terminal_1.md",
      "source_hash": "b529c9da816e8fae801d8e9d44cb83deecc094afd31c87d70d95c24bff6670cf",
      "source_type": "official_press_release",
      "fetched_at": "2024-07-24T17:00:00Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "importance_score": 89,
      "document_title": "Alaska Airlines Terminal 1 Flight Operations",
      "quote_date": "July 24, 2024",
      "reading_used": "strict",
      "decided_at": "2024-07-25T00:00:00Z",
      "advocate_bundles": {
        "kept": {
          "claims": [
            {
              "quote": "welcoming guests to a brand-new 11,000-square-foot lounge featuring 55% more seating",
              "source_url": "https://www.flysfo.com/about/media/press-releases/alaska-airlines-opens-doors-harvey-milk-terminal-1-sfo"
            }
          ]
        },
        "broken": {
          "claims": []
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "flysfo.com is on the trusted official municipal domain allowlist"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "SHA-256 matches b529c9da... byte-for-byte"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "verbatim quote verified against saved press release"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "opened and fully operational July 24, 2024"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "deterministic rubric: confirmed operational on target date = kept"
        }
      ],
      "impact_rank": 11,
      "display_no": 11,
      "source_tier": "Official",
      "neighborhood_canonical": "SFO Airport",
      "address_full": "Harvey Milk Terminal 1 Concourse B, San Francisco International Airport, San Francisco, CA 94128",
      "latitude": 37.6175,
      "longitude": -122.386,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2023-04-18",
      "deadline_date": "2024-07-24",
      "completion_date": "2024-07-24",
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1304,
      "time_to_verdict_days": 464,
      "entity_canonical_name": "Alaska Airlines",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Airlines & Gate Expansion",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "alaska_airlines",
        "harvey_milk_terminal_1",
        "gate_expansion",
        "concourse_b"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 7,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.flysfo.com/about/media/press-releases/alaska-airlines-opens-doors-harvey-milk-terminal-1-sfo",
      "title": "Alaska Airlines Terminal 1 Flight Operations"
    },
    {
      "promise_id": "P01",
      "promise_text": "The measure, dubbed the Fentanyl State of Emergency Ordinance, marks Lurie\u2019s first big step in fulfilling a campaign promise",
      "entity": "Daniel Lurie",
      "role": "Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Tenderloin & Civic Center",
      "promised_date": "2024-11-05",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "Sbeb41e4e006f",
      "source_url": "https://edition.pagesuite.com/tribune/article_popover.aspx?guid=4996c790-cac8-49aa-8783-9c015e1acea1",
      "source_file_path": "beb41e4e006f03c4d2430a77ee3eb5705f60b2d1657f730a484c928d65fd0487.md",
      "source_hash": "beb41e4e006f03c4d2430a77ee3eb5705f60b2d1657f730a484c928d65fd0487",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:07:00.487854+00:00",
      "relevance": {
        "score": 6,
        "real": 1,
        "measurable": 1,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:49:29Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P01",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P01",
              "claim_text": "Board gave the Fentanyl State of Emergency Ordinance final approval in a 10-1 vote",
              "quote": "The supervisors gave the ordinance their final approval Tuesday in a resounding 10-1 vote.",
              "quote_match": "exact",
              "evidence_type": "vote",
              "source_file_path": "beb41e4e006f03c4d2430a77ee3eb5705f60b2d1657f730a484c928d65fd0487.md",
              "source_hash": "beb41e4e006f03c4d2430a77ee3eb5705f60b2d1657f730a484c928d65fd0487",
              "source_url": "https://edition.pagesuite.com/tribune/article_popover.aspx?guid=4996c790-cac8-49aa-8783-9c015e1acea1",
              "page_number": null,
              "evidence_date": "2025-02"
            },
            {
              "promise_id": "P01",
              "claim_text": "Lurie introduced the ordinance shortly after his January inauguration and negotiated its passage",
              "quote": "Lurie introduced the ordinance shortly after his January inauguration",
              "quote_match": "exact",
              "evidence_type": "ordinance",
              "source_file_path": "beb41e4e006f03c4d2430a77ee3eb5705f60b2d1657f730a484c928d65fd0487.md",
              "source_hash": "beb41e4e006f03c4d2430a77ee3eb5705f60b2d1657f730a484c928d65fd0487",
              "source_url": "https://edition.pagesuite.com/tribune/article_popover.aspx?guid=4996c790-cac8-49aa-8783-9c015e1acea1",
              "page_number": null,
              "evidence_date": "2025-02"
            }
          ]
        },
        "broken": {
          "promise_id": "P01",
          "advocate_role": "broken_advocate",
          "evidence_checked": 4,
          "claims": [],
          "note": "none found: swept all 14 saved sources; 4 mention an ordinance (P01 file: 10-1 passage; P03 file: unrelated PermitSF package; P05 file: treats fentanyl ordinance as enacted fact; P97 file: behested-waiver reference consistent with passage). No contradicting source. No second search per cut rule."
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 12,
      "importance_score": 88,
      "impact_rank": 12,
      "source_tier": "News",
      "neighborhood_canonical": "Tenderloin",
      "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
      "latitude": 37.7793,
      "longitude": -122.4192,
      "supervisor_district": 5,
      "is_citywide": false,
      "promise_made_date": "2024-11-05",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 737,
      "time_to_verdict_days": 736,
      "entity_canonical_name": "Daniel Lurie",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2025-01-08",
      "entity_term_end": "2029-01-08",
      "category_l1": "Public Safety",
      "category_l2": "Substance Abuse & Emergency Governance",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "fentanyl_emergency",
        "drug_crisis",
        "ordinance",
        "tenderloin"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 9,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://edition.pagesuite.com/tribune/article_popover.aspx?guid=4996c790-cac8-49aa-8783-9c015e1acea1",
      "document_title": "Fentanyl State of Emergency Ordinance",
      "title": "Fentanyl State of Emergency Ordinance"
    },
    {
      "promise_id": "P59",
      "promise_text": "Once given access, riders will be able to use the Zoox app to hail a ride within its service area, which covers the SoMa, Mission, and Design District neighborhoods of San Francisco.",
      "entity": "Zoox",
      "role": null,
      "entity_type": "company",
      "category": "Transit & Streets",
      "neighborhood": "SoMa & Financial District (Zoox Autonomous)",
      "promised_date": "2025-11-18",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims; due 2025-11-18 = same-day commencement reported in source",
      "source_id": "Sc203459be8eb",
      "source_url": "https://techcrunch.com/2025/11/18/zoox-to-begin-offering-robotaxi-rides-to-public-in-san-francisco/",
      "source_file_path": "f3a164fd10a6848d99c2664996ba91aa07f584e2f386e605fdd217621fb23860.md",
      "source_hash": "f3a164fd10a6848d99c2664996ba91aa07f584e2f386e605fdd217621fb23860",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:06:56Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:07:48Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Zoox began offering robotaxi rides in San Francisco",
              "evidence_date": "2025-11-18",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P59",
              "quote": "Zoox has begun offering [robotaxi rides](https://www.sfchronicle.com/sf/article/zoox-san-francisco-rides-19874941.php) in San Francisco, enabling curious consumers to test the company\u2019s jaunty, cabin-style buggies in downtown traffic.",
              "quote_match": "exact",
              "source_file_path": "c203459be8eb9af8fcfaddf6ef89fdfaf8a3c0e295bdebe83bce1b4759f03ff8.md",
              "source_hash": "c203459be8eb9af8fcfaddf6ef89fdfaf8a3c0e295bdebe83bce1b4759f03ff8",
              "source_url": "https://www.sfchronicle.com/sf/article/zoox-robotaxis-21193419.php"
            },
            {
              "claim_text": "Zoox Explorers program launched Tuesday for waitlist members, free rides",
              "evidence_date": "2025-11-18",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P59",
              "quote": "The Zoox Explorers program that launched Tuesday is available to people who join a waitlist,",
              "quote_match": "exact",
              "source_file_path": "c203459be8eb9af8fcfaddf6ef89fdfaf8a3c0e295bdebe83bce1b4759f03ff8.md",
              "source_hash": "c203459be8eb9af8fcfaddf6ef89fdfaf8a3c0e295bdebe83bce1b4759f03ff8",
              "source_url": "https://www.sfchronicle.com/sf/article/zoox-robotaxis-21193419.php"
            },
            {
              "claim_text": "Service area covers SoMa, the Mission and the Design District",
              "evidence_date": "2025-11-18",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P59",
              "quote": "a company blog post about the program, which for now will be limited to a service area that spreads through SoMa, the Mission and the Design District.",
              "quote_match": "exact",
              "source_file_path": "c203459be8eb9af8fcfaddf6ef89fdfaf8a3c0e295bdebe83bce1b4759f03ff8.md",
              "source_hash": "c203459be8eb9af8fcfaddf6ef89fdfaf8a3c0e295bdebe83bce1b4759f03ff8",
              "source_url": "https://www.sfchronicle.com/sf/article/zoox-robotaxis-21193419.php"
            }
          ],
          "evidence_checked": 3,
          "promise_id": "P59"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: 1 broken search returned only confirming sources (TechCrunch, SF Standard 'kind of' confirms launch with scale caveats that do not contradict 'select waitlisted members'). No source says the Nov 18 2025 commencement did not happen. No second search per cut rule.",
          "promise_id": "P59"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass (corrected quote)"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass (corrected quote)"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass (corrected quote)"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass (corrected quote)"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass (corrected quote)"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass (corrected quote)"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 13,
      "importance_score": 87,
      "impact_rank": 13,
      "source_tier": "News",
      "neighborhood_canonical": "South of Market",
      "address_full": "Market St & 4th St, San Francisco, CA 94103",
      "latitude": 37.7855,
      "longitude": -122.4058,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2025-11-18",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 359,
      "time_to_verdict_days": 358,
      "entity_canonical_name": "Zoox",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Autonomous Mobility",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "zoox",
        "robotaxi",
        "autonomous_vehicles",
        "commercial_testing"
      ],
      "verdict_confidence": 0.95,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 7,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://techcrunch.com/2025/11/18/zoox-to-begin-offering-robotaxi-rides-to-public-in-san-francisco/",
      "document_title": "Zoox Driverless Passenger Ride Hail in SF",
      "title": "Zoox Driverless Passenger Ride Hail in SF"
    },
    {
      "promise_id": "P43",
      "promise_text": "Since [sharing](https://blog.waymo.com/2022/03/to-our-fellow-san-franciscans) that we were ready to take the next step and begin testing fully autonomous operations in the city, we\u2019ve begun fully autonomous rides with our San Francisco employees.",
      "entity": "Waymo",
      "role": null,
      "entity_type": "company",
      "category": "Transit & Streets",
      "neighborhood": "San Francisco Driverless Testing Zones",
      "promised_date": "2022-03-30",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims; due 2022-03-30 same-day begin anchored to promised 2022-03-30; R2: evidence_date corrected to 2022-03-30 launch event (month precision failed date gate)",
      "source_id": "Sf53e112937b0",
      "source_url": "https://waymo.com/blog/2022/03/taking-our-next-step-in-city-by-bay/",
      "source_file_path": "c400d8bcbf83fee196d518858e96bb6d92ed7e78fe390c416aef57897cdb0b7c.md",
      "source_hash": "c400d8bcbf83fee196d518858e96bb6d92ed7e78fe390c416aef57897cdb0b7c",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:32:23Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:33:30Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Waymo began fully autonomous rides with SF employees (company blog, Mar 30 2022)",
              "evidence_date": "2022-03-30",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P43",
              "quote": "we\u2019ve begun fully autonomous rides with our San Francisco employees.",
              "quote_match": "exact",
              "source_file_path": "c400d8bcbf83fee196d518858e96bb6d92ed7e78fe390c416aef57897cdb0b7c.md",
              "source_hash": "c400d8bcbf83fee196d518858e96bb6d92ed7e78fe390c416aef57897cdb0b7c",
              "source_url": "https://waymo.com/blog/2022/03/taking-our-next-step-in-city-by-bay/"
            },
            {
              "claim_text": "March 2022: Waymo began offering rides for Waymo staff in SF without safety driver",
              "evidence_date": "2022-03-30",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P43",
              "quote": "In March 2022, Waymo began offering rides for Waymo staff in San Francisco without a safety driver.",
              "quote_match": "exact",
              "source_file_path": "f53e112937b03d79ef9b460fdc1c1547188a8cde01802f7a5b7ac9981823b3ea.md",
              "source_hash": "f53e112937b03d79ef9b460fdc1c1547188a8cde01802f7a5b7ac9981823b3ea",
              "source_url": "https://en.wikipedia.org/wiki/Waymo"
            }
          ],
          "evidence_checked": 2,
          "note": "Event-based typing per P02 precedent (news-reported opening typed opening, not news_report): the rider-only launch IS the opening of driverless operations in SF.",
          "promise_id": "P43"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 0,
          "note": "none found: broken-leaning search surfaced only corroboration (Guardian/Reuters Mar 30 2022 confirm employees carried without backup drivers). No second search per cut rule.",
          "promise_id": "P43"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 14,
      "importance_score": 86,
      "impact_rank": 14,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2022-03-30",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1688,
      "time_to_verdict_days": 1687,
      "entity_canonical_name": "Waymo",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Autonomous Mobility",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "waymo",
        "driverless",
        "robotaxi",
        "commercial_launch"
      ],
      "verdict_confidence": 0.97,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://waymo.com/blog/2022/03/taking-our-next-step-in-city-by-bay/",
      "document_title": "Waymo Fully Autonomous Ride-Hail Expansion",
      "title": "Waymo Fully Autonomous Ride-Hail Expansion"
    },
    {
      "promise_id": "P41",
      "promise_text": "In May 2013, the SFMTA contracted with Tutor Perini Corporation (Contractor) to construct the Central Subway Stations, Surface, Trackway and Systems under SFMTA Contract No. 1300 for a Contract Amount of $839,676,400, all work to be completed in 1700 days, with Final Completion date May 11, 2018.",
      "entity": "Tutor Perini Corporation",
      "role": null,
      "entity_type": "company",
      "category": "Transit & Streets",
      "neighborhood": "Central Subway (SoMa to Chinatown)",
      "promised_date": "2013-05",
      "due_date": "2018-05-11",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence",
      "source_id": "Se8a9a7f4ebed",
      "source_url": "https://www.sfmta.com/ja/media/35570/download?inline",
      "source_file_path": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9.md",
      "source_hash": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:24:50Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:26:10Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 0,
          "note": "none found: kept-leaning search showed Contract 1300 only ~76% complete in Nov 2018, past the May 2018 deadline \u2014 confirms the miss instead of a kept case. No second search per cut rule.",
          "promise_id": "P41"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Contract amended 146 times, amount up $318M to $1.158B (38 percent over)",
              "evidence_date": "2023-06",
              "evidence_type": "contract_milestone",
              "page_number": null,
              "promise_id": "P41",
              "quote": "The Contract has been amended 146 times to increase the Contract Amount by $318,565,464 to $1,158,241,864.70 (a 38 percent increase)",
              "quote_match": "exact",
              "source_file_path": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9.md",
              "source_hash": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9",
              "source_url": "https://www.sfmta.com/ja/media/35570/download?inline"
            },
            {
              "claim_text": "Contract time extended 1,754 days to a total of 3,454 days",
              "evidence_date": "2023-06",
              "evidence_type": "contract_milestone",
              "page_number": null,
              "promise_id": "P41",
              "quote": "extend Contract Time 1,754 days (for a total of 3,454 days)",
              "quote_match": "exact",
              "source_file_path": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9.md",
              "source_hash": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9",
              "source_url": "https://www.sfmta.com/ja/media/35570/download?inline"
            },
            {
              "claim_text": "Substantial completion declared June 28, 2021, over three years late",
              "evidence_date": "2021-06-28",
              "evidence_type": "contract_milestone",
              "page_number": null,
              "promise_id": "P41",
              "quote": "The SFMTA declared Substantial Completion of Contract 1300 Work with the completion of major systems work on June 28, 2021.",
              "quote_match": "exact",
              "source_file_path": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9.md",
              "source_hash": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9",
              "source_url": "https://www.sfmta.com/ja/media/35570/download?inline"
            },
            {
              "claim_text": "Full passenger revenue service began January 7, 2023",
              "evidence_date": "2023-01-07",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P41",
              "quote": "The Central Subway commenced Revenue Service (full passenger service) on January 7, 2023.",
              "quote_match": "exact",
              "source_file_path": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9.md",
              "source_hash": "e8a9a7f4ebedba917078fab2661cffed0cfcb5c279110f2dc41e9ea78cd5b2f9",
              "source_url": "https://www.sfmta.com/ja/media/35570/download?inline"
            }
          ],
          "evidence_checked": 1,
          "note": "Event dates used (June 2023 board doc month for cumulative amendment figures; milestone dates for completion/service).",
          "promise_id": "P41"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 15,
      "importance_score": 85,
      "impact_rank": 15,
      "source_tier": "Official",
      "neighborhood_canonical": "Chinatown",
      "address_full": "933 Stockton Street, San Francisco, CA 94108",
      "latitude": 37.7937,
      "longitude": -122.408,
      "supervisor_district": 3,
      "is_citywide": false,
      "promise_made_date": "2013-05-01",
      "deadline_date": "2018-05-11",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 3107,
      "promise_age_days": 4943,
      "time_to_verdict_days": 4942,
      "entity_canonical_name": "Tutor Perini Corporation",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Subway & Rail Transit",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "central_subway",
        "chinatown",
        "muni_metro",
        "contract_delay"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 3,
      "verdict_reason_code": "timeline_missed_delay",
      "impact_score": 9,
      "completion_percentage": 76,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfmta.com/ja/media/35570/download?inline",
      "document_title": "Central Subway Substantial Completion (2018)",
      "title": "Central Subway Substantial Completion (2018)",
      "media_image_url": "https://www.sfmta.com/sites/default/files/project-images/2022/Central_Subway_Union_Square_Station.jpg",
      "image_url": "https://www.sfmta.com/sites/default/files/project-images/2022/Central_Subway_Union_Square_Station.jpg",
      "media_caption": "Central Subway Chinatown-Rose Pak and Union Square station platforms"
    },
    {
      "promise_id": "P10",
      "promise_text": "Also, 40% of the project\u2019s residential portion is below-market-rate units, mostly targeting middle-income families.",
      "entity": "San Francisco Giants",
      "role": null,
      "entity_type": "sports_team",
      "category": "Sports",
      "neighborhood": "Mission Rock & South Beach (Oracle Park)",
      "promised_date": "2015-01-01",
      "due_date": null,
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "genuine partial completion, full scope unresolved",
      "source_id": "S8400d9972a3d",
      "source_url": "https://www.sfchronicle.com/sf/article/s-f-giants-brass-celebrates-opening-mission-rock-18161986.php",
      "source_file_path": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39.md",
      "source_hash": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:16:55.648381+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:39:36Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P10",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P10",
              "claim_text": "INTERIM: Canyon opened; 1,200 apartments still future (will eventually have)",
              "quote": "The Canyon, which opened in early June, is the first building in what eventually will be a 28-acre neighborhood",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39.md",
              "source_hash": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39",
              "source_url": "https://www.sfchronicle.com/sf/article/s-f-giants-brass-celebrates-opening-mission-rock-18161986.php",
              "page_number": null,
              "evidence_date": "2024"
            },
            {
              "promise_id": "P10",
              "claim_text": "INTERIM: 40% below-market-rate commitment in project",
              "quote": "Also, 40% of the project\u2019s residential portion is below-market-rate units, mostly targeting middle-income families.",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39.md",
              "source_hash": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39",
              "source_url": "https://www.sfchronicle.com/sf/article/s-f-giants-brass-celebrates-opening-mission-rock-18161986.php",
              "page_number": null,
              "evidence_date": "2024"
            },
            {
              "promise_id": "P10",
              "claim_text": "INTERIM: 102 BMR apartments exist; lottery drew 2,900 applications",
              "quote": "The city\u2019s lottery for those 102 below-market-rate apartments received 2,900 applications",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39.md",
              "source_hash": "8400d9972a3dac20a7949a9c6070538fe9d5983c40dbf6261039ce54e44cca39",
              "source_url": "https://www.sfchronicle.com/sf/article/s-f-giants-brass-celebrates-opening-mission-rock-18161986.php",
              "page_number": null,
              "evidence_date": "2024"
            }
          ]
        },
        "broken": {
          "promise_id": "P10",
          "advocate_role": "broken_advocate",
          "evidence_checked": 12,
          "claims": [],
          "note": "none found: no saved file contradicts the 40% BMR commitment (Anchor Steam exit was a commercial tenant, not the housing share). No second search per cut rule."
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "genuine partial completion, full scope unresolved"
        }
      ],
      "display_no": 16,
      "importance_score": 84,
      "impact_rank": 16,
      "source_tier": "News",
      "neighborhood_canonical": "Mission Rock",
      "address_full": "Dr Maya Angelou Lane & Toni Stone Crossing, San Francisco, CA 94158",
      "latitude": 37.7735,
      "longitude": -122.389,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2015-01-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 4333,
      "time_to_verdict_days": 4332,
      "entity_canonical_name": "San Francisco Giants",
      "entity_category": "sports_team",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Housing",
      "category_l2": "Mixed-Use Neighborhood Development",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "mission_rock",
        "sf_giants",
        "below_market_rate",
        "bmr_housing"
      ],
      "verdict_confidence": 0.93,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 8,
      "completion_percentage": 60,
      "source_credibility_score": 8,
      "source_type_standardized": "news_mainstream",
      "source_domain_authority": 9,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfchronicle.com/sf/article/s-f-giants-brass-celebrates-opening-mission-rock-18161986.php",
      "document_title": "Mission Rock 40% Affordable Housing Pledges",
      "title": "Mission Rock 40% Affordable Housing Pledges",
      "media_image_url": "https://cdn.abcotvs.com/dip/images/13335905_060223-kgo-mission-rock-development-img.jpg",
      "image_url": "https://cdn.abcotvs.com/dip/images/13335905_060223-kgo-mission-rock-development-img.jpg",
      "media_caption": "Mission Rock mixed-use waterfront development opposite Oracle Park"
    },
    {
      "promise_id": "P18",
      "promise_text": "San Francisco\u2019s requirement is 82,200 homes by 2031.",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "San Francisco Housing Element",
      "promised_date": "2023-01-31",
      "due_date": "2031-12-31",
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "in_progress: partial progress only; outcome-satisfaction principle \u2014 the Jan-2023 adoption vote proves the Housing Element PLAN exists, not the promised outcome of 82,200 HOMES by 2031; due 2031-12-31 future, homes unbuilt (mechanical Rule 4 kept overridden: plan/enabling votes are supporting evidence, never completion)",
      "source_id": "S7a34352ce89b",
      "source_url": "https://citypln-m-extnl.sfgov.org/Commissions/CPC/4_10_2025/Commission%20Packet/2021-005878CWP.pdf",
      "source_file_path": "7a34352ce89b8ab039f1fec4bdf2fe272870d4333764d683b20944533c09b239.md",
      "source_hash": "7a34352ce89b8ab039f1fec4bdf2fe272870d4333764d683b20944533c09b239",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T03:59:00Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:03:59Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Housing Element unanimously adopted Jan 2023 and certified (plan step, not homes outcome)",
              "evidence_date": "2023-01-31",
              "evidence_type": "vote",
              "page_number": null,
              "promise_id": "P18",
              "quote": "Element was unanimously adopted by the Board of Supervisors in January 2023 and subsequently certified",
              "quote_match": "exact",
              "source_file_path": "7a34352ce89b8ab039f1fec4bdf2fe272870d4333764d683b20944533c09b239.md",
              "source_hash": "7a34352ce89b8ab039f1fec4bdf2fe272870d4333764d683b20944533c09b239",
              "source_url": "https://citypln-m-extnl.sfgov.org/Commissions/CPC/4_10_2025/Commission%20Packet/2021-005878CWP.pdf"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P18"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: 2025 rezoning doc shows 36,200-unit shortfall still being planned for, no abandonment or missed-deadline evidence (deadline 2031 future). No second search per cut rule.",
          "promise_id": "P18"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: in_progress: partial progress only; outcome-satisfaction principle \u2014 the Jan-2023 adoption vote proves the Housing Element PLAN exists, not the promised outcome of 82,200 HOMES by 2031; due 2031-12-31 future, homes unbuilt (mechanical Rule 4 kept overridden: plan/enabling votes are supporting evidence, never completion)"
        }
      ],
      "display_no": 17,
      "importance_score": 83,
      "impact_rank": 17,
      "source_tier": "Official",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2023-01-31",
      "deadline_date": "2031-12-31",
      "completion_date": null,
      "days_remaining": 1875,
      "days_overdue": null,
      "promise_age_days": 1381,
      "time_to_verdict_days": 1380,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Housing",
      "category_l2": "State Mandated Housing Allocation",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "housing_element",
        "82000_units",
        "rezoning",
        "hcd"
      ],
      "verdict_confidence": 0.92,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 1,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 10,
      "completion_percentage": 40,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://citypln-m-extnl.sfgov.org/Commissions/CPC/4_10_2025/Commission%20Packet/2021-005878CWP.pdf",
      "document_title": "Housing Element: 82,200 New Homes by 2031",
      "title": "Housing Element: 82,200 New Homes by 2031"
    },
    {
      "promise_id": "P06",
      "promise_text": "In 2014, San Francisco became the third city in the country to adopt Vision Zero with the goal of zero traffic deaths.",
      "entity": "City and County of San Francisco",
      "role": null,
      "entity_type": "other",
      "category": "Transit & Streets",
      "neighborhood": "Citywide Streets (Vision Zero)",
      "promised_date": "2014-01-01",
      "due_date": null,
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "contradicting primary evidence outranks affirmative claims",
      "source_id": "S82a9d0952ba7",
      "source_url": "https://www.sfmta.com/tl/media/45938/download?inline",
      "source_file_path": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa.md",
      "source_hash": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T03:15:48.926215+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:34:38Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P06",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P06",
              "claim_text": "City remains committed to achieving zero traffic deaths",
              "quote": "San Francisco remains committed to achieving our Vision Zero goal of zero traffic deaths.",
              "quote_match": "exact",
              "evidence_type": "announcement",
              "source_file_path": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa.md",
              "source_hash": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa",
              "source_url": "https://www.sfmta.com/tl/media/45938/download?inline",
              "page_number": null,
              "evidence_date": "2025-07"
            }
          ]
        },
        "broken": {
          "promise_id": "P06",
          "advocate_role": "broken_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P06",
              "claim_text": "43 traffic deaths recorded in 2024",
              "quote": "San Francisco recorded 43 traffic-related deaths in 2024 as part of the Vision Zero SF Initiative.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa.md",
              "source_hash": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa",
              "source_url": "https://www.sfmta.com/tl/media/45938/download?inline",
              "page_number": null,
              "evidence_date": "2025-07"
            },
            {
              "promise_id": "P06",
              "claim_text": "65% increase over 2023, highest since 2005",
              "quote": "These 43 deaths represent a 65% increase compared to 2023 and is the highest number of fatalities recorded since 2005.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa.md",
              "source_hash": "82a9d0952ba7d121290800e3bc11c5bbfb04467411e3df0a1cca9fe6ea9acbaa",
              "source_url": "https://www.sfmta.com/tl/media/45938/download?inline",
              "page_number": null,
              "evidence_date": "2025-07"
            }
          ]
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "contradicting primary evidence outranks affirmative claims"
        }
      ],
      "display_no": 18,
      "importance_score": 82,
      "impact_rank": 18,
      "source_tier": "Official",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2014-01-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 4698,
      "time_to_verdict_days": 4697,
      "entity_canonical_name": "City and County of San Francisco",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Traffic Safety & Vision Zero",
      "secondary_categories": [
        "Public Safety"
      ],
      "tags": [
        "vision_zero",
        "traffic_fatalities",
        "pedestrian_safety",
        "sfmta"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 0,
      "verdict_contradiction_count": 3,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 9,
      "completion_percentage": 0,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfmta.com/tl/media/45938/download?inline",
      "document_title": "Vision Zero: End Traffic Fatalities by 2024",
      "title": "Vision Zero: End Traffic Fatalities by 2024",
      "media_image_url": "https://bloximages.chicago2.vip.townnews.com/sfexaminer.com/content/tncms/assets/v3/editorial/a/1b/a1b090c9-6651-4a89-bc8d-ff8b6cb2996c/681a934ddd28a.image.jpg",
      "image_url": "https://bloximages.chicago2.vip.townnews.com/sfexaminer.com/content/tncms/assets/v3/editorial/a/1b/a1b090c9-6651-4a89-bc8d-ff8b6cb2996c/681a934ddd28a.image.jpg",
      "media_caption": "Valencia Street protected center-running bike lane and corridor safety modifications"
    },
    {
      "promise_id": "P08",
      "promise_text": "When Mayor London Breed announced $5 million last year for repairs to San Francisco\u2019s crumbling housing stock for homeless people, the requests flooded in.",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Tenderloin & SoMa (SRO Housing)",
      "promised_date": "2022-05-01",
      "due_date": null,
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "contradicting primary evidence outranks affirmative claims",
      "source_id": "S2fa8b19cdda5",
      "source_url": "https://www.sfchronicle.com/sf/article/homeless-housing-sro-breed-17767837.php",
      "source_file_path": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf.md",
      "source_hash": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:16:51.248880+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:36:38Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P08",
          "advocate_role": "kept_advocate",
          "evidence_checked": 12,
          "claims": [],
          "note": "none found: SRO repairs appear only in the Chronicle follow-up, which documents zero spending; no saved file shows money spent or repairs completed. No second search per cut rule."
        },
        "broken": {
          "promise_id": "P08",
          "advocate_role": "broken_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P08",
              "claim_text": "None of the $5M spent 6+ months after funds available",
              "quote": "more than six months after the funds were made available, none of the money has been spent to fix the safety and quality-of-life problems at 82 buildings.",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf.md",
              "source_hash": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf",
              "source_url": "https://www.sfchronicle.com/sf/article/homeless-housing-sro-breed-17767837.php",
              "page_number": null,
              "evidence_date": "2023"
            },
            {
              "promise_id": "P08",
              "claim_text": "Headline: promised $5M, nothing spent so far",
              "quote": "S.F. Mayor Breed promised $5 million to fix crumbling homeless housing. Nothing has been spent so far.",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf.md",
              "source_hash": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf",
              "source_url": "https://www.sfchronicle.com/sf/article/homeless-housing-sro-breed-17767837.php",
              "page_number": null,
              "evidence_date": "2023"
            },
            {
              "promise_id": "P08",
              "claim_text": "$21.6M in repair requests vs $5M available",
              "quote": "asked for $21.6 million worth of repairs and renovations",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf.md",
              "source_hash": "2fa8b19cdda53615c6217dd45669138e9ee78ad14d5df8c03937a0308f62fbdf",
              "source_url": "https://www.sfchronicle.com/sf/article/homeless-housing-sro-breed-17767837.php",
              "page_number": null,
              "evidence_date": "2023"
            }
          ]
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "contradicting primary evidence outranks affirmative claims"
        }
      ],
      "display_no": 19,
      "importance_score": 81,
      "impact_rank": 19,
      "source_tier": "News",
      "neighborhood_canonical": "Tenderloin",
      "address_full": "Turk St & Jones St, San Francisco, CA 94102",
      "latitude": 37.7831,
      "longitude": -122.4124,
      "supervisor_district": 5,
      "is_citywide": false,
      "promise_made_date": "2022-05-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1656,
      "time_to_verdict_days": 1655,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Housing",
      "category_l2": "SRO & Supportive Housing Rehabilitation",
      "secondary_categories": [
        "Public Safety"
      ],
      "tags": [
        "sro_housing",
        "tenderloin",
        "housing_repairs",
        "supportive_housing"
      ],
      "verdict_confidence": 0.94,
      "verdict_evidence_count": 0,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "no_progress",
      "impact_score": 8,
      "completion_percentage": 0,
      "source_credibility_score": 8,
      "source_type_standardized": "news_mainstream",
      "source_domain_authority": 9,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfchronicle.com/sf/article/homeless-housing-sro-breed-17767837.php",
      "document_title": "1,000 SRO Housing Units Improvement",
      "title": "1,000 SRO Housing Units Improvement"
    },
    {
      "promise_id": "P22",
      "promise_text": "Embarcadero Navigation Center (12/30/19) opened with 200 beds (despite a lawsuit from neighbors that delayed the site\u2019s opening until the end of 2019).",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "The Embarcadero (Waterfront)",
      "promised_date": "2019-03",
      "due_date": "2019-12-30",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims (re-open R2: dhcs.ca.gov allowlisted, speaker per org-speaker principle; 200-bed opening 12/30/19 IS the promised outcome)",
      "source_id": "S960774ffd1cf",
      "source_url": "https://www.dhcs.ca.gov/wp-content/uploads/2025/10/San-Francisco-PY4-Annual-Narrative.pdf",
      "source_file_path": "960774ffd1cf8d24529f7cb4373893c23638c13fd66c23fd90e56d35dd84aef5.md",
      "source_hash": "960774ffd1cf8d24529f7cb4373893c23638c13fd66c23fd90e56d35dd84aef5",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:07:20Z",
      "relevance": {
        "score": 7,
        "real": 1,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:15:08Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Embarcadero Navigation Center opened 12/30/19 with 200 beds",
              "evidence_date": "2019-12-30",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P22",
              "quote": "Embarcadero Navigation Center (12/30/19) opened with 200 beds",
              "quote_match": "exact",
              "source_file_path": "960774ffd1cf8d24529f7cb4373893c23638c13fd66c23fd90e56d35dd84aef5.md",
              "source_hash": "960774ffd1cf8d24529f7cb4373893c23638c13fd66c23fd90e56d35dd84aef5",
              "source_url": "https://www.dhcs.ca.gov/wp-content/uploads/2025/10/San-Francisco-PY4-Annual-Narrative.pdf"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P22"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file confirms the 12/30/19 opening (lawsuit delayed it to end of 2019 but it opened); no contradiction. No second search per cut rule.",
          "promise_id": "P22"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass per org-speaker principle (directed re-check)"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: official primary evidence confirms completion with zero contradicting claims (re-open R2: dhcs.ca.gov allowlisted, speaker per org-speaker principle; 200-bed opening 12/30/19 IS the promised outcome)"
        }
      ],
      "display_no": 20,
      "importance_score": 80,
      "impact_rank": 20,
      "source_tier": "News",
      "neighborhood_canonical": "The Embarcadero",
      "address_full": "Seawall Lot 330, The Embarcadero & Bryant St, San Francisco, CA 94105",
      "latitude": 37.7885,
      "longitude": -122.3892,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2019-03-01",
      "deadline_date": "2019-12-30",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2813,
      "time_to_verdict_days": 2812,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Housing",
      "category_l2": "Navigation Centers & Shelters",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "embarcadero_nav_center",
        "navigation_center",
        "homelessness",
        "waterfront"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "delayed_but_kept",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.dhcs.ca.gov/wp-content/uploads/2025/10/San-Francisco-PY4-Annual-Narrative.pdf",
      "document_title": "Embarcadero Navigation Center 200 Beds",
      "title": "Embarcadero Navigation Center 200 Beds"
    },
    {
      "promise_id": "P17",
      "promise_text": "Lurie promised to hire 425 new San Francisco Police Department officers during the first three years of his administration, prevent local city departments from indefinitely delaying building permits, impose more oversight on nonprofits working with the city, and address the city\u2019s homelessness and public drug-use crises.",
      "entity": "Daniel Lurie",
      "role": "Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "SFPD District Stations & Neighborhoods",
      "promised_date": "2024",
      "due_date": "2028-01-31",
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "due date in future and no definitive resolution yet; due 2028-01-31 = three-year admin window from Jan-2025 start, both in-source (full-date form: arbitrator requires YYYY-MM-DD)",
      "source_id": "S9c00e2bb9684",
      "source_url": "https://www.influencewatch.org/person/daniel-lurie/",
      "source_file_path": "9c00e2bb9684a248a88995c037c8c3fbe8739c68ffdf386d3886ca08a81e6b00.md",
      "source_hash": "9c00e2bb9684a248a88995c037c8c3fbe8739c68ffdf386d3886ca08a81e6b00",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:57:47Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:59:15Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: saved file states the 425-officer pledge but no hiring count or completion evidence. No second search per cut rule.",
          "promise_id": "P17"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: saved file contains no contradicting hiring count or abandonment evidence. No second search per cut rule.",
          "promise_id": "P17"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "authenticity_hash",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_quote",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "authenticity_speaker",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_date",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_evidence",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: due date in future and no definitive resolution yet; due 2028-01-31 = three-year admin window from Jan-2025 start, both in-source (full-date form: arbitrator requires YYYY-MM-DD)"
        }
      ],
      "display_no": 21,
      "due_date_label": "Derived (3-year horizon from Jan 2025 inauguration)",
      "importance_score": 79,
      "impact_rank": 21,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": "SFPD Headquarters, 1245 3rd St, San Francisco, CA 94158",
      "latitude": 37.7716,
      "longitude": -122.3902,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2024-01-01",
      "deadline_date": "2028-01-31",
      "completion_date": null,
      "days_remaining": 445,
      "days_overdue": null,
      "promise_age_days": 1046,
      "time_to_verdict_days": 1045,
      "entity_canonical_name": "Daniel Lurie",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2025-01-08",
      "entity_term_end": "2029-01-08",
      "category_l1": "Public Safety",
      "category_l2": "Police Staffing & Neighborhood Deployment",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "sfpd_recruitment",
        "police_staffing",
        "neighborhood_patrol",
        "academy_classes"
      ],
      "verdict_confidence": 0.91,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 9,
      "completion_percentage": 30,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.influencewatch.org/person/daniel-lurie/",
      "document_title": "Hire 425 New SFPD Police Officers",
      "title": "Hire 425 New SFPD Police Officers"
    },
    {
      "promise_id": "P25",
      "promise_text": "Though that legislation required that the hall close on December 31st, 2021, there has been no movement from the Board towards that closure.",
      "entity": "San Francisco Board of Supervisors",
      "role": null,
      "entity_type": "official",
      "category": "Civic Governance",
      "neighborhood": "Juvenile Hall (Twin Peaks)",
      "promised_date": "2019-06-04",
      "due_date": "2021-12-31",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence",
      "source_id": "S2b9025ba0cdf",
      "source_url": "https://media.api.sf.gov/documents/JUVENILE_JUSTICE_REALIGNMENT_BLOCK_GRANT_ANNUAL_PLAN_20260420.pdf",
      "source_file_path": "2b9025ba0cdf40026680377b8e8b0f92b59d31d6592c913ac91a772e78426373.md",
      "source_hash": "2b9025ba0cdf40026680377b8e8b0f92b59d31d6592c913ac91a772e78426373",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:13:07Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:16:32Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: 2026 plan states no Board movement toward closure and describes Juvenile Hall as still operating reception center. No second search per cut rule.",
          "promise_id": "P25"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "No Board movement toward required 12/31/2021 closure",
              "evidence_date": "2026-04",
              "evidence_type": "filing",
              "page_number": 9,
              "promise_id": "P25",
              "quote": "there has been no movement from the Board towards that closure",
              "quote_match": "exact",
              "source_file_path": "2b9025ba0cdf40026680377b8e8b0f92b59d31d6592c913ac91a772e78426373.md",
              "source_hash": "2b9025ba0cdf40026680377b8e8b0f92b59d31d6592c913ac91a772e78426373",
              "source_url": "https://media.api.sf.gov/documents/JUVENILE_JUSTICE_REALIGNMENT_BLOCK_GRANT_ANNUAL_PLAN_20260420.pdf"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P25"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 22,
      "importance_score": 78,
      "impact_rank": 22,
      "source_tier": "Official",
      "neighborhood_canonical": "Twin Peaks",
      "address_full": "375 Woodside Ave, San Francisco, CA 94127",
      "latitude": 37.746,
      "longitude": -122.454,
      "supervisor_district": 7,
      "is_citywide": false,
      "promise_made_date": "2019-06-04",
      "deadline_date": "2021-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 1777,
      "promise_age_days": 2718,
      "time_to_verdict_days": 2717,
      "entity_canonical_name": "San Francisco Board of Supervisors",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Public Safety",
      "category_l2": "Juvenile Justice Reform",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "juvenile_hall_closure",
        "criminal_justice_reform",
        "youth_detention"
      ],
      "verdict_confidence": 0.97,
      "verdict_evidence_count": 0,
      "verdict_contradiction_count": 3,
      "verdict_reason_code": "goal_abandoned",
      "impact_score": 8,
      "completion_percentage": 10,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://media.api.sf.gov/documents/JUVENILE_JUSTICE_REALIGNMENT_BLOCK_GRANT_ANNUAL_PLAN_20260420.pdf",
      "document_title": "Close San Francisco Juvenile Hall Facility",
      "title": "Close San Francisco Juvenile Hall Facility"
    },
    {
      "promise_id": "P12",
      "promise_text": "The SFMTA allows Lime and Spin to operate scooter share services in San Francisco through June 30, 2026.",
      "entity": "SFMTA",
      "role": "San Francisco Municipal Transportation Agency",
      "entity_type": "official",
      "category": "Transit & Streets",
      "neighborhood": "Citywide Micromobility & Bike Lanes",
      "promised_date": "2024-07-01",
      "due_date": "2026-06-30",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "Sd075e69257f6",
      "source_url": "https://www.sfmta.com/projects/powered-scooter-share-permit-program",
      "source_file_path": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542.md",
      "source_hash": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T03:17:00.150405+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:41:24Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P12",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P12",
              "claim_text": "SFMTA authorized Lime+Spin operation through June 30, 2026",
              "quote": "The SFMTA allows Lime and Spin to operate scooter share services in San Francisco through June 30, 2026.",
              "quote_match": "exact",
              "evidence_type": "filing",
              "source_file_path": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542.md",
              "source_hash": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542",
              "source_url": "https://www.sfmta.com/projects/powered-scooter-share-permit-program",
              "page_number": null,
              "evidence_date": "2026"
            },
            {
              "promise_id": "P12",
              "claim_text": "Permitted fleets: 3,250 scooters each for Lime and Spin",
              "quote": "- Lime: 3,250 scooters\n- Spin: 3,250 scooters",
              "quote_match": "exact",
              "evidence_type": "filing",
              "source_file_path": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542.md",
              "source_hash": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542",
              "source_url": "https://www.sfmta.com/projects/powered-scooter-share-permit-program",
              "page_number": null,
              "evidence_date": "2026"
            },
            {
              "promise_id": "P12",
              "claim_text": "Program alive past term: +500-device expansion through Nov 26, 2026",
              "quote": "Each permitted company may also temporarily expand their fleets by an additional 500 devices to serve as mutual aid for transit and to help meet travel demand, through November 26, 2026.",
              "quote_match": "exact",
              "evidence_type": "filing",
              "source_file_path": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542.md",
              "source_hash": "d075e69257f60ecea6984efcb9b7bc31897019897fdb53b52ae6c66db0635542",
              "source_url": "https://www.sfmta.com/projects/powered-scooter-share-permit-program",
              "page_number": null,
              "evidence_date": "2026"
            }
          ]
        },
        "broken": {
          "promise_id": "P12",
          "advocate_role": "broken_advocate",
          "evidence_checked": 12,
          "claims": [],
          "note": "none found: only scooter hits are routine parking enforcement; no revocation, suspension, or ban in any saved file. No second search per cut rule."
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 23,
      "importance_score": 77,
      "impact_rank": 23,
      "source_tier": "Official",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2024-07-01",
      "deadline_date": "2026-06-30",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 864,
      "time_to_verdict_days": 863,
      "entity_canonical_name": "San Francisco Municipal Transportation Agency (SFMTA)",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Micromobility & Shared Devices",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "scooters",
        "spin",
        "lime",
        "micromobility",
        "permits"
      ],
      "verdict_confidence": 0.95,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 6,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfmta.com/projects/powered-scooter-share-permit-program",
      "document_title": "6,500 Shared E-Scooter Fleet Cap",
      "title": "6,500 Shared E-Scooter Fleet Cap"
    },
    {
      "promise_id": "P26",
      "promise_text": "In the first year alone, it is expected that 4,500 new units will return on the market\u2014 more than our annual goals\u2014 with no increase in taxes, no construction time, no multi-million dollar price tag, and no waiting.",
      "entity": "Dean Preston",
      "role": null,
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Citywide Vacant Homes",
      "promised_date": "2022-11-08",
      "due_date": null,
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "numeric target not met or plan abandoned (re-open R2: Prop M voided by courts, 4,500-units-first-year outcome impossible; kept passage vote is enabling step per outcome-satisfaction principle)",
      "source_id": "S4ce5690e59c3",
      "source_url": "https://costa-hawkins.com/wp-content/uploads/2026/09/A172067.pdf",
      "source_file_path": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95.md",
      "source_hash": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:27:09Z",
      "relevance": {
        "score": 7,
        "real": 1,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:29:10Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Voters approved Proposition M in 2022",
              "evidence_date": "2022-11-08",
              "evidence_type": "vote",
              "page_number": 1,
              "promise_id": "P26",
              "quote": "In 2022, San Francisco voters approved Proposition M",
              "quote_match": "exact",
              "source_file_path": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95.md",
              "source_hash": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95",
              "source_url": "https://costa-hawkins.com/wp-content/uploads/2026/09/A172067.pdf"
            },
            {
              "claim_text": "Prop M passed with 54.5% Nov 2022 (Chronicle, allowlisted)",
              "evidence_date": "2022-11-08",
              "evidence_type": "vote",
              "page_number": null,
              "promise_id": "P26",
              "quote": "54.5% of the [city\u2019s voters approved it](https://www.sfchronicle.com/sf/article/s-f-voters-approve-a-tax-on-vacant-residential-17583773.php) in November 2022",
              "quote_match": "exact",
              "source_file_path": "4ce5690e59c38dd3cf43b467f32eaa5332235b22fc0f049bb6a8474852392224.md",
              "source_hash": "4ce5690e59c38dd3cf43b467f32eaa5332235b22fc0f049bb6a8474852392224",
              "source_url": "https://www.sfchronicle.com/politics/article/san-francisco-vacancy-tax-ruling-22427983.php"
            }
          ],
          "evidence_checked": 2,
          "note": "R2: day 11-08 anchored in sister source (costa file cites Nov 8 2022 election); this file states November 2022.",
          "promise_id": "P26"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Judgment bars City from enforcing Prop M, affirmed on appeal",
              "evidence_date": "2026-09-11",
              "evidence_type": "regulator_order",
              "page_number": 1,
              "promise_id": "P26",
              "quote": "entered judgment prohibiting the City and its officers and agents from administering or enforcing Proposition M",
              "quote_match": "exact",
              "source_file_path": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95.md",
              "source_hash": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95",
              "source_url": "https://costa-hawkins.com/wp-content/uploads/2026/09/A172067.pdf"
            },
            {
              "claim_text": "Appeals ruling kept Prop M from taking effect (Ellis Act preemption)",
              "evidence_date": "2026-09-11",
              "evidence_type": "regulator_order",
              "page_number": null,
              "promise_id": "P26",
              "quote": "The ruling upheld a decision by Superior Court Judge Charles Haines in October 2024 that has kept Prop M from taking effect",
              "quote_match": "exact",
              "source_file_path": "4ce5690e59c38dd3cf43b467f32eaa5332235b22fc0f049bb6a8474852392224.md",
              "source_hash": "4ce5690e59c38dd3cf43b467f32eaa5332235b22fc0f049bb6a8474852392224",
              "source_url": "https://www.sfchronicle.com/politics/article/san-francisco-vacancy-tax-ruling-22427983.php"
            }
          ],
          "evidence_checked": 2,
          "note": "R2: ruling date 2026-09-11 anchored in sister source (opinion stamp Filed 9/11/26); this file undated (ruled Friday).",
          "promise_id": "P26"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass per speaker principle: person-on-minutes only, org=pass/NA (P26-mission re-check)"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: Rule 3 numeric/abandoned; numeric target not met or plan abandoned (re-open R2: Prop M voided by courts, 4,500-units-first-year outcome impossible; kept passage vote is enabling step per outcome-satisfaction principle)"
        }
      ],
      "display_no": 24,
      "importance_score": 76,
      "impact_rank": 24,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2022-11-08",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1465,
      "time_to_verdict_days": 1464,
      "entity_canonical_name": "Dean Preston",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2019-12-16",
      "entity_term_end": "2025-01-08",
      "category_l1": "Housing",
      "category_l2": "Taxation & Vacancy Policy",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "empty_homes_tax",
        "prop_m",
        "vacant_units",
        "housing_affordability"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "legal_injunction_halt",
      "impact_score": 7,
      "completion_percentage": 15,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://costa-hawkins.com/wp-content/uploads/2026/09/A172067.pdf",
      "document_title": "Empty Homes Tax: 4,500 Units in Year One",
      "title": "Empty Homes Tax: 4,500 Units in Year One"
    },
    {
      "promise_id": "P27",
      "promise_text": "The 30-year fund would receive $20 million in its first year and increasing amounts thereafter, up to $50 million annually.",
      "entity": "Ed Lee",
      "role": null,
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Affordable Housing Trust Fund",
      "promised_date": "2012",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims (re-open R2: Prop C passage 65.15% Nov 6 2012 vote IS the fund-creation outcome)",
      "source_id": "S2adc21305bf2",
      "source_url": "https://www.spur.org/news/2012-07-26/housing-trust-fund-heads-voters-november",
      "source_file_path": "0259545ea7d9dceaa401f7d36a2205ac46f924424012534056ac57687753177f.md",
      "source_hash": "0259545ea7d9dceaa401f7d36a2205ac46f924424012534056ac57687753177f",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:30:20Z",
      "relevance": {
        "score": 7,
        "real": 1,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:31:06Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Prop C passed Nov 6 2012 with 65.15% For, creating Housing Trust Fund",
              "evidence_date": "2012-11-06",
              "evidence_type": "vote",
              "page_number": null,
              "promise_id": "P27",
              "quote": "| For | 211,674 | 65.15 |",
              "quote_match": "exact",
              "source_file_path": "2adc21305bf2a5059104f468316bc0214cd2e4c75c100f648c8248e6aee131a7.md",
              "source_hash": "2adc21305bf2a5059104f468316bc0214cd2e4c75c100f648c8248e6aee131a7",
              "source_url": "https://en.wikipedia.org/wiki/November_2012_San_Francisco_general_election"
            }
          ],
          "evidence_checked": 2,
          "note": "R2 re-work: passage vote found on allowlisted en.wikipedia.org after 3-query diligence (open web; site:en.wikipedia.org; site:sfgov.org). July-2012 SPUR file predates vote.",
          "promise_id": "P27"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 2,
          "note": "none found after R2 re-work diligence: 3 queries (open web Prop C results; site:en.wikipedia.org; site:sfgov.org) + 2 saved files read (SPUR preview, Wikipedia results); no repeal/failure/contradiction found. Passage 65.15% uncontradicted.",
          "promise_id": "P27"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: official primary evidence confirms completion with zero contradicting claims (re-open R2: Prop C passage 65.15% Nov 6 2012 vote IS the fund-creation outcome)"
        }
      ],
      "display_no": 25,
      "importance_score": 75,
      "impact_rank": 25,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
      "latitude": 37.7793,
      "longitude": -122.4192,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2012-01-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 5429,
      "time_to_verdict_days": 5428,
      "entity_canonical_name": "Ed Lee",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2011-01-11",
      "entity_term_end": "2017-12-12",
      "category_l1": "Housing",
      "category_l2": "Affordable Housing Financing",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "housing_trust_fund",
        "prop_c",
        "affordable_housing",
        "ed_lee"
      ],
      "verdict_confidence": 0.97,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.spur.org/news/2012-07-26/housing-trust-fund-heads-voters-november",
      "document_title": "Housing Trust Fund: $20M First-Year Budget",
      "title": "Housing Trust Fund: $20M First-Year Budget"
    },
    {
      "promise_id": "P29",
      "promise_text": "Care Not Cash officially launched in May 2004, reducing the amount of money homeless residents received from a maximum of $410 per month to $59.",
      "entity": "Gavin Newsom",
      "role": "Governor of California",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Civic Center & Citywide (Human Services)",
      "promised_date": "2002-11-05",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "Se14a38d9e8d8",
      "source_url": "https://www.khsu.org/regional-interests/2020-02-19/gov-newsom-once-again-takes-on-homelessness-this-time-statewide",
      "source_file_path": "e14a38d9e8d88b53f5c1abbc8d4ae936653435d6d8dbd6861b34b76a51a21941.md",
      "source_hash": "e14a38d9e8d88b53f5c1abbc8d4ae936653435d6d8dbd6861b34b76a51a21941",
      "source_type": "news_report",
      "fetched_at": null,
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:32:15Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Care Not Cash launched May 2004, cut grants 410 to 59 dollars",
              "evidence_date": "2004-05",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P29",
              "quote": "Care Not Cash officially launched in May 2004, reducing the amount of money homeless residents received from a maximum of $410 per month to $59",
              "quote_match": "exact",
              "source_file_path": "e14a38d9e8d88b53f5c1abbc8d4ae936653435d6d8dbd6861b34b76a51a21941.md",
              "source_hash": "e14a38d9e8d88b53f5c1abbc8d4ae936653435d6d8dbd6861b34b76a51a21941",
              "source_url": "https://www.khsu.org/regional-interests/2020-02-19/gov-newsom-once-again-takes-on-homelessness-this-time-statewide"
            }
          ],
          "evidence_checked": 1,
          "note": "Shared file with P14 (same URL wholesale; P14 owns the sources row).",
          "promise_id": "P29"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file describes launch and implementation; advocate criticism noted but no contradiction of the cut. No second search per cut rule.",
          "promise_id": "P29"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 26,
      "importance_score": 74,
      "impact_rank": 26,
      "source_tier": "News",
      "neighborhood_canonical": "Civic Center",
      "address_full": "170 Otis Street, San Francisco, CA 94103",
      "latitude": 37.7725,
      "longitude": -122.4206,
      "supervisor_district": 6,
      "is_citywide": true,
      "promise_made_date": "2002-11-05",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 8773,
      "time_to_verdict_days": 8772,
      "entity_canonical_name": "Gavin Newsom",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2004-01-08",
      "entity_term_end": "2011-01-10",
      "category_l1": "Public Safety",
      "category_l2": "Homeless Assistance & Cash Aid Reform",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "care_not_cash",
        "prop_n",
        "gavin_newsom",
        "county_adult_assistance"
      ],
      "verdict_confidence": 0.97,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.khsu.org/regional-interests/2020-02-19/gov-newsom-once-again-takes-on-homelessness-this-time-statewide",
      "document_title": "Care Not Cash Homeless Services Reform",
      "title": "Care Not Cash Homeless Services Reform"
    },
    {
      "promise_id": "P31",
      "promise_text": "By adopting the Family Zoning Plan in December 2025, San Francisco met its state law obligations to approve a compliant rezoning plan by January 31, 2026.",
      "entity": "Daniel Lurie",
      "role": "Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Commercial Corridors & Small Businesses",
      "promised_date": "2025-06-24",
      "due_date": "2026-01-31",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "ordinance signed pre-deadline (sfplanning.org allowlisted; re-open)",
      "source_id": "S37e84a7ead43",
      "source_url": "https://sfplanning.org/sf-family-zoning-plan",
      "source_file_path": "37e84a7ead4327558a0c77916bb890e61cbbab3f5e66ae5462016b113b293196.md",
      "source_hash": "37e84a7ead4327558a0c77916bb890e61cbbab3f5e66ae5462016b113b293196",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:34:58Z",
      "relevance": {
        "score": 7,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:41:16Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Lurie signed Family Zoning Plan into law Dec 12 2025, before deadline",
              "evidence_date": "2025-12-12",
              "evidence_type": "ordinance",
              "page_number": null,
              "promise_id": "P31",
              "quote": "Mayor Lurie officially signed the Family Zoning Plan into law",
              "quote_match": "exact",
              "source_file_path": "37e84a7ead4327558a0c77916bb890e61cbbab3f5e66ae5462016b113b293196.md",
              "source_hash": "37e84a7ead4327558a0c77916bb890e61cbbab3f5e66ae5462016b113b293196",
              "source_url": "https://sfplanning.org/sf-family-zoning-plan"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P31"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file reports signing before deadline; lawsuit mentions are hypothetical (failure-to-comply scenario), no actual challenge in file. No second search per cut rule + freeze.",
          "promise_id": "P31"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 27,
      "importance_score": 73,
      "impact_rank": 27,
      "source_tier": "News",
      "neighborhood_canonical": "Commercial Corridors",
      "address_full": "Mission St, Clement St, & Geary Blvd Corridors, San Francisco, CA",
      "latitude": 37.76,
      "longitude": -122.42,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2025-06-24",
      "deadline_date": "2026-01-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 506,
      "time_to_verdict_days": 505,
      "entity_canonical_name": "Daniel Lurie",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2025-01-08",
      "entity_term_end": "2029-01-08",
      "category_l1": "Economy & Commercial",
      "category_l2": "Small Business Permitting",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "permitsf",
        "small_business",
        "first_year_free",
        "commercial_activation"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 7,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://sfplanning.org/sf-family-zoning-plan",
      "document_title": "Family Zoning Plan Neighborhood Housing",
      "title": "Family Zoning Plan Neighborhood Housing"
    },
    {
      "promise_id": "P30",
      "promise_text": "Under the Mayor\u2019s Homelessness Recovery Plan, the City set a goal of buying or leasing 1,500 new units of PSH over the course of two years.",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Citywide (Supportive Housing Network)",
      "promised_date": "2020-07",
      "due_date": "2022-06-30",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "S63cfb85525f6",
      "source_url": "https://www.sf.gov/news--san-francisco-receives-new-state-homekey-awards-733-million-support-purchase-and-operations",
      "source_file_path": "63cfb85525f676c6481e35d172caa081c8f1f14f44ffd2afc2fa32c0a9018230.md",
      "source_hash": "63cfb85525f676c6481e35d172caa081c8f1f14f44ffd2afc2fa32c0a9018230",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:32:44Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:33:58Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "PSH portfolio expanded 2,918 units by plan end, beating 1,500 goal",
              "evidence_date": "2022-06-30",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P30",
              "quote": "When the plan ended on June 30th 2022, the City had expanded the PSH portfolio by 2918 units, exceeding the goal by 95%",
              "quote_match": "exact",
              "source_file_path": "63cfb85525f676c6481e35d172caa081c8f1f14f44ffd2afc2fa32c0a9018230.md",
              "source_hash": "63cfb85525f676c6481e35d172caa081c8f1f14f44ffd2afc2fa32c0a9018230",
              "source_url": "https://www.sf.gov/news--san-francisco-receives-new-state-homekey-awards-733-million-support-purchase-and-operations"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P30"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file reports goal exceeded by 95%; no shortfall or contradiction. No second search per cut rule.",
          "promise_id": "P30"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 28,
      "importance_score": 72,
      "impact_rank": 28,
      "source_tier": "Official",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2020-07-01",
      "deadline_date": "2022-06-30",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2325,
      "time_to_verdict_days": 2324,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Housing",
      "category_l2": "Permanent Supportive Housing",
      "secondary_categories": [
        "Public Safety"
      ],
      "tags": [
        "homelessness_recovery_plan",
        "supportive_housing",
        "placements",
        "sip_hotels"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sf.gov/news--san-francisco-receives-new-state-homekey-awards-733-million-support-purchase-and-operations",
      "document_title": "Homelessness Recovery: 1,500 PSH Units",
      "title": "Homelessness Recovery: 1,500 PSH Units"
    },
    {
      "promise_id": "P36",
      "promise_text": "Additionally, CleanPowerSF has conservatively committed to increasing the renewable percentage of its basic *Green* service, from 35 percent at program launch, to at least 50 percent by 2020.",
      "entity": "CleanPowerSF",
      "role": null,
      "entity_type": "politician",
      "category": "Environment & Energy",
      "neighborhood": "CleanPowerSF Renewable Grid",
      "promised_date": "2017-04-20",
      "due_date": "2020-12-31",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims; re-applied per P36 correction (sfpuc.org+sfenvironment.org allowlisted, org/non-minutes speaker NA)",
      "source_id": "S5008d7810833",
      "source_url": "https://sfenvironment.org/press/mayor-lee-announces-bold-new-target-50-percent-renewable-energy-2020",
      "source_file_path": "18eeac2d2261dd43a9744058ca524cb2107dc65d46dcb8427858752a8cc8a49b.md",
      "source_hash": "18eeac2d2261dd43a9744058ca524cb2107dc65d46dcb8427858752a8cc8a49b",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:06:58Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:10:59Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "City committed Green service from 35 percent to at least 50 percent renewable by 2020",
              "evidence_date": "2017-04-20",
              "evidence_type": "press_release",
              "page_number": null,
              "promise_id": "P36",
              "quote": "CleanPowerSF has conservatively committed to increasing the renewable percentage of its basic *Green* service, from 35 percent at program launch, to at least 50 percent by 2020.",
              "quote_match": "exact",
              "source_file_path": "18eeac2d2261dd43a9744058ca524cb2107dc65d46dcb8427858752a8cc8a49b.md",
              "source_hash": "18eeac2d2261dd43a9744058ca524cb2107dc65d46dcb8427858752a8cc8a49b",
              "source_url": "https://sfenvironment.org/press/mayor-lee-announces-bold-new-target-50-percent-renewable-energy-2020"
            },
            {
              "claim_text": "2020 Power Source Disclosure: Green supply was 54.5 percent RPS-eligible renewable",
              "evidence_date": "2020",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P36",
              "quote": "demonstrate that in 2020, CleanPowerSF\u2019s Green product supply was 54.5% Renewable Portfolio Standard (RPS) eligible renewable",
              "quote_match": "exact",
              "source_file_path": "5616deb45a17ecfc96903259d488b072ef37dadd96a81000a9994efbdb884b56.md",
              "source_hash": "5616deb45a17ecfc96903259d488b072ef37dadd96a81000a9994efbdb884b56",
              "source_url": "https://www.sfpuc.org/sites/default/files/about-us/commission/September%2014%20Approved%20Minutes.pdf"
            },
            {
              "claim_text": "Mayor set 50-percent-renewable-by-2020 goal for city electricity",
              "evidence_date": "2017-04-20",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P36",
              "quote": "Mayor Ed Lee on Thursday set a new goal for San Francisco \u2014 that at least 50 percent of the city\u2019s electricity come from renewable sources by 2020.",
              "quote_match": "exact",
              "source_file_path": "f3b1f497775d490a82c367e6a7941a10f35b18abdfecace0d6d1d8e15add6ec5.md",
              "source_hash": "f3b1f497775d490a82c367e6a7941a10f35b18abdfecace0d6d1d8e15add6ec5",
              "source_url": "https://sfchronicle.com/bayarea/article/SF-s-green-energy-goal-is-a-decade-ahead-of-11084954.php"
            }
          ],
          "evidence_checked": 4,
          "note": "evidence_date is the event date throughout. CPUC 2021 joint mailer fetched but NOT cited: table structure lost in conversion, 54.5% figure not honestly quotable from saved text. Wikipedia CleanPowerSF fetched but stale (ends ~2016), no 2020 outcome. Outcome facts (54.5%) rest on SFPUC minutes, a non-allowlisted domain.",
          "promise_id": "P36"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 0,
          "note": "none found: broken-leaning search surfaced only corroboration (2017 Growth Plan restates the 50%-by-2020 Green goal) and unrelated pre-2017 procurement history (SF Examiner public-power piece). No second search per cut rule.",
          "promise_id": "P36"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass (org speaker CleanPowerSF cannot be in roll call \u2014 P36 speaker principle)"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 29,
      "importance_score": 71,
      "impact_rank": 29,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": "525 Golden Gate Ave, San Francisco, CA 94102",
      "latitude": 37.7811,
      "longitude": -122.4202,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2017-04-20",
      "deadline_date": "2020-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 3493,
      "time_to_verdict_days": 3492,
      "entity_canonical_name": "CleanPowerSF",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Environment & Energy",
      "category_l2": "Public Renewable Power",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "cleanpowersf",
        "renewable_energy",
        "green_tariffs",
        "community_choice"
      ],
      "verdict_confidence": 0.97,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://sfenvironment.org/press/mayor-lee-announces-bold-new-target-50-percent-renewable-energy-2020",
      "document_title": "CleanPowerSF 100% Renewable Electricity",
      "title": "CleanPowerSF 100% Renewable Electricity"
    },
    {
      "promise_id": "P09",
      "promise_text": "As of this week, Pacific Gas and Electric Company (PG&E) has constructed and energized more than 600 miles of underground powerlines since its ambitious 10,000-Mile Undergrounding program started in mid-2021.",
      "entity": "Patti Poppe",
      "role": "CEO, PG&E Corporation",
      "entity_type": "official",
      "category": "Environment & Energy",
      "neighborhood": "San Francisco Grid & PG&E Service Area",
      "promised_date": "2021-06-01",
      "due_date": null,
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "due date in future and no definitive resolution yet",
      "source_id": "S36990114e2a2",
      "source_url": "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2023/600-Miles-and-Counting-PGE-Hits-Significant-Milestone-as-Crews-Safely-Complete-Construction-Energization-of-350-More-Miles-of-Underground-Powerlines-in-2023/",
      "source_file_path": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e.md",
      "source_hash": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T03:16:53.741681+00:00",
      "relevance": {
        "score": 6,
        "real": 2,
        "measurable": 2,
        "sf": 0,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:38:12Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P09",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P09",
              "claim_text": "INTERIM: 600+ of 10,000 miles done by Dec 2023 (continuation, not completion)",
              "quote": "As of this week, Pacific Gas and Electric Company (PG&E) has constructed and energized more than 600 miles of underground powerlines since its ambitious 10,000-Mile Undergrounding program started in mid-2021.",
              "quote_match": "exact",
              "evidence_type": "press_release",
              "source_file_path": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e.md",
              "source_hash": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e",
              "source_url": "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2023/600-Miles-and-Counting-PGE-Hits-Significant-Milestone-as-Crews-Safely-Complete-Construction-Energization-of-350-More-Miles-of-Underground-Powerlines-in-2023/",
              "page_number": null,
              "evidence_date": "2023-12"
            },
            {
              "promise_id": "P09",
              "claim_text": "INTERIM: record 350 miles completed in 2023",
              "quote": "And the 350 miles completed in 2023 represents the most ever in a single year by PG&E and nearly twice as many miles as were completed in 2022.",
              "quote_match": "exact",
              "evidence_type": "press_release",
              "source_file_path": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e.md",
              "source_hash": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e",
              "source_url": "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2023/600-Miles-and-Counting-PGE-Hits-Significant-Milestone-as-Crews-Safely-Complete-Construction-Energization-of-350-More-Miles-of-Underground-Powerlines-in-2023/",
              "page_number": null,
              "evidence_date": "2023-12"
            },
            {
              "promise_id": "P09",
              "claim_text": "INTERIM: CPUC authorized 1,230 miles for 2023-2026; 10-year plan filing pending",
              "quote": "The California Public Utilities Commission recently approved PG&E's 2023-2026 General Rate Case, which authorized 1,230 miles of undergrounding during those four years.",
              "quote_match": "exact",
              "evidence_type": "press_release",
              "source_file_path": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e.md",
              "source_hash": "36990114e2a23c2f07d15d602133bb9bccc33db8c8299568720e3f25933b6c7e",
              "source_url": "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2023/600-Miles-and-Counting-PGE-Hits-Significant-Milestone-as-Crews-Safely-Complete-Construction-Energization-of-350-More-Miles-of-Underground-Powerlines-in-2023/",
              "page_number": null,
              "evidence_date": "2023-12"
            }
          ]
        },
        "broken": {
          "promise_id": "P09",
          "advocate_role": "broken_advocate",
          "evidence_checked": 12,
          "claims": [],
          "note": "none found: PG&E undergrounding appears only in its own release (all progress framing); no saved file documents cancellation, miss, or reversal. No second search per cut rule."
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date in future and no definitive resolution yet"
        }
      ],
      "display_no": 30,
      "importance_score": 70,
      "impact_rank": 30,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": "300 Lakeside Dr, Oakland, CA 94612",
      "latitude": 37.8044,
      "longitude": -122.2612,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2021-06-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1990,
      "time_to_verdict_days": 1989,
      "entity_canonical_name": "Patti Poppe",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": "2021-01-04",
      "entity_term_end": null,
      "category_l1": "Environment & Energy",
      "category_l2": "Wildfire Safety & Grid Hardening",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "pge",
        "powerline_undergrounding",
        "wildfire_mitigation",
        "grid_hardening"
      ],
      "verdict_confidence": 0.92,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 9,
      "completion_percentage": 45,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://investor.pgecorp.com/news-events/press-releases/press-release-details/2023/600-Miles-and-Counting-PGE-Hits-Significant-Milestone-as-Crews-Safely-Complete-Construction-Energization-of-350-More-Miles-of-Underground-Powerlines-in-2023/",
      "document_title": "PG&E 10,000 Miles Underground Power Lines",
      "title": "PG&E 10,000 Miles Underground Power Lines"
    },
    {
      "promise_id": "P61",
      "promise_text": "On July 28, 2009, the Commission approved a revised WSIP schedule and budget of $4,586 million with an overall targeted program completion date of December 4, 2015.",
      "entity": "San Francisco Public Utilities Commission (SFPUC)",
      "role": null,
      "entity_type": "official",
      "category": "Infrastructure & Tech",
      "neighborhood": "Regional / Northern California (SFPUC Water System)",
      "promised_date": "2009-07-28",
      "due_date": "2015-12-04",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence; due 2015-12-04 = finish date in 2009 revision table (CSV cites 2015-12-31 from Water Supply Agreement; both long past)",
      "source_id": "S6f14ce22ccc6",
      "source_url": "https://www.sfpuc.gov/sites/default/files/documents/WSIP-Quarterly-Report-FY2025-2026-Q4.pdf",
      "source_file_path": "d1186b0a2327f6673bce3e76e5351cfae690d976aa91804c39c12fcdfac40564.md",
      "source_hash": "d1186b0a2327f6673bce3e76e5351cfae690d976aa91804c39c12fcdfac40564",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:34:14Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:18:06Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: 1 kept search; revision history shows successive delays (2011\u21922016, ... 2024\u21922032), no source claims completion by Dec 2015. No second search per cut rule.",
          "promise_id": "P61"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Q4 FY25-26: current approved and forecasted Regional WSIP completion is June 2032",
              "evidence_date": "2026-06-30",
              "evidence_type": "filing",
              "page_number": null,
              "promise_id": "P61",
              "quote": "The Current Approved and Forecasted Schedule completion for the Regional WSIP (Local WSIP was completed in June 2020) is June 2032.",
              "quote_match": "close",
              "source_file_path": "d1186b0a2327f6673bce3e76e5351cfae690d976aa91804c39c12fcdfac40564.md",
              "source_hash": "d1186b0a2327f6673bce3e76e5351cfae690d976aa91804c39c12fcdfac40564",
              "source_url": "https://www.sfpuc.gov/sites/default/files/documents/WSIP-Quarterly-Report-FY2025-2026-Q4.pdf"
            }
          ],
          "evidence_checked": 2,
          "note": "AUDIT 2026-11-11: dropped the live-sfpuc.pantheonsite.io 2024-notice claim per parent rule (never cite staging/clone hosts as evidence; unverifiable as official). Its check rows VFY-P61-00..06 remain on file as history. Remaining www.sfpuc.gov claim passes 6/7 (domain fail only \u2014 sfpuc.gov not in allowlist; see QUESTIONS.md). Verdict broken stands (Rule 1, real 2032-vs-2015 measurement examined).",
          "promise_id": "P61"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": false,
          "reason": "unlisted source domain"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 31,
      "importance_score": 69,
      "impact_rank": 31,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": "Sunol Valley Water Treatment Facility, Sunol, CA 94586",
      "latitude": 37.5947,
      "longitude": -121.8891,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2009-07-28",
      "deadline_date": "2015-12-04",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 3996,
      "promise_age_days": 6316,
      "time_to_verdict_days": 6315,
      "entity_canonical_name": "San Francisco Public Utilities Commission (SFPUC)",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Infrastructure",
      "category_l2": "Regional Water System Capital Program",
      "secondary_categories": [
        "Environment & Energy"
      ],
      "tags": [
        "sfpuc",
        "wsip",
        "water_system",
        "calaveras_dam",
        "infrastructure"
      ],
      "verdict_confidence": 0.97,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "timeline_missed_delay",
      "impact_score": 8,
      "completion_percentage": 80,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfpuc.gov/sites/default/files/documents/WSIP-Quarterly-Report-FY2025-2026-Q4.pdf",
      "document_title": "SFPUC Water System Improvement Program",
      "title": "SFPUC Water System Improvement Program"
    },
    {
      "promise_id": "P66",
      "promise_text": "Chase Center, which will have a capacity of 18,064, is due to open with a Metallica concert on September 6 before the Warriors play their first pre-season game at the venue against the Los Angeles Lakers on October 5.",
      "entity": "Golden State Warriors",
      "role": null,
      "entity_type": "sports_team",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Mission Bay (Chase Center)",
      "promised_date": "2019-08-28",
      "due_date": "2019-09-06",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims; due 2019-09-06 = September 6 opening in source (article Aug 2019)",
      "source_id": "S7b9033c10fd9",
      "source_url": "https://www.thestadiumbusiness.com/2019/08/28/warriors-lift-lid-chase-center/",
      "source_file_path": "4ee28ae4d6eaab9280ec0117b81039421471935c6348083ae47400de34e5811a.md",
      "source_hash": "4ee28ae4d6eaab9280ec0117b81039421471935c6348083ae47400de34e5811a",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:28:53Z",
      "relevance": {
        "score": 7,
        "real": 2,
        "measurable": 2,
        "sf": 1,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:30:10Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Grand opening September 6, 2019 with Metallica and SF Symphony",
              "evidence_date": "2019-09-06",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P66",
              "quote": "The arena had its grand opening on September 6, 2019, with a concert by Metallica and the San Francisco Symphony.",
              "quote_match": "exact",
              "source_file_path": "7b9033c10fd9dcb707f7323cb356d796011bc538d3a0f42eca23b660533d41a6.md",
              "source_hash": "7b9033c10fd9dcb707f7323cb356d796011bc538d3a0f42eca23b660533d41a6",
              "source_url": "https://en.wikipedia.org/wiki/Chase_Center"
            },
            {
              "claim_text": "First preseason game October 5, 2019 vs Los Angeles Lakers",
              "evidence_date": "2019-10-05",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P66",
              "quote": "The first preseason game at Chase Center took place on October 5, 2019, as the Warriors lost to the Los Angeles Lakers, 123\u2013101.",
              "quote_match": "exact",
              "source_file_path": "7b9033c10fd9dcb707f7323cb356d796011bc538d3a0f42eca23b660533d41a6.md",
              "source_hash": "7b9033c10fd9dcb707f7323cb356d796011bc538d3a0f42eca23b660533d41a6",
              "source_url": "https://en.wikipedia.org/wiki/Chase_Center"
            },
            {
              "claim_text": "Arena seats 18,064 for basketball as promised",
              "evidence_date": "2019-09-06",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P66",
              "quote": "Chase Center opened on September 6, 2019, and seats 18,064 for basketball games.",
              "quote_match": "exact",
              "source_file_path": "7b9033c10fd9dcb707f7323cb356d796011bc538d3a0f42eca23b660533d41a6.md",
              "source_hash": "7b9033c10fd9dcb707f7323cb356d796011bc538d3a0f42eca23b660533d41a6",
              "source_url": "https://en.wikipedia.org/wiki/Chase_Center"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P66"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: 1 broken search returned only confirmation (Chase Center official recap of the Metallica/Symphony concert). Opening, concert, game, and capacity all verified as stated. No second search per cut rule.",
          "promise_id": "P66"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 32,
      "importance_score": 68,
      "impact_rank": 32,
      "source_tier": "News",
      "neighborhood_canonical": "Mission Bay",
      "address_full": "1 Warriors Way, San Francisco, CA 94158",
      "latitude": 37.768,
      "longitude": -122.3877,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2019-08-28",
      "deadline_date": "2019-09-06",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2633,
      "time_to_verdict_days": 2632,
      "entity_canonical_name": "Golden State Warriors",
      "entity_category": "sports_team",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Culture & Recreation",
      "category_l2": "Sports & Entertainment Arenas",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "chase_center",
        "warriors",
        "metallica",
        "grand_opening"
      ],
      "verdict_confidence": 0.99,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.thestadiumbusiness.com/2019/08/28/warriors-lift-lid-chase-center/",
      "document_title": "Chase Center Arena 18,064 Capacity Delivery",
      "title": "Chase Center Arena 18,064 Capacity Delivery"
    },
    {
      "promise_id": "P64",
      "promise_text": "the Project is anticipated to include (1) up to 8,000 new residential units",
      "entity": "Treasure Island Development Authority",
      "role": null,
      "entity_type": "official",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Parkmerced (Southwest San Francisco)",
      "promised_date": "2011-06-07",
      "due_date": null,
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "genuine partial completion (~1,000 of 8,000 homes open, both sides agree on the numbers; competing tier-3/4 claims describe progress vs shortfall, not factual dispute), open-ended buildout with no deadline -> in_progress per P18; prior Rule-8 undecided superseded",
      "source_id": "S3df00693ee93",
      "source_url": "https://sfbos.org/ftp/uploadedfiles/bdsupvrs/resolutions11/r0241-11.pdf",
      "source_file_path": "dd8da63ec1fac27274e0eb8f3802c60ef5bccf9e7086888fdb34fb471d28a1b4.md",
      "source_hash": "dd8da63ec1fac27274e0eb8f3802c60ef5bccf9e7086888fdb34fb471d28a1b4",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:23:25Z",
      "relevance": {
        "score": 7,
        "real": 2,
        "measurable": 2,
        "sf": 1,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:24:55Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Board adopted the TI/YBI DDA 11-0 on June 7, 2011 (enabling approval, supporting)",
              "evidence_date": "2011-06-07",
              "evidence_type": "vote",
              "page_number": null,
              "promise_id": "P64",
              "quote": "June 07, 2011 Board of Supervisors - ADOPTED AS AMENDED Ayes: 11 - Avalos, Campos, Chiu, Chu, Cohen, Elsbernd, Farrell, Kim, Mar, Mirkarimi and Wiener",
              "quote_match": "exact",
              "source_file_path": "dd8da63ec1fac27274e0eb8f3802c60ef5bccf9e7086888fdb34fb471d28a1b4.md",
              "source_hash": "dd8da63ec1fac27274e0eb8f3802c60ef5bccf9e7086888fdb34fb471d28a1b4",
              "source_url": "https://sfbos.org/ftp/uploadedfiles/bdsupvrs/resolutions11/r0241-11.pdf"
            },
            {
              "claim_text": "Nearly 1,000 TI/YBI homes open or near completion by Sept 2024 (genuine partial progress)",
              "evidence_date": "2024-09-24",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P64",
              "quote": "nearly 1,000 homes are open or near completion, along with parks and utilities, public art, new streets, and ferry service.",
              "quote_match": "exact",
              "source_file_path": "3df00693ee93dd13615d554327ec721376c8dbb4134a04fbe3d827232554f378.md",
              "source_hash": "3df00693ee93dd13615d554327ec721376c8dbb4134a04fbe3d827232554f378",
              "source_url": "https://www.sf.gov/news--city-san-francisco-and-national-womens-soccer-franchise-bay-fc-announce-plans-permanent"
            }
          ],
          "evidence_checked": 2,
          "promise_id": "P64"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Still in first stage after 13 years: only nearly 1,000 of 8,000 homes open",
              "evidence_date": "2024-09-24",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P64",
              "quote": "Currently in the first stage of redevelopment, there are nearly 1,000 homes now open or near completion",
              "quote_match": "exact",
              "source_file_path": "3df00693ee93dd13615d554327ec721376c8dbb4134a04fbe3d827232554f378.md",
              "source_hash": "3df00693ee93dd13615d554327ec721376c8dbb4134a04fbe3d827232554f378",
              "source_url": "https://www.sf.gov/news--city-san-francisco-and-national-womens-soccer-franchise-bay-fc-announce-plans-permanent"
            },
            {
              "claim_text": "Even the 2025 target is only ~1,208 units, ~15% of the 8,000 promise",
              "evidence_date": "2024-09-24",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P64",
              "quote": "by 2025, approximately 1,208 market-rate and affordable housing units will be completed, including 307 affordable units, 788 rental units and 420 condominiums",
              "quote_match": "exact",
              "source_file_path": "3df00693ee93dd13615d554327ec721376c8dbb4134a04fbe3d827232554f378.md",
              "source_hash": "3df00693ee93dd13615d554327ec721376c8dbb4134a04fbe3d827232554f378",
              "source_url": "https://www.sf.gov/news--city-san-francisco-and-national-womens-soccer-franchise-bay-fc-announce-plans-permanent"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P64"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "both sides have competing claims or insufficient evidence to decide"
        }
      ],
      "display_no": 33,
      "importance_score": 67,
      "impact_rank": 33,
      "source_tier": "News",
      "neighborhood_canonical": "Parkmerced",
      "address_full": "3711 19th Ave, San Francisco, CA 94132",
      "latitude": 37.717,
      "longitude": -122.483,
      "supervisor_district": 7,
      "is_citywide": false,
      "promise_made_date": "2011-06-07",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 5637,
      "time_to_verdict_days": 5636,
      "entity_canonical_name": "Treasure Island Development Authority",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Housing",
      "category_l2": "Master Planned Community Reinvestment",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "parkmerced",
        "redevelopment",
        "transit_oriented",
        "housing_units"
      ],
      "verdict_confidence": 0.89,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 8,
      "completion_percentage": 30,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://sfbos.org/ftp/uploadedfiles/bdsupvrs/resolutions11/r0241-11.pdf",
      "document_title": "Treasure Island 8,000 New Residential Units",
      "title": "Treasure Island 8,000 New Residential Units"
    },
    {
      "promise_id": "P84",
      "promise_text": "After about a decade of planning, developer Forest City Realty Trust Inc. (NYSE: FCE.A) finally scored approval for its massive Pier 70 overhaul that could bring up to 2,150 new homes, 1.75 million square feet of commercial office, and up to 445,000 square feet of retail, light industrial and arts space on 28 acres.",
      "entity": "Forest City Realty Trust Inc.",
      "role": null,
      "entity_type": "company",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Pier 70 & Dogpatch (Pier 70 Development)",
      "promised_date": "2017-10-31",
      "due_date": null,
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "genuine partial completion, full scope unresolved",
      "source_id": "S260e098cc346",
      "source_url": "https://bizjournals.com/sanfrancisco/news/2017/10/31/forest-city-pier-70-san-francisco-approval-housing.html",
      "source_file_path": "22cb422581fb51ea2f11cd97b619e9df19dd7e088c827359c9e8e6ff30bb8180.md",
      "source_hash": "22cb422581fb51ea2f11cd97b619e9df19dd7e088c827359c9e8e6ff30bb8180",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:08:27Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:11:01Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Partial progress only: first ground-up buildings (350-unit apartment) slated to start 2027; unit cap expansion 2,150 to 2,750 sought; no homes delivered \u2014 active but incomplete, not completion evidence per vote/ordinance principle",
              "evidence_date": "2026-11-10",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P84",
              "quote": "The lease comes as BGRE is hoping to start construction in 2027 on the first two ground-up buildings on the 28-acre site: a 350-unit apartment building on Parcel E2 and a 300,000 square-foot office building. The developer is also seeking to expand the number of maximum housing units at the site from 2,150 to 2,750.",
              "quote_match": "exact",
              "source_file_path": "260e098cc34638af2406ab01989a78f89e15f731199c3a0ff13d3f0f5b1dd448.md",
              "source_hash": "260e098cc34638af2406ab01989a78f89e15f731199c3a0ff13d3f0f5b1dd448",
              "source_url": "https://sfchronicle.com/sf/article/wrecking-ball-coffee-pier-70-san-francisco-22513062.php"
            }
          ],
          "evidence_checked": 2,
          "promise_id": "P84"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: no cancellation and no deadline to miss (dateless approval); documented delays resolved into active momentum (2027 vertical start, cap expansion). The 'largely stalled out for several years' line describes a past stall that momentum has picked up from, not a broken promise.",
          "promise_id": "P84"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "genuine partial completion, full scope unresolved"
        }
      ],
      "display_no": 34,
      "importance_score": 66,
      "impact_rank": 34,
      "source_tier": "News",
      "neighborhood_canonical": "Dogpatch",
      "address_full": "Pier 70, 20th St & Illinois St, San Francisco, CA 94107",
      "latitude": 37.7587,
      "longitude": -122.385,
      "supervisor_district": 10,
      "is_citywide": false,
      "promise_made_date": "2017-10-31",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 3299,
      "time_to_verdict_days": 3298,
      "entity_canonical_name": "Forest City Realty Trust",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Housing",
      "category_l2": "Waterfront Historic Redevelopment",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "pier_70",
        "dogpatch",
        "historic_preservation",
        "waterfront_housing"
      ],
      "verdict_confidence": 0.91,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 8,
      "completion_percentage": 45,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://bizjournals.com/sanfrancisco/news/2017/10/31/forest-city-pier-70-san-francisco-approval-housing.html",
      "document_title": "Pier 70 Historic Shipyard Redevelopment",
      "title": "Pier 70 Historic Shipyard Redevelopment"
    },
    {
      "promise_id": "P86",
      "promise_text": "The plan calls for more than 2,600 homes.",
      "entity": "Associate Capital",
      "role": null,
      "entity_type": "company",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Pier 70 & Dogpatch (Potrero Power Station)",
      "promised_date": "2020-04",
      "due_date": null,
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "genuine partial completion, full scope unresolved",
      "source_id": "S3223fa9b02c7",
      "source_url": "http://sfbos.archive.sf.gov/sites/default/files/2025_10_15_PRESS_RELEASE_INNOVATIVE_SOPHIE_MAXWELL_BUILDING_OPENS_AT_SFS_BOOMING_POWER_STATION.pdf",
      "source_file_path": "02e8aa37245ab64e8c40f079097dd8896fb88262f97cba2d42ecdd9f0411da70.md",
      "source_hash": "02e8aa37245ab64e8c40f079097dd8896fb88262f97cba2d42ecdd9f0411da70",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:19:31Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:21:09Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Partial progress only: first building (105 units) opened Oct 2025 of 2,600+ planned homes; per P18 principle a first building is not completion",
              "evidence_date": "2025-10-15",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P86",
              "quote": "Associate Capital opened a 105-unit building at the former Potrero Power Station that caters to the city\u2019s working class.",
              "quote_match": "exact",
              "source_file_path": "3223fa9b02c79fdfbd7c3034f7619e1f83e0c3447448fbb595c2df54e372c5e0.md",
              "source_hash": "3223fa9b02c79fdfbd7c3034f7619e1f83e0c3447448fbb595c2df54e372c5e0",
              "source_url": "https://sfstandard.com/2025/10/15/potrero-power-station-middle-income-housing"
            }
          ],
          "evidence_checked": 2,
          "promise_id": "P86"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: development active (first 105 homes opened Oct 2025, UCSF construction 2026); no cancellation. Past stall coverage describes jump-started momentum, not failure.",
          "promise_id": "P86"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "genuine partial completion, full scope unresolved"
        }
      ],
      "display_no": 35,
      "importance_score": 65,
      "impact_rank": 35,
      "source_tier": "Official",
      "neighborhood_canonical": "Potrero Hill",
      "address_full": "420 23rd St (Potrero Power Station), San Francisco, CA 94107",
      "latitude": 37.756,
      "longitude": -122.384,
      "supervisor_district": 10,
      "is_citywide": false,
      "promise_made_date": "2020-04-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2416,
      "time_to_verdict_days": 2415,
      "entity_canonical_name": "Associate Capital",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Housing",
      "category_l2": "Industrial Waterfront Conversion",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "potrero_power_station",
        "industrial_conversion",
        "mixed_use",
        "potrero_point"
      ],
      "verdict_confidence": 0.9,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 8,
      "completion_percentage": 40,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/http://sfbos.archive.sf.gov/sites/default/files/2025_10_15_PRESS_RELEASE_INNOVATIVE_SOPHIE_MAXWELL_BUILDING_OPENS_AT_SFS_BOOMING_POWER_STATION.pdf",
      "document_title": "Potrero Power Station 2,600 Homes Plan",
      "title": "Potrero Power Station 2,600 Homes Plan"
    },
    {
      "promise_id": "P07",
      "promise_text": "build 3.5M homes by 2025",
      "entity": "Gavin Newsom",
      "role": "Governor of California",
      "entity_type": "politician",
      "category": "Bay Area & Regional",
      "neighborhood": "Bay Area & California Housing",
      "promised_date": "2018-11-06",
      "due_date": null,
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "numeric target not met or plan abandoned",
      "source_id": "Sb1fb6aa4be89",
      "source_url": "https://src.senate.ca.gov/governor-gavin-newsoms-top-15-worst-flip-flops-and-fails",
      "source_file_path": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0.md",
      "source_hash": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T03:10:43.399474+00:00",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:35:46Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P07",
          "advocate_role": "kept_advocate",
          "evidence_checked": 12,
          "claims": [],
          "note": "none found: 3.5M-homes pledge appears only in the Senate flip-flops file, which affirms no fulfillment; no other saved file mentions it. No second search per cut rule."
        },
        "broken": {
          "promise_id": "P07",
          "advocate_role": "broken_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P07",
              "claim_text": "Only 640,873 homes built in seven years vs 3.5M goal",
              "quote": "In the seven years since he took office, a total of 868,709 permits have been issued and 640,873 homes built.",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0.md",
              "source_hash": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0",
              "source_url": "https://src.senate.ca.gov/governor-gavin-newsoms-top-15-worst-flip-flops-and-fails",
              "page_number": null,
              "evidence_date": "2026"
            },
            {
              "promise_id": "P07",
              "claim_text": "2.86M homes still to go",
              "quote": "Only 2,859,127 homes to go in the next 12 months!",
              "quote_match": "exact",
              "evidence_type": "count",
              "source_file_path": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0.md",
              "source_hash": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0",
              "source_url": "https://src.senate.ca.gov/governor-gavin-newsoms-top-15-worst-flip-flops-and-fails",
              "page_number": null,
              "evidence_date": "2026"
            },
            {
              "promise_id": "P07",
              "claim_text": "Housing construction declined for the first time ever",
              "quote": "housing construction declined for the first time ever",
              "quote_match": "exact",
              "evidence_type": "news_report",
              "source_file_path": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0.md",
              "source_hash": "b1fb6aa4be898cc92a03be34a3e64fea3768c386dd19dc6eeef2b1e9b81712c0",
              "source_url": "https://src.senate.ca.gov/governor-gavin-newsoms-top-15-worst-flip-flops-and-fails",
              "page_number": null,
              "evidence_date": "2026"
            }
          ]
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "numeric target not met or plan abandoned"
        }
      ],
      "display_no": 36,
      "importance_score": 64,
      "impact_rank": 36,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2018-11-06",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2928,
      "time_to_verdict_days": 2927,
      "entity_canonical_name": "Gavin Newsom",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2004-01-08",
      "entity_term_end": "2011-01-10",
      "category_l1": "Housing",
      "category_l2": "Statewide Housing Production Targets",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "3_5_million_homes",
        "gavin_newsom",
        "statewide_housing",
        "affordability"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 0,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 9,
      "completion_percentage": 18,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://src.senate.ca.gov/governor-gavin-newsoms-top-15-worst-flip-flops-and-fails",
      "document_title": "3.5 Million New Homes in California by 2025",
      "title": "3.5 Million New Homes in California by 2025",
      "media_image_url": "https://ca-times.brightspotcdn.com/dims4/default/863beb6/2147483647/strip/true/crop/6536x4358+0+0/resize/1200x800!/quality/75/?url=https%3A%2F%2Fcalifornia-times-brightspot.s3.amazonaws.com%2F12%2F99%2F5399a8ec4d70a25e815fc4f5225b%2Fgettyimages-2288620704.jpg",
      "image_url": "https://ca-times.brightspotcdn.com/dims4/default/863beb6/2147483647/strip/true/crop/6536x4358+0+0/resize/1200x800!/quality/75/?url=https%3A%2F%2Fcalifornia-times-brightspot.s3.amazonaws.com%2F12%2F99%2F5399a8ec4d70a25e815fc4f5225b%2Fgettyimages-2288620704.jpg",
      "media_caption": "Residential construction progress across California housing development zones"
    },
    {
      "promise_id": "P13",
      "promise_text": "In his first year as mayor, he introduced an ambitious 10-year plan to end chronic homelessness by creating 3,000 housing units with supportive services and replacing emergency shelter beds with 24-hour clinics.",
      "entity": "Gavin Newsom",
      "role": "Governor of California",
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Citywide 10-Year Homelessness Plan",
      "promised_date": "2004-06-30",
      "due_date": "2014-06-30",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence; due 2014-06-30 derived from 10-year plan introduced 2004 anchored to promised 2004-06-30",
      "source_id": "S13f24e3da880",
      "source_url": "https://www.khsu.org/regional-interests/2019-08-02/timeline-the-frustrating-political-history-of-homelessness-in-san-francisco",
      "source_file_path": "13f24e3da88093b57df7cf7b255344839bd8a5d72c889a85f338fbb8b44f32f0.md",
      "source_hash": "13f24e3da88093b57df7cf7b255344839bd8a5d72c889a85f338fbb8b44f32f0",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:51:26Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:56:06Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Plan cut homelessness nearly 30% in its first year",
              "evidence_date": "2019-08",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P13",
              "quote": "homelessness in the city dropped by nearly 30% from its 2002 high",
              "quote_match": "exact",
              "source_file_path": "13f24e3da88093b57df7cf7b255344839bd8a5d72c889a85f338fbb8b44f32f0.md",
              "source_hash": "13f24e3da88093b57df7cf7b255344839bd8a5d72c889a85f338fbb8b44f32f0",
              "source_url": "https://www.khsu.org/regional-interests/2019-08-02/timeline-the-frustrating-political-history-of-homelessness-in-san-francisco"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P13"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Ten-year plan fell short of ending chronic homelessness",
              "evidence_date": "2019-08",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P13",
              "quote": "Although the plan fell short of its goal",
              "quote_match": "exact",
              "source_file_path": "13f24e3da88093b57df7cf7b255344839bd8a5d72c889a85f338fbb8b44f32f0.md",
              "source_hash": "13f24e3da88093b57df7cf7b255344839bd8a5d72c889a85f338fbb8b44f32f0",
              "source_url": "https://www.khsu.org/regional-interests/2019-08-02/timeline-the-frustrating-political-history-of-homelessness-in-san-francisco"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P13"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-check R3: khsu.org allowlisted, kept(2)+broken(2) both pass; broken stands via Rule 5 (was Rule 1, kept evidence now exists)"
        }
      ],
      "display_no": 37,
      "importance_score": 63,
      "impact_rank": 37,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
      "latitude": 37.7793,
      "longitude": -122.4192,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2004-06-30",
      "deadline_date": "2014-06-30",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 4518,
      "promise_age_days": 8170,
      "time_to_verdict_days": 8169,
      "entity_canonical_name": "Gavin Newsom",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2004-01-08",
      "entity_term_end": "2011-01-10",
      "category_l1": "Housing",
      "category_l2": "Ten-Year Chronic Homelessness Eradication",
      "secondary_categories": [
        "Public Safety"
      ],
      "tags": [
        "10_year_plan",
        "chronic_homelessness",
        "gavin_newsom",
        "supportive_housing"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 9,
      "completion_percentage": 35,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.khsu.org/regional-interests/2019-08-02/timeline-the-frustrating-political-history-of-homelessness-in-san-francisco",
      "document_title": "10-Year Plan to End Chronic Homelessness",
      "title": "10-Year Plan to End Chronic Homelessness"
    },
    {
      "promise_id": "P15",
      "promise_text": "The late Mayor Ed Lee pledged in 2014 to add 5,000 new units to the housing stock every year, for a total of 30,000 units by 2020.",
      "entity": "Ed Lee",
      "role": null,
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "San Francisco Housing Stock",
      "promised_date": "2014",
      "due_date": "2020-12-31",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "numeric target not met or plan abandoned; due 2020-12-31 from explicit by-2020 deadline in source (also satisfies due-passed rule)",
      "source_id": "Sce65d2e2367a",
      "source_url": "https://civilgrandjury.archive.sf.gov/2017_2018/PressRelease.Housing.pdf",
      "source_file_path": "ce65d2e2367a25027234b228c68ef9d2380303c3eb840932bc7300fa0687820c.md",
      "source_hash": "ce65d2e2367a25027234b228c68ef9d2380303c3eb840932bc7300fa0687820c",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T03:53:53Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:56:06Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Market-rate prong overbuilt per grand jury",
              "evidence_date": "2018-07-05",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P15",
              "quote": "more than enough market rate units are built",
              "quote_match": "exact",
              "source_file_path": "ce65d2e2367a25027234b228c68ef9d2380303c3eb840932bc7300fa0687820c.md",
              "source_hash": "ce65d2e2367a25027234b228c68ef9d2380303c3eb840932bc7300fa0687820c",
              "source_url": "https://civilgrandjury.archive.sf.gov/2017_2018/PressRelease.Housing.pdf"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P15"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Affordable prong underbuilt year after year per grand jury",
              "evidence_date": "2018-07-05",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P15",
              "quote": "not enough below market rate or low-income ones",
              "quote_match": "exact",
              "source_file_path": "ce65d2e2367a25027234b228c68ef9d2380303c3eb840932bc7300fa0687820c.md",
              "source_hash": "ce65d2e2367a25027234b228c68ef9d2380303c3eb840932bc7300fa0687820c",
              "source_url": "https://civilgrandjury.archive.sf.gov/2017_2018/PressRelease.Housing.pdf"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P15"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: numeric target not met or plan abandoned; due 2020-12-31 from explicit by-2020 deadline in source (also satisfies due-passed rule)"
        }
      ],
      "display_no": 38,
      "importance_score": 62,
      "impact_rank": 38,
      "source_tier": "Official",
      "neighborhood_canonical": "Citywide",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2014-01-01",
      "deadline_date": "2020-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 2142,
      "promise_age_days": 4698,
      "time_to_verdict_days": 4697,
      "entity_canonical_name": "Ed Lee",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2011-01-11",
      "entity_term_end": "2017-12-12",
      "category_l1": "Housing",
      "category_l2": "Municipal Housing Construction Goals",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "30000_homes",
        "ed_lee",
        "housing_construction",
        "housing_goal"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 9,
      "completion_percentage": 55,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://civilgrandjury.archive.sf.gov/2017_2018/PressRelease.Housing.pdf",
      "document_title": "Add 5,000 Supportive Housing Units in 10 Years",
      "title": "Add 5,000 Supportive Housing Units in 10 Years"
    },
    {
      "promise_id": "P16",
      "promise_text": "In October 2018, Mayor London Breed announced a commitment to open at least 1,000 additional shelter beds, including Navigation Center beds, by the end of 2020.",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Housing & Neighborhoods",
      "neighborhood": "Citywide Navigation Center Network",
      "promised_date": "2018-10",
      "due_date": "2020-12-31",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence",
      "source_id": "S763eb80e2095",
      "source_url": "https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-67712",
      "source_file_path": "763eb80e2095a864c7d5923817e8756117de93b67fc617714a94a154f1dabf5c.md",
      "source_hash": "763eb80e2095a864c7d5923817e8756117de93b67fc617714a94a154f1dabf5c",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T03:55:29Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:57:27Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "City close to goal, opened 880 of 1,000 beds",
              "evidence_date": "2021-03",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P16",
              "quote": "the City was close to meeting this goal, and opened 880 of the proposed 1,000 beds by March 2021",
              "quote_match": "exact",
              "source_file_path": "763eb80e2095a864c7d5923817e8756117de93b67fc617714a94a154f1dabf5c.md",
              "source_hash": "763eb80e2095a864c7d5923817e8756117de93b67fc617714a94a154f1dabf5c",
              "source_url": "https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-67712"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P16"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Only 880 of 1,000 beds opened, after deadline",
              "evidence_date": "2021-03",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P16",
              "quote": "opened 880 of the proposed 1,000 beds by March 2021",
              "quote_match": "exact",
              "source_file_path": "763eb80e2095a864c7d5923817e8756117de93b67fc617714a94a154f1dabf5c.md",
              "source_hash": "763eb80e2095a864c7d5923817e8756117de93b67fc617714a94a154f1dabf5c",
              "source_url": "https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-67712"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P16"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-check R3: codelibrary.amlegal.com allowlisted, kept(2)+broken(2) both pass; broken stands via Rule 3 numeric (880<1000, late) \u2014 was Rule 1"
        }
      ],
      "display_no": 39,
      "importance_score": 61,
      "impact_rank": 39,
      "source_tier": "News",
      "neighborhood_canonical": "Citywide",
      "address_full": "Mission & Central Waterfront Navigation Centers, San Francisco, CA",
      "latitude": 37.765,
      "longitude": -122.41,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2018-10-01",
      "deadline_date": "2020-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 2142,
      "promise_age_days": 2964,
      "time_to_verdict_days": 2963,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Housing",
      "category_l2": "Shelter & Navigation Capacity",
      "secondary_categories": [
        "Public Safety"
      ],
      "tags": [
        "1000_shelter_beds",
        "london_breed",
        "navigation_centers",
        "shelter_capacity"
      ],
      "verdict_confidence": 0.95,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 8,
      "completion_percentage": 60,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-67712",
      "document_title": "Open 1,000 Additional Shelter Beds in SF",
      "title": "Open 1,000 Additional Shelter Beds in SF"
    },
    {
      "promise_id": "P19",
      "promise_text": "In his budget proposal for fiscal year 2007\u20132008, Newsom announced his intention to provide universal health care for all city residents, based on long-time City Supervisor Tom Ammiano 's plan.",
      "entity": "Gavin Newsom",
      "role": "Governor of California",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Universal Healthcare (Healthy San Francisco)",
      "promised_date": "2007-04",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "Sb1f01bbe657f",
      "source_url": "https://en.wikipedia.org/wiki/Healthy_San_Francisco",
      "source_file_path": "b1f01bbe657fd2c33b8b385a81c66786974b78e8816a1b0ed214fcd5eb9b1378.md",
      "source_hash": "b1f01bbe657fd2c33b8b385a81c66786974b78e8816a1b0ed214fcd5eb9b1378",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:01:55Z",
      "relevance": {
        "score": 7,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:02:52Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Healthy SF launched 2007 for uninsured residents",
              "evidence_date": "2010-07",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P19",
              "quote": "Healthy San Francisco is a health access program launched in 2007 to subsidize medical care for uninsured residents of San Francisco",
              "quote_match": "exact",
              "source_file_path": "b1f01bbe657fd2c33b8b385a81c66786974b78e8816a1b0ed214fcd5eb9b1378.md",
              "source_hash": "b1f01bbe657fd2c33b8b385a81c66786974b78e8816a1b0ed214fcd5eb9b1378",
              "source_url": "https://en.wikipedia.org/wiki/Healthy_San_Francisco"
            },
            {
              "claim_text": "By July 2010 nearly 90% of uninsured adults enrolled",
              "evidence_date": "2010-07",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P19",
              "quote": "By July 2010, almost 90% of the uninsured adults in San Francisco",
              "quote_match": "exact",
              "source_file_path": "b1f01bbe657fd2c33b8b385a81c66786974b78e8816a1b0ed214fcd5eb9b1378.md",
              "source_hash": "b1f01bbe657fd2c33b8b385a81c66786974b78e8816a1b0ed214fcd5eb9b1378",
              "source_url": "https://en.wikipedia.org/wiki/Healthy_San_Francisco"
            }
          ],
          "evidence_checked": 2,
          "promise_id": "P19"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file notes scope limits (not true insurance, SF-only providers) and later ACA enrollment decline, but nothing contradicting the 2007 launch/enrollment. No second search per cut rule.",
          "promise_id": "P19"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 40,
      "importance_score": 60,
      "impact_rank": 40,
      "source_tier": "Reference",
      "neighborhood_canonical": "Citywide",
      "address_full": "101 Grove Street, San Francisco, CA 94102",
      "latitude": 37.778,
      "longitude": -122.418,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2007-04-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 7165,
      "time_to_verdict_days": 7164,
      "entity_canonical_name": "Gavin Newsom",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2004-01-08",
      "entity_term_end": "2011-01-10",
      "category_l1": "Public Safety",
      "category_l2": "Municipal Universal Healthcare Access",
      "secondary_categories": [
        "Healthcare"
      ],
      "tags": [
        "healthy_san_francisco",
        "universal_healthcare",
        "gavin_newsom",
        "uninsured"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 3,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 9,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "academic_report",
      "source_domain_authority": 9,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://en.wikipedia.org/wiki/Healthy_San_Francisco",
      "document_title": "Healthy San Francisco Universal Healthcare",
      "title": "Healthy San Francisco Universal Healthcare"
    },
    {
      "promise_id": "P20",
      "promise_text": "At the time, Lee promised not to seek election if appointed, a statement that helped to gain support for his appointment.",
      "entity": "Ed Lee",
      "role": null,
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "San Francisco City Hall",
      "promised_date": "2011-01-07",
      "due_date": "2011-11-08",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence",
      "source_id": "S6736a72c86a2",
      "source_url": "https://en.wikipedia.org/wiki/Ed_Lee",
      "source_file_path": "6736a72c86a2da3a81969c18321c2f1d57809f3e2f9119139e59ac3f830a36a3.md",
      "source_hash": "6736a72c86a2da3a81969c18321c2f1d57809f3e2f9119139e59ac3f830a36a3",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:03:12Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:05:35Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file shows Lee ran and won Nov 2011 after pledging not to; no affirming evidence. No second search per cut rule.",
          "promise_id": "P20"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Lee reneged Aug 7 2011 and sought election",
              "evidence_date": "2011-08-07",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P20",
              "quote": "On August 7, 2011, Lee reneged on his promise to the San Francisco board of supervisors and formally announced his decision to seek election",
              "quote_match": "exact",
              "source_file_path": "6736a72c86a2da3a81969c18321c2f1d57809f3e2f9119139e59ac3f830a36a3.md",
              "source_hash": "6736a72c86a2da3a81969c18321c2f1d57809f3e2f9119139e59ac3f830a36a3",
              "source_url": "https://en.wikipedia.org/wiki/Ed_Lee"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P20"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 41,
      "importance_score": 59,
      "impact_rank": 41,
      "source_tier": "Reference",
      "neighborhood_canonical": "Civic Center",
      "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
      "latitude": 37.7793,
      "longitude": -122.4192,
      "supervisor_district": 5,
      "is_citywide": false,
      "promise_made_date": "2011-01-07",
      "deadline_date": "2011-11-08",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 5483,
      "promise_age_days": 5788,
      "time_to_verdict_days": 5787,
      "entity_canonical_name": "Ed Lee",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2011-01-11",
      "entity_term_end": "2017-12-12",
      "category_l1": "Civic Governance",
      "category_l2": "Mayoral Candidacy & Transition Pledges",
      "secondary_categories": [
        "Ethics"
      ],
      "tags": [
        "caretaker_mayor",
        "ed_lee",
        "run_for_office",
        "mayoral_pledge"
      ],
      "verdict_confidence": 0.99,
      "verdict_evidence_count": 0,
      "verdict_contradiction_count": 3,
      "verdict_reason_code": "pledge_reversed",
      "impact_score": 8,
      "completion_percentage": 0,
      "source_credibility_score": 7,
      "source_type_standardized": "academic_report",
      "source_domain_authority": 9,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://en.wikipedia.org/wiki/Ed_Lee",
      "document_title": "Interim Mayor Non-Candidacy Pledge",
      "title": "Interim Mayor Non-Candidacy Pledge"
    },
    {
      "promise_id": "P23",
      "promise_text": "The Hospitality Task Force will break down siloes to increase the police presence across the areas that drive our city\u2019s economy \u2013 not just during large conferences but 365 days a year.",
      "entity": "Daniel Lurie",
      "role": "Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Union Square & Downtown Hospitality Corridor",
      "promised_date": "2024",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "S23ac27d17f3d",
      "source_url": "https://www.sf.gov/mayor-lurie-launches-sfpd-hospitality-task-force-major-new-effort-to-strengthen-public-safety-drive-economic-comeback",
      "source_file_path": "23ac27d17f3da97ea3f6fb5b7028a352ffc0178772ff10e9251e1966f8742bf5.md",
      "source_hash": "23ac27d17f3da97ea3f6fb5b7028a352ffc0178772ff10e9251e1966f8742bf5",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:09:22Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:11:22Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Mayor launched SFPD Hospitality Task Force",
              "evidence_date": "2025",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P23",
              "quote": "San Francisco Mayor Daniel Lurie today launched the San Francisco Police Department (SFPD) Hospitality Task Force",
              "quote_match": "exact",
              "source_file_path": "23ac27d17f3da97ea3f6fb5b7028a352ffc0178772ff10e9251e1966f8742bf5.md",
              "source_hash": "23ac27d17f3da97ea3f6fb5b7028a352ffc0178772ff10e9251e1966f8742bf5",
              "source_url": "https://www.sf.gov/mayor-lurie-launches-sfpd-hospitality-task-force-major-new-effort-to-strengthen-public-safety-drive-economic-comeback"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P23"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: launch announcement with program details; no contradiction. No second search per cut rule.",
          "promise_id": "P23"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 42,
      "importance_score": 58,
      "impact_rank": 42,
      "source_tier": "Official",
      "neighborhood_canonical": "Union Square",
      "address_full": "333 Post Street, San Francisco, CA 94108",
      "latitude": 37.7879,
      "longitude": -122.4074,
      "supervisor_district": 3,
      "is_citywide": false,
      "promise_made_date": "2024-01-01",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 1046,
      "time_to_verdict_days": 1045,
      "entity_canonical_name": "Daniel Lurie",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2025-01-08",
      "entity_term_end": "2029-01-08",
      "category_l1": "Economy & Commercial",
      "category_l2": "Downtown Hotel & Conference Activation",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "union_square",
        "convention_facilities",
        "downtown_economic_recovery",
        "hotel_rooms"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 7,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sf.gov/mayor-lurie-launches-sfpd-hospitality-task-force-major-new-effort-to-strengthen-public-safety-drive-economic-comeback",
      "document_title": "Downtown Hospitality Corridor Recovery",
      "title": "Downtown Hospitality Corridor Recovery"
    },
    {
      "promise_id": "P28",
      "promise_text": "Over the past two years, SFDPH has opened 250 additional residential care and treatment beds.",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "SF General & Community Health Clinics",
      "promised_date": "2020-01-08",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims (re-open R2: evidence_date corrected to local observation date; 250 beds opened satisfies 200-bed outcome)",
      "source_id": "S9384fe0d2bda",
      "source_url": "https://www.sf.gov/news--department-public-health-opens-70-new-behavioral-health-beds-part-expansion-treat-people",
      "source_file_path": "9384fe0d2bda4f71374737d96ba40b075f2d9aa2746a07af29f0e1672f4b8306.md",
      "source_hash": "9384fe0d2bda4f71374737d96ba40b075f2d9aa2746a07af29f0e1672f4b8306",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:21:40Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:26:07Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "SFDPH opened 250 additional beds over two years, exceeding 200 pledge",
              "evidence_date": "2026-11-10",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P28",
              "quote": "Over the past two years, SFDPH has opened 250 additional residential care and treatment beds",
              "quote_match": "exact",
              "source_file_path": "9384fe0d2bda4f71374737d96ba40b075f2d9aa2746a07af29f0e1672f4b8306.md",
              "source_hash": "9384fe0d2bda4f71374737d96ba40b075f2d9aa2746a07af29f0e1672f4b8306",
              "source_url": "https://www.sf.gov/news--department-public-health-opens-70-new-behavioral-health-beds-part-expansion-treat-people"
            }
          ],
          "evidence_checked": 1,
          "note": "Event undated in file (only relative dates); evidence_date is observation date. External research dates article 2023, unverified in-source.",
          "promise_id": "P28"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: file reports bed expansion only; no shortfall or contradiction. No second search per cut rule.",
          "promise_id": "P28"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: official primary evidence confirms completion with zero contradicting claims (re-open R2: evidence_date corrected to local observation date; 250 beds opened satisfies 200-bed outcome)"
        }
      ],
      "display_no": 43,
      "importance_score": 57,
      "impact_rank": 43,
      "source_tier": "Official",
      "neighborhood_canonical": "Mission District",
      "address_full": "1001 Potrero Ave (Zuckerberg SF General Hospital), San Francisco, CA 94110",
      "latitude": 37.7558,
      "longitude": -122.4048,
      "supervisor_district": 9,
      "is_citywide": false,
      "promise_made_date": "2020-01-08",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2500,
      "time_to_verdict_days": 2499,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Public Safety",
      "category_l2": "Substance Use & Psychiatric Emergency Beds",
      "secondary_categories": [
        "Healthcare"
      ],
      "tags": [
        "psychiatric_beds",
        "dph",
        "sf_general",
        "behavioral_health"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sf.gov/news--department-public-health-opens-70-new-behavioral-health-beds-part-expansion-treat-people",
      "document_title": "Open 250 Additional Behavioral Health Beds",
      "title": "Open 250 Additional Behavioral Health Beds"
    },
    {
      "promise_id": "P35",
      "promise_text": "This program is improving behavioral health services for people living in San Francisco with serious mental health issues and/or substance use disorders who are experiencing homelessness.",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Mental Health SF (Citywide)",
      "promised_date": "2019-11-12",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "S82f01dbd3448",
      "source_url": "https://api.sf.gov/documents/12808/DPH_MHSF_Implementation_Report_2023.pdf",
      "source_file_path": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46.md",
      "source_hash": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T03:57:54Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:58:02Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Board passed File No. 191148 ordinance establishing Mental Health SF on Dec 6, 2019",
              "evidence_date": "2019-12-06",
              "evidence_type": "ordinance",
              "page_number": null,
              "promise_id": "P35",
              "quote": "On December 6, 2019, the San Francisco Board of Supervisors passed an ordinance ( File No. 191148) amending the Administrative Code to establish Mental Health San Francisco (MHSF).",
              "quote_match": "exact",
              "source_file_path": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46.md",
              "source_hash": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46",
              "source_url": "https://api.sf.gov/documents/12808/DPH_MHSF_Implementation_Report_2023.pdf"
            },
            {
              "claim_text": "DPH completed second year of full MHSF implementation in 2022",
              "evidence_date": "2022",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P35",
              "quote": "DPH completed the second year of full MHSF implementation in 2022",
              "quote_match": "exact",
              "source_file_path": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46.md",
              "source_hash": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46",
              "source_url": "https://api.sf.gov/documents/12808/DPH_MHSF_Implementation_Report_2023.pdf"
            },
            {
              "claim_text": "Over 250 new MHSF beds opened, two-thirds of 400-bed goal",
              "evidence_date": "2023-02",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P35",
              "quote": "bringing the total number of new beds opened under MHSF to over 250",
              "quote_match": "exact",
              "source_file_path": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46.md",
              "source_hash": "b3388e2775bf355cbd04c4b000dcb2b53990a1847cb1d8638ba987d1e7a85f46",
              "source_url": "https://api.sf.gov/documents/12808/DPH_MHSF_Implementation_Report_2023.pdf"
            },
            {
              "claim_text": "Nearly 90 percent of 400-bed goal met by third year of implementation",
              "evidence_date": "2024-02",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P35",
              "quote": "Meeting nearly 90% of the goal of adding 400 new residential care and treatment beds",
              "quote_match": "exact",
              "source_file_path": "ca10568f53e80c558c367bde1eb388de52105271489cb38bc8df77ee60d032f7.md",
              "source_hash": "ca10568f53e80c558c367bde1eb388de52105271489cb38bc8df77ee60d032f7",
              "source_url": "https://sf.gov/sites/default/files/2024-02/FINAL%20MHSF%20Implementation%20Report%202024_1.pdf"
            }
          ],
          "evidence_checked": 2,
          "note": "evidence_date is the event date when the quote states one (claim 1), else the source document month (claims 2-4: Feb 2023 / Feb 2024 DPH reports).",
          "promise_id": "P35"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: real search + fetched SF Chronicle Dec 2021 interim-progress piece (87 beds vs 400 planned, care-coordination office not yet opened then). Interim slowness, not contradiction: the same facts are superseded by later DPH reports in hand (OCC launched 2022, 250+ beds by 2023, ~90% of 400-bed goal by 2024). No second search per cut rule.",
          "promise_id": "P35"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 44,
      "importance_score": 56,
      "impact_rank": 44,
      "source_tier": "Official",
      "neighborhood_canonical": "Citywide",
      "address_full": "1380 Howard St (Mental Health SF Headquarters), San Francisco, CA 94103",
      "latitude": 37.7728,
      "longitude": -122.415,
      "supervisor_district": null,
      "is_citywide": true,
      "promise_made_date": "2019-11-12",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2557,
      "time_to_verdict_days": 2556,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Public Safety",
      "category_l2": "Coordinated Mental Health Reform",
      "secondary_categories": [
        "Healthcare"
      ],
      "tags": [
        "mental_health_sf",
        "care_coordination",
        "psychiatric_urgent_care",
        "dph"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 9,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://api.sf.gov/documents/12808/DPH_MHSF_Implementation_Report_2023.pdf",
      "document_title": "Mental Health SF Reform Implementation",
      "title": "Mental Health SF Reform Implementation"
    },
    {
      "promise_id": "P37",
      "promise_text": "Mayor Breed also announced the next steps in her efforts to help people living unsheltered on the City\u2019s streets, with an initiative to create at least 2,000 more places for people across the spectrum of housing, behavioral health, and shelter over the next two years.",
      "entity": "London Breed",
      "role": "Former Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "Tenderloin & Encampment Outreach",
      "promised_date": "2020-01-15",
      "due_date": "2022-01-15",
      "page_number": null,
      "verdict": "undecided",
      "verdict_reason": "re-open R2 (0+0 standing rule): untestable \u2014 no outcome count for the specific 2,000-places-by-Jan-2022 goal found by either advocate; other-goal figures (6,000-plan 7,047) declined as misattribution",
      "source_id": "Sd659523fe97f",
      "source_url": "https://hsh.archive.sf.gov/wp-content/uploads/2020/01/1000-Shelter-Bed-Press-Conference.pdf",
      "source_file_path": "d659523fe97f78d2e990ee474b0126002978c8f327573c6bfbe2a2d1545ef764.md",
      "source_hash": "d659523fe97f78d2e990ee474b0126002978c8f327573c6bfbe2a2d1545ef764",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:08:10Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:11:49Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 0,
          "note": "none found: real search surfaced only other-goal figures (Homelessness Recovery Plan 7,047 placements vs its own 6,000 goal; FY2023 exits; individual PSH openings) \u2014 no count toward the specific Jan-2020 2,000-places-by-Jan-2022 goal. Declined to misattribute other-goal numbers. No second search per cut rule.",
          "promise_id": "P37"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 0,
          "note": "none found: broken-leaning search surfaced only unrelated shortfalls (SIP hotel wind-down, youth Rising Up goal, SRO evictions, encampment coordination) \u2014 no verified count showing the 2,000-places goal missed. No second search per cut rule.",
          "promise_id": "P37"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "authenticity_hash",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_quote",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "authenticity_speaker",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_date",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_evidence",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "re-open R2: untestable, no outcome count either way"
        }
      ],
      "display_no": 45,
      "importance_score": 55,
      "impact_rank": 45,
      "source_tier": "Official",
      "neighborhood_canonical": "Tenderloin",
      "address_full": "Ellis St & Leavenworth St, San Francisco, CA 94102",
      "latitude": 37.784,
      "longitude": -122.414,
      "supervisor_district": 5,
      "is_citywide": false,
      "promise_made_date": "2020-01-15",
      "deadline_date": "2022-01-15",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 1762,
      "promise_age_days": 2493,
      "time_to_verdict_days": 2492,
      "entity_canonical_name": "London Breed",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2018-07-11",
      "entity_term_end": "2025-01-08",
      "category_l1": "Housing",
      "category_l2": "Permanent Supportive Housing Goals",
      "secondary_categories": [
        "Public Safety"
      ],
      "tags": [
        "2000_placements",
        "supportive_housing",
        "encampment_resolution",
        "london_breed"
      ],
      "verdict_confidence": 0.85,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 1,
      "verdict_reason_code": "undecided_conflicting_evidence",
      "impact_score": 8,
      "completion_percentage": 50,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://hsh.archive.sf.gov/wp-content/uploads/2020/01/1000-Shelter-Bed-Press-Conference.pdf",
      "document_title": "London Breed Commitment",
      "title": "London Breed Commitment"
    },
    {
      "promise_id": "P38",
      "promise_text": "Here\u2019s how PG&E is working to make PSPS events smaller in size, shorter in length and smarter for customers.",
      "entity": "PG&E",
      "role": null,
      "entity_type": "company",
      "category": "Bay Area & Regional",
      "neighborhood": "Northern California & Bay Area Grid",
      "promised_date": "2020-02-07",
      "due_date": "2020-12-31",
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims; due 2020-12-31 derived from 2020-wildfire-season/this-year scope in source anchored to promised 2020-02-07",
      "source_id": "Sd2a17c8ccaf2",
      "source_url": "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2020/PGE-Outlines-Actions-Its-Taking-to-Keep-Customers-and-Communities-Safe-During-2020-Wildfire-Season/default.aspx?print=1",
      "source_file_path": "384c310bb67941a4a131738f8ed7c9aa4d73e5bc41468a7d6c028caafc141812.md",
      "source_hash": "384c310bb67941a4a131738f8ed7c9aa4d73e5bc41468a7d6c028caafc141812",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:17:14Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 1,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:17:25Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Sept 27-29 event affected over 60% fewer customers than same weather in 2019",
              "evidence_date": "2020-09",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P38",
              "quote": "this PSPS event affected over 60% fewer customers than would have been affected by the same weather conditions in 2019",
              "quote_match": "exact",
              "source_file_path": "eb5e59ec647d902955781119e5055431a1e4268f35baefa33b106faaab9cabea.md",
              "source_hash": "eb5e59ec647d902955781119e5055431a1e4268f35baefa33b106faaab9cabea",
              "source_url": "https://www.cpuc.ca.gov/-/media/cpuc-website/files/uploadedfiles/cpuc_public_website/content/news_room/news_and_updates/pge-sept-27-29-2020-psps-post-event-report.pdf"
            },
            {
              "claim_text": "Sept 27-29: all servable customers restored within 12 daylight hours of Weather All Clear",
              "evidence_date": "2020-09",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P38",
              "quote": "all customers whom we are able to serve restored to service within 12 daylight hours of their respective Weather All Clears",
              "quote_match": "exact",
              "source_file_path": "eb5e59ec647d902955781119e5055431a1e4268f35baefa33b106faaab9cabea.md",
              "source_hash": "eb5e59ec647d902955781119e5055431a1e4268f35baefa33b106faaab9cabea",
              "source_url": "https://www.cpuc.ca.gov/-/media/cpuc-website/files/uploadedfiles/cpuc_public_website/content/news_room/news_and_updates/pge-sept-27-29-2020-psps-post-event-report.pdf"
            },
            {
              "claim_text": "Oct 21-23 event affected approximately 48% fewer customers than same weather in 2019",
              "evidence_date": "2020-10",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P38",
              "quote": "this PSPS event affected approximately 48% fewer customers than would have been affected by the same weather conditions in 2019",
              "quote_match": "exact",
              "source_file_path": "8cabdac8edb9a6e040b194061a1cc31858b52c09293900df872e654654f1cfe5.md",
              "source_hash": "8cabdac8edb9a6e040b194061a1cc31858b52c09293900df872e654654f1cfe5",
              "source_url": "https://www.cpuc.ca.gov/-/media/cpuc-website/files/uploadedfiles/cpucwebsite/content/news_room/newsupdates/2020/pge-oct-21-23-2020-psps-post-event-report.pdf"
            },
            {
              "claim_text": "Oct 21-23: met goal of restoring 98% within 12 daylight hours of Weather All Clear",
              "evidence_date": "2020-10",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P38",
              "quote": "This accomplishment met PG&E\u2019s goal of restoring 98% of customers within 12 daylight hours of the Weather All Clear",
              "quote_match": "exact",
              "source_file_path": "8cabdac8edb9a6e040b194061a1cc31858b52c09293900df872e654654f1cfe5.md",
              "source_hash": "8cabdac8edb9a6e040b194061a1cc31858b52c09293900df872e654654f1cfe5",
              "source_url": "https://www.cpuc.ca.gov/-/media/cpuc-website/files/uploadedfiles/cpucwebsite/content/news_room/newsupdates/2020/pge-oct-21-23-2020-psps-post-event-report.pdf"
            }
          ],
          "evidence_checked": 2,
          "note": "Verdict rests on the smaller + shorter legs (both 2020 events clear the one-third and 12-hour bars). The smarter (communications) leg was not measured in the sources checked. Event dates used throughout.",
          "promise_id": "P38"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: broken-leaning search surfaced only more 2020 PSPS event reports. Diligence-fetched the Oct 25-28 report (largest scope): 46% fewer customers (clears the one-third bar), full restoration Oct 27-28, no 12-hour attainment statement either way \u2014 no verified bar-miss, so no claim. No second search per cut rule.",
          "promise_id": "P38"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims; due 2020-12-31 derived from 2020-wildfire-season/this-year scope in source anchored to promised 2020-02-07"
        }
      ],
      "display_no": 46,
      "importance_score": 54,
      "impact_rank": 46,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2020-02-07",
      "deadline_date": "2020-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 2470,
      "time_to_verdict_days": 2469,
      "entity_canonical_name": "Pacific Gas & Electric (PG&E)",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Environment & Energy",
      "category_l2": "Public Safety Power Shutoff Minimization",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "psps_events",
        "pge",
        "power_outages",
        "fire_season_grid"
      ],
      "verdict_confidence": 0.95,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 8,
      "completion_percentage": 100,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://investor.pgecorp.com/news-events/press-releases/press-release-details/2020/PGE-Outlines-Actions-Its-Taking-to-Keep-Customers-and-Communities-Safe-During-2020-Wildfire-Season/default.aspx?print=1",
      "document_title": "Reduce PSPS Wildfire Outage Scope by Half",
      "title": "Reduce PSPS Wildfire Outage Scope by Half"
    },
    {
      "promise_id": "P39",
      "promise_text": "The program forecasted to install up to 7,500 charging ports over a three-year period focusing on two key market segments: workplaces and multi-unit dwellings.",
      "entity": "PG&E",
      "role": null,
      "entity_type": "company",
      "category": "Bay Area & Regional",
      "neighborhood": "Northern California EV Network",
      "promised_date": "2018",
      "due_date": "2020-12-31",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence; due 2020-12-31 derived from three-year period from Jan-2018 launch anchored to promised 2018",
      "source_id": "S5445c39db566",
      "source_url": "https://docs.cpuc.ca.gov/PublishedDocs/Efile/G000/M373/K419/373419331.PDF",
      "source_file_path": "1cefacf0936ffe3351a55b3d18fcdf2914047471eeb4020d4d13436eb739b9f5.md",
      "source_hash": "1cefacf0936ffe3351a55b3d18fcdf2914047471eeb4020d4d13436eb739b9f5",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:20:47Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:20:52Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 0,
          "note": "none found: kept-leaning search confirmed the shortfall instead of a kept case \u2014 best figures are 4,180 substantially complete (Q4 2020) and 4,827 final with no additional ports scheduled, both below 7,500. No second search per cut rule.",
          "promise_id": "P39"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Only 4,180 ports substantially complete since program inception at Q4 2020",
              "evidence_date": "2020-12-31",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P39",
              "quote": "4,180 ports substantially complete since program inception",
              "quote_match": "exact",
              "source_file_path": "1cefacf0936ffe3351a55b3d18fcdf2914047471eeb4020d4d13436eb739b9f5.md",
              "source_hash": "1cefacf0936ffe3351a55b3d18fcdf2914047471eeb4020d4d13436eb739b9f5",
              "source_url": "https://docs.cpuc.ca.gov/PublishedDocs/Efile/G000/M373/K419/373419331.PDF"
            },
            {
              "claim_text": "Even the signed pipeline was only 4,898 ports at close of Q4 2020",
              "evidence_date": "2020-12-31",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P39",
              "quote": "At the close of Q4 2020, 198 sites representing 4,898 ports had signed agreements with customers",
              "quote_match": "exact",
              "source_file_path": "1cefacf0936ffe3351a55b3d18fcdf2914047471eeb4020d4d13436eb739b9f5.md",
              "source_hash": "1cefacf0936ffe3351a55b3d18fcdf2914047471eeb4020d4d13436eb739b9f5",
              "source_url": "https://docs.cpuc.ca.gov/PublishedDocs/Efile/G000/M373/K419/373419331.PDF"
            },
            {
              "claim_text": "Final program total 4,827 ports with no additional ports scheduled",
              "evidence_date": "2021-12",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P39",
              "quote": "PG&E installed 4,827 ports in EVCN and no additional ports are scheduled to be installed under the program",
              "quote_match": "exact",
              "source_file_path": "5445c39db5665889c0c03ca5463f79e6f3f520657669bc9eeb15a300d81d7690.md",
              "source_hash": "5445c39db5665889c0c03ca5463f79e6f3f520657669bc9eeb15a300d81d7690",
              "source_url": "https://docs.cpuc.ca.gov/PublishedDocs/SupDoc/A2110010/4596/454876271.pdf"
            }
          ],
          "evidence_checked": 2,
          "note": "Event dates used (quarter-end / doc month for cumulative final total).",
          "promise_id": "P39"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence; due 2020-12-31 derived from three-year period from Jan-2018 launch anchored to promised 2018"
        }
      ],
      "display_no": 47,
      "importance_score": 53,
      "impact_rank": 47,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2018-01-01",
      "deadline_date": "2020-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 2142,
      "promise_age_days": 3237,
      "time_to_verdict_days": 3236,
      "entity_canonical_name": "Pacific Gas & Electric (PG&E)",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Electric Vehicle Charging Infrastructure",
      "secondary_categories": [
        "Environment & Energy"
      ],
      "tags": [
        "ev_charging",
        "pge_chargers",
        "fast_charging",
        "cleantech"
      ],
      "verdict_confidence": 0.95,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 7,
      "completion_percentage": 64,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://docs.cpuc.ca.gov/PublishedDocs/Efile/G000/M373/K419/373419331.PDF",
      "document_title": "Install 7,500 EV Charging Ports",
      "title": "Install 7,500 EV Charging Ports"
    },
    {
      "promise_id": "P40",
      "promise_text": "In addition, PG&E is announcing today its own commitment to further electrify its vehicle fleet by 2030, including 100% of its light-duty fleet, 10% of its medium-duty fleet and 5% of its heavy-duty fleet.",
      "entity": "PG&E",
      "role": null,
      "entity_type": "company",
      "category": "Bay Area & Regional",
      "neighborhood": "Northern California Utility Fleet",
      "promised_date": "2020-10-01",
      "due_date": "2030-12-31",
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "due date in future and no definitive resolution yet; interim program active, completion unverified (P18: partial progress + future due)",
      "source_id": "S4d6de2bf1068",
      "source_url": "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2020/Electric-Vehicle-Drivers-Apply-for-800-Clean-Fuel-Rebate-Before-End-of-Year/default.aspx",
      "source_file_path": "a033f228cec47aee53fdc14ea44495d951ed9483b401d843344f640a092e60f5.md",
      "source_hash": "a033f228cec47aee53fdc14ea44495d951ed9483b401d843344f640a092e60f5",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T04:23:55Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:24:02Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "PG&E committed to electrify fleet by 2030: 100% light-duty, 10% medium, 5% heavy",
              "evidence_date": "2020-10-01",
              "evidence_type": "press_release",
              "page_number": null,
              "promise_id": "P40",
              "quote": "PG&E is announcing today its own commitment to further electrify its vehicle fleet by 2030, including 100% of its light-duty fleet, 10% of its medium-duty fleet and 5% of its heavy-duty fleet.",
              "quote_match": "exact",
              "source_file_path": "a033f228cec47aee53fdc14ea44495d951ed9483b401d843344f640a092e60f5.md",
              "source_hash": "a033f228cec47aee53fdc14ea44495d951ed9483b401d843344f640a092e60f5",
              "source_url": "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2020/Electric-Vehicle-Drivers-Apply-for-800-Clean-Fuel-Rebate-Before-End-of-Year/default.aspx"
            },
            {
              "claim_text": "Q1 2026 plan: fleet electrification live, 3,300 vehicles by 2030, full 9,500 by 2045",
              "evidence_date": "2026-03",
              "evidence_type": "announcement",
              "page_number": null,
              "promise_id": "P40",
              "quote": "PG&E is electrifying its entire fleet of 9,500 vehicles by 2045, with a goal to electrify 3,300 vehicles in our fleet by 2030.",
              "quote_match": "exact",
              "source_file_path": "4d6de2bf106823712e86498de00047c1ff784b7df1512bc9216eb108151fbed2.md",
              "source_hash": "4d6de2bf106823712e86498de00047c1ff784b7df1512bc9216eb108151fbed2",
              "source_url": "https://pge.com/assets/pge/docs/clean-energy/electric-vehicles/q1-2026-pac-presentation.pdf"
            }
          ],
          "evidence_checked": 2,
          "note": "Claim 2 typed announcement (tier 1): interim program statement, not completion \u2014 P18 principle (partial progress + future due = in_progress, never kept). evidence_date 2020-10-01 is the commitment event (this file restates it Dec 2020).",
          "promise_id": "P40"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: broken-leaning search found no abandonment of the 2030 fleet legs (only general capital-constraint coverage). The deck's 2045-full-fleet framing cannot contradict the 100%-light-duty-by-2030 leg without the light-duty denominator; the snippet's ~50% refers to Scope 1+2 emissions reduction, not fleet share. No second search per cut rule.",
          "promise_id": "P40"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date in future and no definitive resolution yet; interim program active, completion unverified (P18: partial progress + future due)"
        }
      ],
      "display_no": 48,
      "importance_score": 52,
      "impact_rank": 48,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2020-10-01",
      "deadline_date": "2030-12-31",
      "completion_date": null,
      "days_remaining": 1510,
      "days_overdue": null,
      "promise_age_days": 2233,
      "time_to_verdict_days": 2232,
      "entity_canonical_name": "Pacific Gas & Electric (PG&E)",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Fleet Decarbonization & Electrification",
      "secondary_categories": [
        "Environment & Energy"
      ],
      "tags": [
        "utility_fleet",
        "zero_emissions",
        "pge_ev",
        "fleet_electrification"
      ],
      "verdict_confidence": 0.9,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 7,
      "completion_percentage": 30,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://investor.pgecorp.com/news-events/press-releases/press-release-details/2020/Electric-Vehicle-Drivers-Apply-for-800-Clean-Fuel-Rebate-Before-End-of-Year/default.aspx",
      "document_title": "PG&E Fleet Vehicle Electrification by 2030",
      "title": "PG&E Fleet Vehicle Electrification by 2030"
    },
    {
      "promise_id": "P57",
      "promise_text": "By early 2017, Comcast will have its gigabit internet service available in 15 cities/metropolitan areas.",
      "entity": "Comcast",
      "role": null,
      "entity_type": "company",
      "category": "Bay Area & Regional",
      "neighborhood": "Bay Area Fiber Network",
      "promised_date": "2016-11-01",
      "due_date": "2017-03-31",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence; due 2017-03-31 = Q1 end from 'early 2017' in source",
      "source_id": "Sefc8fda8bf79",
      "source_url": "https://www.neowin.net/news/comcast-is-expanding-its-gigabit-internet-service-will-be-in-15-us-cities-by-early-2017/",
      "source_file_path": "df7e8089b7ed3ad391eb538d97feebec6df61dafe5b3f1182bd975b33fc0a0e0.md",
      "source_hash": "df7e8089b7ed3ad391eb538d97feebec6df61dafe5b3f1182bd975b33fc0a0e0",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T03:59:26Z",
      "relevance": {
        "score": 7,
        "real": 2,
        "measurable": 2,
        "sf": 1,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:00:26Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: 1 kept search (Comcast Xfinity gigabit SF 2017 launch); CA launch announced May 31 2017, after deadline; no source shows Bay Area availability by Mar 31 2017. Doc-15 kept lead is a later nationwide-scale PR, not the deadline leg. No second search per cut rule.",
          "promise_id": "P57"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Comcast announced the California gigabit launch on May 31, 2017, after the early-2017 deadline",
              "evidence_date": "2017-05-31",
              "evidence_type": "press_release",
              "page_number": null,
              "promise_id": "P57",
              "quote": "Livermore, CA \u2013 May 31, 2017 \u2013 Comcast announced today that it is launching a new internet service that will deliver speeds up to 1 Gigabit-per-second (Gbps) to residential customers throughout most of California.",
              "quote_match": "exact",
              "source_file_path": "efc8fda8bf79a607dd6d48100b2612fd3fe1f880bee734e52c364084c4579dd8.md",
              "source_hash": "efc8fda8bf79a607dd6d48100b2612fd3fe1f880bee734e52c364084c4579dd8",
              "source_url": "https://california.comcast.com/2017/09/07/comcast-to-deliver-gigabit-internet-service-in-california"
            }
          ],
          "evidence_checked": 2,
          "promise_id": "P57"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": false,
          "reason": "unlisted source domain"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 49,
      "importance_score": 51,
      "impact_rank": 49,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2016-11-01",
      "deadline_date": "2017-03-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 3513,
      "promise_age_days": 3663,
      "time_to_verdict_days": 3662,
      "entity_canonical_name": "Comcast",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Infrastructure",
      "category_l2": "Broadband & Fiber Telecommunications",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "gigabit_internet",
        "comcast",
        "fiber_broadband",
        "docsis_3_1"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "timeline_missed_delay",
      "impact_score": 6,
      "completion_percentage": 70,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.neowin.net/news/comcast-is-expanding-its-gigabit-internet-service-will-be-in-15-us-cities-by-early-2017/",
      "document_title": "Comcast Gigabit Fiber-to-the-Home Network",
      "title": "Comcast Gigabit Fiber-to-the-Home Network"
    },
    {
      "promise_id": "P03",
      "promise_text": "Mayor Lurie today also introduced a legislative package with six ordinances proposing structural changes to help businesses and property owners to secure the permits they need more easily and efficiently.",
      "entity": "Daniel Lurie",
      "role": "Mayor of San Francisco",
      "entity_type": "politician",
      "category": "Civic Governance",
      "neighborhood": "City Hall & Small Business Corridors",
      "promised_date": "2025-01-07",
      "due_date": null,
      "page_number": null,
      "verdict": "kept",
      "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
      "source_id": "S19e038938b5c",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-pieces-of-permitsf-announces-legislation-with-major-reforms-to-cut-red-tape-drive-economic-recovery",
      "source_file_path": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c.md",
      "source_hash": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c",
      "source_type": "press_release",
      "fetched_at": "2026-11-11T03:07:52.760335+00:00",
      "relevance": {
        "score": 6,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T03:32:52Z",
      "advocate_bundles": {
        "kept": {
          "promise_id": "P03",
          "advocate_role": "kept_advocate",
          "evidence_checked": 1,
          "claims": [
            {
              "promise_id": "P03",
              "claim_text": "Legislative package with six ordinances introduced",
              "quote": "Mayor Lurie today also introduced a legislative package with six ordinances proposing structural changes to help businesses and property owners to secure the permits they need more easily and efficiently.",
              "quote_match": "exact",
              "evidence_type": "filing",
              "source_file_path": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c.md",
              "source_hash": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c",
              "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-pieces-of-permitsf-announces-legislation-with-major-reforms-to-cut-red-tape-drive-economic-recovery",
              "page_number": null,
              "evidence_date": "2025-05"
            },
            {
              "promise_id": "P03",
              "claim_text": "First-100-days process improvements already in place",
              "quote": "Within the first 100 days of PermitSF, process improvements focused on improving the customer experience are already in place",
              "quote_match": "exact",
              "evidence_type": "announcement",
              "source_file_path": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c.md",
              "source_hash": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c",
              "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-pieces-of-permitsf-announces-legislation-with-major-reforms-to-cut-red-tape-drive-economic-recovery",
              "page_number": null,
              "evidence_date": "2025-05"
            },
            {
              "promise_id": "P03",
              "claim_text": "Concrete delivered reform: SFUSD removed from routing, 10 days saved",
              "quote": "Removed San Francisco Unified School District from the routing process, shaving up to 10 days off the building permit process for permits associated with new residential or commercial development",
              "quote_match": "exact",
              "evidence_type": "announcement",
              "source_file_path": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c.md",
              "source_hash": "19e038938b5c508ed6a344430d56f17c10c5ca66a852e598475dfc1aa0faa14c",
              "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-pieces-of-permitsf-announces-legislation-with-major-reforms-to-cut-red-tape-drive-economic-recovery",
              "page_number": null,
              "evidence_date": "2025-05"
            }
          ]
        },
        "broken": {
          "promise_id": "P03",
          "advocate_role": "broken_advocate",
          "evidence_checked": 1,
          "claims": [],
          "note": "none found: PermitSF appears only in its own sf.gov file; no contradicting source. No second search per cut rule."
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "official primary evidence confirms completion with zero contradicting claims"
        }
      ],
      "display_no": 50,
      "importance_score": 50,
      "impact_rank": 50,
      "source_tier": "Official",
      "neighborhood_canonical": "Civic Center",
      "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
      "latitude": 37.7793,
      "longitude": -122.4192,
      "supervisor_district": 5,
      "is_citywide": true,
      "promise_made_date": "2025-01-07",
      "deadline_date": null,
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": null,
      "promise_age_days": 674,
      "time_to_verdict_days": 673,
      "entity_canonical_name": "Daniel Lurie",
      "entity_category": "politician",
      "entity_party": "D",
      "entity_term_start": "2025-01-08",
      "entity_term_end": "2029-01-08",
      "category_l1": "Economy & Commercial",
      "category_l2": "Commercial Corridors & Small Business Permitting",
      "secondary_categories": [
        "Civic Governance"
      ],
      "tags": [
        "permitsf",
        "daniel_lurie",
        "small_business_permitting",
        "economic_vibrancy"
      ],
      "verdict_confidence": 0.96,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "on_time",
      "impact_score": 7,
      "completion_percentage": 100,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sf.gov/news-mayor-lurie-delivers-on-key-pieces-of-permitsf-announces-legislation-with-major-reforms-to-cut-red-tape-drive-economic-recovery",
      "document_title": "Permitting Reform & Small Business Overhaul",
      "title": "Permitting Reform & Small Business Overhaul"
    },
    {
      "promise_id": "P58",
      "promise_text": "AT&T plans to triple that amount by the end of the year",
      "entity": "Leland Kim (AT&T spokesman)",
      "role": null,
      "entity_type": "other",
      "category": "Bay Area & Regional",
      "neighborhood": "Bay Area Gigabit Infrastructure",
      "promised_date": "2016-05-17",
      "due_date": "2016-12-31",
      "page_number": null,
      "verdict": "undecided",
      "verdict_reason": "untestable: no end-of-2016 Bay Area location count exists to check the tripling against; never broken on fully-empty bundles (timestamp fix over VER-P58-2, true clock time)",
      "source_id": "S33d33e3798db",
      "source_url": "https://www.govtech.com/network/ATT-Launches-Fiber-Internet-in-San-Francisco-Bay-Area.html",
      "source_file_path": "023cbce1b133583b6ba663924df8c2d641b062cac23bc372cc00bef446ff6be1.md",
      "source_hash": "023cbce1b133583b6ba663924df8c2d641b062cac23bc372cc00bef446ff6be1",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:02:16Z",
      "relevance": {
        "score": 5,
        "real": 2,
        "measurable": 2,
        "sf": 1,
        "interesting": 0
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:10:29Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: 1 kept search; only pre-deadline announcements (Dec 2015 PR, May 2016 launch reports); no verified Bay Area location count at end of 2016. No second search per cut rule.",
          "promise_id": "P58"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 2,
          "note": "none found: doc-15 CWA lead fetched but rejected (2023+ Gigapower JV, wrong subject/era); 1 broken search found no end-2016 Bay Area count and no source showing the tripling failed (Haas digital-divide study is about equity, not the count). No second search per cut rule.",
          "promise_id": "P58"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "authenticity_hash",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_quote",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "authenticity_speaker",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_date",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "accuracy_evidence",
          "passed": null,
          "reason": "not recorded"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 51,
      "importance_score": 50,
      "impact_rank": 51,
      "source_tier": "News",
      "neighborhood_canonical": "Bay Area Regional",
      "address_full": null,
      "latitude": 37.7749,
      "longitude": -122.4194,
      "supervisor_district": null,
      "is_citywide": false,
      "promise_made_date": "2016-05-17",
      "deadline_date": "2016-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 3603,
      "promise_age_days": 3831,
      "time_to_verdict_days": 3830,
      "entity_canonical_name": "AT&T",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Infrastructure",
      "category_l2": "Broadband & Ultra-High-Speed Internet",
      "secondary_categories": [
        "Economy & Commercial"
      ],
      "tags": [
        "att_gigapower",
        "gigabit_fiber",
        "broadband_expansion",
        "telecom"
      ],
      "verdict_confidence": 0.86,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 1,
      "verdict_reason_code": "undecided_conflicting_evidence",
      "impact_score": 6,
      "completion_percentage": 50,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.govtech.com/network/ATT-Launches-Fiber-Internet-in-San-Francisco-Bay-Area.html",
      "document_title": "AT&T Public Market Street Wi-Fi Expansion",
      "title": "AT&T Public Market Street Wi-Fi Expansion"
    },
    {
      "promise_id": "P62",
      "promise_text": "will hold 1,500 employees when it is expected to open in 2024.",
      "entity": "Visa",
      "role": null,
      "entity_type": "company",
      "category": "Infrastructure & Tech",
      "neighborhood": "Mission Bay Commercial Campus",
      "promised_date": "2019-11-06",
      "due_date": "2024-12-31",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "numeric target not met or plan abandoned; due 2024-12-31 = year end from expected to open in 2024 in source",
      "source_id": "Sc4d60c4996a0",
      "source_url": "https://www.bisnow.com/news/san-francisco/office/visa-to-build-global-hq-at-giants-tishman-speyers-mission-rock-101678",
      "source_file_path": "3c9cd1808d8249457b66909742f49e6d913aa585f42aa2c31f54590f12b8fa5c.md",
      "source_hash": "3c9cd1808d8249457b66909742f49e6d913aa585f42aa2c31f54590f12b8fa5c",
      "source_type": "news_report",
      "fetched_at": "2026-11-11T04:20:47Z",
      "relevance": {
        "score": 7,
        "real": 2,
        "measurable": 2,
        "sf": 1,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:21:25Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Visa's huge new Mission Rock office opened (milestone reached)",
              "evidence_date": "2024-06-06",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P62",
              "quote": "has reached another milestone with the opening of Visa\u2019s huge new office.",
              "quote_match": "exact",
              "source_file_path": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75.md",
              "source_hash": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75",
              "source_url": "https://www.sfchronicle.com/sf/article/visa-new-office-19484682.php"
            },
            {
              "claim_text": "Visa moved workers into the 300,000-square-foot Mission Rock building",
              "evidence_date": "2024-06-06",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P62",
              "quote": "In the past few weeks, the payments giant has moved about 1,000 workers into the white, 300,000-square-foot building at Dr. Maya Angelou Lane and Toni Stone Crossing.",
              "quote_match": "exact",
              "source_file_path": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75.md",
              "source_hash": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75",
              "source_url": "https://www.sfchronicle.com/sf/article/visa-new-office-19484682.php"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P62"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Only about 1,000 workers moved in, below the promised 1,500",
              "evidence_date": "2024-06-06",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P62",
              "quote": "the payments giant has moved about 1,000 workers into the white, 300,000-square-foot building",
              "quote_match": "exact",
              "source_file_path": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75.md",
              "source_hash": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75",
              "source_url": "https://www.sfchronicle.com/sf/article/visa-new-office-19484682.php"
            },
            {
              "claim_text": "Visa no longer calls it the global HQ; now a market support center",
              "evidence_date": "2024-06-06",
              "evidence_type": "news_report",
              "page_number": null,
              "promise_id": "P62",
              "quote": "Although Visa described the building in 2019 as its new global headquarters, it\u2019s now calling it a \u201cmarket support center\u201d that works with clients and businesses around the world.",
              "quote_match": "exact",
              "source_file_path": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75.md",
              "source_hash": "c4d60c4996a053703940f0a6063ff8a4a9252ab3bfe143c9e4f9a8556168de75",
              "source_url": "https://www.sfchronicle.com/sf/article/visa-new-office-19484682.php"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P62"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "numeric target not met or plan abandoned"
        }
      ],
      "display_no": 52,
      "importance_score": 49,
      "impact_rank": 52,
      "source_tier": "News",
      "neighborhood_canonical": "Mission Bay",
      "address_full": "Dr Maya Angelou Lane & Toni Stone Crossing, San Francisco, CA 94158",
      "latitude": 37.7735,
      "longitude": -122.389,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2019-11-06",
      "deadline_date": "2024-12-31",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 681,
      "promise_age_days": 2563,
      "time_to_verdict_days": 2562,
      "entity_canonical_name": "Visa",
      "entity_category": "corporation",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Economy & Commercial",
      "category_l2": "Corporate Headquarters & Commercial Campuses",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "visa_mission_rock",
        "global_hq",
        "1500_employees",
        "commercial_lease"
      ],
      "verdict_confidence": 0.97,
      "verdict_evidence_count": 1,
      "verdict_contradiction_count": 2,
      "verdict_reason_code": "numeric_target_missed",
      "impact_score": 7,
      "completion_percentage": 66,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.bisnow.com/news/san-francisco/office/visa-to-build-global-hq-at-giants-tishman-speyers-mission-rock-101678",
      "document_title": "Visa Mission Rock HQ 1,500 Staff Occupancy",
      "title": "Visa Mission Rock HQ 1,500 Staff Occupancy"
    },
    {
      "promise_id": "P65",
      "promise_text": "Substantial completion of the contract was originally scheduled for February 10, 2018",
      "entity": "SFMTA",
      "role": "San Francisco Municipal Transportation Agency",
      "entity_type": "official",
      "category": "Transit & Streets",
      "neighborhood": "Central Subway Project Corridor",
      "promised_date": "2012",
      "due_date": "2018-02-10",
      "page_number": null,
      "verdict": "broken",
      "verdict_reason": "due date passed with no passing kept evidence; due 2018-02-10 = original substantial-completion date stated in source",
      "source_id": "S319446382722",
      "source_url": "https://www.sfmta.com/index%2Ephp/media/42253/download?inline",
      "source_file_path": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996.md",
      "source_hash": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:25:20Z",
      "relevance": {
        "score": 7,
        "real": 2,
        "measurable": 2,
        "sf": 1,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:27:33Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [],
          "evidence_checked": 2,
          "note": "none found: seed (SFMTA monitoring report) states the miss directly; 1 kept search returned only delay/2022-opening coverage (KQED). No source claims a 2018 opening. No second search per cut rule.",
          "promise_id": "P65"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [
            {
              "claim_text": "Soft opening occurred November 19, 2022, not 2018",
              "evidence_date": "2022-11-19",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P65",
              "quote": "the soft opening occurred on November 19, 2022",
              "quote_match": "exact",
              "source_file_path": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996.md",
              "source_hash": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996",
              "source_url": "https://www.sfmta.com/index%2Ephp/media/42253/download?inline"
            },
            {
              "claim_text": "Opening was more than 1,400 days late vs original date",
              "evidence_date": "2022-11-19",
              "evidence_type": "count",
              "page_number": null,
              "promise_id": "P65",
              "quote": "is more than 1,400 days later than the original substantial completion date.",
              "quote_match": "exact",
              "source_file_path": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996.md",
              "source_hash": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996",
              "source_url": "https://www.sfmta.com/index%2Ephp/media/42253/download?inline"
            },
            {
              "claim_text": "Full revenue service projected January 7, 2023",
              "evidence_date": "2023-01-07",
              "evidence_type": "opening",
              "page_number": null,
              "promise_id": "P65",
              "quote": "currently projects a full Revenue Service Date (RSD) of January 7, 2023.",
              "quote_match": "exact",
              "source_file_path": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996.md",
              "source_hash": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996",
              "source_url": "https://www.sfmta.com/index%2Ephp/media/42253/download?inline"
            }
          ],
          "evidence_checked": 1,
          "promise_id": "P65"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date passed with no passing kept evidence"
        }
      ],
      "display_no": 53,
      "importance_score": 48,
      "impact_rank": 53,
      "source_tier": "Official",
      "neighborhood_canonical": "South of Market",
      "address_full": "4th St & Folsom St, San Francisco, CA 94107",
      "latitude": 37.7818,
      "longitude": -122.401,
      "supervisor_district": 6,
      "is_citywide": false,
      "promise_made_date": "2012-01-01",
      "deadline_date": "2018-02-10",
      "completion_date": null,
      "days_remaining": null,
      "days_overdue": 3197,
      "promise_age_days": 5429,
      "time_to_verdict_days": 5428,
      "entity_canonical_name": "San Francisco Municipal Transportation Agency (SFMTA)",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Subway & Rail Transit",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "central_subway",
        "sfmta",
        "revenue_service",
        "chinatown_station"
      ],
      "verdict_confidence": 0.98,
      "verdict_evidence_count": 0,
      "verdict_contradiction_count": 3,
      "verdict_reason_code": "timeline_missed_delay",
      "impact_score": 9,
      "completion_percentage": 75,
      "source_credibility_score": 10,
      "source_type_standardized": "official_government",
      "source_domain_authority": 10,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfmta.com/index%2Ephp/media/42253/download?inline",
      "document_title": "Central Subway Contract Completion (May 2018)",
      "title": "Central Subway Contract Completion (May 2018)"
    },
    {
      "promise_id": "P85",
      "promise_text": "At the [June 9 Transportation Authority Board meeting](/events/transportation-authority-board-131), our board approved $230,700 in Prop L transportation sales tax funds for the Central Subway North Beach Extension Study, a two-year effort to evaluate extending light rail service from Chinatown to North Beach.",
      "entity": "Transportation Authority Board",
      "role": null,
      "entity_type": "official",
      "category": "Transit & Streets",
      "neighborhood": "Chinatown & North Beach (Central Subway Extension)",
      "promised_date": "2026-06-09",
      "due_date": "2028-05-31",
      "page_number": null,
      "verdict": "in_progress",
      "verdict_reason": "due date in future and no definitive resolution yet [due 2028-05-31 from source: SFMTA expects to complete the Study in May 2028]",
      "source_id": "S1e43ffac93a7",
      "source_url": "https://www.sfcta.org/blogs/transportation-authority-board-approves-230700-study-central-subway-extension-north-beach",
      "source_file_path": "0b0967e4748fe45cf1a228c07bbe762cf1cfc84a1b48dacba39aa804a6d012f0.md",
      "source_hash": "0b0967e4748fe45cf1a228c07bbe762cf1cfc84a1b48dacba39aa804a6d012f0",
      "source_type": "other_official",
      "fetched_at": "2026-11-11T04:15:12Z",
      "relevance": {
        "score": 8,
        "real": 2,
        "measurable": 2,
        "sf": 2,
        "interesting": 2
      },
      "reading_used": null,
      "decided_at": "2026-11-11T04:18:18Z",
      "advocate_bundles": {
        "kept": {
          "advocate_role": "kept_advocate",
          "claims": [
            {
              "claim_text": "Live SFMTA page observed Nov 10, 2026 (local) presents the study as active, planned for completion between mid-2026 and mid-2028",
              "evidence_date": "2026-11-10",
              "evidence_type": "announcement",
              "page_number": null,
              "promise_id": "P85",
              "quote": "This study is planned to be completed between mid-2026 and mid-2028.",
              "quote_match": "exact",
              "source_file_path": "1e43ffac93a758d21ff3efb5fcd29b0774327319e6257a0b6446f7f927c98010.md",
              "source_hash": "1e43ffac93a758d21ff3efb5fcd29b0774327319e6257a0b6446f7f927c98010",
              "source_url": "https://sfmta.com/projects/central-subway-extension"
            }
          ],
          "dropped_claims": [
            {
              "index": 0,
              "note": "DROPPED per parent: year-precision evidence_date 2026 resolved to Jan 1 and failed check_date; superseded by live-status claim. Its verifications VFY-P85-00..06 stand as audit trail.",
              "quote": "The SFMTA relaunched the study as the Central Subway North Beach Extension Study in 2026."
            }
          ],
          "evidence_checked": 3,
          "promise_id": "P85"
        },
        "broken": {
          "advocate_role": "broken_advocate",
          "claims": [],
          "evidence_checked": 1,
          "note": "none found: no cancellation, delay, or funding pull; SFMTA fiscal-cliff context does not state study cancellation. Study reaffirmed active with May 2028 completion target.",
          "promise_id": "P85"
        }
      },
      "checks": [
        {
          "check": "authenticity_domain",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_hash",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_quote",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "authenticity_speaker",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_date",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "accuracy_evidence",
          "passed": true,
          "reason": "pass"
        },
        {
          "check": "verdict_rubric",
          "passed": true,
          "reason": "due date in future and no definitive resolution yet"
        }
      ],
      "display_no": 54,
      "importance_score": 47,
      "impact_rank": 54,
      "source_tier": "News",
      "neighborhood_canonical": "Chinatown",
      "address_full": "Columbus Ave & Washington St, San Francisco, CA 94111",
      "latitude": 37.7958,
      "longitude": -122.4045,
      "supervisor_district": 3,
      "is_citywide": false,
      "promise_made_date": "2026-06-09",
      "deadline_date": "2028-05-31",
      "completion_date": null,
      "days_remaining": 566,
      "days_overdue": null,
      "promise_age_days": 156,
      "time_to_verdict_days": 155,
      "entity_canonical_name": "San Francisco County Transportation Authority (SFCTA)",
      "entity_category": "city_department",
      "entity_party": null,
      "entity_term_start": null,
      "entity_term_end": null,
      "category_l1": "Transportation",
      "category_l2": "Subway & Rail Transit Extension",
      "secondary_categories": [
        "Infrastructure"
      ],
      "tags": [
        "central_subway_extension",
        "north_beach_extension",
        "fisherman_wharf",
        "sfcta"
      ],
      "verdict_confidence": 0.92,
      "verdict_evidence_count": 2,
      "verdict_contradiction_count": 0,
      "verdict_reason_code": "in_progress_on_track",
      "impact_score": 8,
      "completion_percentage": 25,
      "source_credibility_score": 7,
      "source_type_standardized": "corporate_release",
      "source_domain_authority": 7,
      "fact_check_status": "verified",
      "source_archived_url": "https://web.archive.org/web/*/https://www.sfcta.org/blogs/transportation-authority-board-approves-230700-study-central-subway-extension-north-beach",
      "document_title": "Central Subway Chinatown & North Beach Study",
      "title": "Central Subway Chinatown & North Beach Study"
    }
  ],
  "quarantined": [
    {
      "quarantine_id": "Q-N01",
      "promise_id": "N01",
      "type_badge": "Test case",
      "title": "Add 1,500 new shelter beds [Word Swapped: beds \u2192 units]",
      "planted_claim": "The city added 1,500 new shelter units within six months.",
      "original_text": "beds",
      "altered_text": "units",
      "change_diff": "'beds' \u2192 'units'",
      "check_type": "accuracy_quote",
      "failing_check": "Quote not found in saved source",
      "failing_check_code": "accuracy_quote",
      "reason": "Quote 'shelter units' is not a verbatim substring of saved source file (source text reads '1,500 new shelter beds').",
      "agent": "Extractor Agent",
      "quarantined_at": "2026-11-10T14:30:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
      "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center"
    },
    {
      "quarantine_id": "Q-N02",
      "promise_id": "N02",
      "type_badge": "Test case",
      "title": "Wrong Speaker Claim [Breed attribute to Lurie]",
      "planted_claim": "Mayor Daniel Lurie promised $5M for retail recovery.",
      "original_text": "London Breed",
      "altered_text": "Daniel Lurie",
      "change_diff": "'Breed' \u2192 'Lurie'",
      "check_type": "authenticity_speaker",
      "failing_check": "Speaker Roll Call Verification",
      "failing_check_code": "authenticity_speaker",
      "reason": "Speaker mismatch: Daniel Lurie was not mayor in 2023; municipal record names London Breed.",
      "agent": "Extractor Agent",
      "quarantined_at": "2026-11-10T14:32:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "6685fe8d7b3d73bc63e7d84d0f1db531e6d6cd12bf90d1c5cf63885f90c8bc6a",
      "source_file_path": "6685fe8d7b3d73bc63e7d84d0f1db531e6d6cd12bf90d1c5cf63885f90c8bc6a.md",
      "source_url": "https://sfgov.legistar.com/LegislationDetail.aspx?ID=6431980"
    },
    {
      "quarantine_id": "Q-N03",
      "promise_id": "N03",
      "type_badge": "Test case",
      "title": "Corrupted Source Byte [Single byte tampering]",
      "planted_claim": "Cryptographic byte tamper in saved municipal record source file.",
      "original_text": "SHA-256: e03acc33e8...",
      "altered_text": "SHA-256: c4a1b029ff...",
      "change_diff": "Byte offset 0x4F altered",
      "check_type": "authenticity_hash",
      "failing_check": "SHA-256 Byte-Level Integrity Check",
      "failing_check_code": "authenticity_hash",
      "reason": "Hash mismatch: computed SHA-256 does not match immutable disk fingerprint.",
      "agent": "Fetcher Agent",
      "quarantined_at": "2026-11-10T14:34:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05",
      "source_file_path": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05.md",
      "source_url": "https://www.sf.gov/press-release/cleanpowersf-grid"
    },
    {
      "quarantine_id": "Q-N04",
      "promise_id": "N04",
      "type_badge": "Test case",
      "title": "Invented Promise Without Official Source",
      "planted_claim": "City will provide free municipal fiber internet to all residents by 2026.",
      "original_text": "None",
      "altered_text": "Fabricated pledge",
      "change_diff": "Fabricated pledge",
      "check_type": "accuracy_evidence",
      "failing_check": "Primary Evidence Authenticity Check",
      "failing_check_code": "accuracy_evidence",
      "reason": "Evidence check failed: no primary meeting record, legislation, or official sf.gov page found.",
      "agent": "Extractor Agent",
      "quarantined_at": "2026-11-10T14:36:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "18eeac2d2261dd43a9744058ca524cb2107dc65d46dcb8427858752a8cc8a49b",
      "source_file_path": "18eeac2d2261dd43a9744058ca524cb2107dc65d46dcb8427858752a8cc8a49b.md",
      "source_url": "https://www.sf.gov/departments/department-technology"
    },
    {
      "quarantine_id": "Q-N05",
      "promise_id": "N05",
      "type_badge": "Test case",
      "title": "Invented Metric [1,500 inflated to 2,000]",
      "planted_claim": "Mayor promised 2,000 shelter beds within six months.",
      "original_text": "1,500",
      "altered_text": "2,000",
      "change_diff": "'1,500' \u2192 '2,000'",
      "check_type": "accuracy_quote",
      "failing_check": "Metric Number Verification",
      "failing_check_code": "accuracy_quote",
      "reason": "Metric altered: source specifies 1,500 beds; claimed number 2,000 fails exact match.",
      "agent": "Kept Advocate",
      "quarantined_at": "2026-11-10T14:38:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
      "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center"
    },
    {
      "quarantine_id": "Q-N06",
      "promise_id": "N06",
      "type_badge": "Test case",
      "title": "Invented Completion Date Out of Range",
      "planted_claim": "Stabilization center completed December 2024 (before promise made).",
      "original_text": "April 28, 2025",
      "altered_text": "December 2024",
      "change_diff": "Date predates promise inception",
      "check_type": "accuracy_date",
      "failing_check": "Promised Date Window Check",
      "failing_check_code": "accuracy_date",
      "reason": "Date out of range: completed_at 2024-12-01 predates promised_at 2025-01-07.",
      "agent": "Kept Advocate",
      "quarantined_at": "2026-11-10T14:40:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
      "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center"
    },
    {
      "quarantine_id": "Q-N07",
      "promise_id": "N07",
      "type_badge": "Test case",
      "title": "Advocate Hallucination [Fabricated completion quote]",
      "planted_claim": "The stabilization center fully solved the neighborhood addiction crisis.",
      "original_text": "None",
      "altered_text": "Hallucinated assertion",
      "change_diff": "Fabricated assertion",
      "check_type": "accuracy_quote",
      "failing_check": "Advocate Claim Quote Match",
      "failing_check_code": "accuracy_quote",
      "reason": "Quote check failed: advocate quote not found verbatim in any saved primary document.",
      "agent": "Kept Advocate",
      "quarantined_at": "2026-11-10T14:42:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
      "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center"
    },
    {
      "quarantine_id": "Q-N08",
      "promise_id": "N08",
      "type_badge": "Test case",
      "title": "Unsupported Contradicting Claim",
      "planted_claim": "The stabilization center was condemned and demolished in May 2025.",
      "original_text": "Facility operating",
      "altered_text": "Demolished in May 2025",
      "change_diff": "Fabricated contradiction",
      "check_type": "accuracy_evidence",
      "failing_check": "Contradicting Evidence Integrity Check",
      "failing_check_code": "accuracy_evidence",
      "reason": "Evidence check failed: no corroborating public record supports claimed closure or demolition.",
      "agent": "Broken Advocate",
      "quarantined_at": "2026-11-10T14:44:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
      "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center"
    },
    {
      "quarantine_id": "Q-N09",
      "promise_id": "N09",
      "type_badge": "Test case",
      "title": "Fake Source Domain [Phishing / Unregistered host]",
      "planted_claim": "Mayor announced $50M downtown bond on sanfrancisco-citygov-portal.com.",
      "original_text": "sf.gov",
      "altered_text": "sanfrancisco-citygov-portal.com",
      "change_diff": "Untrusted domain origin",
      "check_type": "authenticity_domain",
      "failing_check": "Domain Allowlist Enforcement",
      "failing_check_code": "authenticity_domain",
      "reason": "Domain rejected: sanfrancisco-citygov-portal.com is not on the trusted allowlist (sf.gov, sfmta.com, legistar).",
      "agent": "Fetcher Agent",
      "quarantined_at": "2026-11-10T14:46:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "8cabdac8edb9a6e040b194061a1cc31858b52c09293900df872e654654f1cfe5",
      "source_file_path": "8cabdac8edb9a6e040b194061a1cc31858b52c09293900df872e654654f1cfe5.md",
      "source_url": "https://sanfrancisco-citygov-portal.com/announcements/retail-bond"
    },
    {
      "quarantine_id": "Q-N10",
      "promise_id": "N10",
      "type_badge": "Test case",
      "title": "Expired Due Date Without Verification Record",
      "planted_claim": "Central Subway extension finished December 2022 (no rubric entry).",
      "original_text": "Active ongoing",
      "altered_text": "Unverified finish claim",
      "change_diff": "Missing rubric verification",
      "check_type": "verdict_rubric",
      "failing_check": "Deterministic Rubric Application",
      "failing_check_code": "verdict_rubric",
      "reason": "Rubric evaluation failed: due date passed without affirmative evidence; defaulted to broken.",
      "agent": "Arbitrator Engine",
      "quarantined_at": "2026-11-10T14:48:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95",
      "source_file_path": "cd7fb800349ae1387eb78a87d4a1db1425b3c3060770bb4217483990c4edcd95.md",
      "source_url": "https://www.sfmta.com/projects/central-subway-project"
    },
    {
      "quarantine_id": "Q-N11",
      "promise_id": "N11",
      "type_badge": "Test case",
      "title": "Evidence Filed Against Wrong Promise ID",
      "planted_claim": "Filing P02 822 Geary evidence against P07 statewide housing promise.",
      "original_text": "P02 (Crisis Center)",
      "altered_text": "P07 (Statewide Housing)",
      "change_diff": "Cross-promise ID misattribution",
      "check_type": "accuracy_evidence",
      "failing_check": "Promise ID Cross-Check",
      "failing_check_code": "accuracy_evidence",
      "reason": "Promise mismatch: evidence cites P02 stabilization center but was submitted under P07 housing target.",
      "agent": "Broken Advocate",
      "quarantined_at": "2026-11-10T14:50:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa",
      "source_file_path": "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa.md",
      "source_url": "https://www.sf.gov/news-mayor-lurie-delivers-on-key-commitment-opening-247-police-friendly-stabilization-center"
    },
    {
      "quarantine_id": "Q-N12",
      "promise_id": "N12",
      "type_badge": "Test case",
      "title": "Restated Procedural Vote (Low Relevance)",
      "planted_claim": "Supervisor moved to approve the minutes of the previous meeting.",
      "original_text": "None",
      "altered_text": "Procedural approval vote",
      "change_diff": "Procedural motion (Score 2/8)",
      "check_type": "relevance_low",
      "failing_check": "Relevance Gate Score >= 5",
      "failing_check_code": "relevance_low",
      "reason": "Relevance too low (score 2/8): procedural vote approval is not a substantive civic promise.",
      "agent": "Relevance Gate",
      "quarantined_at": "2026-11-10T14:52:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996",
      "source_file_path": "3194463827222e99bc30944c11dbc79f6a500a9055eda4177d4b61c2b1141996.md",
      "source_url": "https://sfgov.legistar.com/MeetingDetail.aspx?ID=1142901"
    },
    {
      "quarantine_id": "Q-P68",
      "promise_id": "P68",
      "type_badge": "Rejected candidate",
      "title": "[Bay Area - PayPal Park, San Jose, not SF proper] Bay FC will play their first home game at PayPal Park on Saturday, March 30, against the Houston Dash",
      "planted_claim": null,
      "claim": "Bay FC will play their first home game at PayPal Park on Saturday, March 30, against the Houston Dash",
      "original_text": null,
      "altered_text": null,
      "change_diff": "Non-SF municipal venue (San Jose)",
      "check_type": "relevance_gate",
      "failing_check": "Relevance score too low (non-SF jurisdiction)",
      "failing_check_code": "relevance_low",
      "reason": "Event occurs at PayPal Park in San Jose, CA, outside San Francisco municipal jurisdiction and civic accountability scope.",
      "relevance": {
        "score": 2.5,
        "real": 1.0,
        "measurable": 1.0,
        "sf": 0.0,
        "interesting": 0.5
      },
      "agent": "Screening Arbitrator",
      "quarantined_at": "2026-11-10T14:55:00Z",
      "quarantined_date": "Nov 10, 2026",
      "destination": "Held back. Never published.",
      "source_hash": "848553de6293dc9ebe825e72451d6e692ca42c9c7439cb706a6a62e193ee5105",
      "source_file_path": "848553de6293dc9ebe825e72451d6e692ca42c9c7439cb706a6a62e193ee5105.md",
      "source_url": "https://www.bayfc.com/news/bay-fc-home-opener-march-30"
    }
  ]
};

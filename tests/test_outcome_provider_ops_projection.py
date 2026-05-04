from __future__ import annotations

import importlib


def _provider_payload() -> dict[str, object]:
    return {
        "query": "Pituitary neuroendocrine tumor invasive architecture",
        "search_strategy": {
            "query": "Pituitary neuroendocrine tumor invasive architecture",
            "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
            "keywords": ["invasive architecture", "pituitary neuroendocrine tumor"],
        },
        "search_date": "2026-05-03",
        "why_worth_doing": "Guideline-bound evidence supports the study question.",
        "provider_payloads": [
            {
                "provider": "pubmed",
                "query": "pituitary neuroendocrine tumor invasive architecture",
                "retrieved_at": "2026-05-03T08:00:00Z",
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:PUBMED_API_KEY"},
                "rate_limit_status": {"status": "ok", "remaining": 8},
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/pubmed.json"],
                "request_id": "pubmed-run",
                "records": [
                    {
                        "pmid": "12345678",
                        "title": "Invasive pituitary neuroendocrine tumor architecture",
                        "category": "anchor_papers",
                        "citation_ledger_ref": "paper/evidence_ledger.json#pmid-12345678",
                    }
                ],
            },
            {
                "provider": "crossref",
                "query": "TRIPOD AI pituitary endocrine prediction reporting",
                "retrieved_at": "2026-05-03T08:01:00Z",
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:CROSSREF_MAILTO"},
                "rate_limit_status": {"status": "ok", "remaining": 42},
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/crossref.json"],
                "request_id": "crossref-run",
                "items": [
                    {
                        "DOI": "10.1000/systematic-review",
                        "title": ["Systematic review of pituitary prediction models"],
                        "category": "systematic_reviews",
                        "citation_ledger_ref": "paper/evidence_ledger.json#doi-systematic-review",
                    },
                    {
                        "DOI": "10.1000/tripod-ai",
                        "title": ["TRIPOD+AI reporting guideline"],
                        "category": "guidelines",
                        "citation_ledger_ref": "paper/evidence_ledger.json#doi-tripod-ai",
                    },
                ],
            },
            {
                "provider": "semantic_scholar",
                "query": "clinical endocrinology pituitary invasive biomarker",
                "retrieved_at": "2026-05-03T08:02:00Z",
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:SEMANTIC_SCHOLAR_API_KEY"},
                "rate_limit_status": {"status": "ok", "remaining": 12},
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/semantic-scholar.json"],
                "request_id": "semantic-scholar-run",
                "results": [
                    {
                        "paperId": "SEMANTIC123",
                        "title": "Neighboring clinical endocrinology paper",
                        "category": "journal_neighbor_refs",
                        "score": 0.91,
                        "score_source_ref": "semantic-scholar:query-run",
                        "citation_ledger_ref": "paper/evidence_ledger.json#semantic-SEMANTIC123",
                    }
                ],
            },
        ],
        "screening_decisions": [
            {"ref": "pmid:12345678", "decision": "include", "reason": "Clinical anchor."},
            {"ref": "doi:10.1000/tripod-ai", "decision": "include", "reason": "Reporting guideline."},
        ],
    }


def _outcome_payload() -> dict[str, object]:
    return {
        "learning_entries": [
            {
                "entry_id": "learn::major-revision::claim",
                "source_outcome": "major_revision",
                "failure_mode": "claim_overreach",
                "source_ref": "reviews/round-1.md#claim",
                "issue_summary": "Primary clinical claim exceeded the evidence ledger.",
                "claim_refs": ["paper/claim_evidence_map.json#claim-primary"],
                "evidence_refs": ["paper/evidence_ledger.json#claim-primary"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#claim-primary"],
            },
            {
                "entry_id": "learn::desk-reject::external-validation",
                "source_outcome": "editorial_desk_reject",
                "failure_mode": "weak_external_validation",
                "source_ref": "reviews/desk-reject.md#editor",
                "issue_summary": "External validation was too weak for the target claim.",
                "claim_refs": ["paper/claim_evidence_map.json#claim-secondary"],
                "evidence_refs": ["paper/evidence_ledger.json#claim-secondary"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#claim-secondary"],
            },
        ]
    }


def _journal_fixture_matrix() -> list[dict[str, object]]:
    return [
        {
            "journal_family": "general_internal_medicine",
            "fixture_ref": "fixtures/journals/general_internal_medicine.json",
            "profile_ref": "paper/journal_requirements/general_internal_medicine.json",
            "coverage": {
                "cover_letter": True,
                "submission_checklist": True,
                "supplement_naming": True,
            },
        },
        {
            "journal_family": "clinical_endocrinology",
            "fixture_ref": "fixtures/journals/clinical_endocrinology.json",
            "profile_ref": "paper/journal_requirements/clinical_endocrinology.json",
            "coverage": {
                "cover_letter": True,
                "submission_checklist": True,
                "supplement_naming": True,
            },
        },
    ]


def test_outcome_provider_ops_projection_merges_l3_inputs_without_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.outcome_provider_ops_projection")

    projection = module.build_outcome_provider_ops_projection(
        outcome_calibration_payload=_outcome_payload(),
        provider_runtime_payload=_provider_payload(),
        journal_family_fixture_matrix=_journal_fixture_matrix(),
    )

    assert projection["surface"] == "outcome_provider_ops_projection"
    assert projection["lane_id"] == "L3_outcome_calibration_and_provider_ops"
    assert projection["status"] == "ready"
    assert projection["authority_mode"] == "observability_only"
    assert projection["observability_only"] is True
    assert projection["source_surfaces"] == [
        "ai_reviewer_calibration_learning_read_model",
        "ai_reviewer_outcome_learning_regression",
        "literature_provider_runtime",
        "scheduled_provider_health_read_model",
        "journal_family_fixture_matrix",
    ]
    assert projection["authority_contract"] == {
        "authority": "observability_projection_only",
        "read_model_only": True,
        "observability_only": True,
        "can_authorize_quality": False,
        "can_authorize_drafting": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "can_bypass_ai_reviewer": False,
        "can_bypass_publication_gate": False,
        "required_authority_surfaces": [
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
            "AI reviewer publication gate",
        ],
    }
    assert projection["outcome_calibration"]["outcome_counts"] == {
        "editorial_desk_reject": 1,
        "major_revision": 1,
    }
    assert projection["provider_ops"]["provider_health_status"] == "ready"
    assert projection["provider_ops"]["partial_outage_providers"] == []
    assert projection["provider_ops"]["citation_ledger_drift"]["status"] == "stable"
    assert projection["journal_family_fixture_matrix"]["status"] == "ready"
    assert projection["journal_family_fixture_matrix"]["covered_families"] == [
        "clinical_endocrinology",
        "general_internal_medicine",
    ]
    assert projection["journal_family_fixture_matrix"]["required_coverage"] == [
        "cover_letter",
        "submission_checklist",
        "supplement_naming",
    ]
    assert projection["quality_claim_authorized"] is False
    assert projection["submission_ready_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
    assert projection["diagnostics"] == []


def test_outcome_provider_ops_projection_surfaces_provider_drift_without_bypassing_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.outcome_provider_ops_projection")
    provider_payload = _provider_payload()
    provider_payload["citation_freshness"] = {
        "status": "stale",
        "stale_refs": ["paper/evidence_ledger.json#pmid-12345678"],
        "checked_at": "2026-05-04T00:00:00Z",
    }
    provider_payloads = list(provider_payload["provider_payloads"])  # type: ignore[arg-type]
    crossref = dict(provider_payloads[1])  # type: ignore[arg-type]
    crossref["response_status"] = "partial_outage"
    provider_payloads[1] = crossref
    provider_payload["provider_payloads"] = provider_payloads

    projection = module.build_outcome_provider_ops_projection(
        outcome_calibration_payload=_outcome_payload(),
        provider_runtime_payload=provider_payload,
        journal_family_fixture_matrix=[
            {
                "journal_family": "general_internal_medicine",
                "fixture_ref": "fixtures/journals/general_internal_medicine.json",
                "coverage": {"cover_letter": True, "submission_checklist": True},
            }
        ],
    )

    assert projection["status"] == "blocked"
    assert projection["provider_ops"]["provider_health_status"] == "blocked"
    assert projection["provider_ops"]["partial_outage_providers"] == ["crossref"]
    assert projection["provider_ops"]["citation_ledger_drift"] == {
        "status": "drifted",
        "stale_refs": ["paper/evidence_ledger.json#pmid-12345678"],
        "missing_providers": [],
    }
    assert projection["journal_family_fixture_matrix"]["status"] == "blocked"
    assert projection["journal_family_fixture_matrix"]["missing_coverage"] == {
        "general_internal_medicine": ["supplement_naming"],
    }
    assert [item["reason_code"] for item in projection["diagnostics"]] == [
        "provider_partial_outage_crossref",
        "stale_citation_ledger_refs",
        "journal_family_fixture_missing_supplement_naming",
    ]
    assert projection["authority_contract"]["can_bypass_ai_reviewer"] is False
    assert projection["authority_contract"]["can_bypass_publication_gate"] is False
    assert projection["quality_claim_authorized"] is False
    assert projection["submission_ready_authorized"] is False

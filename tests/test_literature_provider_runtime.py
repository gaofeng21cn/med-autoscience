from __future__ import annotations

import importlib
from pathlib import Path


def _complete_provider_payload() -> dict[str, object]:
    return {
        "search_date": "2026-05-03",
        "search_strategy": {
            "query": "Pituitary neuroendocrine tumor invasive architecture",
            "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
            "keywords": ["invasive architecture", "pituitary neuroendocrine tumor"],
        },
        "why_worth_doing": "Guideline-bound evidence and recent neighboring papers support the study question.",
        "providers": [
            {
                "provider_name": "pubmed",
                "query": "pituitary neuroendocrine tumor invasive architecture",
                "retrieved_at": "2026-05-03T08:00:00Z",
                "source_refs": ["pubmed:query-run-2026-05-03"],
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:PUBMED_API_KEY"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 8,
                    "reset_at": "2026-05-03T09:00:00Z",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/pubmed-2026-05-03.json"],
                "items": [
                    {
                        "ref": "pmid:anchor-1",
                        "category": "anchor_papers",
                        "title": "Invasive pituitary neuroendocrine tumor architecture",
                        "citation_ledger_ref": "paper/evidence_ledger.json#anchor-1",
                    }
                ],
            },
            {
                "provider_name": "crossref",
                "query": "TRIPOD AI pituitary endocrine prediction reporting",
                "retrieved_at": "2026-05-03T08:01:00Z",
                "source_refs": ["crossref:query-run-2026-05-03"],
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:CROSSREF_MAILTO"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 42,
                    "reset_at": "2026-05-03T09:00:00Z",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/crossref-2026-05-03.json"],
                "items": [
                    {
                        "ref": "doi:10.1000/systematic-review",
                        "category": "systematic_reviews",
                        "title": "Systematic review of pituitary prediction models",
                        "citation_ledger_ref": "paper/evidence_ledger.json#systematic-review",
                    },
                    {
                        "ref": "guideline:TRIPOD+AI",
                        "category": "guidelines",
                        "title": "TRIPOD+AI reporting guideline",
                        "citation_ledger_ref": "paper/evidence_ledger.json#tripod-ai",
                    },
                ],
            },
            {
                "provider_name": "semantic_scholar",
                "query": "clinical endocrinology pituitary invasive biomarker",
                "retrieved_at": "2026-05-03T08:02:00Z",
                "source_refs": ["semantic-scholar:query-run-2026-05-03"],
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:SEMANTIC_SCHOLAR_API_KEY"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 12,
                    "reset_at": "2026-05-03T09:00:00Z",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": [
                    "ops/provider_responses/semantic-scholar-2026-05-03.json"
                ],
                "items": [
                    {
                        "ref": "journal-neighbor:clinical-endocrinology-2025",
                        "category": "journal_neighbor_refs",
                        "title": "Neighboring clinical endocrinology paper",
                        "score": 0.91,
                        "score_source_ref": "semantic-scholar:query-run-2026-05-03",
                        "citation_ledger_ref": "paper/evidence_ledger.json#journal-neighbor",
                    }
                ],
            },
        ],
        "screening_decisions": [
            {
                "ref": "pmid:anchor-1",
                "decision": "include",
                "reason": "Defines the clinical anchor and endpoint context.",
            },
            {
                "ref": "pmid:off-topic",
                "decision": "exclude",
                "reason": "Wrong population for the target claim.",
            },
        ],
        "citation_ledger_refs": ["paper/evidence_ledger.json#anchor-1"],
    }


def _provider_backed_intake_payload() -> dict[str, object]:
    return {
        "query": "Pituitary neuroendocrine tumor invasive architecture",
        "search_strategy": {
            "query": "Pituitary neuroendocrine tumor invasive architecture",
            "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
            "keywords": ["invasive architecture", "pituitary neuroendocrine tumor"],
        },
        "search_date": "2026-05-03",
        "why_worth_doing": "Guideline-bound evidence and recent neighboring papers support the study question.",
        "provider_payloads": [
            {
                "provider": "pubmed",
                "query": "pituitary neuroendocrine tumor invasive architecture",
                "retrieved_at": "2026-05-03T08:00:00Z",
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:PUBMED_API_KEY"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 8,
                    "reset_at": "2026-05-03T09:00:00Z",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/pubmed-2026-05-03.json"],
                "request_id": "pubmed-run-2026-05-03",
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
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 42,
                    "reset_at": "2026-05-03T09:00:00Z",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/crossref-2026-05-03.json"],
                "request_id": "crossref-run-2026-05-03",
                "items": [
                    {
                        "DOI": "10.1000/systematic-review",
                        "title": ["Systematic review of pituitary prediction models"],
                        "category": "systematic_reviews",
                        "citation_ledger_ref": "paper/evidence_ledger.json#doi-10.1000-systematic-review",
                    },
                    {
                        "DOI": "10.1000/tripod-ai",
                        "title": ["TRIPOD+AI reporting guideline"],
                        "category": "guidelines",
                        "citation_ledger_ref": "paper/evidence_ledger.json#doi-10.1000-tripod-ai",
                    },
                ],
            },
            {
                "provider": "semantic_scholar",
                "query": "clinical endocrinology pituitary invasive biomarker",
                "retrieved_at": "2026-05-03T08:02:00Z",
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:SEMANTIC_SCHOLAR_API_KEY"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 12,
                    "reset_at": "2026-05-03T09:00:00Z",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-03T08:05:00Z",
                    "expires_at": "2026-05-04T08:05:00Z",
                },
                "provider_response_ledger_refs": [
                    "ops/provider_responses/semantic-scholar-2026-05-03.json"
                ],
                "request_id": "semantic-scholar-run-2026-05-03",
                "results": [
                    {
                        "paperId": "SEMANTIC123",
                        "title": "Neighboring clinical endocrinology paper",
                        "category": "journal_neighbor_refs",
                        "score": 0.91,
                        "score_source_ref": "semantic-scholar:query-run-2026-05-03",
                        "citation_ledger_ref": "paper/evidence_ledger.json#semantic-SEMANTIC123",
                    }
                ],
            },
        ],
        "screening_decisions": [
            {
                "ref": "pmid:12345678",
                "decision": "include",
                "reason": "Defines the clinical anchor and endpoint context.",
            },
            {
                "ref": "doi:10.1000/tripod-ai",
                "decision": "include",
                "reason": "Required reporting guideline for the target claim.",
            },
        ],
    }


def test_provider_runtime_normalizes_provider_backed_intake_and_records_provenance(
    tmp_path: Path,
) -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    literature_os = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _provider_backed_intake_payload()

    result = provider_runtime.materialize_literature_provider_runtime(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "ready"
    assert result["missing_reason"] == ""
    assert result["provider_provenance"] == [
        {
            "provider_name": "pubmed",
            "query": "pituitary neuroendocrine tumor invasive architecture",
            "retrieved_at": "2026-05-03T08:00:00Z",
            "response_status": "ok",
            "source_refs": ["pubmed:pubmed-run-2026-05-03"],
        },
        {
            "provider_name": "crossref",
            "query": "TRIPOD AI pituitary endocrine prediction reporting",
            "retrieved_at": "2026-05-03T08:01:00Z",
            "response_status": "ok",
            "source_refs": ["crossref:crossref-run-2026-05-03"],
        },
        {
            "provider_name": "semantic_scholar",
            "query": "clinical endocrinology pituitary invasive biomarker",
            "retrieved_at": "2026-05-03T08:02:00Z",
            "response_status": "ok",
            "source_refs": ["semantic_scholar:semantic-scholar-run-2026-05-03"],
        },
    ]
    assert result["citation_ledger_refs"] == [
        "paper/evidence_ledger.json#pmid-12345678",
        "paper/evidence_ledger.json#doi-10.1000-systematic-review",
        "paper/evidence_ledger.json#doi-10.1000-tripod-ai",
        "paper/evidence_ledger.json#semantic-SEMANTIC123",
    ]

    literature_payload = result["literature_intelligence_payload"]
    assert literature_payload["anchor_papers"] == ["pmid:12345678"]
    assert literature_payload["systematic_reviews"] == ["doi:10.1000/systematic-review"]
    assert literature_payload["guidelines"] == ["doi:10.1000/tripod-ai"]
    assert literature_payload["journal_neighbor_refs"] == ["semantic_scholar:SEMANTIC123"]
    assert literature_payload["high_score_neighbor_refs"] == [
        {
            "ref": "semantic_scholar:SEMANTIC123",
            "score": 0.91,
            "score_source_ref": "semantic-scholar:query-run-2026-05-03",
        }
    ]
    assert literature_payload["provider_provenance"] == result["provider_provenance"]
    assert literature_payload["why_worth_doing"] == payload["why_worth_doing"]
    assert literature_payload["searched_sources"] == [
        "pubmed:pubmed-run-2026-05-03",
        "crossref:crossref-run-2026-05-03",
        "semantic_scholar:semantic-scholar-run-2026-05-03",
    ]
    literature_result = literature_os.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=literature_payload,
    )
    assert literature_result["status"] == "ready"


def test_provider_backed_intake_fails_closed_when_item_lacks_citation_ledger_ref() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _provider_backed_intake_payload()
    provider_payloads = list(payload["provider_payloads"])  # type: ignore[arg-type]
    pubmed = dict(provider_payloads[0])  # type: ignore[arg-type]
    pubmed["records"] = [
        {
            "pmid": "12345678",
            "title": "Invasive pituitary neuroendocrine tumor architecture",
            "category": "anchor_papers",
        }
    ]
    provider_payloads[0] = pubmed
    payload["provider_payloads"] = provider_payloads

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_provider_citation_ledger_refs_pubmed"
    assert "paper/evidence_ledger.json#pmid-12345678" not in projection["citation_ledger_refs"]


def test_provider_backed_intake_projects_provider_operations_contract() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )

    projection = provider_runtime.build_literature_provider_runtime_projection(
        _provider_backed_intake_payload()
    )

    provider_operations = projection["provider_operations"]
    assert provider_operations["status"] == "ready"
    assert provider_operations["required_providers"] == [
        "pubmed",
        "crossref",
        "semantic_scholar",
    ]
    assert provider_operations["credential_status"]["pubmed"] == {
        "status": "ready",
        "ready": True,
        "credential_ref": "env:PUBMED_API_KEY",
    }
    assert provider_operations["rate_limit_status"]["crossref"] == {
        "status": "ok",
        "limited": False,
        "remaining": 42,
        "reset_at": "2026-05-03T09:00:00Z",
        "backoff": {"policy": "exponential", "retry_after_seconds": 0},
    }
    assert provider_operations["backoff"]["semantic_scholar"] == {
        "policy": "exponential",
        "retry_after_seconds": 0,
    }
    assert provider_operations["cache_freshness"]["semantic_scholar"]["status"] == "fresh"
    assert provider_operations["provider_response_ledger_refs"] == [
        "ops/provider_responses/pubmed-2026-05-03.json",
        "ops/provider_responses/crossref-2026-05-03.json",
        "ops/provider_responses/semantic-scholar-2026-05-03.json",
    ]
    assert projection["provider_response_ledger_refs"] == provider_operations[
        "provider_response_ledger_refs"
    ]
    assert projection["query_fingerprint"].startswith("sha256:")
    assert provider_operations["provider_query_fingerprints"]["pubmed"].startswith("sha256:")
    assert projection["authority_contract"] == {
        "authority": "provider_operations_read_model_only",
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def test_provider_runtime_projects_complete_payload_and_materializes_literature_os_ready(
    tmp_path: Path,
) -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    literature_os = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_provider_payload()

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["surface"] == "literature_provider_runtime"
    assert projection["schema_version"] == 1
    assert projection["status"] == "ready"
    assert projection["missing_reason"] == ""
    assert projection["providers"] == ["pubmed", "crossref", "semantic_scholar"]
    assert projection["search_date"] == "2026-05-03"
    assert projection["search_strategy"] == payload["search_strategy"]
    assert projection["citation_ledger_refs"] == [
        "paper/evidence_ledger.json#anchor-1",
        "paper/evidence_ledger.json#systematic-review",
        "paper/evidence_ledger.json#tripod-ai",
        "paper/evidence_ledger.json#journal-neighbor",
    ]
    assert projection["literature_intelligence_payload"]["provider_provenance"] == projection[
        "provider_provenance"
    ]
    assert projection["literature_intelligence_payload"]["why_worth_doing"] == payload[
        "why_worth_doing"
    ]
    assert projection["literature_intelligence_payload"]["high_score_neighbor_refs"] == [
        {
            "ref": "journal-neighbor:clinical-endocrinology-2025",
            "score": 0.91,
            "score_source_ref": "semantic-scholar:query-run-2026-05-03",
        }
    ]
    assert projection["screening_decisions"] == payload["screening_decisions"]
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
    assert projection["authority_contract"]["can_authorize_quality"] is False
    assert projection["authority_contract"]["can_authorize_submission"] is False
    assert projection["authority_contract"]["can_authorize_finalize"] is False
    assert projection["credential_status"]["pubmed"]["ready"] is True
    assert projection["rate_limit_status"]["crossref"]["limited"] is False
    assert projection["backoff"]["semantic_scholar"]["retry_after_seconds"] == 0
    assert projection["cache_freshness"]["semantic_scholar"]["status"] == "fresh"
    assert projection["provider_response_ledger_refs"] == [
        "ops/provider_responses/pubmed-2026-05-03.json",
        "ops/provider_responses/crossref-2026-05-03.json",
        "ops/provider_responses/semantic-scholar-2026-05-03.json",
    ]
    assert projection["query_fingerprint"].startswith("sha256:")
    assert projection["source_response_digest"] == {
        "provider_count": 3,
        "source_ref_count": 3,
        "item_count": 4,
        "response_statuses": ["ok"],
    }

    result = provider_runtime.materialize_literature_provider_runtime(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "ready"
    assert result["artifact_path"].endswith(
        "artifacts/medical_paper/literature_provider_runtime.json"
    )
    literature_payload = result["literature_intelligence_payload"]
    literature_result = literature_os.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=literature_payload,
    )
    assert literature_result["status"] == "ready"


def test_provider_runtime_fails_closed_for_unknown_provider() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    payload["providers"] = [
        {
            "provider_name": "scopus",
            "query": "pituitary",
            "retrieved_at": "2026-05-03T08:00:00Z",
            "source_refs": ["scopus:query-run"],
            "response_status": "ok",
        }
    ]

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "unsupported_provider_scopus"
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False


def test_provider_runtime_fails_closed_when_required_provider_is_missing() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    payload["providers"] = [
        provider
        for provider in payload["providers"]  # type: ignore[union-attr]
        if provider["provider_name"] != "semantic_scholar"  # type: ignore[index]
    ]

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_provider_sources_semantic_scholar"


def test_provider_runtime_fails_closed_when_credential_is_missing() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    pubmed = dict(providers[0])  # type: ignore[arg-type]
    pubmed["credential_status"] = {"status": "missing"}
    providers[0] = pubmed
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_credential_pubmed"


def test_provider_runtime_fails_closed_when_provider_is_unavailable() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    providers[0] = {
        **dict(providers[0]),  # type: ignore[arg-type]
        "response_status": "network_unavailable",
    }
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "provider_unavailable_pubmed"


def test_provider_runtime_fails_closed_when_rate_limited_or_cache_stale() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    crossref = dict(providers[1])  # type: ignore[arg-type]
    crossref["rate_limit_status"] = {
        "status": "rate_limited",
        "remaining": 0,
        "reset_at": "2026-05-03T09:15:00Z",
        "backoff": {"policy": "exponential", "retry_after_seconds": 900},
    }
    providers[1] = crossref
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "rate_limited_crossref"
    assert projection["rate_limit_status"]["crossref"]["limited"] is True
    assert projection["backoff"]["crossref"]["retry_after_seconds"] == 900

    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    semantic_scholar = dict(providers[2])  # type: ignore[arg-type]
    semantic_scholar["cache_freshness"] = {
        "status": "stale",
        "checked_at": "2026-05-03T08:05:00Z",
        "expires_at": "2026-05-02T08:05:00Z",
    }
    providers[2] = semantic_scholar
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "stale_cache_semantic_scholar"
    assert projection["cache_freshness"]["semantic_scholar"]["stale"] is True


def test_provider_runtime_fails_closed_when_provider_response_ledger_is_missing() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    pubmed = dict(providers[0])  # type: ignore[arg-type]
    pubmed["provider_response_ledger_refs"] = []
    providers[0] = pubmed
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_provider_response_ledger_pubmed"


def test_provider_runtime_requires_provider_refs_and_screening_reasons() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    providers[0] = {
        **dict(providers[0]),  # type: ignore[arg-type]
        "source_refs": [],
    }
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_provider_source_refs_pubmed"

    payload = _complete_provider_payload()
    payload["screening_decisions"] = [
        {"ref": "pmid:anchor-1", "decision": "include", "reason": ""},
    ]

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_screening_decision_reason"


def test_provider_runtime_fails_closed_when_literature_category_or_rationale_is_missing() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    crossref = dict(providers[1])  # type: ignore[arg-type]
    crossref["items"] = [
        {
            "ref": "doi:10.1000/systematic-review",
            "category": "systematic_reviews",
            "title": "Systematic review of pituitary prediction models",
            "citation_ledger_ref": "paper/evidence_ledger.json#systematic-review",
        }
    ]
    providers[1] = crossref
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_guideline_refs"
    assert projection["diagnostics"] == [
        {
            "reason_code": "missing_guideline_refs",
            "severity": "blocking",
            "category": "literature_intelligence_readiness",
        }
    ]

    payload = _complete_provider_payload()
    payload["why_worth_doing"] = ""

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_study_rationale"
    assert projection["diagnostics"] == [
        {
            "reason_code": "missing_study_rationale",
            "severity": "blocking",
            "category": "literature_intelligence_readiness",
        }
    ]

    payload = _complete_provider_payload()
    payload["search_strategy"] = {
        "query": "Pituitary neuroendocrine tumor invasive architecture",
        "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
    }

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_keyword_terms"
    assert projection["diagnostics"] == [
        {
            "reason_code": "missing_keyword_terms",
            "severity": "blocking",
            "category": "literature_intelligence_readiness",
        }
    ]


def test_provider_health_read_model_projects_scheduled_checks_without_authority() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )

    projection = provider_runtime.build_literature_provider_runtime_projection(
        _complete_provider_payload()
    )

    provider_health = projection["provider_health"]
    assert provider_health["contract"] == "scheduled_provider_health_read_model"
    assert provider_health["status"] == "ready"
    assert provider_health["diagnostics"] == []
    assert provider_health["checks"] == [
        "credential_status",
        "rate_limit_backoff",
        "cache_age",
        "query_fingerprint_drift",
        "provider_response_ledger_completeness",
        "citation_ledger_completeness",
        "screening_reason_completeness",
    ]
    assert provider_health["credential_status"] == projection["credential_status"]
    assert provider_health["rate_limit_status"] == projection["rate_limit_status"]
    assert provider_health["backoff"] == projection["backoff"]
    assert provider_health["cache_freshness"] == projection["cache_freshness"]
    assert provider_health["cache_age"]["pubmed"] == {
        "retrieved_at": "2026-05-03T08:00:00Z",
        "checked_at": "2026-05-03T08:05:00Z",
        "expires_at": "2026-05-04T08:05:00Z",
        "status": "fresh",
        "stale": False,
    }
    assert provider_health["provider_response_ledger"]["complete"] is True
    assert provider_health["citation_ledger"]["complete"] is True
    assert provider_health["screening_reasons"]["complete"] is True
    assert provider_health["query_fingerprint_drift"] == {
        "status": "stable",
        "expected_query_fingerprint": "",
        "actual_query_fingerprint": projection["query_fingerprint"],
        "expected_provider_query_fingerprints": {},
        "actual_provider_query_fingerprints": projection["provider_operations"][
            "provider_query_fingerprints"
        ],
        "drifted_providers": [],
    }
    assert provider_health["authority_contract"] == {
        "authority": "provider_health_read_model_only",
        "read_model_only": True,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }
    assert provider_health["health_can_authorize_quality"] is False
    assert provider_health["health_can_authorize_submission"] is False
    assert provider_health["health_can_authorize_finalize"] is False


def test_provider_health_fails_closed_for_query_fingerprint_drift() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    baseline = provider_runtime.build_literature_provider_runtime_projection(
        _complete_provider_payload()
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    pubmed = dict(providers[0])  # type: ignore[arg-type]
    pubmed["query"] = "changed pituitary query"
    providers[0] = pubmed
    payload["providers"] = providers
    payload["expected_query_fingerprint"] = baseline["query_fingerprint"]
    payload["expected_provider_query_fingerprints"] = baseline["provider_operations"][
        "provider_query_fingerprints"
    ]

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "query_fingerprint_drift_pubmed"
    provider_health = projection["provider_health"]
    assert provider_health["status"] == "blocked"
    assert provider_health["query_fingerprint_drift"]["status"] == "drifted"
    assert provider_health["query_fingerprint_drift"]["drifted_providers"] == ["pubmed"]
    assert provider_health["diagnostics"][0] == {
        "reason_code": "query_fingerprint_drift_pubmed",
        "severity": "blocking",
        "provider_name": "pubmed",
        "category": "query_fingerprint_drift",
    }


def test_provider_health_reports_stale_citation_and_missing_screening_reason_diagnostics() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    payload["citation_freshness"] = {
        "status": "stale",
        "stale_refs": ["paper/evidence_ledger.json#anchor-1"],
        "checked_at": "2026-05-04T00:00:00Z",
    }
    payload["screening_decisions"] = [
        {"ref": "pmid:anchor-1", "decision": "include", "reason": ""},
    ]

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "stale_citation_ledger_refs"
    provider_health = projection["provider_health"]
    assert provider_health["citation_freshness"] == {
        "status": "stale",
        "stale": True,
        "checked_at": "2026-05-04T00:00:00Z",
        "stale_refs": ["paper/evidence_ledger.json#anchor-1"],
    }
    assert provider_health["screening_reasons"] == {
        "complete": False,
        "missing_refs": ["pmid:anchor-1"],
    }
    assert [item["reason_code"] for item in provider_health["diagnostics"]] == [
        "stale_citation_ledger_refs",
        "missing_screening_decision_reason",
    ]


def test_provider_health_fail_closed_for_partial_outage_and_ledger_gaps() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    crossref = dict(providers[1])  # type: ignore[arg-type]
    crossref["response_status"] = "partial_outage"
    crossref["provider_response_ledger_refs"] = []
    crossref["items"] = [
        {
            "ref": "doi:10.1000/systematic-review",
            "category": "systematic_reviews",
            "title": "Systematic review of pituitary prediction models",
        }
    ]
    providers[1] = crossref
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "provider_partial_outage_crossref"
    provider_health = projection["provider_health"]
    assert provider_health["status"] == "blocked"
    assert provider_health["provider_response_ledger"]["complete"] is False
    assert provider_health["provider_response_ledger"]["missing_providers"] == ["crossref"]
    assert provider_health["citation_ledger"]["complete"] is False
    assert provider_health["citation_ledger"]["missing_providers"] == ["crossref"]
    assert [item["reason_code"] for item in provider_health["diagnostics"]] == [
        "provider_partial_outage_crossref",
        "missing_provider_response_ledger_crossref",
        "missing_provider_citation_ledger_refs_crossref",
    ]

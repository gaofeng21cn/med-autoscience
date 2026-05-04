from __future__ import annotations

import importlib
from pathlib import Path


def _complete_provider_payload() -> dict[str, object]:
    return {
        "search_date": "2026-05-03",
        "search_strategy": {
            "query": "Pituitary neuroendocrine tumor invasive architecture",
            "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
        },
        "providers": [
            {
                "provider_name": "pubmed",
                "query": "pituitary neuroendocrine tumor invasive architecture",
                "retrieved_at": "2026-05-03T08:00:00Z",
                "source_refs": ["pubmed:query-run-2026-05-03"],
                "response_status": "ok",
                "items": [
                    {
                        "ref": "pmid:anchor-1",
                        "category": "anchor_papers",
                        "title": "Invasive pituitary neuroendocrine tumor architecture",
                    }
                ],
            },
            {
                "provider_name": "crossref",
                "query": "TRIPOD AI pituitary endocrine prediction reporting",
                "retrieved_at": "2026-05-03T08:01:00Z",
                "source_refs": ["crossref:query-run-2026-05-03"],
                "response_status": "ok",
                "items": [
                    {
                        "ref": "doi:10.1000/systematic-review",
                        "category": "systematic_reviews",
                        "title": "Systematic review of pituitary prediction models",
                    },
                    {
                        "ref": "guideline:TRIPOD+AI",
                        "category": "guidelines",
                        "title": "TRIPOD+AI reporting guideline",
                    },
                ],
            },
            {
                "provider_name": "semantic_scholar",
                "query": "clinical endocrinology pituitary invasive biomarker",
                "retrieved_at": "2026-05-03T08:02:00Z",
                "source_refs": ["semantic-scholar:query-run-2026-05-03"],
                "response_status": "ok",
                "items": [
                    {
                        "ref": "journal-neighbor:clinical-endocrinology-2025",
                        "category": "journal_neighbor_refs",
                        "title": "Neighboring clinical endocrinology paper",
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
        },
        "search_date": "2026-05-03",
        "provider_payloads": [
            {
                "provider": "pubmed",
                "query": "pituitary neuroendocrine tumor invasive architecture",
                "retrieved_at": "2026-05-03T08:00:00Z",
                "response_status": "ok",
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
                "request_id": "semantic-scholar-run-2026-05-03",
                "results": [
                    {
                        "paperId": "SEMANTIC123",
                        "title": "Neighboring clinical endocrinology paper",
                        "category": "journal_neighbor_refs",
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
    assert projection["citation_ledger_refs"] == ["paper/evidence_ledger.json#anchor-1"]
    assert projection["screening_decisions"] == payload["screening_decisions"]
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
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


def test_provider_runtime_fails_closed_when_provider_is_unavailable() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    providers[0] = {
        "provider_name": "pubmed",
        "query": "pituitary",
        "retrieved_at": "2026-05-03T08:00:00Z",
        "source_refs": ["pubmed:query-run"],
        "response_status": "network_unavailable",
    }
    payload["providers"] = providers

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "provider_unavailable_pubmed"


def test_provider_runtime_requires_provider_refs_and_screening_reasons() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    payload = _complete_provider_payload()
    providers = list(payload["providers"])  # type: ignore[arg-type]
    providers[0] = {
        "provider_name": "pubmed",
        "query": "pituitary",
        "retrieved_at": "2026-05-03T08:00:00Z",
        "source_refs": [],
        "response_status": "ok",
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

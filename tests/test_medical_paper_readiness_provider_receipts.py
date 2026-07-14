from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.medical_paper_readiness_payload_authoring import (
    author_operator_payload,
    provider_receipts_from_host_payloads,
)
from med_autoscience.controllers.medical_paper_readiness_payload_authoring.provider_adapters import (
    payload_from_provider_adapters,
)


GENERATED_AT = "2026-07-14T00:00:00+00:00"
RECEIPT_REF = "opl://connect/references/verify/readiness-literature"


def _write_study(study_root: Path) -> None:
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(
        """\
study_id: study-001
title: Diabetes mortality prediction
paper_urls:
  - https://pubmed.ncbi.nlm.nih.gov/100/
  - https://pubmed.ncbi.nlm.nih.gov/101/
  - https://pubmed.ncbi.nlm.nih.gov/102/
""",
        encoding="utf-8",
    )


def _evidence() -> list[dict[str, object]]:
    return [
        {
            "reference_id": "pmid:100",
            "provider": "pubmed",
            "lookup_status": "found",
            "status": "matched",
            "match_status": "identifier_matched",
            "matched_identifiers": {"pmid": "100"},
            "metadata": {"title": "Anchor cohort paper", "year": 2024},
        },
        {
            "reference_id": "pmid:101",
            "provider": "pubmed",
            "lookup_status": "found",
            "status": "matched",
            "match_status": "identifier_matched",
            "matched_identifiers": {"pmid": "101"},
            "provider_identifiers": {"pmid": "101", "doi": "10.1000/guideline"},
            "metadata": {"title": "TRIPOD guideline statement", "year": 2023},
        },
        {
            "reference_id": "pmid:102",
            "provider": "pubmed",
            "lookup_status": "found",
            "status": "matched",
            "match_status": "identifier_matched",
            "matched_identifiers": {"pmid": "102"},
            "provider_identifiers": {"pmid": "102", "doi": "10.1000/systematic"},
            "metadata": {"title": "Systematic review and meta-analysis", "year": 2025},
        },
        {
            "reference_id": "doi:10.1000/guideline",
            "provider": "crossref",
            "lookup_status": "found",
            "status": "matched",
            "match_status": "identifier_matched",
            "matched_identifiers": {"doi": "10.1000/guideline"},
            "metadata": {"title": "TRIPOD guideline statement", "year": 2023},
        },
        {
            "reference_id": "doi:10.1000/systematic",
            "provider": "crossref",
            "lookup_status": "found",
            "status": "matched",
            "match_status": "identifier_matched",
            "matched_identifiers": {"doi": "10.1000/systematic"},
            "metadata": {"title": "Systematic review and meta-analysis", "year": 2025},
        },
        {
            "reference_id": "doi:10.1000/systematic",
            "provider": "semantic_scholar",
            "provider_id": "semantic-scholar",
            "lookup_status": "found",
            "status": "matched",
            "match_status": "identifier_matched",
            "matched_identifiers": {"doi": "10.1000/systematic"},
            "provider_identifiers": {
                "doi": "10.1000/systematic",
                "semantic_scholar": "S2-SYSTEMATIC",
            },
            "metadata": {"title": "Systematic review and meta-analysis", "year": 2025},
        },
    ]


def _payload(study_root: Path, evidence: list[dict[str, object]]) -> dict[str, object]:
    return payload_from_provider_adapters(
        study_root=study_root,
        generated_at=GENERATED_AT,
        surface_key="literature_scout",
        provider_receipts=({"receipt_ref": RECEIPT_REF, "provider_evidence": evidence},),
        source="test",
        surface="medical_paper_readiness_operator_payload",
        schema_version=1,
    )


def test_readiness_authoring_consumes_complete_opl_connect_receipt(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    _write_study(study_root)

    payload = _payload(study_root, _evidence())

    assert payload["source_basis"] == "study_contract_and_opl_connect_provider_receipts"
    providers = {provider["provider"]: provider for provider in payload["provider_payloads"]}
    assert set(providers) == {"pubmed", "crossref", "semantic_scholar"}
    assert all(provider["provider_response_ledger_refs"] == [RECEIPT_REF] for provider in providers.values())
    assert all(provider["credential_status"]["credential_ref"] == RECEIPT_REF for provider in providers.values())
    assert all("policy" not in provider["rate_limit_status"]["backoff"] for provider in providers.values())
    assert all("expires_at" not in provider["cache_freshness"] for provider in providers.values())
    assert payload["quality_claim_authorized"] is False


def test_readiness_authoring_does_not_promote_legacy_local_provider_projection_without_receipt(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_study(study_root)
    legacy_path = (
        study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json"
    )
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "status": "ready",
                "provider_provenance": [
                    {"provider_name": "pubmed", "source_refs": ["legacy:pubmed"]},
                    {"provider_name": "crossref", "source_refs": ["legacy:crossref"]},
                    {
                        "provider_name": "semantic_scholar",
                        "source_refs": ["legacy:semantic-scholar"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = author_operator_payload(
        study_root=study_root,
        surface_key="literature_provider_runtime",
        generated_at=GENERATED_AT,
    )

    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "opl_connect_reference_receipt_required_pubmed"
    assert payload["provider_resolution"]["status"] == "request_only"
    assert payload["provider_resolution"]["provider_resolution_request"]["providers"] == [
        "pubmed"
    ]


def test_readiness_authoring_returns_crossref_resolution_for_partial_receipt(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    _write_study(study_root)

    payload = _payload(study_root, _evidence()[:3])

    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "provider_adapter_fetch_failed_crossref"
    assert payload["provider_resolution"]["status"] == "missing_evidence"
    assert payload["provider_resolution"]["provider_resolution_request"]["providers"] == ["crossref"]


def test_readiness_authoring_returns_semantic_resolution_for_partial_receipt(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    _write_study(study_root)

    payload = _payload(study_root, _evidence()[:5])

    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "provider_adapter_fetch_failed_semantic_scholar"
    assert payload["provider_resolution"]["status"] == "missing_evidence"
    assert payload["provider_resolution"]["provider_resolution_request"]["providers"] == [
        "semantic-scholar"
    ]


def test_hosted_readiness_payloads_extract_and_deduplicate_connect_receipts() -> None:
    receipt = {
        "receipt_ref": RECEIPT_REF,
        "provider_evidence": _evidence(),
    }
    nested_receipt = {
        "provider_receipt_ref": "opl://connect/references/verify/nested",
        "opl_connect_reference_verification": {
            "provider_evidence": _evidence()[:1],
        },
    }

    receipts = provider_receipts_from_host_payloads(
        {
            "prompt_contract": {
                "provider_receipts": (receipt,),
            },
            "handoff_packet": {
                "provider_receipts": [receipt],
            },
        },
        nested_receipt,
    )

    assert receipts == [
        receipt,
        {
            "receipt_ref": "opl://connect/references/verify/nested",
            "opl_connect_reference_verification": nested_receipt[
                "opl_connect_reference_verification"
            ],
        },
    ]

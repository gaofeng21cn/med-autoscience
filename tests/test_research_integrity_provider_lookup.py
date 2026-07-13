from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.research_integrity import build_reference_provider_lookup_bundle
from med_autoscience.research_integrity.provider_lookup import PROVIDER_LOOKUP_MODE


class FakeOplConnectRunner:
    def __init__(self, evidence: list[dict[str, Any]]) -> None:
        self.evidence = evidence
        self.calls: list[tuple[list[str], float]] = []
        self.references: list[dict[str, Any]] = []

    def __call__(
        self,
        args: list[str],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls.append((list(args), timeout_seconds))
        references_path = Path(args[args.index("--references-file") + 1])
        self.references = json.loads(references_path.read_text(encoding="utf-8"))["references"]
        return {
            "version": "g2",
            "opl_connect_reference_verification": {
                "surface_kind": "opl_connect_reference_verification_readonly",
                "status": "completed",
                "provider_evidence": self.evidence,
            },
        }


def _matched_crossref(reference_id: str = "smith2024") -> dict[str, Any]:
    return {
        "reference_id": reference_id,
        "provider": "crossref",
        "provider_id": "crossref",
        "lookup_status": "found",
        "status": "matched",
        "match_status": "identifier_matched",
        "matched_identifiers": {"doi": "10.1000/abc"},
        "metadata": {
            "title": "A Mature Classifier Paper",
            "year": "2024",
            "journal": "Medical AI",
        },
        "retraction_or_update_flags": {},
        "receipt_ref": "opl://connect/references/verify/crossref-smith2024",
    }


def test_provider_lookup_consumes_canonical_opl_connect_receipt() -> None:
    runner = FakeOplConnectRunner([_matched_crossref()])

    bundle = build_reference_provider_lookup_bundle(
        references=[
            {
                "id": "smith2024",
                "doi": "10.1000/ABC",
                "title": "A Mature Classifier Paper",
            }
        ],
        provider_config={"providers": ["crossref"], "max_retries": 2},
        opl_runner=runner,
    )

    args, timeout = runner.calls[0]
    assert args[:3] == ["connect", "references", "verify"]
    assert args[args.index("--providers") + 1] == "crossref"
    assert args[args.index("--max-retries") + 1] == "2"
    assert args[-1] == "--json"
    assert timeout == 30.0
    assert runner.references[0]["id"] == "smith2024"
    assert bundle["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert bundle["provider_summary"] == {"found": 1, "not_found": 0, "error": 0}
    assert bundle["references"][0]["attestation"]["status"] == "verified"
    assert bundle["status"] == "clear"
    assert bundle["authority_boundary"]["provider_lookup_owner"] == "OPL Connect"
    assert bundle["authority_boundary"]["mas_can_call_external_provider"] is False


def test_provider_lookup_preserves_domain_claim_support_gate() -> None:
    runner = FakeOplConnectRunner([_matched_crossref("clinical2025")])

    bundle = build_reference_provider_lookup_bundle(
        references={
            "id": "clinical2025",
            "doi": "10.1000/abc",
            "title": "A Mature Classifier Paper",
        },
        provider_config={"providers": ["crossref"]},
        opl_runner=runner,
        claim_spans=[
            {
                "claim_id": "C1",
                "citation_refs": [{"ref": "ref:clinical2025"}],
                "evidence_refs": ["analysis/results.json#/C1"],
                "support_grade": "direct_support",
            }
        ],
    )

    matrix = bundle["gate_input_bundle"]["surfaces"]["claim_citation_support_matrix_v2"]
    assert matrix["claims"][0]["support_grade"] == "direct_support"


def test_provider_lookup_keeps_connector_errors_as_non_authorizing_review_evidence() -> None:
    runner = FakeOplConnectRunner(
        [
            {
                "reference_id": "unresolved",
                "provider": "crossref",
                "provider_id": "crossref",
                "lookup_status": "error",
                "status": "deferred",
                "matched_identifiers": {},
                "metadata": {},
                "retraction_or_update_flags": {},
                "error": {"code": "provider_unavailable"},
            }
        ]
    )

    bundle = build_reference_provider_lookup_bundle(
        references={"id": "unresolved", "title": "Unresolved Citation"},
        provider_config={"providers": ["crossref"]},
        opl_runner=runner,
    )

    assert bundle["status"] == "needs_review"
    assert bundle["references"][0]["attestation"]["status"] == "unresolved"
    assert bundle["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert bundle["authority_boundary"]["can_materialize_provider_receipt"] is False


def test_provider_lookup_contract_declares_opl_connect_transport_boundary() -> None:
    contract = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/research-integrity-layer.json").read_text()
    )

    boundary = contract["provider_lookup_boundary"]
    target = contract["implementation_contract"]["provider_lookup_target"]
    assert boundary["provider_lookup_mode"] == PROVIDER_LOOKUP_MODE
    assert boundary["provider_lookup_owner"] == "OPL Connect"
    assert boundary["mas_can_call_external_provider"] is False
    assert target["owner"] == "OPL Connect"
    assert target["mas_role"] == "consume_provider_receipts_and_apply_medical_gate_judgment"


def test_provider_lookup_rejects_unsupported_provider() -> None:
    with pytest.raises(ValueError, match="unsupported provider lookup provider"):
        build_reference_provider_lookup_bundle(
            references={"id": "bad"},
            provider_config={"providers": ["google_scholar"]},
            opl_runner=FakeOplConnectRunner([]),
        )

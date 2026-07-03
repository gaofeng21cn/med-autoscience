from __future__ import annotations

from med_autoscience.domain_entry_contract import build_domain_entry_contract


def test_domain_entry_contract_exposes_research_integrity_stage_hook_trigger() -> None:
    contracts = {item["command"]: item for item in build_domain_entry_contract()["command_contracts"]}
    hook = contracts["research-integrity-review-publication-gate-stage-hook"]

    assert hook["required_fields"] == []
    assert hook["optional_fields"] == [
        "payload",
        "stage_id",
        "stage_event",
        "stage_hook_ref",
        "reference",
        "references",
        "provider_evidence",
        "provider_receipts",
        "source_refs",
        "reference_manager_ref",
        "manuscript_ref",
        "claim_spans",
        "claim",
        "claims",
        "citation_refs",
        "evidence_refs",
        "reference_attestation_refs",
        "manuscript_sections",
        "manuscript",
        "numeric_facts",
        "display_facts",
        "reference_attestations",
        "display_to_claim_map",
        "reporting_guideline_expectations",
    ]

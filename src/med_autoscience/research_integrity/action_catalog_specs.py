from __future__ import annotations

from collections.abc import Sequence
from typing import Any


RESEARCH_INTEGRITY_MCP_INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "research_integrity_gate_input": {
        "type": "object",
        "properties": {
            "payload": {"type": "object"},
            "reference_checks": {"type": "array"},
            "reference": {"type": "object"},
            "references": {"type": "array"},
            "claim_spans": {"type": "array"},
            "claim": {"type": "object"},
            "claims": {"type": "array"},
            "citation_refs": {"type": "array"},
            "evidence_refs": {"type": "array"},
            "reference_attestation_refs": {"type": "array"},
            "manuscript_sections": {"type": "object"},
            "manuscript": {"type": "object"},
            "numeric_facts": {"type": "array"},
            "display_facts": {"type": "array"},
            "provider_evidence": {"type": "array"},
            "reference_attestations": {"type": "array"},
            "display_to_claim_map": {"type": "object"},
            "reporting_guideline_expectations": {"type": "object"},
        },
    },
    "research_integrity_reference_verification": {
        "type": "object",
        "properties": {
            "payload": {"type": "object"},
            "reference": {"type": "object"},
            "references": {"type": "array"},
            "provider_evidence": {"type": "array"},
            "provider_receipts": {"type": "array"},
            "source_refs": {"type": "array"},
            "reference_manager_ref": {"type": "string"},
            "manuscript_ref": {"type": "string"},
        },
    },
    "research_integrity_review_publication_gate_stage_hook": {
        "type": "object",
        "properties": {
            "payload": {"type": "object"},
            "stage_id": {"type": "string"},
            "stage_event": {"type": "string"},
            "stage_hook_ref": {"type": "string"},
            "reference": {"type": "object"},
            "references": {"type": "array"},
            "provider_evidence": {"type": "array"},
            "provider_receipts": {"type": "array"},
            "source_refs": {"type": "array"},
            "reference_manager_ref": {"type": "string"},
            "manuscript_ref": {"type": "string"},
            "claim_spans": {"type": "array"},
            "claim": {"type": "object"},
            "claims": {"type": "array"},
            "citation_refs": {"type": "array"},
            "evidence_refs": {"type": "array"},
            "reference_attestation_refs": {"type": "array"},
            "manuscript_sections": {"type": "object"},
            "manuscript": {"type": "object"},
            "numeric_facts": {"type": "array"},
            "display_facts": {"type": "array"},
            "reference_attestations": {"type": "array"},
            "display_to_claim_map": {"type": "object"},
            "reporting_guideline_expectations": {"type": "object"},
        },
    },
}


def research_integrity_action_specs(
    *,
    mas_truth_owner: str,
    authoritative_truth_refs: Sequence[str],
) -> tuple[dict[str, Any], ...]:
    return (
        {
            "action_id": "research_integrity_gate_input",
            "title": "Build Research Integrity gate input",
            "summary": (
                "Build a structured Research Integrity gate input bundle from supplied reference, "
                "claim, manuscript, and provider-evidence payloads. It only produces evidence, "
                "gate input, and blocker candidates; it does not write publication authority, "
                "owner receipts, typed blockers, human gates, runtime queues, provider attempts, "
                "publication_eval, controller_decisions, or current_package."
            ),
            "effect": "read_only",
            "command": "MedAutoScienceDomainEntry.dispatch(research-integrity-gate-input payload)",
            "surface_kind": "research_integrity_gate_input_bundle",
            "workspace_locator_fields": list(
                RESEARCH_INTEGRITY_MCP_INPUT_SCHEMAS["research_integrity_gate_input"]["properties"]
            ),
            "mcp_public_runtime": False,
            "authority_boundary": _authority_boundary(
                mas_truth_owner=mas_truth_owner,
                surface_authority="research_integrity_gate_input_only",
                authoritative_truth_refs=authoritative_truth_refs,
            ),
        },
        {
            "action_id": "research_integrity_reference_verification",
            "title": "Build Research Integrity reference verification payload",
            "summary": (
                "Trigger the complete-reference verification lane for supplied manuscript or reference "
                "manager refs. It only returns a Research Integrity gate input or evidence bundle; it "
                "does not write publication authority, owner receipts, typed blockers, human gates, "
                "runtime queues, provider attempts, publication_eval, controller_decisions, or current_package."
            ),
            "effect": "read_only",
            "command": "MedAutoScienceDomainEntry.dispatch(research-integrity-reference-verification payload)",
            "surface_kind": "research_integrity_reference_verification_gate_input_bundle",
            "workspace_locator_fields": list(
                RESEARCH_INTEGRITY_MCP_INPUT_SCHEMAS["research_integrity_reference_verification"][
                    "properties"
                ]
            ),
            "mcp_public_runtime": False,
            "authority_boundary": _authority_boundary(
                mas_truth_owner=mas_truth_owner,
                surface_authority="research_integrity_reference_verification_gate_input_only",
                authoritative_truth_refs=authoritative_truth_refs,
            ),
        },
        {
            "action_id": "research_integrity_review_publication_gate_stage_hook",
            "title": "Trigger Research Integrity review/publication gate hook",
            "summary": (
                "Mandatory Review/Publication Gate stage-hook input: when a reference list, "
                "manuscript closeout, review gate, or publication gate is entered, trigger "
                "research-integrity-reference-verification and return the gate input bundle, "
                "including manuscript consistency / meta review. It cannot write publication "
                "authority, owner receipts, typed blockers, human gates, runtime queues, "
                "provider attempts, publication_eval, controller_decisions, or current_package."
            ),
            "effect": "read_only",
            "command": (
                "MedAutoScienceDomainEntry.dispatch("
                "research-integrity-review-publication-gate-stage-hook payload)"
            ),
            "surface_kind": "research_integrity_review_publication_gate_stage_hook",
            "workspace_locator_fields": list(
                RESEARCH_INTEGRITY_MCP_INPUT_SCHEMAS[
                    "research_integrity_review_publication_gate_stage_hook"
                ]["properties"]
            ),
            "mcp_public_runtime": False,
            "authority_boundary": {
                **_authority_boundary(
                    mas_truth_owner=mas_truth_owner,
                    surface_authority="mandatory_stage_hook_gate_input_only",
                    authoritative_truth_refs=authoritative_truth_refs,
                ),
                "stage_hook_consumers": ["review_gate", "publication_gate"],
                "triggered_action": "research-integrity-reference-verification",
                "can_request_provider_lookup": True,
            },
        },
    )


def _authority_boundary(
    *,
    mas_truth_owner: str,
    surface_authority: str,
    authoritative_truth_refs: Sequence[str],
) -> dict[str, Any]:
    return {
        "domain_truth_owner": mas_truth_owner,
        "helper_owner": mas_truth_owner,
        "helper_write_policy": "no_domain_truth_writes",
        "surface_authority": surface_authority,
        "outputs_are_gate_inputs": True,
        "can_write_mas_study_truth": False,
        "can_write_publication_eval_latest": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_mutate_current_package": False,
        "can_write_current_package": False,
        "can_sign_owner_receipt": False,
        "can_write_owner_receipt": False,
        "can_materialize_typed_blocker": False,
        "can_write_typed_blocker": False,
        "can_materialize_human_gate": False,
        "can_write_runtime_queue_or_provider_attempt": False,
        "can_authorize_publication_quality": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "authoritative_truth_refs": list(authoritative_truth_refs),
    }


__all__ = [
    "RESEARCH_INTEGRITY_MCP_INPUT_SCHEMAS",
    "research_integrity_action_specs",
]

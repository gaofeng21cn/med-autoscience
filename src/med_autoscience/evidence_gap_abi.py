from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.evidence_gap_decision import (
    GAP_CLASSES,
    HARD_GATE_CLASSES,
    NONBLOCKING_GAP_CLASSES,
    READINESS_FORBIDDEN_CLAIMS,
    SCHEMA_VERSION,
    materialize_typed_blocker_if_required,
    merge_gap_decisions,
    normalize_decision,
    summarize_gap_decisions,
)


ABI_SURFACE_KIND = "mas_evidence_gap_consumption_abi"
ABI_VERSION = "evidence-gap-consumption-abi.v1"
ABI_CONTRACT_REF = "contracts/evidence-gap-consumption-abi.json"
DECISION_POLICY_REF = "contracts/evidence-gap-decision-policy.json"
DECISION_SCHEMA_REF = "contracts/schemas/evidence-gap-decision.schema.json"
MISSING_EVIDENCE_POLICY = "classify_with_evidence_gap_decision_then_progress_first"

ABI_COMPONENTS = (
    "EvidenceCondition",
    "EvidenceBudget",
    "HardGateRegistry",
    "SoftGapLedger",
    "AssumptionLedger",
    "WorkbenchGapView",
)

CONSUMER_REFS = {
    "study_progress": "/study_progress/evidence_gap_decisions",
    "domain_diagnostic_report": "/domain_diagnostic_report/evidence_gap_decisions",
    "domain_action_materializer": "/ai_route_contexts/*/evidence_gap_decisions",
    "opl_stage_control_plane": "/product_entry_manifest/evidence_gap_consumption_abi",
    "workbench": "/study_workbench/evidence_gap_view",
    "mcp_action_catalog": "/mcp_tools/*/metadata/evidence_gap_consumption_abi",
}


def build_evidence_gap_consumption_abi() -> dict[str, Any]:
    return {
        "surface_kind": ABI_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "version": ABI_VERSION,
        "owner": "MedAutoScience",
        "state": "active_contract",
        "decision_policy_ref": DECISION_POLICY_REF,
        "decision_schema_ref": DECISION_SCHEMA_REF,
        "machine_boundary": (
            "This ABI projects EvidenceGapDecision for OPL, Workbench, MCP, action-catalog, "
            "study-progress, domain diagnostic, and action materializer consumers. It does not create a second "
            "truth source and does not authorize paper progress, provider running, publication "
            "readiness, submission readiness, live runtime readiness, or production readiness."
        ),
        "missing_evidence_policy": MISSING_EVIDENCE_POLICY,
        "components": {
            "EvidenceCondition": {
                "purpose": "Per-gap condition projected from mas_evidence_gap_decision.",
                "input_surface_kind": "mas_evidence_gap_decision",
                "fields": [
                    "gap_class",
                    "severity",
                    "current_action_can_continue",
                    "typed_blocker_eligibility",
                    "claim_boundary",
                    "identity",
                    "missing_ref_family",
                    "evidence_refs",
                    "diagnostic_refs",
                ],
            },
            "EvidenceBudget": {
                "purpose": "Progress-first execution budget for incomplete evidence.",
                "hard_gate_classes": sorted(HARD_GATE_CLASSES),
                "nonblocking_gap_classes": sorted(NONBLOCKING_GAP_CLASSES),
                "default_policy": "continue_current_action_for_nonblocking_gap_classes",
                "forbidden_claims": list(READINESS_FORBIDDEN_CLAIMS),
            },
            "HardGateRegistry": {
                "purpose": "Only authority_gate and human_gate may materialize countable typed blockers.",
                "typed_blocker_countable_gap_classes": sorted(HARD_GATE_CLASSES),
                "typed_blocker_surface_kind": "mas_evidence_gap_typed_blocker",
                "forbidden_gap_classes_for_typed_blocker_count": sorted(NONBLOCKING_GAP_CLASSES),
            },
            "SoftGapLedger": {
                "purpose": "Nonblocking quality, observability, and tail-evidence accounting.",
                "ledger_fields": ["soft_gap_ledger", "observability_backlog", "evidence_tail_ledger"],
                "continues_current_action": True,
                "does_not_clear_claim_boundary": True,
            },
            "AssumptionLedger": {
                "purpose": "Explicit assumptions for safe non-critical missing refs.",
                "ledger_field": "assumption_ledger",
                "continues_current_action": True,
                "does_not_clear_claim_boundary": True,
            },
            "WorkbenchGapView": {
                "purpose": "Read-only Workbench summary split by hard gates, soft gaps, assumptions, and evidence tails.",
                "field": "evidence_gap_view",
                "projection_only": True,
                "can_execute": False,
                "can_write_domain_truth": False,
            },
        },
        "consumer_refs": dict(CONSUMER_REFS),
        "legacy_policy_replacement": {
            "retired_policy": "missing evidence -> typed_blocker",
            "replacement_policy": MISSING_EVIDENCE_POLICY,
            "typed_blocker_allowed_only_when": sorted(HARD_GATE_CLASSES),
            "nonblocking_gap_classes": sorted(NONBLOCKING_GAP_CLASSES),
        },
    }


def evidence_gap_abi_ref() -> dict[str, Any]:
    return {
        "surface_kind": ABI_SURFACE_KIND,
        "version": ABI_VERSION,
        "contract_ref": ABI_CONTRACT_REF,
        "decision_policy_ref": DECISION_POLICY_REF,
        "decision_schema_ref": DECISION_SCHEMA_REF,
        "missing_evidence_policy": MISSING_EVIDENCE_POLICY,
        "component_refs": list(ABI_COMPONENTS),
        "projection_only": True,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
    }


def build_workbench_gap_view(
    *decision_groups: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
) -> dict[str, Any]:
    decisions = merge_gap_decisions(*decision_groups)
    summary = summarize_gap_decisions(decisions)
    grouped: dict[str, list[dict[str, Any]]] = {gap_class: [] for gap_class in GAP_CLASSES}
    typed_blockers: list[dict[str, Any]] = []
    repair_owners: Counter[str] = Counter()
    for decision in decisions:
        normalized = normalize_decision(decision)
        grouped.setdefault(normalized.gap_class, []).append(normalized.to_payload())
        repair_owners[normalized.repair_owner] += 1
        blocker = materialize_typed_blocker_if_required(normalized)
        if blocker is not None:
            typed_blockers.append(blocker)
    return {
        "surface_kind": "mas_workbench_gap_view",
        "schema_version": SCHEMA_VERSION,
        "abi_ref": evidence_gap_abi_ref(),
        "summary": summary,
        "hard_gate_registry": {
            "surface_kind": "HardGateRegistry",
            "typed_blocker_count": len(typed_blockers),
            "typed_blockers": typed_blockers,
            "hard_gate_decisions": grouped.get("authority_gate", []) + grouped.get("human_gate", []),
        },
        "soft_gap_ledger": _ledger_view(
            "SoftGapLedger",
            grouped.get("soft_quality_gap", [])
            + grouped.get("observability_backlog", [])
            + grouped.get("evidence_tail", []),
        ),
        "assumption_ledger": _ledger_view("AssumptionLedger", grouped.get("proceed_with_assumption", [])),
        "evidence_budget": {
            "surface_kind": "EvidenceBudget",
            "current_action_can_continue": summary["current_action_can_continue"],
            "allowed_next_actions": list(summary["allowed_next_actions"]),
            "forbidden_claims": list(summary["forbidden_claims"]),
            "claim_boundary": dict(summary["claim_boundary"]),
        },
        "repair_owners": dict(sorted(repair_owners.items())),
        "projection_boundary": {
            "projection_only": True,
            "can_execute": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
    }


def _ledger_view(surface_kind: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "surface_kind": surface_kind,
        "count": len(decisions),
        "decisions": decisions,
        "current_action_can_continue": True,
        "does_not_clear_claim_boundary": True,
    }


__all__ = [
    "ABI_COMPONENTS",
    "ABI_CONTRACT_REF",
    "ABI_SURFACE_KIND",
    "ABI_VERSION",
    "CONSUMER_REFS",
    "DECISION_POLICY_REF",
    "DECISION_SCHEMA_REF",
    "MISSING_EVIDENCE_POLICY",
    "build_evidence_gap_consumption_abi",
    "build_workbench_gap_view",
    "evidence_gap_abi_ref",
]

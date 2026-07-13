from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission.payload_helpers import (
    dedupe,
    mapping,
    text,
    text_items,
)


def paper_audit_pack(
    *,
    study_id: str,
    objective_id: str,
    objective_kind: str,
    artifact_refs: list[str],
    source_refs: list[dict[str, str]],
    readback: Mapping[str, Any],
    current_blocker: Mapping[str, Any],
    platform_diagnostics: Mapping[str, Any],
    legacy_import: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    legacy = mapping(legacy_import)
    family_refs = {
        "analysis_rationale_log": audit_refs(
            family="analysis_rationale_log",
            refs=[
                f"mission://{study_id}/objective/{objective_id}",
                f"mission://{study_id}/readback/{text(readback.get('surface_kind')) or 'paper_mission_readback'}",
            ],
        ),
        "decision_trace": audit_refs(
            family="decision_trace",
            refs=dedupe(
                [
                    f"mission://{study_id}/decision/{objective_kind}",
                    text(current_blocker.get("source_ref")) or "",
                    text(current_blocker.get("work_unit_id")) or "",
                ]
            ),
        ),
        "evidence_ledger_delta": audit_refs(
            family="evidence_ledger_delta",
            refs=dedupe(
                text_items(legacy.get("evidence_and_review_ledger_refs"))
                + [item["uri"] for item in source_refs]
            ),
        ),
        "review_ledger_delta": audit_refs(
            family="review_ledger_delta",
            refs=dedupe(
                text_items(legacy.get("legacy_owner_state_refs"))
                + [
                    f"mission://{study_id}/quality-audit/{objective_id}",
                    f"mission://{study_id}/authority-boundary/no-write",
                ]
            ),
        ),
        "revision_log_delta": audit_refs(
            family="revision_log_delta",
            refs=[
                f"mission://{study_id}/revision-log/{objective_id}",
                f"mission://{study_id}/paper-progress/no-write-import",
            ],
        ),
        "failed_path_ledger": audit_refs(
            family="failed_path_ledger",
            refs=dedupe(
                [
                    text(current_blocker.get("blocker_id")) or "",
                    text(current_blocker.get("status")) or "",
                    f"mission://{study_id}/failed-path/legacy-owner-callable-not-authority",
                ]
            ),
        ),
        "artifact_lineage": audit_refs(
            family="artifact_lineage",
            refs=dedupe(
                artifact_refs
                + text_items(legacy.get("current_artifact_refs"))
                + [f"mission://{study_id}/candidate/{objective_id}"]
            ),
        ),
        "reproducibility_refs": audit_refs(
            family="reproducibility_refs",
            refs=dedupe(
                text_items(legacy.get("opl_current_control_refs"))
                + [
                    text(platform_diagnostics.get("domain_diagnostic_scanned_at")) or "",
                    f"mission://{study_id}/runtime-diagnostics/read-only",
                ]
            ),
        ),
    }
    return {
        family: {
            "status": "candidate_ref_chain",
            "refs": refs,
        }
        for family, refs in family_refs.items()
    }


def audit_refs(*, family: str, refs: list[str]) -> list[dict[str, str]]:
    clean_refs = dedupe([ref for ref in refs if ref])
    if not clean_refs:
        clean_refs = [f"mission://audit-pack/{family}/missing"]
    return [
        {
            "ref_id": f"{family}::{index}",
            "ref_kind": ref_kind(ref),
            "uri": ref,
        }
        for index, ref in enumerate(clean_refs, start=1)
    ]


def source_ref_payloads(refs: list[str]) -> list[dict[str, str]]:
    payloads = [
        {
            "ref_id": f"source_ref::{index}",
            "ref_kind": ref_kind(ref),
            "uri": ref,
        }
        for index, ref in enumerate(refs, start=1)
    ]
    if payloads:
        return payloads
    return [
        {
            "ref_id": "source_ref::missing",
            "ref_kind": "missing_readback_ref",
            "uri": "mission://source-refs/missing",
        }
    ]


def authority_touchpoints(
    *,
    study_id: str,
    source_refs: list[dict[str, str]],
    platform_diagnostics: Mapping[str, Any],
) -> list[dict[str, str]]:
    touchpoints = [
        {
            "touchpoint_id": f"touchpoint::{study_id}::study-progress",
            "owner": "MedAutoScience",
            "surface": "study progress",
            "status": "read_only",
        },
        {
            "touchpoint_id": f"touchpoint::{study_id}::runtime-readback",
            "owner": "MedAutoScience",
            "surface": "runtime readback",
            "status": "read_only"
            if platform_diagnostics.get("runtime_readback_available")
            else "not_touched",
        },
        {
            "touchpoint_id": f"touchpoint::{study_id}::mas-authority-kernel",
            "owner": "MedAutoScience",
            "surface": "MAS Authority Kernel",
            "status": "not_touched",
        },
        {
            "touchpoint_id": f"touchpoint::{study_id}::opl-runtime",
            "owner": "one-person-lab",
            "surface": "OPL runtime/current-control",
            "status": "read_only"
            if platform_diagnostics.get("runtime_readback_available")
            else "not_touched",
        },
    ]
    for source_ref in source_refs:
        kind = source_ref["ref_kind"]
        if kind in {"publication_eval", "controller_decision", "owner_answer"}:
            touchpoints.append(
                {
                    "touchpoint_id": f"touchpoint::{study_id}::{kind}",
                    "owner": "MedAutoScience",
                    "surface": kind,
                    "status": "read_only",
                }
            )
    return touchpoints


def ref_kind(ref: str) -> str:
    if "publication_eval/latest.json" in ref:
        return "publication_eval"
    if "controller_decisions/latest.json" in ref:
        return "controller_decision"
    if "runtime_readback" in ref:
        return "runtime_readback"
    if "runtime_status_summary.json" in ref:
        return "runtime_status_summary"
    if "closeout" in ref or "owner_answer" in ref:
        return "owner_answer"
    if ref.startswith("supervisor-decision::"):
        return "supervisor_decision"
    if ref.startswith("provider_attempt_pending_count="):
        return "provider_attempt_readback"
    return "artifact_ref"

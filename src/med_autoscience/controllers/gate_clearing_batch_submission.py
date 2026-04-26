from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable


BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
BUNDLE_STAGE_GATE_BLOCKERS = frozenset(
    {
        "stale_study_delivery_mirror",
        "stale_submission_minimal_authority",
        "submission_surface_qc_failure_present",
        "submission_hardening_incomplete",
    }
)
SUBMISSION_MINIMAL_REPAIR_GATE_BLOCKERS = frozenset(
    {
        "stale_submission_minimal_authority",
        "submission_surface_qc_failure_present",
        "submission_hardening_incomplete",
    }
)
DIRECT_SUBMISSION_DELIVERY_SYNC_STALE_REASONS = frozenset(
    {
        "delivery_projection_missing",
        "delivery_manifest_source_changed",
        "delivery_manifest_source_mismatch",
    }
)
SUBMISSION_MINIMAL_SOURCE_MISSING_STALE_REASONS = frozenset(
    {
        "current_submission_source_missing",
        "delivery_manifest_sources_missing",
    }
)


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _gate_blockers(gate_report: dict[str, Any]) -> set[str]:
    return {
        str(item or "").strip()
        for item in (gate_report.get("blockers") or [])
        if str(item or "").strip()
    }


def bundle_stage_repair_requested(*, gate_report: dict[str, Any]) -> bool:
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    if current_required_action in BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS:
        return True
    return bool(_gate_blockers(gate_report) & BUNDLE_STAGE_GATE_BLOCKERS)


def bundle_stage_batch_action(
    *,
    source_action: dict[str, Any] | None,
    gate_report: dict[str, Any],
) -> dict[str, Any]:
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    reason = (
        str((source_action or {}).get("reason") or "").strip()
        or str(gate_report.get("controller_stage_note") or "").strip()
        or "Run one controller-owned finalize/submission repair batch before returning to the same paper line."
    )
    route_rationale = (
        str((source_action or {}).get("route_rationale") or "").strip()
        or str(gate_report.get("controller_stage_note") or "").strip()
        or "The remaining bundle-stage blockers are deterministic finalize/submission repairs."
    )
    route_key_question = (
        str((source_action or {}).get("route_key_question") or "").strip()
        or "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"
    )
    priority = str((source_action or {}).get("priority") or "").strip() or "now"
    requires_controller_decision = bool((source_action or {}).get("requires_controller_decision"))
    if source_action is None:
        requires_controller_decision = True
    return {
        **(source_action or {}),
        "action_type": "route_back_same_line",
        "priority": priority,
        "reason": reason,
        "route_target": "finalize",
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "requires_controller_decision": requires_controller_decision,
        "current_required_action": current_required_action or None,
    }


def study_delivery_status(gate_report: dict[str, Any]) -> str:
    return str(gate_report.get("study_delivery_status") or "").strip()


def study_delivery_stale_reason(gate_report: dict[str, Any]) -> str:
    return str(gate_report.get("study_delivery_stale_reason") or "").strip()


def submission_minimal_core_outputs_missing(gate_report: dict[str, Any]) -> bool:
    manifest_present = bool(_non_empty_text(gate_report.get("submission_minimal_manifest_path")))
    if gate_report.get("submission_minimal_present") is not None:
        manifest_present = bool(gate_report.get("submission_minimal_present"))
    return (
        not manifest_present
        or not bool(gate_report.get("submission_minimal_docx_present"))
        or not bool(gate_report.get("submission_minimal_pdf_present"))
    )


def submission_minimal_refresh_requested(*, gate_report: dict[str, Any]) -> bool:
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    if current_required_action == "complete_bundle_stage":
        return True
    if _gate_blockers(gate_report) & SUBMISSION_MINIMAL_REPAIR_GATE_BLOCKERS:
        return True
    return (
        submission_minimal_core_outputs_missing(gate_report)
        and study_delivery_status(gate_report).startswith("stale")
        and study_delivery_stale_reason(gate_report) in SUBMISSION_MINIMAL_SOURCE_MISSING_STALE_REASONS
    )


def direct_submission_delivery_sync_requested(*, gate_report: dict[str, Any]) -> bool:
    return (
        study_delivery_status(gate_report).startswith("stale")
        and study_delivery_stale_reason(gate_report) in DIRECT_SUBMISSION_DELIVERY_SYNC_STALE_REASONS
    )


def current_package_authority_fingerprints(
    *,
    paper_root: Path,
    path_fingerprints: Callable[..., list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    return path_fingerprints(
        paper_root / "submission_minimal" / "submission_manifest.json",
        paper_root / "submission_minimal" / "manuscript.docx",
        paper_root / "submission_minimal" / "paper.pdf",
        paper_root / "submission_minimal" / "Supplementary_Material.docx",
        paper_root / "submission_minimal" / "references.bib",
        limit=16,
    )


def current_package_authority_settled(
    *,
    paper_root: Path,
    path_fingerprints: Callable[..., list[dict[str, Any]]],
    settle_window_ns: int,
) -> tuple[bool, list[dict[str, Any]]]:
    fingerprints = current_package_authority_fingerprints(paper_root=paper_root, path_fingerprints=path_fingerprints)
    now_ns = time.time_ns()
    for fingerprint in fingerprints:
        if not fingerprint.get("exists"):
            continue
        mtime_ns = fingerprint.get("mtime_ns")
        if not isinstance(mtime_ns, int):
            continue
        if now_ns - mtime_ns < settle_window_ns:
            return False, fingerprints
    return True, fingerprints


def sync_submission_minimal_delivery_after_settle(
    *,
    paper_root: Path,
    profile: Any,
    sync_submission_minimal_delivery: Callable[..., dict[str, Any]],
    path_fingerprints: Callable[..., list[dict[str, Any]]],
    settle_window_ns: int,
) -> dict[str, Any]:
    authority_settled, authority_fingerprints = current_package_authority_settled(
        paper_root=paper_root,
        path_fingerprints=path_fingerprints,
        settle_window_ns=settle_window_ns,
    )
    if not authority_settled:
        return {
            "status": "skipped_authority_not_settled",
            "authority_fingerprints": authority_fingerprints,
            "settle_window_ns": settle_window_ns,
        }
    result = sync_submission_minimal_delivery(paper_root=paper_root, profile=profile)
    result["authority_fingerprints"] = authority_fingerprints
    result["settle_window_ns"] = settle_window_ns
    return result

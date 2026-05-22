from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience import study_task_intake_surfaces as surfaces
from med_autoscience.study_task_intake_fast_lane import (
    build_manuscript_fast_lane_contract,
    build_manuscript_fast_lane_progress_override,
    render_manuscript_fast_lane_markdown_lines,
    render_manuscript_fast_lane_runtime_context_lines,
    task_intake_requests_manuscript_fast_lane,
)
from med_autoscience.study_task_intake_fast_lane_closeout import (
    task_intake_yields_to_manuscript_fast_lane_closeout as _fast_lane_closeout_yields_task_intake,
    task_intake_yields_to_verified_manuscript_fast_lane_closeout as _verified_fast_lane_closeout_yields_task_intake,
)
from med_autoscience import study_task_intake_direct_completion as direct_completion
from med_autoscience.study_task_intake_delivery_closeout import (
    task_intake_yields_to_current_delivery_package_closeout as _delivery_package_closeout_yields_task_intake,
)
from med_autoscience.study_task_intake_stop_loss import (
    build_publishability_stop_loss_intake,
    build_publishability_stop_loss_progress_override,
    render_publishability_stop_loss_markdown_lines,
    render_publishability_stop_loss_runtime_context_lines,
    task_intake_requests_publishability_stop_loss,
)
from med_autoscience.study_task_intake_manual_hold import (
    build_manual_hold_intake,
    build_manual_hold_progress_override,
    render_manual_hold_markdown_lines,
    render_manual_hold_runtime_context_lines,
    task_intake_requests_manual_hold,
)
from med_autoscience.study_task_intake_revision import (
    build_reviewer_revision_intake,
    submission_revision_operating_state,
    task_intake_is_reviewer_revision,
    task_intake_requests_submission_package_refresh,
)
from med_autoscience.study_task_intake_reviewer_quality import (
    evaluation_summary_has_open_reviewer_first_blockers as _evaluation_summary_has_open_reviewer_first_blockers,
    reviewer_revision_has_open_reviewer_first_blockers,
)
from med_autoscience.study_task_intake_rebuttal_closeout import (
    task_intake_yields_to_rebuttal_route_coverage_closeout as _rebuttal_route_coverage_closeout_yields_task_intake,
)
from med_autoscience.submission_revision_operating_contract import build_submission_revision_operating_contract

SCHEMA_VERSION = surfaces.SCHEMA_VERSION
TASK_INTAKE_RELATIVE_ROOT = surfaces.TASK_INTAKE_RELATIVE_ROOT
STARTUP_BRIEF_BLOCK_BEGIN = surfaces.STARTUP_BRIEF_BLOCK_BEGIN
STARTUP_BRIEF_BLOCK_END = surfaces.STARTUP_BRIEF_BLOCK_END

_ENTRY_MODE_LABELS = {
    "full_research": "完整研究（full_research）",
    "manuscript_fast_lane": "论文快修通道（manuscript_fast_lane）",
}
_ANALYSIS_ROUTE_MARKERS = (
    "统计分析",
    "subgroup",
    "association analysis",
    "补充分析",
    "分层",
    "卡方",
    "analysis-campaign",
    "return_to_analysis_campaign", "analysis route-back", "analysis/harmonization",
    "methodology correction", "methodological correction", "方法学勘误", "方法学污染",
    "harmonization owner", "unit-harmonized", "unit harmonized",
    "unit-standardized", "unit standardized", "变量归一化对齐", "数据归一化对齐", "单位统一", "单位对齐",
)
_BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
_DETERMINISTIC_SUBMISSION_CLOSEOUT_BLOCKERS = frozenset({
    "stale_submission_minimal_authority",
    "stale_study_delivery_mirror",
    "submission_surface_qc_failure_present",
    "submission_hardening_incomplete",
})
def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_strings(values: Iterable[object]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return normalized


def _entry_mode_label(value: object) -> str:
    text = _non_empty_text(value) or "full_research"
    return _ENTRY_MODE_LABELS.get(text, text)


def _normalize_timestamp(value: object) -> datetime | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def task_intake_root(*, study_root: Path) -> Path:
    return surfaces.task_intake_root(study_root=study_root)


def latest_task_intake_json_path(*, study_root: Path) -> Path:
    return surfaces.latest_task_intake_json_path(study_root=study_root)


def latest_task_intake_markdown_path(*, study_root: Path) -> Path:
    return surfaces.latest_task_intake_markdown_path(study_root=study_root)


def _timestamped_task_intake_json_path(*, study_root: Path, slug: str) -> Path:
    return surfaces.timestamped_task_intake_json_path(study_root=study_root, slug=slug)


def _timestamped_task_intake_markdown_path(*, study_root: Path, slug: str) -> Path:
    return surfaces.timestamped_task_intake_markdown_path(study_root=study_root, slug=slug)


def read_latest_task_intake(*, study_root: Path) -> dict[str, Any] | None:
    return surfaces.read_latest_task_intake(study_root=study_root)


def summarize_task_intake(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    task_intent = _non_empty_text(payload.get("task_intent"))
    entry_mode = _non_empty_text(payload.get("entry_mode")) or "full_research"
    if task_intent is None and entry_mode is None:
        return None
    summary = {
        "task_id": _non_empty_text(payload.get("task_id")),
        "study_id": _non_empty_text(payload.get("study_id")),
        "emitted_at": _non_empty_text(payload.get("emitted_at")),
        "entry_mode": entry_mode,
        "task_intent": task_intent,
        "journal_target": _non_empty_text(payload.get("journal_target")),
        "constraints": _normalized_strings(payload.get("constraints") or []),
        "evidence_boundary": _normalized_strings(payload.get("evidence_boundary") or []),
        "trusted_inputs": _normalized_strings(payload.get("trusted_inputs") or []),
        "reference_papers": _normalized_strings(payload.get("reference_papers") or []),
        "first_cycle_outputs": _normalized_strings(payload.get("first_cycle_outputs") or []),
    }
    stop_loss_intake = build_publishability_stop_loss_intake(payload)
    if stop_loss_intake is not None:
        summary["stop_loss_intake"] = stop_loss_intake
    manual_hold_intake = build_manual_hold_intake(payload)
    if manual_hold_intake is not None:
        summary["manual_hold_intake"] = manual_hold_intake
    revision_intake = build_reviewer_revision_intake(payload)
    if revision_intake is not None:
        summary["revision_intake"] = revision_intake
    manuscript_fast_lane = build_manuscript_fast_lane_contract(payload)
    if manuscript_fast_lane is not None:
        summary["manuscript_fast_lane"] = manuscript_fast_lane
    operating_state = submission_revision_operating_state(payload)
    if operating_state is not None:
        summary["submission_revision_operating_contract"] = build_submission_revision_operating_contract(
            operating_state, trigger="task_intake", evidence={"task_id": summary["task_id"], "entry_mode": entry_mode}
        )
    return summary


def _task_intake_text_corpus(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    values: list[object] = [
        payload.get("task_intent"),
        *(payload.get("constraints") or []),
        *(payload.get("evidence_boundary") or []),
        *(payload.get("trusted_inputs") or []),
        *(payload.get("reference_papers") or []),
        *(payload.get("first_cycle_outputs") or []),
    ]
    return tuple(_normalized_strings(values))


def _task_intake_contains_any(payload: dict[str, Any] | None, markers: tuple[str, ...]) -> bool:
    corpus = _task_intake_text_corpus(payload)
    if not corpus:
        return False
    for text in corpus:
        lowered = text.lower()
        if any(marker.lower() in lowered for marker in markers):
            return True
    return False


def task_intake_overrides_auto_manual_finish(payload: dict[str, Any] | None) -> bool:
    # 这里只接受 durable task intake 中明确写出的强语义，不做泛化 NLP 推断。
    return (
        task_intake_requests_publishability_stop_loss(payload)
        or task_intake_requests_manual_hold(payload)
        or task_intake_is_reviewer_revision(payload)
        or task_intake_requests_manuscript_fast_lane(payload)
        or task_intake_requests_submission_package_refresh(payload)
    )


def _integer_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return None


def _mapping_value(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _surface_emitted_at(payload: dict[str, Any] | None) -> datetime | None:
    if not isinstance(payload, dict):
        return None
    return _normalize_timestamp(payload.get("emitted_at") or payload.get("generated_at") or payload.get("created_at"))


def _closeout_surface_is_fresher_than_task_intake(
    payload: dict[str, Any] | None,
    *surfaces: dict[str, Any] | None,
) -> bool:
    task_intake_emitted_at = _surface_emitted_at(payload)
    if task_intake_emitted_at is None:
        return False
    latest_surface_emitted_at = max(
        (
            surface_emitted_at
            for surface_emitted_at in (_surface_emitted_at(surface) for surface in surfaces)
            if surface_emitted_at is not None
        ),
        default=None,
    )
    return latest_surface_emitted_at is not None and latest_surface_emitted_at >= task_intake_emitted_at


def _latest_revision_handoff_verification(*, study_root: Path | None) -> dict[str, Any] | None:
    if study_root is None:
        return None
    root = task_intake_root(study_root=study_root)
    if not root.exists():
        return None
    candidates: list[tuple[datetime, str, dict[str, Any]]] = []
    for path in root.glob("revision_handoff_verification_*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        timestamp = _surface_emitted_at(payload)
        if timestamp is None:
            try:
                timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
        candidates.append((timestamp, path.name, payload))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def task_intake_yields_to_manuscript_fast_lane_closeout(
    payload: dict[str, Any] | None,
    *,
    study_root: Path | None,
) -> bool:
    if not task_intake_overrides_auto_manual_finish(payload):
        return False
    return _fast_lane_closeout_yields_task_intake(
        payload,
        task_intake_root=task_intake_root(study_root=study_root) if study_root is not None else None,
    )


def _revision_handoff_verification_confirms_writeback(
    *,
    task_intake_payload: dict[str, Any] | None,
    verification_payload: dict[str, Any] | None,
) -> bool:
    if not isinstance(task_intake_payload, dict) or not isinstance(verification_payload, dict):
        return False
    task_id = _non_empty_text(task_intake_payload.get("task_id"))
    source_task_id = _non_empty_text(verification_payload.get("source_task_id"))
    if task_id is None or source_task_id != task_id:
        return False
    task_emitted_at = _surface_emitted_at(task_intake_payload)
    verification_emitted_at = _surface_emitted_at(verification_payload)
    if task_emitted_at is None or verification_emitted_at is None or verification_emitted_at < task_emitted_at:
        return False
    if verification_payload.get("task_intake_has_newer_superseding_task") is True:
        return False
    evidence = _mapping_value(verification_payload.get("evidence"))
    evidence_task_intake = _mapping_value(evidence.get("task_intake"))
    if evidence_task_intake.get("newer_task_intake_found") is True:
        return False
    answer = (_non_empty_text(verification_payload.get("answer")) or "").lower()
    if not answer.startswith("yes"):
        return False
    boundary = _mapping_value(verification_payload.get("boundary"))
    if boundary.get("not_first_cycle_writeback_blockers") is True:
        return True
    next_route = (_non_empty_text(verification_payload.get("next_route")) or "").lower()
    if "close_write_stage" in next_route:
        return True
    checklist = verification_payload.get("checklist_status")
    if isinstance(checklist, list) and checklist:
        statuses = [
            (_non_empty_text((item or {}).get("status")) or "")
            for item in checklist
            if isinstance(item, dict)
        ]
        if statuses and all(status.startswith("complete") for status in statuses):
            return True
    publication_eval = _mapping_value(evidence.get("publication_eval"))
    quality_note = (_non_empty_text(publication_eval.get("quality_closure_note")) or "").lower()
    return "does not identify" in quality_note and "writeback defect" in quality_note


def _gate_report_clear_for_quality_closeout(gate_report: dict[str, Any] | None) -> bool:
    if not isinstance(gate_report, dict):
        return False
    if _non_empty_text(gate_report.get("status")) != "clear":
        return False
    blockers = {
        str(item or "").strip()
        for item in (gate_report.get("blockers") or [])
        if str(item or "").strip()
    }
    if blockers:
        return False
    if gate_report.get("allow_write") is False:
        return False
    current_required_action = _non_empty_text(gate_report.get("current_required_action"))
    return current_required_action in {None, *_BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS}


def _evaluation_summary_requests_ai_reviewer_quality_closure(
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not isinstance(evaluation_summary, dict):
        return False
    quality_closure_truth = _mapping_value(evaluation_summary.get("quality_closure_truth"))
    quality_review_loop = _mapping_value(evaluation_summary.get("quality_review_loop"))
    study_quality_truth = _mapping_value(evaluation_summary.get("study_quality_truth"))
    reviewer_first = _mapping_value(study_quality_truth.get("reviewer_first"))
    closure_state = (
        _non_empty_text(quality_closure_truth.get("state"))
        or _non_empty_text(quality_review_loop.get("closure_state"))
    )
    if closure_state != "quality_repair_required":
        return False
    corpus = _normalized_strings(
        [
            quality_closure_truth.get("summary"),
            quality_review_loop.get("summary"),
            quality_review_loop.get("recommended_next_action"),
            study_quality_truth.get("summary"),
            reviewer_first.get("summary"),
            *((quality_review_loop.get("blocking_issues") or []) if isinstance(quality_review_loop.get("blocking_issues"), list) else []),
            *((quality_review_loop.get("next_review_focus") or []) if isinstance(quality_review_loop.get("next_review_focus"), list) else []),
        ]
    )
    markers = ("ai reviewer", "ai_reviewer", "assessment_provenance.owner=ai_reviewer", "reviewer-authored")
    return any(marker in text.lower() for text in corpus for marker in markers)


def _task_intake_yields_to_verified_reviewer_quality_closeout(
    *,
    payload: dict[str, Any] | None,
    study_root: Path | None,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not task_intake_is_reviewer_revision(payload):
        return False
    if not _evaluation_summary_requests_ai_reviewer_quality_closure(evaluation_summary):
        return False
    gate_report = (
        publishability_gate_report
        if isinstance(publishability_gate_report, dict)
        else _mapping_value((evaluation_summary or {}).get("promotion_gate_status"))
    )
    if not _gate_report_clear_for_quality_closeout(gate_report):
        return False
    if not _closeout_surface_is_fresher_than_task_intake(
        payload,
        gate_report,
        evaluation_summary,
    ):
        return False
    return _revision_handoff_verification_confirms_writeback(
        task_intake_payload=payload,
        verification_payload=_latest_revision_handoff_verification(study_root=study_root),
    )


def _task_intake_yields_to_blocked_submission_closeout(
    publishability_gate_report: dict[str, Any] | None,
) -> bool:
    if not isinstance(publishability_gate_report, dict):
        return False
    if _non_empty_text(publishability_gate_report.get("status")) != "blocked":
        return False
    blockers = {
        str(item or "").strip()
        for item in (publishability_gate_report.get("blockers") or [])
        if str(item or "").strip()
    }
    if not blockers or blockers - _DETERMINISTIC_SUBMISSION_CLOSEOUT_BLOCKERS:
        return False
    open_supplementary_count = _integer_value(
        publishability_gate_report.get("paper_line_open_supplementary_count")
    )
    if open_supplementary_count != 0:
        return False
    if _non_empty_text(publishability_gate_report.get("medical_publication_surface_status")) == "blocked":
        return False
    if publishability_gate_report.get("medical_publication_surface_current") is False:
        return False
    return True


def _task_intake_yields_to_bundle_only_submission_closeout(
    *,
    payload: dict[str, Any] | None,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    quality_closure_truth = _mapping_value((evaluation_summary or {}).get("quality_closure_truth"))
    quality_review_loop = _mapping_value((evaluation_summary or {}).get("quality_review_loop"))
    quality_assessment = _mapping_value((evaluation_summary or {}).get("quality_assessment"))
    human_review_readiness = _mapping_value(quality_assessment.get("human_review_readiness"))
    closure_state = (
        _non_empty_text(quality_closure_truth.get("state"))
        or _non_empty_text(quality_review_loop.get("closure_state"))
    )
    if closure_state != "bundle_only_remaining":
        return False
    human_review_status = _non_empty_text(human_review_readiness.get("status"))
    if human_review_status not in {None, "ready"}:
        return False
    if isinstance(publishability_gate_report, dict):
        if _non_empty_text(publishability_gate_report.get("status")) not in {None, "clear"}:
            return False
        gate_blockers = {
            str(item or "").strip()
            for item in (publishability_gate_report.get("blockers") or [])
            if str(item or "").strip()
        }
        if gate_blockers:
            return False
        current_required_action = _non_empty_text(publishability_gate_report.get("current_required_action"))
        if (
            current_required_action is not None
            and current_required_action not in _BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS
        ):
            return False
        if publishability_gate_report.get("bundle_tasks_downstream_only") is True:
            return False
    return _closeout_surface_is_fresher_than_task_intake(
        payload,
        publishability_gate_report,
        evaluation_summary,
    )


def _evaluation_summary_reports_bundle_only_remaining(
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not isinstance(evaluation_summary, dict):
        return False
    quality_closure_truth = _mapping_value(evaluation_summary.get("quality_closure_truth"))
    quality_review_loop = _mapping_value(evaluation_summary.get("quality_review_loop"))
    closure_state = (
        _non_empty_text(quality_closure_truth.get("state"))
        or _non_empty_text(quality_review_loop.get("closure_state"))
    )
    return closure_state == "bundle_only_remaining"


def _evaluation_summary_confirms_scientific_quality_closed(
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not isinstance(evaluation_summary, dict):
        return False
    study_quality_truth = _mapping_value(evaluation_summary.get("study_quality_truth"))
    if study_quality_truth.get("contract_closed") is True:
        return True
    narrowest_scientific_gap = _mapping_value(study_quality_truth.get("narrowest_scientific_gap"))
    return _non_empty_text(narrowest_scientific_gap.get("state")) == "closed"


def _evaluation_summary_confirms_reviewer_first_ready(
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not isinstance(evaluation_summary, dict):
        return False
    study_quality_truth = _mapping_value(evaluation_summary.get("study_quality_truth"))
    reviewer_first = _mapping_value(study_quality_truth.get("reviewer_first"))
    if reviewer_first.get("ready") is True:
        return True
    return _non_empty_text(reviewer_first.get("status")) == "ready"


def _task_intake_yields_to_reviewer_bundle_stage_closeout(
    *,
    payload: dict[str, Any] | None,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not _evaluation_summary_confirms_reviewer_first_ready(evaluation_summary):
        return False
    gate_report = (
        publishability_gate_report
        if isinstance(publishability_gate_report, dict)
        else _mapping_value((evaluation_summary or {}).get("promotion_gate_status"))
    )
    if not gate_report:
        return False
    return _task_intake_yields_to_bundle_only_submission_closeout(
        payload=payload,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )


def _task_intake_yields_to_verified_bundle_only_closeout(
    *,
    payload: dict[str, Any] | None,
    study_root: Path | None,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not _evaluation_summary_reports_bundle_only_remaining(evaluation_summary):
        return False
    if not _evaluation_summary_confirms_scientific_quality_closed(evaluation_summary):
        return False
    gate_report = (
        publishability_gate_report
        if isinstance(publishability_gate_report, dict)
        else _mapping_value((evaluation_summary or {}).get("promotion_gate_status"))
    )
    if not _gate_report_clear_for_quality_closeout(gate_report):
        return False
    if not _closeout_surface_is_fresher_than_task_intake(
        payload,
        gate_report,
        evaluation_summary,
    ):
        return False
    return _revision_handoff_verification_confirms_writeback(
        task_intake_payload=payload,
        verification_payload=_latest_revision_handoff_verification(study_root=study_root),
    )


def task_intake_yields_to_deterministic_submission_closeout(
    payload: dict[str, Any] | None,
    *,
    study_root: Path | None = None,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None = None,
) -> bool:
    if not task_intake_overrides_auto_manual_finish(payload):
        return False
    if direct_completion.task_intake_yields_to_direct_foreground_completion(
        payload,
        task_intake_root=task_intake_root(study_root=study_root) if study_root is not None else None,
    ):
        return True
    if _verified_fast_lane_closeout_yields_task_intake(
        payload,
        task_intake_root=task_intake_root(study_root=study_root) if study_root is not None else None,
        publishability_gate_report=publishability_gate_report,
        evaluation_summary=evaluation_summary,
    ):
        return True
    blocked_submission_closeout = _task_intake_yields_to_blocked_submission_closeout(publishability_gate_report)
    if task_intake_is_reviewer_revision(payload):
        if _rebuttal_route_coverage_closeout_yields_task_intake(
            task_intake_payload=payload,
            study_root=study_root,
            publishability_gate_report=publishability_gate_report,
            evaluation_summary=evaluation_summary,
        ):
            return True
        if _task_intake_yields_to_verified_reviewer_quality_closeout(
            payload=payload,
            study_root=study_root,
            publishability_gate_report=publishability_gate_report,
            evaluation_summary=evaluation_summary,
        ):
            return True
        if _task_intake_yields_to_verified_bundle_only_closeout(
            payload=payload,
            study_root=study_root,
            publishability_gate_report=publishability_gate_report,
            evaluation_summary=evaluation_summary,
        ):
            return True
        if _delivery_package_closeout_yields_task_intake(
            payload,
            study_root=study_root,
            publishability_gate_report=publishability_gate_report,
        ):
            return True
        if _evaluation_summary_has_open_reviewer_first_blockers(evaluation_summary):
            return False
        if (
            blocked_submission_closeout
            and _evaluation_summary_reports_bundle_only_remaining(evaluation_summary)
            and _closeout_surface_is_fresher_than_task_intake(
                payload,
                publishability_gate_report,
                evaluation_summary,
            )
        ):
            return True
        return _task_intake_yields_to_reviewer_bundle_stage_closeout(
            payload=payload,
            publishability_gate_report=publishability_gate_report,
            evaluation_summary=evaluation_summary,
        )
    if blocked_submission_closeout:
        return True
    return _task_intake_yields_to_bundle_only_submission_closeout(
        payload=payload,
        publishability_gate_report=publishability_gate_report,
        evaluation_summary=evaluation_summary,
    )


def build_task_intake_progress_override(
    payload: dict[str, Any] | None,
    *,
    study_root: Path | None = None,
    publishability_gate_report: dict[str, Any] | None = None,
    evaluation_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not task_intake_overrides_auto_manual_finish(payload):
        return None
    stop_loss_override = build_publishability_stop_loss_progress_override(payload)
    if stop_loss_override is not None:
        return stop_loss_override
    manual_hold_override = build_manual_hold_progress_override(payload)
    if manual_hold_override is not None:
        return manual_hold_override
    if task_intake_yields_to_deterministic_submission_closeout(
        payload,
        study_root=study_root,
        publishability_gate_report=publishability_gate_report,
        evaluation_summary=evaluation_summary,
    ):
        return None
    if task_intake_requests_manuscript_fast_lane(payload):
        return build_manuscript_fast_lane_progress_override(payload)
    route_target = "analysis-campaign" if _task_intake_contains_any(payload, _ANALYSIS_ROUTE_MARKERS) else "write"
    route_target_label = {
        "analysis-campaign": "补充分析与稳健性验证",
        "write": "论文写作与结果收紧",
    }[route_target]
    current_required_action = {
        "analysis-campaign": "return_to_analysis_campaign",
        "write": "continue_write_stage",
    }[route_target]
    same_line_state = "bounded_analysis" if route_target == "analysis-campaign" else "same_line_route_back"
    same_line_state_label = {
        "bounded_analysis": "有限补充分析",
        "same_line_route_back": "同线质量修复",
    }[same_line_state]
    first_cycle_outputs = _normalized_strings(payload.get("first_cycle_outputs") or [])
    current_focus = (
        first_cycle_outputs[0]
        if first_cycle_outputs
        else "当前最新 task intake 指定的首轮修订产出是否已经补齐并写回 manuscript？"
    )
    blocker_summary = (
        "最新 task intake 已明确要求回到待修订状态；旧的 submission-ready/finalize 收口判断不能继续作为当前真相。"
    )
    route_summary = (
        f"最新 task intake 已明确重开同一论文线修订；先回到“{route_target_label}”，"
        f"完成“{current_focus}”，再重新评估 submission-ready/finalize。"
    )
    execution_summary = (
        f"当前质量执行线服从最新 task intake；先回到“{route_target_label}”，完成“{current_focus}”。"
    )
    quality_closure_summary = (
        f"{blocker_summary} 当前应先完成“{current_focus}”，再进入下一轮论文质量复评。"
    )
    operating_state = "reviewer_revision" if task_intake_is_reviewer_revision(payload) else "submission_package_refresh"
    submission_revision_operating_contract = build_submission_revision_operating_contract(
        operating_state, trigger="task_intake_progress_override", evidence={"route_target": route_target, "current_focus": current_focus}
    )
    return {
        "blocker_summary": blocker_summary,
        "current_stage_summary": blocker_summary,
        "next_system_action": route_summary,
        "current_required_action": current_required_action,
        "paper_stage": route_target,
        "paper_stage_summary": route_summary,
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "summary": quality_closure_summary,
            "current_required_action": current_required_action,
            "route_target": route_target,
        },
        "submission_revision_operating_contract": submission_revision_operating_contract,
        "quality_execution_lane": {
            "lane_id": "general_quality_repair",
            "lane_label": "质量修复",
            "repair_mode": same_line_state,
            "route_target": route_target,
            "route_key_question": current_focus,
            "summary": execution_summary,
            "why_now": blocker_summary,
        },
        "same_line_route_truth": {
            "surface_kind": "same_line_route_truth",
            "same_line_state": same_line_state,
            "same_line_state_label": same_line_state_label,
            "route_mode": "return",
            "route_target": route_target,
            "route_target_label": route_target_label,
            "summary": route_summary,
            "current_focus": current_focus,
        },
        "same_line_route_surface": {
            "surface_kind": "same_line_route_surface",
            "lane_id": "general_quality_repair",
            "repair_mode": same_line_state,
            "route_target": route_target,
            "route_target_label": route_target_label,
            "route_key_question": current_focus,
            "summary": execution_summary,
            "why_now": blocker_summary,
            "current_required_action": current_required_action,
            "closure_state": "quality_repair_required",
        },
    }


def render_task_intake_markdown(payload: dict[str, Any]) -> str:
    return surfaces.render_task_intake_markdown(
        payload,
        entry_mode_label=_entry_mode_label,
        render_stop_loss_lines=render_publishability_stop_loss_markdown_lines,
        render_manual_hold_lines=render_manual_hold_markdown_lines,
        build_reviewer_revision_intake=build_reviewer_revision_intake,
        render_manuscript_fast_lane_lines=render_manuscript_fast_lane_markdown_lines,
    )


def render_task_intake_runtime_context(payload: dict[str, Any]) -> str:
    return surfaces.render_task_intake_runtime_context(
        payload,
        normalized_strings=_normalized_strings,
        non_empty_text=_non_empty_text,
        build_reviewer_revision_intake=build_reviewer_revision_intake,
        render_manual_hold_lines=render_manual_hold_runtime_context_lines,
        render_stop_loss_lines=render_publishability_stop_loss_runtime_context_lines,
        render_manuscript_fast_lane_lines=render_manuscript_fast_lane_runtime_context_lines,
    )


def render_startup_brief_task_block(payload: dict[str, Any]) -> str:
    return surfaces.render_startup_brief_task_block(payload, render_markdown=render_task_intake_markdown)


def upsert_startup_brief_task_block(*, existing_text: str, payload: dict[str, Any]) -> str:
    return surfaces.upsert_startup_brief_task_block(
        existing_text=existing_text,
        payload=payload,
        render_markdown=render_task_intake_markdown,
    )


def write_task_intake(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    entry_mode: str,
    task_intent: str,
    journal_target: str | None = None,
    constraints: Iterable[object] = (),
    evidence_boundary: Iterable[object] = (),
    trusted_inputs: Iterable[object] = (),
    reference_papers: Iterable[object] = (),
    first_cycle_outputs: Iterable[object] = (),
    task_intake_kind: str | None = None,
) -> dict[str, Any]:
    return surfaces.write_task_intake(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        entry_mode=entry_mode,
        task_intent=task_intent,
        emitted_at=_utc_now(),
        slug=_timestamp_slug(),
        non_empty_text=_non_empty_text,
        normalized_strings=_normalized_strings,
        render_markdown=render_task_intake_markdown,
        build_stop_loss_intake=build_publishability_stop_loss_intake,
        build_manual_hold_intake=build_manual_hold_intake,
        build_reviewer_revision_intake=build_reviewer_revision_intake,
        journal_target=journal_target,
        constraints=constraints,
        evidence_boundary=evidence_boundary,
        trusted_inputs=trusted_inputs,
        reference_papers=reference_papers,
        first_cycle_outputs=first_cycle_outputs,
        task_intake_kind=task_intake_kind,
    )

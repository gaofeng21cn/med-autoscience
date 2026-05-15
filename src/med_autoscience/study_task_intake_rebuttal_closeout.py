from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


_BUNDLE_STAGE_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
_FINALIZE_OWNER_MARKERS = ("finalize", "bundle-stage", "bundle_stage", "package closure")


def task_intake_yields_to_rebuttal_route_coverage_closeout(
    *,
    task_intake_payload: dict[str, Any] | None,
    study_root: Path | None,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    closeout = latest_rebuttal_route_coverage_closeout(study_root=study_root)
    if closeout is None:
        return False
    if not _surface_is_fresher_than_task_intake(task_intake_payload, closeout):
        return False
    if not _gate_allows_bundle_stage(publishability_gate_report, evaluation_summary):
        return False
    return _rebuttal_route_coverage_closeout_complete(closeout)


def latest_rebuttal_route_coverage_closeout(*, study_root: Path | None) -> dict[str, Any] | None:
    if study_root is None:
        return None
    closeout_root = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "stage_knowledge"
        / "analysis-campaign"
        / "closeouts"
    )
    if not closeout_root.exists():
        return None
    candidates: list[tuple[datetime, str, dict[str, Any]]] = []
    for path in closeout_root.glob("rebuttal_route_coverage_*.json"):
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


def _rebuttal_route_coverage_closeout_complete(payload: dict[str, Any]) -> bool:
    if payload.get("coverage_complete") is not True:
        return False
    if _integer_value(payload.get("active_upstream_repair_units")) not in {None, 0}:
        return False
    total = _integer_value(payload.get("feedback_items_total"))
    covered = _integer_value(payload.get("items_with_valid_route"))
    if total is not None and total <= 0:
        return False
    if total is not None and covered != total:
        return False
    if total is None and covered is not None and covered <= 0:
        return False
    route_classes = _integer_value(payload.get("required_route_classes_present"))
    if route_classes is not None and route_classes <= 0:
        return False
    if not _slice_ledger_confirms_route_coverage(payload.get("slice_ledger"), expected_total=total):
        return False
    if not _next_owner_is_finalize_or_bundle(payload.get("next_owner_recommendation")):
        return False
    boundary = _mapping(payload.get("authority_boundary"))
    if boundary.get("mutated_submission_package") is True or boundary.get("mutated_current_package") is True:
        return False
    return True


def _slice_ledger_confirms_route_coverage(value: object, *, expected_total: int | None) -> bool:
    if not isinstance(value, list):
        return True
    for item in value:
        if not isinstance(item, dict):
            continue
        slice_id = _text(item.get("slice_id"))
        if slice_id != "reviewer_revision_route_coverage":
            continue
        if _text(item.get("status")) not in {"complete", "completed", "done"}:
            return False
        covered = _integer_value(item.get("covered_items"))
        if expected_total is not None and covered != expected_total:
            return False
        if expected_total is None and covered is not None and covered <= 0:
            return False
        return True
    return True


def _gate_allows_bundle_stage(
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    gate_report = publishability_gate_report if isinstance(publishability_gate_report, dict) else {}
    if not gate_report:
        gate_report = _mapping((evaluation_summary or {}).get("promotion_gate_status"))
    if _text(gate_report.get("status")) != "clear":
        return False
    if gate_report.get("allow_write") is False:
        return False
    blockers = [text for text in _text_iter(gate_report.get("blockers")) if text]
    if blockers:
        return False
    current_required_action = _text(gate_report.get("current_required_action"))
    if current_required_action not in _BUNDLE_STAGE_ACTIONS:
        return False
    supervisor_phase = _text(gate_report.get("supervisor_phase"))
    if supervisor_phase and supervisor_phase not in {"bundle_stage_ready", "bundle_stage_blocked"}:
        return False
    closure_truth = _mapping((evaluation_summary or {}).get("quality_closure_truth"))
    review_loop = _mapping((evaluation_summary or {}).get("quality_review_loop"))
    closure_state = _text(closure_truth.get("state")) or _text(review_loop.get("closure_state"))
    return closure_state in {None, "bundle_only_remaining"}


def _next_owner_is_finalize_or_bundle(value: object) -> bool:
    text = _text(value)
    if text is None:
        return False
    lowered = text.lower()
    return any(marker in lowered for marker in _FINALIZE_OWNER_MARKERS)


def _surface_is_fresher_than_task_intake(
    task_intake_payload: dict[str, Any] | None,
    surface: dict[str, Any],
) -> bool:
    task_time = _surface_emitted_at(task_intake_payload)
    surface_time = _surface_emitted_at(surface)
    return task_time is not None and surface_time is not None and surface_time >= task_time


def _surface_emitted_at(payload: dict[str, Any] | None) -> datetime | None:
    if not isinstance(payload, dict):
        return None
    for key in ("emitted_at", "generated_at", "created_at", "completed_at"):
        parsed = _parse_timestamp(payload.get(key))
        if parsed is not None:
            return parsed
    return None


def _parse_timestamp(value: object) -> datetime | None:
    text = _text(value)
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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _text_iter(value: object) -> Iterable[str]:
    if isinstance(value, (list, tuple, set)):
        for item in value:
            text = _text(item)
            if text is not None:
                yield text
        return
    text = _text(value)
    if text is not None:
        yield text


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "latest_rebuttal_route_coverage_closeout",
    "task_intake_yields_to_rebuttal_route_coverage_closeout",
]

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .primitives import _compact_mapping, _mapping, _text, _text_list


TERMINAL_CLOSEOUT_REQUIRED_USER_STAGE_LOG_FIELDS = (
    "stage_work_done",
    "paper_work_done",
    "changed_stage_surfaces",
    "changed_paper_surfaces",
    "progress_delta_classification",
)
TERMINAL_CLOSEOUT_TELEMETRY_FIELDS = ("duration", "token_usage", "cost")
NEXT_FORCED_DELTA_SUMMARY_KEYS = (
    "required_delta_kind",
    "reason",
    "work_unit_id",
    "eval_id",
    "next_owner",
    "allowed_outcomes",
    "target_surface",
    "target_surface_specificity",
    "missing_explicit_target_surface",
    "target_surface_fallback_reason",
    "target_surface_diagnostic",
    "acceptance_refs",
    "owner_action",
)


def _latest_terminal_stage_summary(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not latest_terminal_stage_log:
        return None
    semantic_completeness = _stage_semantic_completeness(paper_stage_log)
    telemetry_completeness = _stage_telemetry_completeness(latest_terminal_stage_log)
    missing_user_fields = _missing_user_stage_log_fields(
        latest_terminal_stage_log=latest_terminal_stage_log,
        paper_stage_log=paper_stage_log,
    )
    missing_telemetry_fields = _missing_telemetry_fields(latest_terminal_stage_log)
    changed_stage_status = _field_presence_status(paper_stage_log, "changed_stage_surfaces")
    changed_paper_status = _field_presence_status(paper_stage_log, "changed_paper_surfaces")
    changed_surfaces_status = (
        "missing"
        if changed_stage_status == "missing" and changed_paper_status == "missing"
        else "present"
    )
    explicit_blocker = _text(latest_terminal_stage_log.get("typed_blocker_reason")) is not None
    infer_from_surfaces = not explicit_blocker or _explicit_closeout_blocker_is_telemetry_diagnostic_only(
        explicit=_text(latest_terminal_stage_log.get("typed_blocker_reason")) or "",
        latest_terminal_stage_log=latest_terminal_stage_log,
        missing_user_fields=missing_user_fields,
        missing_telemetry_fields=missing_telemetry_fields,
        changed_surfaces_status=changed_surfaces_status,
        progress_delta_classification=_terminal_progress_delta_classification(paper_stage_log),
    )
    progress_delta_classification = _terminal_progress_delta_classification(
        paper_stage_log,
        infer_from_surfaces=infer_from_surfaces,
    )
    progress_delta_classification_source = _terminal_progress_delta_classification_source(
        paper_stage_log,
        infer_from_surfaces=infer_from_surfaces,
    )
    return {
        "stage_attempt_id": _text(latest_terminal_stage_log.get("stage_attempt_id")),
        "stage_id": _text(latest_terminal_stage_log.get("stage_id")),
        "action_type": _text(latest_terminal_stage_log.get("action_type")),
        "status": _text(latest_terminal_stage_log.get("status")),
        "stage_name": _text(paper_stage_log.get("stage_name")),
        "problem_summary": _text(paper_stage_log.get("problem_summary")),
        "stage_goal": _text(paper_stage_log.get("stage_goal")),
        "outcome": _text(paper_stage_log.get("outcome")),
        "progress_delta_classification": progress_delta_classification,
        "progress_delta_classification_source": progress_delta_classification_source,
        "stage_work_done": _text_list(paper_stage_log.get("stage_work_done")),
        "paper_work_done": _text_list(paper_stage_log.get("paper_work_done")),
        "changed_stage_surfaces": _text_list(paper_stage_log.get("changed_stage_surfaces")),
        "changed_paper_surfaces": _text_list(paper_stage_log.get("changed_paper_surfaces")),
        "remaining_blockers": _text_list(paper_stage_log.get("remaining_blockers")),
        "evidence_refs": _text_list(paper_stage_log.get("evidence_refs")),
        "missing_user_stage_log_fields": missing_user_fields,
        "observability_status": _text(latest_terminal_stage_log.get("observability_status"))
        or ("observed" if not missing_telemetry_fields else "missing"),
        "missing_observability_fields": missing_telemetry_fields,
        "semantic_completeness": semantic_completeness,
        "duration": _mapping(latest_terminal_stage_log.get("duration")) or None,
        "token_usage": _mapping(latest_terminal_stage_log.get("token_usage")) or None,
        "cost": _mapping(latest_terminal_stage_log.get("cost")) or None,
        "telemetry_completeness": telemetry_completeness,
        "closeout_refs": _text_list(latest_terminal_stage_log.get("closeout_refs")),
        "terminal_closeout_semantic_completeness": _terminal_closeout_semantic_completeness(
            latest_terminal_stage_log=latest_terminal_stage_log,
            paper_stage_log=paper_stage_log,
            next_forced_delta=next_forced_delta,
            progress_delta_classification=progress_delta_classification,
            progress_delta_classification_source=progress_delta_classification_source,
            missing_user_fields=missing_user_fields,
            missing_telemetry_fields=missing_telemetry_fields,
        ),
        "source_path": _text(latest_terminal_stage_log.get("source_path")),
    }


def _terminal_closeout_semantic_completeness(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    progress_delta_classification: str | None,
    progress_delta_classification_source: str | None,
    missing_user_fields: list[str],
    missing_telemetry_fields: list[str],
) -> dict[str, Any]:
    changed_stage_status = _field_presence_status(paper_stage_log, "changed_stage_surfaces")
    changed_paper_status = _field_presence_status(paper_stage_log, "changed_paper_surfaces")
    changed_surfaces_status = (
        "missing"
        if changed_stage_status == "missing" and changed_paper_status == "missing"
        else "present"
    )
    typed_blocker = _terminal_closeout_typed_blocker(
        latest_terminal_stage_log=latest_terminal_stage_log,
        missing_user_fields=missing_user_fields,
        missing_telemetry_fields=missing_telemetry_fields,
        changed_surfaces_status=changed_surfaces_status,
        progress_delta_classification=progress_delta_classification,
    )
    result = {
        "status": "complete" if typed_blocker is None else "typed_blocker",
        "required_user_stage_log_fields": "complete" if not missing_user_fields else "missing",
        "missing_user_stage_log_fields": missing_user_fields,
        "changed_surfaces": changed_surfaces_status,
        "changed_stage_surfaces": changed_stage_status,
        "changed_paper_surfaces": changed_paper_status,
        "progress_delta_classification": progress_delta_classification or "missing",
        "telemetry": "complete" if not missing_telemetry_fields else "missing",
        "missing_telemetry_fields": missing_telemetry_fields,
        "typed_blocker": typed_blocker,
        "typed_blocker_diagnostic": _text(latest_terminal_stage_log.get("diagnostic")),
        "next_forced_delta": (
            _compact_mapping(next_forced_delta, NEXT_FORCED_DELTA_SUMMARY_KEYS) or None
            if typed_blocker is not None
            else None
        ),
    }
    if progress_delta_classification_source is not None:
        result["progress_delta_classification_source"] = progress_delta_classification_source
    return result


def _terminal_closeout_typed_blocker(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    missing_user_fields: list[str],
    missing_telemetry_fields: list[str],
    changed_surfaces_status: str,
    progress_delta_classification: str | None,
) -> str | None:
    explicit = _text(latest_terminal_stage_log.get("typed_blocker_reason"))
    if explicit is not None:
        if _explicit_closeout_blocker_is_telemetry_diagnostic_only(
            explicit=explicit,
            latest_terminal_stage_log=latest_terminal_stage_log,
            missing_user_fields=missing_user_fields,
            missing_telemetry_fields=missing_telemetry_fields,
            changed_surfaces_status=changed_surfaces_status,
            progress_delta_classification=progress_delta_classification,
        ):
            return None
        return explicit
    if changed_surfaces_status == "missing":
        return "typed_closeout_packet_required"
    blocking_missing_user_fields = [
        field for field in missing_user_fields if field != "progress_delta_classification"
    ]
    if blocking_missing_user_fields or progress_delta_classification is None:
        return "typed_closeout_packet_required"
    return None


def _explicit_closeout_blocker_is_telemetry_diagnostic_only(
    *,
    explicit: str,
    latest_terminal_stage_log: Mapping[str, Any],
    missing_user_fields: list[str],
    missing_telemetry_fields: list[str],
    changed_surfaces_status: str,
    progress_delta_classification: str | None,
) -> bool:
    if explicit != "typed_closeout_packet_required":
        return False
    if changed_surfaces_status == "missing" or progress_delta_classification is None:
        return False
    blocking_missing_user_fields = [
        field for field in missing_user_fields if field != "progress_delta_classification"
    ]
    if blocking_missing_user_fields:
        return False
    diagnostic = _text(latest_terminal_stage_log.get("diagnostic"))
    if not missing_telemetry_fields and diagnostic not in {
        "missing_usage_telemetry",
        "missing_observability_telemetry",
        "missing_observability_fields",
    }:
        return False
    return True


def _terminal_closeout_typed_blocker_projection(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> dict[str, Any]:
    if not latest_terminal_stage_log:
        return {}
    missing_user_fields = _missing_user_stage_log_fields(
        latest_terminal_stage_log=latest_terminal_stage_log,
        paper_stage_log=paper_stage_log,
    )
    missing_telemetry_fields = _missing_telemetry_fields(latest_terminal_stage_log)
    changed_stage_status = _field_presence_status(paper_stage_log, "changed_stage_surfaces")
    changed_paper_status = _field_presence_status(paper_stage_log, "changed_paper_surfaces")
    changed_surfaces_status = (
        "missing"
        if changed_stage_status == "missing" and changed_paper_status == "missing"
        else "present"
    )
    blocker_id = _terminal_closeout_typed_blocker(
        latest_terminal_stage_log=latest_terminal_stage_log,
        missing_user_fields=missing_user_fields,
        missing_telemetry_fields=missing_telemetry_fields,
        changed_surfaces_status=changed_surfaces_status,
        progress_delta_classification=_terminal_progress_delta_classification(paper_stage_log),
    )
    if blocker_id is None:
        return {}
    return {
        "blocker_id": blocker_id,
        "blocker_type": "provider_completed_without_typed_closeout",
        "owner": "one-person-lab",
        "summary": "Provider completion needs a typed closeout packet.",
    }


def _missing_user_stage_log_fields(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> list[str]:
    explicit = _text_list(latest_terminal_stage_log.get("missing_user_stage_log_fields"))
    if explicit:
        return explicit
    return [
        field
        for field in TERMINAL_CLOSEOUT_REQUIRED_USER_STAGE_LOG_FIELDS
        if _user_stage_log_field_missing(paper_stage_log, field)
    ]


def _terminal_progress_delta_classification(
    paper_stage_log: Mapping[str, Any],
    *,
    infer_from_surfaces: bool = True,
) -> str | None:
    explicit = _text(paper_stage_log.get("progress_delta_classification"))
    if explicit is not None:
        return explicit
    if not infer_from_surfaces:
        return None
    if _text_list(paper_stage_log.get("changed_paper_surfaces")):
        return "deliverable_progress"
    if _text_list(paper_stage_log.get("changed_stage_surfaces")):
        return "platform_repair"
    return None


def _terminal_progress_delta_classification_source(
    paper_stage_log: Mapping[str, Any],
    *,
    infer_from_surfaces: bool = True,
) -> str | None:
    if _text(paper_stage_log.get("progress_delta_classification")) is not None:
        return "explicit"
    explicit_source = _text(paper_stage_log.get("progress_delta_classification_source"))
    if explicit_source is not None:
        return explicit_source
    if not infer_from_surfaces:
        return None
    if _text_list(paper_stage_log.get("changed_paper_surfaces")):
        return "inferred_from_changed_paper_surfaces"
    if _text_list(paper_stage_log.get("changed_stage_surfaces")):
        return "inferred_from_changed_stage_surfaces"
    return None


def _missing_telemetry_fields(latest_terminal_stage_log: Mapping[str, Any]) -> list[str]:
    explicit = _text_list(latest_terminal_stage_log.get("missing_observability_fields"))
    if explicit:
        return explicit
    return [
        field
        for field in TERMINAL_CLOSEOUT_TELEMETRY_FIELDS
        if not _mapping(latest_terminal_stage_log.get(field))
    ]


def _user_stage_log_field_missing(paper_stage_log: Mapping[str, Any], field: str) -> bool:
    if field not in paper_stage_log:
        return True
    if field in {"changed_stage_surfaces", "changed_paper_surfaces"}:
        return False
    value = paper_stage_log.get(field)
    return value in (None, "", [], {})


def _field_presence_status(paper_stage_log: Mapping[str, Any], field: str) -> str:
    if field not in paper_stage_log:
        return "missing"
    values = _text_list(paper_stage_log.get(field))
    return "present" if values else "present_empty"


def _stage_semantic_completeness(paper_stage_log: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "stage_name",
        "problem_summary",
        "stage_goal",
        "stage_work_done",
        "changed_stage_surfaces",
        "outcome",
        "remaining_blockers",
        "evidence_refs",
    )
    aliases = {
        "stage_work_done": ("stage_work_done", "paper_work_done"),
        "changed_stage_surfaces": ("changed_stage_surfaces", "changed_paper_surfaces"),
    }
    missing = [
        field
        for field in required_fields
        if not _has_stage_semantic_field(paper_stage_log, aliases.get(field, (field,)))
    ]
    return {
        "status": "complete" if not missing else "missing_required_fields",
        "required_fields": list(required_fields),
        "missing_fields": missing,
    }


def _stage_telemetry_completeness(latest_terminal_stage_log: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = ("duration", "token_usage", "cost")
    missing = [field for field in required_fields if not _mapping(latest_terminal_stage_log.get(field))]
    return {
        "status": "complete" if not missing else "missing_required_fields",
        "required_fields": list(required_fields),
        "missing_fields": missing,
    }


def _has_stage_semantic_field(payload: Mapping[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        if key in {"changed_stage_surfaces", "changed_paper_surfaces", "remaining_blockers"} and key in payload:
            return True
        value = payload.get(key)
        if _text(value) is not None:
            return True
        if _text_list(value):
            return True
    return False

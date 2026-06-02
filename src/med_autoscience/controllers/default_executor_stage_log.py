from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def paper_stage_log_for_default_executor_execution(
    *,
    study_id: str,
    action_type: str,
    next_executable_owner: str | None,
    required_output_surface: str | None,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    owner_result = _mapping(execution.get("owner_result"))
    repair_evidence = _mapping(owner_result.get("repair_execution_evidence"))
    status = _text(execution.get("execution_status")) or _text(owner_result.get("status"))
    blocked_reason = (
        _text(execution.get("typed_blocker"))
        or _text(execution.get("blocked_reason"))
        or _text(owner_result.get("blocked_reason"))
        or _first_text(_string_list(repair_evidence.get("blockers")))
        or _first_text(_string_list(_mapping(repair_evidence.get("manuscript_surface_hygiene")).get("blockers")))
    )
    changed_surfaces = _changed_paper_surfaces(owner_result=owner_result, repair_evidence=repair_evidence)
    stage_work_done = _paper_work_done(
        status=status,
        owner_result=owner_result,
        repair_evidence=repair_evidence,
        changed_surfaces=changed_surfaces,
    )
    duration = _duration_observability(execution)
    token_usage = _token_usage_observability(execution)
    cost = _cost_observability(execution)
    next_forced_delta = _next_forced_delta(
        action_type=action_type,
        next_executable_owner=next_executable_owner,
        required_output_surface=required_output_surface,
        dispatch=dispatch,
        changed_surfaces=changed_surfaces,
        blocked_reason=blocked_reason,
    )
    return {
        "surface_kind": "mas_paper_facing_stage_log_summary",
        "schema_version": 1,
        "status": "available",
        "stage_name": _stage_name(action_type=action_type, dispatch=dispatch),
        "current_owner": next_executable_owner,
        "problem_summary": _problem_summary(
            action_type=action_type,
            required_output_surface=required_output_surface,
            blocked_reason=blocked_reason,
        ),
        "stage_goal": _stage_goal(
            action_type=action_type,
            required_output_surface=required_output_surface,
            dispatch=dispatch,
        ),
        "stage_work_done": stage_work_done,
        "paper_work_done": stage_work_done,
        "changed_stage_surfaces": changed_surfaces,
        "changed_paper_surfaces": changed_surfaces,
        "outcome": _outcome(status=status, blocked_reason=blocked_reason, owner_result=owner_result),
        "remaining_blockers": _remaining_blockers(blocked_reason=blocked_reason, repair_evidence=repair_evidence),
        "duration": duration,
        "token_usage": token_usage,
        "cost": cost,
        "usage_refs": _usage_refs(execution=execution),
        "cost_refs": _cost_refs(execution=execution),
        **_progress_delta_projection(
            execution=execution,
            changed_surfaces=changed_surfaces,
            next_forced_delta=next_forced_delta,
        ),
        "evidence_refs": _evidence_refs(
            study_id=study_id,
            dispatch_path=dispatch_path,
            dispatch=dispatch,
            execution=execution,
            owner_result=owner_result,
            repair_evidence=repair_evidence,
        ),
        "language_boundary": _language_boundary(),
        "authority": _authority(),
    }


def _progress_delta_projection(
    *,
    execution: Mapping[str, Any],
    changed_surfaces: list[str],
    next_forced_delta: Mapping[str, Any],
) -> dict[str, Any]:
    if _mapping(execution.get("anti_loop_budget")):
        return {
            "progress_delta_classification": "typed_blocker",
            "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
            "paper_progress_delta": {"count": 0, "token_usage_total": 0},
            "platform_repair_delta": {"count": 0, "token_usage_total": 0},
            "next_forced_delta": dict(next_forced_delta),
        }
    total_tokens = _token_usage_total(execution)
    if changed_surfaces:
        deliverable_delta = {"count": 1, "token_usage_total": total_tokens}
        return {
            "progress_delta_classification": "deliverable_progress",
            "deliverable_progress_delta": deliverable_delta,
            "paper_progress_delta": deliverable_delta,
            "platform_repair_delta": {"count": 0, "token_usage_total": 0},
            "next_forced_delta": dict(next_forced_delta),
        }
    if _platform_repair_delta(execution):
        return {
            "progress_delta_classification": "platform_repair",
            "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
            "paper_progress_delta": {"count": 0, "token_usage_total": 0},
            "platform_repair_delta": {"count": 1, "token_usage_total": total_tokens},
            "next_forced_delta": dict(next_forced_delta),
        }
    return {
        "progress_delta_classification": "typed_blocker",
        "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
        "paper_progress_delta": {"count": 0, "token_usage_total": 0},
        "platform_repair_delta": {"count": 0, "token_usage_total": 0},
        "next_forced_delta": dict(next_forced_delta),
    }


def _next_forced_delta(
    *,
    action_type: str,
    next_executable_owner: str | None,
    required_output_surface: str | None,
    dispatch: Mapping[str, Any],
    changed_surfaces: list[str],
    blocked_reason: str | None,
) -> dict[str, Any]:
    source_action = _mapping(dispatch.get("source_action"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    work_unit_id = (
        _text(source_action.get("executable_work_unit"))
        or _text(source_action.get("controller_work_unit_id"))
        or _work_unit_id(source_action.get("next_work_unit"))
        or _work_unit_id(prompt_contract.get("next_work_unit"))
        or _text(owner_route.get("work_unit_id"))
        or _text(_mapping(owner_route.get("source_refs")).get("work_unit_id"))
        or action_type
    )
    target_surface = (
        required_output_surface
        or _text(prompt_contract.get("required_output_surface"))
        or _text(owner_route.get("target_surface"))
        or _text(owner_route.get("next_forced_target_surface"))
        or "owner_authorized_output_surface_or_typed_blocker"
    )
    required_delta_kind = "paper_progress_delta_or_typed_blocker"
    if changed_surfaces:
        reason = "deliverable_progress_observed_next_quality_or_blocker_required"
    elif blocked_reason:
        reason = f"typed_blocker::{blocked_reason}"
    else:
        reason = "no_deliverable_delta_observed"
    return {
        "required_delta_kind": required_delta_kind,
        "work_unit_id": work_unit_id,
        "target_surface": {"surface_ref": target_surface},
        "owner_action": {
            "next_owner": next_executable_owner or _text(owner_route.get("next_owner")),
            "action_type": action_type,
            "work_unit_id": work_unit_id,
        },
        "acceptance_refs": ["owner_receipt_ref", "typed_blocker_ref", "changed_surface_ref"],
        "reason": reason,
    }


def _token_usage_total(execution: Mapping[str, Any]) -> int:
    for value in (_token_usage_observability(execution), _observability_mapping(execution.get("usage"))):
        total = _first_number_value(
            value.get("total_tokens"),
            value.get("total"),
            value.get("token_total"),
        )
        if total is not None:
            return int(total)
        partial = _sum_number_values(
            value.get("input_tokens"),
            value.get("cached_input_tokens"),
            value.get("output_tokens"),
            value.get("reasoning_tokens"),
        )
        if partial is not None:
            return int(partial)
    return 0


def _sum_number_values(*values: object) -> int | float | None:
    total: int | float = 0
    observed = False
    for value in values:
        number = _number_value(value)
        if number is None:
            continue
        total += number
        observed = True
    return total if observed else None


def _platform_repair_delta(execution: Mapping[str, Any]) -> bool:
    reason_blob = " ".join(
        text
        for text in (
            _text(execution.get("blocked_reason")),
            _text(execution.get("why_not_applied")),
            *_string_list(_mapping(execution.get("paper_stage_log")).get("remaining_blockers")),
        )
        if text is not None
    ).lower()
    return any(
        token in reason_blob
        for token in (
            "runtime_recovery",
            "currentness",
            "controller",
            "read_model",
            "provider",
            "opl_stage_attempt_admission_required",
        )
    )


def _stage_name(*, action_type: str, dispatch: Mapping[str, Any]) -> str:
    source_action = _mapping(dispatch.get("source_action"))
    work_unit = (
        _text(source_action.get("executable_work_unit"))
        or _text(source_action.get("controller_work_unit_id"))
        or _work_unit_id(source_action.get("next_work_unit"))
    )
    if work_unit:
        return work_unit
    return action_type


def _problem_summary(*, action_type: str, required_output_surface: str | None, blocked_reason: str | None) -> str:
    if blocked_reason:
        return f"{action_type} ended with typed blocker {blocked_reason}."
    if required_output_surface:
        return f"{action_type} was dispatched to produce {required_output_surface}."
    return f"{action_type} was dispatched by the MAS owner route."


def _stage_goal(*, action_type: str, required_output_surface: str | None, dispatch: Mapping[str, Any]) -> str:
    source_action = _mapping(dispatch.get("source_action"))
    if summary := _text(_mapping(source_action.get("next_work_unit")).get("summary")):
        return summary
    if required_output_surface:
        return f"Produce the owner-authorized output surface: {required_output_surface}."
    return f"Complete the owner-authorized {action_type} work unit."


def _paper_work_done(
    *,
    status: str | None,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
    changed_surfaces: list[str],
) -> list[str]:
    explicit = _string_list(owner_result.get("paper_work_done"))
    if explicit:
        return explicit
    work_done: list[str] = []
    if changed_surfaces:
        work_done.append("Recorded paper-facing artifact changes.")
    if repair_evidence.get("evidence_ledger_update_done") is True:
        work_done.append("Updated the evidence ledger.")
    if repair_evidence.get("review_ledger_update_done") is True:
        work_done.append("Updated the review ledger.")
    if repair_evidence.get("ai_reviewer_recheck_done") is True:
        work_done.append("Recorded an AI reviewer recheck request.")
    if not work_done and status in {"blocked", "repeat_suppressed"}:
        work_done.append("Recorded a typed owner blocker without claiming paper readiness.")
    if not work_done and status:
        work_done.append(f"Recorded owner execution status: {status}.")
    return work_done


def _observability_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _number_value(value: object) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = float(text)
        except ValueError:
            return None
        return int(parsed) if parsed.is_integer() else parsed
    return None


def _first_number_value(*values: object) -> int | float | None:
    for value in values:
        number = _number_value(value)
        if number is not None:
            return number
    return None


def _duration_observability(execution: Mapping[str, Any]) -> dict[str, Any]:
    duration = _observability_mapping(execution.get("duration"))
    if duration:
        return duration
    seconds = _first_number_value(
        execution.get("duration_seconds"),
        execution.get("elapsed_seconds"),
        execution.get("runtime_duration_seconds"),
    )
    return {"seconds": seconds} if seconds is not None else {}


def _token_usage_observability(execution: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("token_usage", "usage", "tokenUsage"):
        usage = _observability_mapping(execution.get(key))
        if usage:
            return usage
    return {}


def _cost_observability(execution: Mapping[str, Any]) -> dict[str, Any]:
    cost = _observability_mapping(execution.get("cost"))
    if cost:
        return cost
    usd = _first_number_value(execution.get("cost_usd"), execution.get("usd_cost"))
    return {"usd": usd} if usd is not None else {}


def _refs_from_unknown(value: object) -> list[str]:
    if isinstance(value, Mapping):
        return [
            text
            for candidate in (
                value.get("ref"),
                value.get("ref_id"),
                value.get("path"),
                value.get("uri"),
            )
            if (text := _text(candidate)) is not None
        ]
    if isinstance(value, list | tuple | set):
        refs: list[str] = []
        for item in value:
            refs.extend(_refs_from_unknown(item))
        return refs
    if text := _text(value):
        return [text]
    return []


def _usage_refs(*, execution: Mapping[str, Any]) -> list[str]:
    refs = [
        *_refs_from_unknown(execution.get("usage_ref")),
        *_refs_from_unknown(execution.get("usage_refs")),
        *_refs_from_unknown(execution.get("token_usage_ref")),
        *_refs_from_unknown(execution.get("token_usage_refs")),
        *_refs_from_unknown(_observability_mapping(execution.get("token_usage")).get("source_refs")),
        *_refs_from_unknown(_observability_mapping(execution.get("usage")).get("source_refs")),
    ]
    request_path = _text(execution.get("request_path"))
    if request_path and (_duration_observability(execution) or _token_usage_observability(execution)):
        refs.append(f"{request_path}#usage")
    return _unique_texts(refs)


def _cost_refs(*, execution: Mapping[str, Any]) -> list[str]:
    refs = [
        *_refs_from_unknown(execution.get("cost_ref")),
        *_refs_from_unknown(execution.get("cost_refs")),
        *_refs_from_unknown(_observability_mapping(execution.get("cost")).get("source_refs")),
    ]
    request_path = _text(execution.get("request_path"))
    if request_path and _cost_observability(execution):
        refs.append(f"{request_path}#cost")
    return _unique_texts(refs)


def _changed_paper_surfaces(
    *,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> list[str]:
    canonical_delta = _mapping(repair_evidence.get("canonical_artifact_delta"))
    refs = [
        *_string_list(owner_result.get("changed_paper_surfaces")),
        *_paths_from_ref_dicts(owner_result.get("changed_artifact_refs")),
        *_paths_from_ref_dicts(repair_evidence.get("changed_artifact_refs")),
        *_paths_from_ref_dicts(canonical_delta.get("artifact_refs")),
        _text(repair_evidence.get("evidence_ledger_ref")),
        _text(repair_evidence.get("review_ledger_ref")),
    ]
    return _unique_texts(refs)


def _outcome(*, status: str | None, blocked_reason: str | None, owner_result: Mapping[str, Any]) -> str | None:
    if status == "blocked" and blocked_reason:
        return f"blocked:{blocked_reason}"
    if status:
        return status
    return _text(owner_result.get("status"))


def _remaining_blockers(*, blocked_reason: str | None, repair_evidence: Mapping[str, Any]) -> list[str]:
    blockers = [
        blocked_reason,
        *_string_list(repair_evidence.get("blockers")),
        *_string_list(_mapping(repair_evidence.get("manuscript_surface_hygiene")).get("blockers")),
    ]
    return _unique_texts(blockers)


def _evidence_refs(
    *,
    study_id: str,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
    execution: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> list[str]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    refs = [
        _workspace_or_study_ref(dispatch_path, study_id=study_id),
        f"{_workspace_or_study_ref(dispatch_path, study_id=study_id)}#prompt_contract",
        _text(owner_result.get("record_path")),
        _text(repair_evidence.get("evidence_ledger_ref")),
        _text(repair_evidence.get("review_ledger_ref")),
        _text(repair_evidence.get("ai_reviewer_recheck_request_ref")),
        _text(_mapping(dispatch.get("refs")).get("scan_latest")),
        _text(prompt_contract.get("request_packet_ref")),
        _text(execution.get("request_path")),
        *_string_list(execution.get("evidence_refs")),
        *_string_list(owner_result.get("evidence_refs")),
        *_string_list(repair_evidence.get("source_refs")),
    ]
    return _unique_texts(refs)


def _workspace_or_study_ref(path: Path, *, study_id: str) -> str:
    parts = path.parts
    if "studies" in parts:
        index = parts.index("studies")
        return str(Path(*parts[index:]))
    if path.is_absolute():
        return str(path)
    return str(Path("studies") / study_id / path)


def _authority() -> dict[str, Any]:
    return {
        "kind": "read_only_paper_facing_stage_log_projection",
        "writes_authority_surface": False,
        "truth_owner": "MedAutoScience",
        "can_write_paper": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
    }


def _language_boundary() -> dict[str, Any]:
    return {
        "paper_body_included": False,
        "paper_body_target": False,
        "internal_review_language_allowed_in_paper_body": False,
        "summary_scope": "stage_log_read_model_only",
    }


def _work_unit_id(value: object) -> str | None:
    mapped = _mapping(value)
    return _text(mapped.get("unit_id")) or _text(mapped.get("work_unit_id")) or _text(value)


def _paths_from_ref_dicts(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    paths: list[str] = []
    for item in value:
        mapped = _mapping(item)
        if path := _text(mapped.get("path")):
            paths.append(path)
        elif text := _text(item):
            paths.append(text)
    return paths


def _unique_texts(values: list[str | None]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text is not None and text not in result:
            result.append(text)
    return result


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _first_text(value: list[str]) -> str | None:
    return value[0] if value else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["paper_stage_log_for_default_executor_execution"]

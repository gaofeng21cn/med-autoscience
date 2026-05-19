from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.publication_eval_reviewer_os import (
    current_ai_reviewer_route_back_action,
    validate_ai_reviewer_operating_system_trace,
)


def project_transition(
    *,
    study_id: str,
    publication_eval: Mapping[str, Any],
    active_run_id: str | None,
    publication_eval_relative_path: Path,
    source_refs: Iterable[str],
    completion_receipt_consumption: Mapping[str, Any],
) -> dict[str, Any] | None:
    route_back_action = current_ai_reviewer_route_back_action(publication_eval)
    if route_back_action is not None:
        return _route_back_transition(
            study_id=study_id,
            action=route_back_action,
            active_run_id=active_run_id,
            publication_eval_relative_path=publication_eval_relative_path,
            source_refs=source_refs,
            completion_receipt_consumption=completion_receipt_consumption,
        )
    if _requires_ai_reviewer_re_eval(publication_eval):
        return _transition(
            study_id=study_id,
            decision_type="ai_reviewer_re_eval",
            route_target="review",
            next_work_unit=_ai_reviewer_re_eval_work_unit(publication_eval),
            controller_action="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            typed_blocker=None,
            guard_boundary=_guard_boundary(required_owner_surface=str(publication_eval_relative_path)),
            source_refs=source_refs,
            completion_receipt_consumption=completion_receipt_consumption,
        )
    return None


def _route_back_transition(
    *,
    study_id: str,
    action: Mapping[str, Any],
    active_run_id: str | None,
    publication_eval_relative_path: Path,
    source_refs: Iterable[str],
    completion_receipt_consumption: Mapping[str, Any],
) -> dict[str, Any]:
    if active_run_id:
        return _transition(
            study_id=study_id,
            decision_type="active_runtime_watch",
            route_target="runtime",
            next_work_unit=_work_unit("watch_active_run", "runtime", "Watch the active MAS runtime run."),
            controller_action="runtime_watch",
            owner="mas_runtime",
            typed_blocker=None,
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=True),
            source_refs=source_refs,
            completion_receipt_consumption=completion_receipt_consumption,
        )
    route_target = _text(action.get("route_target")) or "write"
    next_work_unit = _compact_work_unit(action.get("next_work_unit")) or _work_unit(
        "publication_eval_route_back",
        route_target,
        "Route the current AI reviewer finding back to the specified same-line owner.",
    )
    return _transition(
        study_id=study_id,
        decision_type="route_back_same_line",
        route_target=route_target,
        next_work_unit=next_work_unit,
        controller_action="ensure_study_runtime",
        owner=route_target,
        typed_blocker=None,
        guard_boundary=_guard_boundary(required_owner_surface=str(publication_eval_relative_path)),
        source_refs=source_refs,
        completion_receipt_consumption=completion_receipt_consumption,
    )


def _requires_ai_reviewer_re_eval(publication_eval: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    return (
        _text(publication_eval.get("domain_ready_verdict")) == "ai_reviewer_re_eval"
        or (provenance.get("ai_reviewer_required") is True and _text(provenance.get("owner")) != "ai_reviewer")
        or _medical_prose_quality_unready(publication_eval)
        or _ai_reviewer_trace_invalid(publication_eval)
    )


def _medical_prose_quality_unready(publication_eval: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer" or provenance.get("ai_reviewer_required") is not False:
        return False
    quality_assessment = _mapping(publication_eval.get("quality_assessment"))
    if "medical_journal_prose_quality" not in quality_assessment:
        return False
    prose_quality = _mapping(quality_assessment.get("medical_journal_prose_quality"))
    return _text(prose_quality.get("status")) != "ready"


def _ai_reviewer_trace_invalid(publication_eval: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer" or provenance.get("ai_reviewer_required") is not False:
        return False
    quality_assessment = _mapping(publication_eval.get("quality_assessment"))
    prose_quality = _mapping(quality_assessment.get("medical_journal_prose_quality"))
    if _text(prose_quality.get("status")) != "ready":
        return False
    return bool(validate_ai_reviewer_operating_system_trace(publication_eval.get("reviewer_operating_system")))


def _ai_reviewer_re_eval_work_unit(publication_eval: Mapping[str, Any]) -> dict[str, str]:
    if _medical_prose_quality_unready(publication_eval) or _ai_reviewer_trace_invalid(publication_eval):
        return _work_unit(
            "ai_reviewer_medical_prose_quality_review",
            "review",
            "Re-run AI reviewer manuscript-quality review and close medical_journal_prose_quality currentness before finalize.",
        )
    return _work_unit("ai_reviewer_recheck", "review", "Return the current manuscript and evidence refs to the AI reviewer workflow.")


def _transition(
    *,
    study_id: str,
    decision_type: str,
    route_target: str,
    next_work_unit: Mapping[str, Any],
    controller_action: str,
    owner: str,
    typed_blocker: Mapping[str, Any] | None,
    guard_boundary: Mapping[str, Any],
    source_refs: Iterable[str],
    completion_receipt_consumption: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "study_id": study_id,
        "decision_type": decision_type,
        "route_target": route_target,
        "next_work_unit": dict(next_work_unit),
        "controller_action": controller_action,
        "owner": owner,
        "typed_blocker": dict(typed_blocker) if typed_blocker else None,
        "guard_boundary": dict(guard_boundary),
        "source_refs": list(source_refs),
    }
    if completion_receipt_consumption:
        payload["completion_receipt_consumption"] = dict(completion_receipt_consumption)
    return payload


def _work_unit(unit_id: str, lane: str, summary: str) -> dict[str, str]:
    return {"unit_id": unit_id, "lane": lane, "summary": summary}


def _guard_boundary(
    *,
    required_owner_surface: str | None = None,
    opl_generic_runner_may_resume: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "runner_boundary": "mas_domain_read_model_only",
        "can_write_domain_truth": False,
        "can_execute_generic_state_machine": False,
        "opl_generic_runner_may_resume": opl_generic_runner_may_resume,
        "mas_owner_apply_receipt_required": False,
    }
    if required_owner_surface:
        payload["required_owner_surface"] = required_owner_surface
    return payload


def _compact_work_unit(value: object) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    unit_id = _text(value.get("unit_id"))
    if not unit_id:
        return None
    payload = {"unit_id": unit_id}
    for key in ("lane", "summary"):
        text = _text(value.get(key))
        if text:
            payload[key] = text
    return payload


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["project_transition"]

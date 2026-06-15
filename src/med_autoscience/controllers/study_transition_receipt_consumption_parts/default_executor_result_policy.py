from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


_DEFAULT_EXECUTOR_CONSUMABLE_OWNER_RESULT_STATUSES = frozenset({"executed", "applied", "ok"})
_DEFAULT_EXECUTOR_CONSUMABLE_REPAIR_EVIDENCE_STATUSES = frozenset(
    {
        "progress_delta_candidate",
        "executed",
        "applied",
    }
)


def default_executor_owner_result_consumable(
    *,
    action_type: str | None,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> bool:
    if default_executor_dispatch_zero_execution_blocker(owner_result):
        return False
    if _current_manuscript_digest_mismatch(owner_result=owner_result, repair_evidence=repair_evidence):
        return False
    if action_type == "return_to_ai_reviewer_workflow":
        return _ai_reviewer_workflow_owner_result_satisfies_route_output(
            owner_result=owner_result
        ) or _ai_reviewer_record_only_owner_receipt_satisfies_route_output(owner_result=owner_result)
    if action_type == "run_quality_repair_batch":
        return _quality_repair_batch_owner_result_satisfies_route_output(
            owner_result=owner_result,
            repair_evidence=repair_evidence,
        )
    if action_type == "run_gate_clearing_batch" and _text(owner_result.get("blocked_reason")):
        return True
    if action_type == "publication_gate_specificity_required":
        return publication_gate_specificity_owner_result_satisfies_route_output(owner_result=owner_result)
    if owner_result.get("ok") is True:
        return True
    if _text(owner_result.get("status")) in _DEFAULT_EXECUTOR_CONSUMABLE_OWNER_RESULT_STATUSES:
        return True
    if _text(repair_evidence.get("status")) in _DEFAULT_EXECUTOR_CONSUMABLE_REPAIR_EVIDENCE_STATUSES:
        return True
    return bool(_mapping_list(repair_evidence.get("changed_artifact_refs")))


def publication_gate_specificity_owner_result_satisfies_route_output(*, owner_result: Mapping[str, Any]) -> bool:
    if not _text(owner_result.get("report_json")):
        return False
    publication_eval = _mapping(owner_result.get("publication_eval"))
    if not _text(publication_eval.get("eval_id")):
        return False
    return _is_publication_eval_latest_path(_text(publication_eval.get("artifact_path")))


def default_executor_dispatch_zero_execution_blocker(owner_result: Mapping[str, Any]) -> bool:
    dispatcher_result = _mapping(owner_result.get("dispatcher_result"))
    if not dispatcher_result:
        return False
    execution_count = dispatcher_result.get("execution_count")
    if execution_count not in {0, "0"}:
        return False
    blocked_reason = _text(owner_result.get("blocked_reason"))
    blocked_reasons = _string_set(owner_result.get("blocked_reasons"))
    dispatch_reason = _text(dispatcher_result.get("reason"))
    return (
        blocked_reason == "domain_owner_action_dispatch_execution_count_zero"
        or "domain_owner_action_dispatch_execution_count_zero" in blocked_reasons
        or "run_quality_repair_batch_not_visible_in_current_opl_control_state" in blocked_reasons
        or "no current executable" in dispatch_reason
    )


def default_executor_consumed_blocked_reason(
    *,
    action_type: str | None,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> str | None:
    if action_type == "run_gate_clearing_batch" and _gate_replay_blocked(owner_result):
        return "publication_gate_replay_blocked"
    if action_type == "run_quality_repair_batch":
        if "manuscript_story_surface_delta_missing" in _string_set(repair_evidence.get("blockers")):
            return "manuscript_story_surface_delta_missing"
        hygiene = _mapping(repair_evidence.get("manuscript_surface_hygiene"))
        if "manuscript_story_surface_delta_missing" in _string_set(hygiene.get("blockers")):
            return "manuscript_story_surface_delta_missing"
        if (
            hygiene.get("story_surface_delta_required") is True
            and hygiene.get("story_surface_delta_present") is not True
            and _text(owner_result.get("status")) == "blocked"
        ):
            return "manuscript_story_surface_delta_missing"
    return _text(owner_result.get("blocked_reason")) or _text(repair_evidence.get("blocked_reason")) or None


def gate_replay_blockers(owner_result: Mapping[str, Any]) -> list[str]:
    gate_replay = _mapping(owner_result.get("gate_replay"))
    blockers = _string_items(gate_replay.get("blockers"))
    if blockers:
        return blockers
    return _string_items(owner_result.get("gate_blockers"))


def gate_replay_blocker_fields(owner_result: Mapping[str, Any]) -> dict[str, Any]:
    if not _gate_replay_blocked(owner_result):
        return {}
    blockers = gate_replay_blockers(owner_result)
    return {
        key: value
        for key, value in {
            "gate_replay_status": "blocked",
            "gate_replay_blockers": blockers,
            "publication_gate_report_ref": _text(_mapping(owner_result.get("gate_replay")).get("report_json")),
        }.items()
        if value not in ("", [], None)
    }


def _gate_replay_blocked(owner_result: Mapping[str, Any]) -> bool:
    gate_replay = _mapping(owner_result.get("gate_replay"))
    lifecycle = _mapping(owner_result.get("publication_work_unit_lifecycle"))
    return (
        _text(gate_replay.get("status")) == "blocked"
        or _text(owner_result.get("gate_replay_status")) == "blocked"
        or _text(lifecycle.get("gate_replay_status")) == "blocked"
    )


def _current_manuscript_digest_mismatch(
    *,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> bool:
    blocked_reasons = _string_set(owner_result.get("blocked_reasons"))
    blocked_reasons.add(_text(owner_result.get("blocked_reason")))
    blocked_reasons.add(_text(repair_evidence.get("blocked_reason")))
    return "quality_repair_batch_current_manuscript_digest_mismatch" in blocked_reasons


def _ai_reviewer_workflow_owner_result_satisfies_route_output(*, owner_result: Mapping[str, Any]) -> bool:
    eval_id = _text(owner_result.get("eval_id"))
    if not eval_id:
        return False
    artifact_path = _text(owner_result.get("artifact_path"))
    if not _is_publication_eval_latest_path(artifact_path):
        return False
    publication_eval_surface = _text(owner_result.get("publication_eval_surface"))
    if publication_eval_surface and publication_eval_surface != "artifacts/publication_eval/latest.json":
        return False
    if not _mapping(owner_result.get("reviewer_operating_system")):
        return False
    refresh = _mapping(owner_result.get("controller_decision_refresh"))
    return _text(refresh.get("refresh_status")) == "materialized"


def _ai_reviewer_record_only_owner_receipt_satisfies_route_output(*, owner_result: Mapping[str, Any]) -> bool:
    if _text(owner_result.get("owner")) != "ai_reviewer":
        return False
    if not _text(owner_result.get("owner_receipt_ref")):
        return False
    if not _text(owner_result.get("publication_eval_record_ref")):
        return False
    if owner_result.get("record_only_surface") is not True:
        return False
    if _text(owner_result.get("publication_eval_surface")) != "not_written":
        return False
    if owner_result.get("publication_eval_latest_write_authorized") is not False:
        return False
    if owner_result.get("controller_decision_write_authorized") is not False:
        return False
    return _text(owner_result.get("status")) in {
        "closed_with_domain_owner_refs",
        "owner_receipt",
    }


def _quality_repair_batch_owner_result_satisfies_route_output(
    *,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> bool:
    if _text(owner_result.get("status")) == "handoff_ready" and _mapping(owner_result.get("writer_worker_handoff")):
        return True
    if "manuscript_story_surface_delta_missing" in _string_set(repair_evidence.get("blockers")):
        return True
    if _text(owner_result.get("blocked_reason")) == "manuscript_story_surface_delta_missing":
        return True
    hygiene = _mapping(repair_evidence.get("manuscript_surface_hygiene"))
    if "manuscript_story_surface_delta_missing" in _string_set(hygiene.get("blockers")):
        return True
    if hygiene.get("story_surface_delta_required") is True:
        return hygiene.get("story_surface_delta_present") is True
    return bool(_story_surface_changed_refs(repair_evidence.get("changed_artifact_refs")))


def _story_surface_changed_refs(value: object) -> list[Mapping[str, Any]]:
    return [
        ref
        for ref in _mapping_list(value)
        if (parts := Path(_text(ref.get("path"))).expanduser().parts)
        and (parts[-2:] == ("paper", "draft.md") or parts[-3:] == ("paper", "build", "review_manuscript.md"))
    ]


def _is_publication_eval_latest_path(path_text: str) -> bool:
    if not path_text:
        return False
    path = Path(path_text).expanduser()
    return path.parts[-3:] == ("artifacts", "publication_eval", "latest.json")


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item))]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        text = _text(value)
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _text(item))}

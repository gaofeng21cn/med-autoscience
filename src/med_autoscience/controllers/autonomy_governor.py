from __future__ import annotations

from typing import Any, Mapping


_QUALITY_AUTHORITY_SURFACES = [
    "study_charter",
    "evidence_ledger",
    "review_ledger",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _autonomy_slo(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(profile_payload.get("autonomy_slo"))


def _runtime_failure(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_autonomy_slo(profile_payload).get("runtime_failure_classification"))


def _slo_execution_plan(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_autonomy_slo(profile_payload).get("slo_execution_plan"))


def _quality_constraint(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_autonomy_slo(profile_payload).get("quality_constraint"))


def _quality_ledger_enforcement(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(profile_payload.get("quality_ledger_enforcement"))


def _fast_lane_manifest(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(profile_payload.get("fast_lane_execution_manifest"))


def _first_step(execution_plan: Mapping[str, Any]) -> dict[str, Any]:
    for step in _list(execution_plan.get("steps")):
        if isinstance(step, Mapping):
            return dict(step)
    return {}


def _authority_surfaces(profile_payload: Mapping[str, Any]) -> list[str]:
    surfaces = [
        surface
        for item in _list(_quality_constraint(profile_payload).get("must_preserve_authority_surfaces"))
        if (surface := _text(item)) is not None
    ]
    return surfaces or list(_QUALITY_AUTHORITY_SURFACES)


def _quality_floor(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    enforcement = _quality_ledger_enforcement(profile_payload)
    return {
        "gate_relaxation_allowed": False,
        "authority_surfaces": _authority_surfaces(profile_payload),
        "ledger_enforcement_state": _text(enforcement.get("enforcement_state")) or "not_evaluated",
    }


def _state_and_owner(
    *,
    runtime_failure: Mapping[str, Any],
    execution_plan: Mapping[str, Any],
    quality_enforcement: Mapping[str, Any],
    fast_lane_manifest: Mapping[str, Any],
) -> tuple[str, str, bool, bool]:
    action_mode = _text(runtime_failure.get("action_mode"))
    blocker_class = _text(runtime_failure.get("blocker_class"))
    plan_state = _text(execution_plan.get("state"))
    fast_lane_allowed = _bool(quality_enforcement.get("fast_lane_allowed"))
    manifest_state = _text(fast_lane_manifest.get("manifest_state"))
    if action_mode in {"external_fix_required", "provider_backoff_and_recheck"}:
        return "blocked_external_runtime", "external_runtime_or_human", False, True
    if action_mode == "platform_repair_required" or blocker_class == "platform_protocol_or_runner_bug":
        return "blocked_platform_repair", "mas_mds_platform_repair", False, True
    if action_mode == "wait_for_user_or_explicit_resume":
        return "blocked_human_gate", "human", False, True
    if plan_state == "blocked_by_runtime_gate":
        return "blocked_runtime_gate", "mas_controller", False, True
    if plan_state == "ready_for_controller_execution":
        if fast_lane_allowed is False:
            return "blocked_quality_floor", "mas_quality_gate", False, False
        if fast_lane_allowed is True and manifest_state not in {None, "ready", "not_required"}:
            return "blocked_fast_lane_manifest", "mas_controller", False, False
        return "dispatch_controller_fast_lane", "mas_controller", True, False
    return "monitor_only", "mas_controller", False, False


def build_autonomy_governor_decision(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime_failure = _runtime_failure(profile_payload)
    execution_plan = _slo_execution_plan(profile_payload)
    quality_enforcement = _quality_ledger_enforcement(profile_payload)
    fast_lane_manifest = _fast_lane_manifest(profile_payload)
    governor_state, next_step_owner, auto_dispatch_allowed, requires_human_or_external_fix = _state_and_owner(
        runtime_failure=runtime_failure,
        execution_plan=execution_plan,
        quality_enforcement=quality_enforcement,
        fast_lane_manifest=fast_lane_manifest,
    )
    next_control_action = _first_step(execution_plan)
    replay_case = _mapping(profile_payload.get("study_soak_replay_case"))
    return {
        "surface": "mas_autonomy_governor",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "governor_state": governor_state,
        "owner_boundary": {
            "product_owner": "MedAutoScience",
            "runtime_backend": "MedDeepScientist",
            "mds_role": "migration_runtime_oracle_only",
        },
        "execution_permission": {
            "auto_dispatch_allowed": auto_dispatch_allowed,
            "requires_human_or_external_fix": requires_human_or_external_fix,
            "gate_relaxation_allowed": False,
            "paper_body_edit_allowed": False,
        },
        "next_control_action": next_control_action,
        "quality_floor": _quality_floor(profile_payload),
        "runtime_failure_classification": dict(runtime_failure),
        "fast_lane_manifest_state": _text(fast_lane_manifest.get("manifest_state")) or "not_provided",
        "soak_replay_case": {
            "case_family": _text(replay_case.get("case_family")),
            "required_truth_surfaces": list(_list(replay_case.get("required_truth_surfaces"))),
        },
        "operator_answer": {
            "what_is_blocking": _text(runtime_failure.get("blocker_class")) or governor_state,
            "who_owns_next_step": next_step_owner,
            "can_mas_continue_automatically": auto_dispatch_allowed,
        },
    }

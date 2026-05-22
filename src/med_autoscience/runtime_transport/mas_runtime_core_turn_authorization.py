from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_transition_currentness
from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers.owner_route_reconcile_parts import platform_current_controller
from med_autoscience.controllers.study_runtime_execution_parts.controller_authorization_context import (
    _load_controller_decision_authorization_context,
)
from med_autoscience.runtime_transport import mas_runtime_core_hard_methodology
from med_autoscience.runtime_transport import mas_runtime_core_turn_actions
from med_autoscience.runtime_transport import mas_runtime_core_turn_owner_handoff
from med_autoscience.runtime_transport import mas_runtime_core_turn_prompt
from med_autoscience.runtime_transport.mas_runtime_core_worker_env import (
    load_workspace_mas_config_env,
    workspace_root_from_quest_root,
)


def _codex_turn_prompt(
    *,
    quest_id: str,
    run_id: str,
    reason: str,
    claimed_user_messages: tuple[dict[str, Any], ...],
    runtime_state: Mapping[str, Any] | None = None,
    quest_root: Path | None = None,
) -> str:
    authorization = _controller_authorization(
        runtime_state,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    claimed_user_messages = mas_runtime_core_turn_prompt.claimed_messages_for_prompt(
        claimed_user_messages=claimed_user_messages,
        authorization=authorization,
    )
    messages = json.dumps(list(claimed_user_messages), ensure_ascii=False, indent=2, sort_keys=True)
    runtime_context = _resolved_runtime_context(
        authorization=authorization,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    authorization_section = mas_runtime_core_turn_prompt.controller_authorization_prompt_section(
        authorization=authorization,
        quest_id=quest_id,
        runtime_context=runtime_context,
    )
    closeout_path = f"artifacts/runtime/turn_closeouts/{run_id}.json"
    return (
        f"You are running a MAS runtime turn for quest `{quest_id}`.\n"
        f"Run id: `{run_id}`.\n"
        f"Turn reason: `{reason}`.\n\n"
        "Read the quest-local runtime files, continue the research workflow according to MAS contracts, "
        "and leave durable artifacts/receipts in the quest workspace. Do not bypass MAS quality gates.\n\n"
        "Runtime worker role:\n"
        "- This Codex process is the MAS managed runtime worker for this run. "
        "`execution_owner_guard.supervisor_only=true` protects foreground/manual agents from taking over a live run; "
        "it does not block this managed runtime worker from executing MAS-authorized quest-local work inside the stated "
        "quality and authority boundaries.\n"
        "- Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this runtime turn. "
        "If another control-plane gate blocks a specific write surface, produce the allowed durable repair artifact "
        "or a blocked closeout that names that non-supervisor gate precisely.\n\n"
        f"{authorization_section}"
        "Turn closeout contract:\n"
        f"- Before ending this turn, write `{closeout_path}`.\n"
        "- The closeout must be valid JSON with this shape:\n"
        "```json\n"
        "{\n"
        '  "schema_version": 1,\n'
        f'  "quest_id": "{quest_id}",\n'
        f'  "run_id": "{run_id}",\n'
        '  "status": "completed",\n'
        '  "completed_at": "<UTC ISO-8601 timestamp>",\n'
        '  "meaningful_artifact_delta": true,\n'
        '  "artifact_refs": ["relative/path/to/new-or-updated-durable-artifact"],\n'
        '  "blocked_reason": null,\n'
        '  "next_owner": null\n'
        "}\n"
        "```\n"
        "- If no safe meaningful artifact delta is possible, write a blocked closeout instead: set "
        '`"status": "blocked"`, `"meaningful_artifact_delta": false`, include a concrete `"blocked_reason"`, '
        'and set `"next_owner"` to the MAS/controller owner that must act next.\n'
        "- Do not exit silently with only console output; MAS treats a successful Codex process without this closeout as incomplete.\n"
        "- Do not mutate paper/current_package, manuscript/current_package, submission_minimal/current_package, "
        "publication gate conclusions, or medical claims unless an explicit MAS controller contract authorizes that surface.\n"
        "- Do not relax MAS quality gates, quality thresholds, publication gates, or authority boundaries.\n\n"
        f"Claimed user messages:\n```json\n{messages}\n```\n"
    )


def _resolved_runtime_context(
    *,
    authorization: Mapping[str, Any],
    quest_root: Path | None,
    quest_id: str,
) -> dict[str, str]:
    if quest_root is None:
        return {"quest_id": quest_id}
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    workspace_root = workspace_root_from_quest_root(resolved_quest_root)
    study_id = _text(authorization.get("study_id")) or _study_id_for_quest_root(
        quest_root=resolved_quest_root,
        quest_id=quest_id,
    )
    study_root = _resolve_study_root_from_quest_root_light(quest_root=resolved_quest_root, quest_id=study_id)
    env: dict[str, str] = {}
    load_workspace_mas_config_env(quest_root=resolved_quest_root, env=env)
    context: dict[str, str] = {
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "study_id": study_id,
    }
    if workspace_root is not None:
        context["workspace_root"] = str(workspace_root)
    if study_root is not None:
        context["study_root"] = str(study_root)
    med_repo = _text(env.get("MED_AUTOSCIENCE_REPO"))
    if med_repo is not None:
        context["med_autoscience_repo"] = med_repo
    profile = _text(env.get("MED_AUTOSCIENCE_PROFILE")) or _default_workspace_profile(workspace_root)
    if profile is not None:
        context["med_autoscience_profile"] = profile
    return context


def _default_workspace_profile(workspace_root: Path | None) -> str | None:
    if workspace_root is None:
        return None
    profile_root = workspace_root / "ops" / "medautoscience" / "profiles"
    for pattern in ("*.local.toml", "*.workspace.toml"):
        for path in sorted(profile_root.glob(pattern)):
            if path.is_file():
                return str(path.resolve())
    return None


def _read_runtime_state(*, quest_root: Path) -> dict[str, Any]:
    path = quest_root / ".ds" / "runtime_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _sanitize_runtime_state_before_turn(
    *,
    runtime_state: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping):
        return {}
    sanitized = dict(runtime_state)
    cleared_keys: list[str] = []
    for key in ("last_controller_decision_authorization", "current_controller_authorization"):
        value = sanitized.get(key)
        if not isinstance(value, Mapping):
            continue
        closed = _closed_publication_work_unit_for_authorization(
            authorization=dict(value),
            quest_root=quest_root,
            quest_id=quest_id,
        )
        if closed is None:
            continue
        sanitized.pop(key, None)
        cleared_keys.append(key)
    if not cleared_keys:
        return sanitized
    sanitized["quest_id"] = _text(sanitized.get("quest_id")) or quest_id
    sanitized["continuation_policy"] = "auto"
    sanitized["continuation_anchor"] = "decision"
    sanitized["continuation_reason"] = "closed_controller_work_unit_authorization_cleared"
    sanitized["continuation_updated_at"] = _utc_now()
    sanitized["same_fingerprint_auto_turn_count"] = 0
    sanitized["last_runtime_turn_state_sanitization"] = {
        "reason": "publication_work_unit_lifecycle_done",
        "cleared_keys": cleared_keys,
        "applied_at": _utc_now(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }
    _write_runtime_state(quest_root=quest_root, runtime_state=sanitized)
    return sanitized


def _sync_current_controller_authorization_for_turn(
    *,
    runtime_state: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
    run_id: str,
) -> dict[str, Any]:
    currentness = _materialize_fresh_domain_transition_controller_decision_for_turn(
        quest_root=quest_root,
        quest_id=quest_id,
    )
    owner_handoff_authorization = _blocked_closeout_owner_handoff_authorization(runtime_state)
    current_authorization = _current_controller_decision_authorization(
        quest_root=quest_root,
        quest_id=quest_id,
    )
    runtime_authorization = _runtime_state_downstream_authorization_after_provenance_limited_result(
        runtime_state=runtime_state,
        current_authorization=current_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    if runtime_authorization:
        updated = dict(runtime_state)
        authorization = _bind_authorization_to_turn(
            authorization=runtime_authorization,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
        )
        if _mapping(updated.get("current_controller_authorization")) == authorization:
            return updated
        updated["quest_id"] = _text(updated.get("quest_id")) or quest_id
        updated["current_controller_authorization"] = authorization
        updated["current_controller_authorization_synced_at"] = _utc_now()
        updated["current_controller_authorization_sync_status"] = "downstream_hard_methodology_authorization"
        if currentness is not None:
            updated["current_controller_authorization_currentness"] = currentness
        _write_runtime_state(quest_root=quest_root, runtime_state=updated)
        return updated
    if owner_handoff_authorization and not _owner_handoff_authorization_is_superseded(
        authorization=owner_handoff_authorization,
        current_authorization=current_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
    ):
        updated = dict(runtime_state)
        authorization = _bind_authorization_to_turn(
            authorization=owner_handoff_authorization,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
        )
        if _mapping(updated.get("current_controller_authorization")) == authorization:
            return updated
        updated["quest_id"] = _text(updated.get("quest_id")) or quest_id
        updated["current_controller_authorization"] = authorization
        updated["current_controller_authorization_synced_at"] = _utc_now()
        updated["current_controller_authorization_sync_status"] = "blocked_turn_closeout_owner_handoff"
        if currentness is not None:
            updated["current_controller_authorization_currentness"] = currentness
        _write_runtime_state(quest_root=quest_root, runtime_state=updated)
        return updated
    if not current_authorization and owner_handoff_authorization:
        current_authorization = _runtime_state_controller_authorization_after_terminal_source_blocker(
            runtime_state=runtime_state,
            owner_handoff_authorization=owner_handoff_authorization,
            quest_root=quest_root,
            quest_id=quest_id,
        )
    if not current_authorization:
        if _current_controller_decision_exists(quest_root=quest_root, quest_id=quest_id):
            updated = dict(runtime_state)
            if "current_controller_authorization" in updated:
                updated.pop("current_controller_authorization", None)
                updated["current_controller_authorization_sync_status"] = "current_controller_decision_not_runtime_authorizing"
                updated["current_controller_authorization_synced_at"] = _utc_now()
                _write_runtime_state(quest_root=quest_root, runtime_state=updated)
            return updated
        return dict(runtime_state)
    if _closed_publication_work_unit_for_authorization(
        authorization=current_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
    ) is not None:
        return dict(runtime_state)
    updated = dict(runtime_state)
    authorization = _bind_authorization_to_turn(
        authorization=current_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id=run_id,
    )
    if _mapping(updated.get("current_controller_authorization")) == authorization:
        return updated
    updated["quest_id"] = _text(updated.get("quest_id")) or quest_id
    updated["current_controller_authorization"] = authorization
    updated["current_controller_authorization_synced_at"] = _utc_now()
    if currentness is not None:
        updated["current_controller_authorization_currentness"] = currentness
    _write_runtime_state(quest_root=quest_root, runtime_state=updated)
    return updated


def _materialize_fresh_domain_transition_controller_decision_for_turn(
    *,
    quest_root: Path,
    quest_id: str,
) -> dict[str, Any] | None:
    study_root = _resolve_study_root_from_quest_root_light(quest_root=quest_root, quest_id=quest_id)
    if study_root is None:
        return None
    return domain_transition_currentness.materialize_fresh_domain_transition_controller_decision_if_required(
        study_root=study_root,
        source="mas_runtime_core_turn_authorization",
    )


def _controller_authorization(
    runtime_state: Mapping[str, Any] | None,
    *,
    quest_root: Path | None = None,
    quest_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping):
        return {}
    owner_handoff_authorization = _blocked_closeout_owner_handoff_authorization(runtime_state)
    current_controller_authorization = _current_controller_decision_authorization(
        quest_root=quest_root,
        quest_id=quest_id,
    )
    runtime_authorization = _runtime_state_downstream_authorization_after_provenance_limited_result(
        runtime_state=runtime_state,
        current_authorization=current_controller_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    if runtime_authorization:
        return runtime_authorization
    if owner_handoff_authorization and not _owner_handoff_authorization_is_superseded(
        authorization=owner_handoff_authorization,
        current_authorization=current_controller_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
    ):
        return owner_handoff_authorization
    if current_controller_authorization:
        if _closed_publication_work_unit_for_authorization(
            authorization=current_controller_authorization,
            quest_root=quest_root,
            quest_id=quest_id,
        ) is None:
            return current_controller_authorization
    if owner_handoff_authorization:
        runtime_authorization = _runtime_state_controller_authorization_after_terminal_source_blocker(
            runtime_state=runtime_state,
            owner_handoff_authorization=owner_handoff_authorization,
            quest_root=quest_root,
            quest_id=quest_id,
        )
        if runtime_authorization:
            return runtime_authorization
    if _current_controller_decision_exists(quest_root=quest_root, quest_id=quest_id):
        return {}
    for key in ("current_controller_authorization", "last_controller_decision_authorization"):
        value = runtime_state.get(key)
        if isinstance(value, Mapping):
            authorization = dict(value)
            if _closed_publication_work_unit_for_authorization(
                authorization=authorization,
                quest_root=quest_root,
                quest_id=quest_id,
            ) is not None:
                return {}
            return authorization
    return {}


def _runtime_state_downstream_authorization_after_provenance_limited_result(
    *,
    runtime_state: Mapping[str, Any],
    current_authorization: Mapping[str, Any],
    quest_root: Path | None,
    quest_id: str | None,
) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping) or not isinstance(current_authorization, Mapping):
        return {}
    if not _authorization_is_provenance_limited_audit(current_authorization):
        return {}
    study_root = _resolve_study_root_from_quest_root_light(quest_root=quest_root, quest_id=quest_id)
    if study_root is None:
        return {}
    blocker_state = provenance_limited_harmonization_owner_result.typed_blocker_state(study_root=study_root)
    if not _provenance_limited_result_routes_to_analysis_harmonization(blocker_state):
        return {}
    for key in ("last_controller_decision_authorization", "current_controller_authorization"):
        authorization = _mapping(runtime_state.get(key))
        if not _authorization_is_downstream_hard_methodology(authorization):
            continue
        if _closed_publication_work_unit_for_authorization(
            authorization=authorization,
            quest_root=quest_root,
            quest_id=quest_id,
        ) is not None:
            continue
        return _normalized_controller_decision_authorization(authorization)
    return {}


def _authorization_is_provenance_limited_audit(authorization: Mapping[str, Any]) -> bool:
    return (
        "provenance_limited_harmonization_audit" in set(_primary_controller_work_unit_ids(authorization))
        or "provenance_limited_harmonization_audit" in set(_controller_action_names(authorization))
    )


def _authorization_is_downstream_hard_methodology(authorization: Mapping[str, Any]) -> bool:
    return bool(
        authorization
        and set(_controller_work_unit_ids(authorization)).intersection(
            {
                "unit_harmonized_external_validation_rerun",
                "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            }
        )
    )


def _provenance_limited_result_routes_to_analysis_harmonization(blocker_state: Mapping[str, Any] | None) -> bool:
    state = _mapping(blocker_state)
    return (
        _text(state.get("blocked_reason")) == "unit_harmonized_rerun_required"
        and _text(state.get("next_owner")) == "analysis_harmonization_owner"
        and _text(state.get("next_work_unit")) == "unit_harmonized_external_validation_rerun"
    )


def _blocked_closeout_owner_handoff_authorization(runtime_state: Mapping[str, Any]) -> dict[str, Any]:
    return mas_runtime_core_turn_owner_handoff.blocked_closeout_owner_handoff_authorization(
        runtime_state,
        action_names_for_authorization=_controller_action_names,
        mapping=_mapping,
        text=_text,
    )


def _owner_handoff_authorization_is_superseded(
    *,
    authorization: Mapping[str, Any],
    current_authorization: Mapping[str, Any],
    quest_root: Path | None,
    quest_id: str | None,
) -> bool:
    study_root = _resolve_study_root_from_quest_root_light(quest_root=quest_root, quest_id=quest_id)
    terminal_source_superseded = mas_runtime_core_turn_owner_handoff.terminal_source_provenance_handoff_superseded(
        authorization,
        study_root=study_root,
        action_names_for_authorization=_controller_action_names,
        work_unit_ids_for_authorization=_controller_work_unit_ids,
        mapping=_mapping,
        text=_text,
    )
    return mas_runtime_core_turn_owner_handoff.owner_handoff_authorization_is_superseded(
        authorization,
        current_authorization,
        terminal_source_provenance_superseded=terminal_source_superseded,
        action_names_for_authorization=_controller_action_names,
        work_unit_ids_for_authorization=_controller_work_unit_ids,
        primary_work_unit_ids_for_authorization=_primary_controller_work_unit_ids,
        text=_text,
    )


def _runtime_state_controller_authorization_after_terminal_source_blocker(
    *,
    runtime_state: Mapping[str, Any],
    owner_handoff_authorization: Mapping[str, Any],
    quest_root: Path | None,
    quest_id: str | None,
) -> dict[str, Any]:
    study_root = _resolve_study_root_from_quest_root_light(quest_root=quest_root, quest_id=quest_id)
    if not mas_runtime_core_turn_owner_handoff.terminal_source_provenance_handoff_superseded(
        owner_handoff_authorization,
        study_root=study_root,
        action_names_for_authorization=_controller_action_names,
        work_unit_ids_for_authorization=_controller_work_unit_ids,
        mapping=_mapping,
        text=_text,
    ):
        return {}
    for key in ("last_controller_decision_authorization", "current_controller_authorization"):
        value = runtime_state.get(key)
        if not isinstance(value, Mapping):
            continue
        authorization = dict(value)
        if (
            "recover_transport_model_provenance" in _controller_work_unit_ids(authorization)
            or "recover_transport_model_provenance" in _controller_action_names(authorization)
        ):
            continue
        if _closed_publication_work_unit_for_authorization(
            authorization=authorization,
            quest_root=quest_root,
            quest_id=quest_id,
        ) is not None:
            continue
        return _normalized_controller_decision_authorization(authorization)
    return {}


def _normalized_controller_decision_authorization(authorization: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(authorization)
    normalized["authorization_basis"] = "current_controller_decision"
    next_work_unit = _mapping(normalized.get("next_work_unit"))
    if (next_work_unit_id := _text(next_work_unit.get("unit_id"))) is not None:
        normalized.setdefault("work_unit_id", next_work_unit_id)
    fingerprint = _text(normalized.get("blocker_authority_fingerprint")) or _text(next_work_unit.get("fingerprint"))
    normalized.setdefault("work_unit_fingerprint", fingerprint)
    return normalized


def _current_controller_decision_authorization(
    *,
    quest_root: Path | None,
    quest_id: str | None,
) -> dict[str, Any]:
    if quest_root is None:
        return {}
    study_root = _resolve_study_root_from_quest_root_light(quest_root=Path(quest_root), quest_id=quest_id)
    if study_root is None:
        return {}
    authorization = _load_controller_decision_authorization_context(study_root=study_root)
    if _controller_decision_is_runtime_authorizing(authorization) and _authorization_is_ai_reviewer_redrive(
        authorization
    ):
        return _normalized_controller_decision_authorization(authorization)
    story_surface_delta_authorization = _current_story_surface_delta_authorization(study_root=study_root)
    if story_surface_delta_authorization:
        return story_surface_delta_authorization
    if not _controller_decision_is_runtime_authorizing(authorization):
        return {}
    return _normalized_controller_decision_authorization(authorization)


def _controller_decision_is_runtime_authorizing(authorization: object) -> bool:
    if not isinstance(authorization, Mapping):
        return False
    if bool(authorization.get("requires_human_confirmation")):
        return False
    return bool(_controller_action_names(authorization))


def _authorization_is_ai_reviewer_redrive(authorization: Mapping[str, Any]) -> bool:
    if "return_to_ai_reviewer_workflow" not in set(_controller_action_names(authorization)):
        return False
    work_unit_ids = set(_controller_work_unit_ids(authorization))
    if work_unit_ids.intersection({"ai_reviewer_recheck", "ai_reviewer_medical_prose_quality_review"}):
        return True
    fingerprint = _text(authorization.get("work_unit_fingerprint"))
    return bool(fingerprint and fingerprint.startswith("domain-transition::ai_reviewer_re_eval::"))


def _current_story_surface_delta_authorization(*, study_root: Path) -> dict[str, Any]:
    publication_eval_payload = _read_json_mapping(
        Path(study_root).expanduser().resolve() / "artifacts" / "publication_eval" / "latest.json"
    )
    if not publication_eval_payload:
        return {}
    authorization = platform_current_controller.story_surface_delta_authorization_payload(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        read_json_object=_read_json_mapping_or_none,
    )
    return dict(authorization) if isinstance(authorization, Mapping) else {}


def _current_controller_decision_exists(
    *,
    quest_root: Path | None,
    quest_id: str | None,
) -> bool:
    if quest_root is None:
        return False
    study_root = _resolve_study_root_from_quest_root_light(quest_root=quest_root, quest_id=quest_id)
    if study_root is None:
        return False
    return (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


def _bind_authorization_to_turn(
    *,
    authorization: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
    run_id: str,
) -> dict[str, Any]:
    bound = dict(authorization)
    bound["active_run_id"] = run_id
    bound.setdefault("run_id", run_id)
    bound["quest_id"] = _text(bound.get("quest_id")) or quest_id
    bound["study_id"] = _text(bound.get("study_id")) or _study_id_for_quest_root(quest_root=quest_root, quest_id=quest_id)
    next_work_unit = _mapping(bound.get("next_work_unit"))
    next_work_unit_id = _text(next_work_unit.get("unit_id"))
    if _text(bound.get("work_unit_id")) is None and next_work_unit_id is not None:
        bound["work_unit_id"] = next_work_unit_id
    if _text(bound.get("work_unit_fingerprint")) is None:
        bound["work_unit_fingerprint"] = _text(next_work_unit.get("fingerprint"))
    action_names = _controller_action_names(bound)
    if action_names:
        bound["controller_actions"] = action_names
    return bound


def _study_id_for_quest_root(*, quest_root: Path, quest_id: str) -> str:
    study_root = _resolve_study_root_from_quest_root_light(quest_root=quest_root, quest_id=quest_id)
    if study_root is None:
        return quest_id
    return _yaml_string_field(study_root / "study.yaml", "study_id") or study_root.name


def _closed_publication_work_unit_for_authorization(
    *,
    authorization: Mapping[str, Any],
    quest_root: Path | None,
    quest_id: str | None,
) -> dict[str, Any] | None:
    if quest_root is None:
        return None
    study_root = _resolve_study_root_from_quest_root_light(quest_root=Path(quest_root), quest_id=quest_id)
    if study_root is None:
        return None
    lifecycle_path = publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
        study_root=study_root,
    )
    try:
        payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    if not publication_work_unit_lifecycle.lifecycle_payload_is_closed(dict(payload)):
        return None
    source_eval_id = _text(payload.get("source_eval_id"))
    authorization_eval_id = _authorization_publication_eval_id(
        authorization=authorization,
        study_root=study_root,
    )
    if source_eval_id is None or authorization_eval_id is None or source_eval_id != authorization_eval_id:
        return None
    lifecycle_work_unit = _mapping(payload.get("work_unit"))
    lifecycle_work_unit_id = _text(lifecycle_work_unit.get("unit_id"))
    authorization_work_unit_ids = set(_controller_work_unit_ids(authorization))
    if lifecycle_work_unit_id is None or lifecycle_work_unit_id not in authorization_work_unit_ids:
        return None
    return {
        "reason": "publication_work_unit_lifecycle_done",
        "source_eval_id": source_eval_id,
        "work_unit_id": lifecycle_work_unit_id,
        "lifecycle_path": str(lifecycle_path),
    }


def _authorization_publication_eval_id(
    *,
    authorization: Mapping[str, Any],
    study_root: Path,
) -> str | None:
    direct_eval_id = _text(
        authorization.get("publication_eval_id")
        or authorization.get("source_eval_id")
        or _mapping(authorization.get("publication_eval_ref")).get("eval_id")
    )
    if direct_eval_id is not None:
        return direct_eval_id
    decision = _read_json_mapping(study_root / "artifacts" / "controller_decisions" / "latest.json")
    if not _authorization_matches_controller_decision(authorization=authorization, decision=decision):
        return None
    return _text(
        decision.get("publication_eval_id")
        or decision.get("source_eval_id")
        or _mapping(decision.get("publication_eval_ref")).get("eval_id")
    )


def _authorization_matches_controller_decision(
    *,
    authorization: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> bool:
    if not decision:
        return False
    authorization_decision_id = _text(authorization.get("decision_id"))
    decision_id = _text(decision.get("decision_id"))
    if authorization_decision_id is not None and decision_id is not None:
        return authorization_decision_id == decision_id
    authorization_work_units = set(_controller_work_unit_ids(authorization))
    decision_work_units = set(_controller_work_unit_ids(decision))
    if not authorization_work_units or not authorization_work_units.intersection(decision_work_units):
        return False
    authorization_fingerprint = _text(authorization.get("work_unit_fingerprint"))
    decision_fingerprint = _text(decision.get("work_unit_fingerprint"))
    return (
        authorization_fingerprint is None
        or decision_fingerprint is None
        or authorization_fingerprint == decision_fingerprint
    )


def _resolve_study_root_from_quest_root_light(*, quest_root: Path, quest_id: str | None) -> Path | None:
    resolved = Path(quest_root).expanduser().resolve()
    if resolved.parent.name != "quests" or resolved.parent.parent.name != "runtime":
        return None
    if len(resolved.parents) >= 3 and resolved.parents[2].name != "ops":
        workspace_root = resolved.parents[2]
    elif len(resolved.parents) >= 5 and resolved.parents[3].name == "ops":
        workspace_root = resolved.parents[4]
    else:
        return None
    quest_name = _text(quest_id) or resolved.name
    candidate_ids = [quest_name]
    declared_study_id = _yaml_string_field(resolved / "quest.yaml", "study_id")
    if declared_study_id is not None and declared_study_id not in candidate_ids:
        candidate_ids.insert(0, declared_study_id)
    studies_root = workspace_root / "studies"
    for study_id in candidate_ids:
        candidate = (studies_root / study_id).resolve()
        if (candidate / "study.yaml").exists():
            return candidate
    if not studies_root.exists():
        return None
    for binding_path in sorted(studies_root.glob("*/runtime_binding.yaml")):
        binding_text = _yaml_string_field(binding_path, "quest_id")
        if binding_text != quest_name:
            continue
        candidate = binding_path.parent.resolve()
        if (candidate / "study.yaml").exists():
            return candidate
    return None


def _controller_action_names(authorization: Mapping[str, Any]) -> list[str]:
    return mas_runtime_core_turn_actions.controller_action_names(authorization)


def _controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    return mas_runtime_core_turn_actions.controller_work_unit_ids(authorization)


def _primary_controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    return mas_runtime_core_turn_actions.primary_controller_work_unit_ids(authorization)


def _authorization_has_hard_methodology_target(authorization: Mapping[str, Any]) -> bool:
    return mas_runtime_core_hard_methodology.authorization_has_hard_methodology_target(authorization)


def _write_runtime_state(*, quest_root: Path, runtime_state: Mapping[str, Any]) -> None:
    path = quest_root / ".ds" / "runtime_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(runtime_state), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_json_mapping_or_none(path: Path) -> dict[str, Any] | None:
    payload = _read_json_mapping(path)
    return payload or None


def _yaml_string_field(path: Path, field_name: str) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    prefix = f"{field_name}:"
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        value = stripped[len(prefix) :].strip().strip("\"'")
        return value or None
    return None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

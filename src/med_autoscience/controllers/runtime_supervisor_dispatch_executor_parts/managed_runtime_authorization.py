from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


def resolve_managed_runtime_authorization(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    action_type: str,
    requested: bool,
) -> dict[str, Any]:
    if not requested:
        return {"status": "not_requested"}
    env = os.environ
    if _text(env.get("MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER")) != "1":
        return {"status": "blocked", "blocked_reason": "managed_runtime_worker_env_missing"}
    quest_root_text = _text(env.get("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT"))
    run_id = _text(env.get("MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID"))
    env_quest_id = _text(env.get("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID"))
    quest_id = env_quest_id or _text(dispatch.get("quest_id")) or study_id
    if quest_root_text is None or run_id is None:
        return {"status": "blocked", "blocked_reason": "managed_runtime_identity_incomplete"}
    quest_root = Path(quest_root_text).expanduser().resolve()
    expected_quest_root = (profile.runtime_root / quest_id).expanduser().resolve()
    if quest_root != expected_quest_root:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_quest_root_mismatch",
            "quest_root": str(quest_root),
            "expected_quest_root": str(expected_quest_root),
        }
    home_status = _managed_home_status(env=env, quest_root=quest_root, run_id=run_id)
    if home_status.get("valid") is not True:
        return {
            "status": "blocked",
            "blocked_reason": _text(home_status.get("reason")) or "managed_runtime_home_invalid",
            "quest_root": str(quest_root),
            "run_id": run_id,
            "home_check": home_status,
        }
    runtime_state = _read_json_object(quest_root / ".ds" / "runtime_state.json")
    if runtime_state is None:
        return {"status": "blocked", "blocked_reason": "managed_runtime_state_missing", "quest_root": str(quest_root)}
    runtime_quest_id = _text(runtime_state.get("quest_id"))
    if runtime_quest_id is not None and runtime_quest_id != quest_id:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_quest_id_mismatch",
            "quest_root": str(quest_root),
            "quest_id": quest_id,
            "runtime_quest_id": runtime_quest_id,
        }
    if _text(runtime_state.get("active_run_id")) != run_id or runtime_state.get("worker_running") is not True:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_run_not_current",
            "quest_root": str(quest_root),
            "active_run_id": _text(runtime_state.get("active_run_id")),
            "run_id": run_id,
        }
    authorization = _mapping(runtime_state.get("current_controller_authorization")) or _mapping(
        runtime_state.get("last_controller_decision_authorization")
    )
    if not authorization:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_controller_authorization_missing",
            "quest_root": str(quest_root),
            "run_id": run_id,
        }
    authorization_run_id = _text(authorization.get("active_run_id"))
    if authorization_run_id is not None and authorization_run_id != run_id:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_authorization_run_mismatch",
            "quest_root": str(quest_root),
            "run_id": run_id,
            "authorization_run_id": authorization_run_id,
        }
    authorization_quest_id = _text(authorization.get("quest_id"))
    if authorization_quest_id is not None and authorization_quest_id != quest_id:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_authorization_quest_mismatch",
            "quest_root": str(quest_root),
            "quest_id": quest_id,
            "authorization_quest_id": authorization_quest_id,
        }
    authorization_study_id = _text(authorization.get("study_id"))
    if authorization_study_id is not None and authorization_study_id != study_id:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_authorization_study_mismatch",
            "quest_root": str(quest_root),
            "study_id": study_id,
            "authorization_study_id": authorization_study_id,
        }
    action_names = controller_action_names(authorization)
    if action_type not in action_names:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_action_not_authorized",
            "authorized_actions": action_names,
            "quest_root": str(quest_root),
            "run_id": run_id,
        }
    work_unit_fingerprint = _text(authorization.get("work_unit_fingerprint"))
    work_unit_id = _text(authorization.get("work_unit_id")) or _text(_mapping(authorization.get("next_work_unit")).get("unit_id"))
    if work_unit_fingerprint is None or work_unit_id is None:
        return {
            "status": "blocked",
            "blocked_reason": "managed_runtime_authorization_incomplete",
            "quest_root": str(quest_root),
            "run_id": run_id,
        }
    return {
        "status": "authorized",
        "quest_root": str(quest_root),
        "quest_id": quest_id,
        "run_id": run_id,
        "decision_id": _text(authorization.get("decision_id")),
        "authorization_basis": _text(authorization.get("authorization_basis")),
        "route_target": _text(authorization.get("route_target")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "authorized_actions": action_names,
        "authorization": authorization,
    }


def runtime_authorized_dispatch(
    *,
    dispatch: Mapping[str, Any],
    action_type: str,
    authorization: Mapping[str, Any],
    supported_action_types: Iterable[str],
) -> dict[str, Any]:
    owner = _runtime_authorized_owner_for_action(action_type)
    study_id = _text(dispatch.get("study_id")) or _text(authorization.get("study_id")) or "unknown-study"
    quest_id = _text(authorization.get("quest_id")) or _text(dispatch.get("quest_id")) or study_id
    work_unit_fingerprint = _text(authorization.get("work_unit_fingerprint")) or "unknown-work-unit"
    decision_id = _text(authorization.get("decision_id")) or work_unit_fingerprint
    owner_route = owner_route_part.ensure_owner_route_v2(
        {
            "surface": "runtime_supervisor_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": quest_id,
            "truth_epoch": decision_id,
            "runtime_health_epoch": _text(dispatch.get("runtime_health_epoch")),
            "work_unit_fingerprint": work_unit_fingerprint,
            "failure_signature": action_type,
            "route_epoch": decision_id,
            "source_fingerprint": work_unit_fingerprint,
            "current_owner": "managed_runtime",
            "next_owner": owner,
            "owner_reason": action_type,
            "active_run_id": _text(authorization.get("run_id")),
            "allowed_actions": [action_type],
            "blocked_actions": [item for item in supported_action_types if item != action_type],
            "idempotency_key": f"managed-runtime::{study_id}::{action_type}::{work_unit_fingerprint}",
            "source_refs": {
                "controller_decision_id": decision_id,
                "authorization_basis": _text(authorization.get("authorization_basis")),
                "quest_root": _text(authorization.get("quest_root")),
            },
        }
    )
    prompt_contract = dict(_mapping(dispatch.get("prompt_contract")))
    prompt_contract.update(
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": action_type,
            "next_executable_owner": owner,
            "owner_route": owner_route,
            "idempotency_key": owner_route.get("idempotency_key"),
            "repeat_suppression_key": work_unit_fingerprint,
        }
    )
    return {
        **dict(dispatch),
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "next_executable_owner": owner,
        "owner_route": owner_route,
        "idempotency_key": owner_route.get("idempotency_key"),
        "repeat_suppression_key": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "dispatch_status": "ready",
        "prompt_contract": prompt_contract,
        "dispatch_authority": "managed_runtime_controller_authorization",
        "source_dispatch": dict(dispatch),
    }


def controller_action_names(authorization: Mapping[str, Any]) -> list[str]:
    raw_actions = authorization.get("controller_actions")
    if isinstance(raw_actions, str):
        items: list[object] = [raw_actions]
    elif isinstance(raw_actions, (list, tuple)):
        items = list(raw_actions)
    else:
        items = []
    names: list[str] = []
    for item in items:
        raw_name = item.get("action_type") or item.get("action") or item.get("name") if isinstance(item, Mapping) else item
        name = str(raw_name or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def _managed_home_status(*, env: Mapping[str, str], quest_root: Path, run_id: str) -> dict[str, Any]:
    expected_home = (quest_root / ".ds" / "codex_homes" / run_id).resolve()
    home = _env_path(env.get("HOME"))
    codex_home = _env_path(env.get("CODEX_HOME"))
    if home is None:
        return {"valid": False, "reason": "managed_runtime_home_missing", "expected_home": str(expected_home)}
    if home.resolve() != expected_home:
        return {
            "valid": False,
            "reason": "managed_runtime_home_mismatch",
            "home": str(home),
            "expected_home": str(expected_home),
        }
    expected_codex_home = (expected_home / ".codex").resolve()
    if codex_home is None or codex_home.resolve() != expected_codex_home:
        return {
            "valid": False,
            "reason": "managed_runtime_codex_home_mismatch",
            "codex_home": str(codex_home) if codex_home is not None else None,
            "expected_codex_home": str(expected_codex_home),
        }
    return {"valid": True, "home": str(home), "codex_home": str(codex_home)}


def _runtime_authorized_owner_for_action(action_type: str) -> str:
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    if action_type == "canonical_paper_inputs_rehydrate_required":
        return "write"
    if action_type == "unit_harmonized_external_validation_rerun":
        return "analysis_harmonization_owner"
    if action_type == "recover_transport_model_provenance":
        return "source_provenance_owner"
    if action_type == "provenance_limited_harmonization_audit":
        return "provenance_limited_harmonization_owner"
    if action_type in {"current_package_freshness_required", "artifact_display_surface_materialization_required"}:
        return "artifact_os"
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "runtime_platform_repair":
        return "external_supervisor"
    return "mas_controller"


def _env_path(value: str | None) -> Path | None:
    text = _text(value)
    return Path(text).expanduser() if text is not None else None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "controller_action_names",
    "resolve_managed_runtime_authorization",
    "runtime_authorized_dispatch",
]

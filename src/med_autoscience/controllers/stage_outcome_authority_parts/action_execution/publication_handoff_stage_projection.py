from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


STAGE_ID = "08-publication_package_handoff"
STAGE_ROOT_RELATIVE_PATH = Path("artifacts/stage_outputs") / STAGE_ID
CURRENT_POINTER_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "current.json"
CURRENT_OWNER_DELTA_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "projection" / "current_owner_delta.json"
PROJECTION_WRITER_ID = "mas_terminal_handoff_stage_current_projection_writer.v1"


def write_stage_current_projection(
    *,
    study_root: Path,
    owner: str,
    action: str,
    reason: str,
    source_ref: str,
    owner_answer_kind: str,
    stage_status: str,
    terminal_outcome_kind: str,
    terminal_outcome_ref: str,
    closeout_binding: Mapping[str, Any],
    authority_boundary: Mapping[str, Any],
    next_action: object | None = None,
) -> dict[str, Any]:
    binding = _manifest_closeout_binding(closeout_binding)
    idempotency_key = _text(closeout_binding.get("idempotency_key"))
    provider_attempt_ref = _text(closeout_binding.get("provider_attempt_ref"))
    attempt_lease_ref = _text(closeout_binding.get("attempt_lease_ref"))
    attempt_lease_status = _text(closeout_binding.get("attempt_lease_status")) or "active"
    execution_authorization_decision_ref = _text(closeout_binding.get("execution_authorization_decision_ref"))
    closeout_refs = _text_list(closeout_binding.get("closeout_refs"))
    generation = closeout_binding.get("generation") if isinstance(closeout_binding.get("generation"), int) else 0
    owner_delta_payload: dict[str, Any] = {
        "owner": owner,
        "action": action,
        "reason": reason,
        "source_ref": source_ref,
        "source_kind": owner_answer_kind,
        "delta_id": idempotency_key,
        "idempotency_key": idempotency_key,
        "latest_owner_answer_ref": source_ref,
        "latest_owner_answer_kind": owner_answer_kind,
        "latest_owner_receipt_ref": source_ref if owner_answer_kind == "owner_receipt" else None,
        "latest_typed_blocker_ref": source_ref if owner_answer_kind == "typed_blocker" else None,
        "stage_run_id": _text(closeout_binding.get("stage_run_id")),
        "stage_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
        "current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
        "source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
        "provider_attempt_ref": provider_attempt_ref,
        "attempt_lease_ref": attempt_lease_ref,
        "attempt_lease_status": attempt_lease_status,
        "execution_authorization_decision_ref": execution_authorization_decision_ref,
        "closeout_refs": closeout_refs,
        "closeout_binding": binding,
        "projection_writer": PROJECTION_WRITER_ID,
        "projection_role": "mas_terminal_owner_answer_projection_not_opl_current_owner_delta_publish",
        "stage_run_current_authority": "opl_stage_transition_authority_only",
        "authority_boundary": _stage_transition_authority_boundary(authority_boundary),
        "hard_gate": {
            "state": "domain_owner_answer_recorded",
            "owner_answer_ref": source_ref,
            "owner_answer_kind": owner_answer_kind,
            "owner_answer_stage_run_id": _text(closeout_binding.get("stage_run_id")),
            "owner_answer_generation": generation,
            "owner_answer_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
            "stage_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
            "owner_answer_current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
            "current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
            "owner_answer_source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
            "owner_answer_idempotency_key": idempotency_key,
            "owner_answer_provider_attempt_ref": provider_attempt_ref,
            "owner_answer_attempt_lease_ref": attempt_lease_ref,
            "owner_answer_attempt_lease_status": attempt_lease_status,
            "owner_answer_execution_authorization_decision_ref": execution_authorization_decision_ref,
            "owner_answer_closeout_refs": closeout_refs,
        },
    }
    if isinstance(next_action, Mapping):
        owner_delta_payload["next_action"] = dict(next_action)
        if surface_key := _text(next_action.get("surface_key")):
            owner_delta_payload["surface_key"] = surface_key
    current_pointer_payload = {
        "surface_kind": "stage_current_pointer",
        "schema_version": 1,
        "current_stage": {
            "stage_id": STAGE_ID,
            "status": stage_status,
            "latest_attempt_id": _text(closeout_binding.get("attempt_id")) or provider_attempt_ref,
            "stage_run_id": _text(closeout_binding.get("stage_run_id")),
            "terminal_outcome_kind": terminal_outcome_kind,
            "terminal_outcome_ref": terminal_outcome_ref,
            "source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
        },
        "closeout_binding": binding,
        "projection_only": True,
        "body_included": False,
        "projection_writer": PROJECTION_WRITER_ID,
        "projection_role": "mas_terminal_stage_current_projection_not_opl_stage_run_current_pointer",
        "stage_run_current_authority": "opl_stage_transition_authority_only",
        "authority_boundary": _stage_transition_authority_boundary(authority_boundary),
    }
    _write_json(study_root / CURRENT_OWNER_DELTA_RELATIVE_PATH, owner_delta_payload)
    _write_json(study_root / CURRENT_POINTER_RELATIVE_PATH, current_pointer_payload)
    return {
        "projection_writer": PROJECTION_WRITER_ID,
        "current_owner_delta_ref": CURRENT_OWNER_DELTA_RELATIVE_PATH.as_posix(),
        "current_pointer_ref": CURRENT_POINTER_RELATIVE_PATH.as_posix(),
    }


def manifest_closeout_binding(closeout_binding: Mapping[str, Any]) -> dict[str, Any]:
    return _manifest_closeout_binding(closeout_binding)


def _manifest_closeout_binding(closeout_binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": _text(closeout_binding.get("surface_kind")) or "publication_handoff_closeout_binding",
        "trusted_opl_execution_authorization": bool(closeout_binding.get("trusted_opl_execution_authorization")),
        "bound_to_stage_run": bool(closeout_binding.get("bound_to_stage_run")),
        "bound_to_stage_manifest": bool(closeout_binding.get("bound_to_stage_manifest")),
        "bound_to_current_pointer": bool(closeout_binding.get("bound_to_current_pointer")),
        "bound_to_source_fingerprint": bool(closeout_binding.get("bound_to_source_fingerprint")),
        "provider_attempt_ref": _text(closeout_binding.get("provider_attempt_ref")),
        "attempt_lease_ref": _text(closeout_binding.get("attempt_lease_ref")),
        "attempt_lease_status": _text(closeout_binding.get("attempt_lease_status")) or "active",
        "execution_authorization_decision_ref": _text(closeout_binding.get("execution_authorization_decision_ref")),
        "stage_run_id": _text(closeout_binding.get("stage_run_id")),
        "stage_run_ref": _text(closeout_binding.get("stage_run_ref")),
        "stage_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
        "current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
        "closeout_refs": _text_list(closeout_binding.get("closeout_refs")),
        "source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
        "work_unit_fingerprint": _text(closeout_binding.get("work_unit_fingerprint")),
        "idempotency_key": _text(closeout_binding.get("idempotency_key")),
        "generation": closeout_binding.get("generation") if isinstance(closeout_binding.get("generation"), int) else 0,
        "body_included": False,
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stage_transition_authority_boundary(boundary: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(boundary)
    payload.update(
        {
            "can_write_stage_current_pointer": False,
            "can_write_stage_run_terminal_state": False,
            "can_publish_opl_current_owner_delta": False,
            "provider_completion_counts_as_stage_transition": False,
            "read_model_update_counts_as_stage_transition": False,
            "worklist_update_counts_as_stage_transition": False,
        }
    )
    return payload


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "CURRENT_OWNER_DELTA_RELATIVE_PATH",
    "CURRENT_POINTER_RELATIVE_PATH",
    "PROJECTION_WRITER_ID",
    "STAGE_ID",
    "STAGE_ROOT_RELATIVE_PATH",
    "manifest_closeout_binding",
    "write_stage_current_projection",
]

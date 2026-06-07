from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_readiness as readiness_surface


STAGE_ID = "08-publication_package_handoff"
STAGE_ROOT_RELATIVE_PATH = Path("artifacts/stage_outputs") / STAGE_ID
STAGE_MANIFEST_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "stage_manifest.json"
CURRENT_POINTER_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "current.json"
CURRENT_OWNER_DELTA_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "projection" / "current_owner_delta.json"
OWNER_RECEIPT_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "receipts" / "owner_receipt.json"
TYPED_BLOCKER_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "receipts" / "typed_blocker.json"


def materialize_stage_native_owner_answer(
    *,
    study_id: str,
    study_root: Path,
    owner_result: Mapping[str, Any],
    owner_delta_result: Mapping[str, Any],
    closeout_binding: Mapping[str, Any] | None,
    apply: bool,
) -> dict[str, Any]:
    binding = _stage_native_closeout_binding(
        study_id=study_id,
        source_binding=_mapping(closeout_binding),
        owner_delta_result=owner_delta_result,
    )
    terminal_kind = _terminal_kind(owner_delta_result)
    if terminal_kind is None:
        return _blocked(
            reason="missing_owner_delta_result",
            binding=binding,
            apply=apply,
        )
    if not _trusted(binding):
        return _blocked(
            reason="trusted_opl_execution_authorization_required",
            binding=binding,
            apply=apply,
        )
    manifest_path = study_root / STAGE_MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        return _blocked(
            reason="stage_manifest_missing",
            binding=binding,
            apply=apply,
        )
    if not apply:
        return {
            "surface_kind": "medical_paper_readiness_stage_native_closeout",
            "status": "dry_run",
            "terminal_outcome_kind": terminal_kind,
            "stage_id": STAGE_ID,
            "will_write_ref": _outcome_ref(terminal_kind),
            "closeout_binding": binding,
            "authority_boundary": _authority_boundary(),
        }
    generated_at = _utc_now()
    if terminal_kind == "owner_receipt":
        receipt = _owner_receipt_payload(
            study_id=study_id,
            study_root=study_root,
            owner_result=owner_result,
            owner_delta_result=owner_delta_result,
            generated_at=generated_at,
            closeout_binding=binding,
        )
        _write_json(study_root / OWNER_RECEIPT_RELATIVE_PATH, receipt)
        _unlink_if_exists(study_root / TYPED_BLOCKER_RELATIVE_PATH)
        _update_stage_manifest(
            study_root=study_root,
            terminal_status="completed",
            owner_receipt_refs=["receipts/owner_receipt.json"],
            typed_blocker_refs=[],
            closeout_binding=binding,
        )
        _write_current_owner_delta(
            study_root=study_root,
            owner="publication_gate_owner",
            action="publication_handoff_owner_gate",
            reason="medical_paper_readiness_surface_ready",
            source_ref=OWNER_RECEIPT_RELATIVE_PATH.as_posix(),
            owner_answer_kind="owner_receipt",
            closeout_binding=binding,
            next_action=None,
        )
        _write_current_pointer(
            study_root=study_root,
            stage_status="success",
            terminal_outcome_kind="owner_receipt",
            terminal_outcome_ref=OWNER_RECEIPT_RELATIVE_PATH.as_posix(),
            closeout_binding=binding,
        )
        return _materialized(
            terminal_kind="owner_receipt",
            written_ref=OWNER_RECEIPT_RELATIVE_PATH.as_posix(),
            closeout_binding=binding,
        )
    blocker = _typed_blocker_payload(
        study_id=study_id,
        study_root=study_root,
        owner_result=owner_result,
        owner_delta_result=owner_delta_result,
        generated_at=generated_at,
        closeout_binding=binding,
    )
    _write_json(study_root / TYPED_BLOCKER_RELATIVE_PATH, blocker)
    _unlink_if_exists(study_root / OWNER_RECEIPT_RELATIVE_PATH)
    _update_stage_manifest(
        study_root=study_root,
        terminal_status="blocked",
        owner_receipt_refs=[],
        typed_blocker_refs=["receipts/typed_blocker.json"],
        closeout_binding=binding,
    )
    _write_current_owner_delta(
        study_root=study_root,
        owner="MedAutoScience",
        action="complete_medical_paper_readiness_surface",
        reason=_blocker_reason(owner_result, owner_delta_result),
        source_ref=TYPED_BLOCKER_RELATIVE_PATH.as_posix(),
        owner_answer_kind="typed_blocker",
        closeout_binding=binding,
        next_action=_mapping(_mapping(owner_result).get("guarded_operator_action_result")).get("next_action"),
    )
    _write_current_pointer(
        study_root=study_root,
        stage_status="blocked",
        terminal_outcome_kind="typed_blocker",
        terminal_outcome_ref=TYPED_BLOCKER_RELATIVE_PATH.as_posix(),
        closeout_binding=binding,
    )
    return _materialized(
        terminal_kind="typed_blocker",
        written_ref=TYPED_BLOCKER_RELATIVE_PATH.as_posix(),
        closeout_binding=binding,
    )


def _owner_receipt_payload(
    *,
    study_id: str,
    study_root: Path,
    owner_result: Mapping[str, Any],
    owner_delta_result: Mapping[str, Any],
    generated_at: str,
    closeout_binding: Mapping[str, Any],
) -> dict[str, Any]:
    refs = _owner_result_refs(owner_delta_result)
    receipt_id = f"medical-paper-readiness:{study_id}:{_fingerprint([refs, owner_delta_result])[:16]}"
    return {
        "surface_kind": "mas_stage_owner_receipt",
        "schema_version": 1,
        "receipt_id": receipt_id,
        "study_id": study_id,
        "quest_id": study_id,
        "stage_id": STAGE_ID,
        "stage_run_id": _text(closeout_binding.get("stage_run_id")),
        "stage_run_ref": _text(closeout_binding.get("stage_run_ref")),
        "stage_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
        "current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
        "owner": "MedAutoScience",
        "authority_type": "medical_owner_receipt",
        "receipt_ref": receipt_id,
        "schema_refs": _schema_refs(),
        "capability_refs": [
            "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/medical_owner_receipt",
        ],
        "domain_semantic_refs": {
            "owner_route_refs": [f"medical-paper-readiness-owner-route:{study_id}:{STAGE_ID}"],
            "medical_owner_receipt_refs": [receipt_id],
        },
        "receipt_kind": "medical_paper_readiness_surface",
        "receipt_status": "medical_paper_readiness_ready",
        "artifact_refs": refs,
        "produced_artifact_refs": [OWNER_RECEIPT_RELATIVE_PATH.as_posix()],
        "consumed_artifact_refs": refs,
        "readiness_ref": _readiness_ref(study_root=study_root, owner_result=owner_result),
        "completed_surface_key": _text(owner_result.get("completed_surface_key")),
        "next_owner_delta": {
            "owner": "publication_gate_owner",
            "action": "publication_handoff_owner_gate",
            "reason": "medical_paper_readiness_surface_ready",
        },
        "idempotency_key": _text(closeout_binding.get("idempotency_key")) or receipt_id,
        "intent_fingerprint": _fingerprint([refs, owner_delta_result]),
        "source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
        "work_unit_fingerprint": _text(closeout_binding.get("work_unit_fingerprint")),
        "closeout_refs": _text_list(closeout_binding.get("closeout_refs")),
        "closeout_binding": _closeout_binding_for_receipt(
            closeout_binding=closeout_binding,
            receipt_ref=OWNER_RECEIPT_RELATIVE_PATH.as_posix(),
        ),
        "recorded_at": generated_at,
        "body_included": False,
        "refs_only": True,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
        "authority_boundary": _authority_boundary(),
    }


def _typed_blocker_payload(
    *,
    study_id: str,
    study_root: Path,
    owner_result: Mapping[str, Any],
    owner_delta_result: Mapping[str, Any],
    generated_at: str,
    closeout_binding: Mapping[str, Any],
) -> dict[str, Any]:
    blocker_id = _blocker_reason(owner_result, owner_delta_result)
    blocker_ref = f"medical-paper-readiness-typed-blocker:{study_id}:{_fingerprint([owner_delta_result, blocker_id])[:16]}"
    next_action = _mapping(_mapping(owner_result).get("guarded_operator_action_result")).get("next_action")
    return {
        "surface_kind": "mas_stage_owner_receipt",
        "schema_version": 1,
        "receipt_id": blocker_ref,
        "study_id": study_id,
        "quest_id": study_id,
        "stage_id": STAGE_ID,
        "stage_run_id": _text(closeout_binding.get("stage_run_id")),
        "stage_run_ref": _text(closeout_binding.get("stage_run_ref")),
        "stage_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
        "current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
        "owner": "MedAutoScience",
        "authority_type": "typed_blocker",
        "receipt_ref": blocker_ref,
        "schema_refs": _schema_refs(),
        "capability_refs": [
            "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/typed_blocker",
        ],
        "domain_semantic_refs": {
            "typed_blocker_refs": [blocker_ref],
        },
        "typed_blocker_refs": [blocker_ref],
        "receipt_kind": "typed_blocker",
        "receipt_status": "typed_blocker_or_stop_loss",
        "blocker_id": blocker_id,
        "blocked_surface": "publication_handoff_owner_gate",
        "required_input": "complete_medical_paper_readiness_surface",
        "next_safe_action": "complete_medical_paper_readiness_surface",
        "next_action": dict(next_action) if isinstance(next_action, Mapping) else None,
        "readiness_ref": _readiness_ref(study_root=study_root, owner_result=owner_result),
        "artifact_refs": [TYPED_BLOCKER_RELATIVE_PATH.as_posix()],
        "produced_artifact_refs": [TYPED_BLOCKER_RELATIVE_PATH.as_posix()],
        "owner_delta_result_kind": _text(owner_delta_result.get("result_kind")),
        "source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
        "work_unit_fingerprint": _text(closeout_binding.get("work_unit_fingerprint")),
        "closeout_refs": _text_list(closeout_binding.get("closeout_refs")),
        "closeout_binding": _closeout_binding_for_receipt(
            closeout_binding=closeout_binding,
            receipt_ref=TYPED_BLOCKER_RELATIVE_PATH.as_posix(),
        ),
        "recorded_at": generated_at,
        "body_included": False,
        "refs_only": True,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
        "authority_boundary": _authority_boundary(),
    }


def _update_stage_manifest(
    *,
    study_root: Path,
    terminal_status: str,
    owner_receipt_refs: list[str],
    typed_blocker_refs: list[str],
    closeout_binding: Mapping[str, Any],
) -> None:
    manifest_path = study_root / STAGE_MANIFEST_RELATIVE_PATH
    manifest = _read_json_object(manifest_path)
    if not manifest:
        return
    manifest["stage_id"] = _text(manifest.get("stage_id")) or STAGE_ID
    manifest["stage_run_id"] = _text(closeout_binding.get("stage_run_id"))
    manifest["stage_run_ref"] = _text(closeout_binding.get("stage_run_ref"))
    manifest["stage_manifest_ref"] = _text(closeout_binding.get("stage_manifest_ref"))
    manifest["current_pointer_ref"] = _text(closeout_binding.get("current_pointer_ref"))
    manifest["current_pointer_state"] = "current_pointer_promoted"
    manifest["closeout_binding_refs"] = _text_list(closeout_binding.get("closeout_refs"))
    manifest["source_fingerprint"] = _text(closeout_binding.get("source_fingerprint"))
    manifest["work_unit_fingerprint"] = _text(closeout_binding.get("work_unit_fingerprint"))
    manifest["closeout_binding"] = _manifest_closeout_binding(closeout_binding)
    manifest["owner_receipt_refs"] = owner_receipt_refs
    manifest["typed_blocker_refs"] = typed_blocker_refs
    manifest["terminal_status"] = terminal_status
    _write_json(manifest_path, manifest)


def _write_current_owner_delta(
    *,
    study_root: Path,
    owner: str,
    action: str,
    reason: str,
    source_ref: str,
    owner_answer_kind: str,
    closeout_binding: Mapping[str, Any],
    next_action: object,
) -> None:
    idempotency_key = _text(closeout_binding.get("idempotency_key"))
    closeout_refs = _text_list(closeout_binding.get("closeout_refs"))
    payload = {
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
        "provider_attempt_ref": _text(closeout_binding.get("provider_attempt_ref")),
        "attempt_lease_ref": _text(closeout_binding.get("attempt_lease_ref")),
        "attempt_lease_status": _text(closeout_binding.get("attempt_lease_status")) or "active",
        "execution_authorization_decision_ref": _text(closeout_binding.get("execution_authorization_decision_ref")),
        "closeout_refs": closeout_refs,
        "closeout_binding": _manifest_closeout_binding(closeout_binding),
        "hard_gate": {
            "state": "domain_owner_answer_recorded",
            "owner_answer_ref": source_ref,
            "owner_answer_kind": owner_answer_kind,
            "owner_answer_stage_run_id": _text(closeout_binding.get("stage_run_id")),
            "owner_answer_generation": closeout_binding.get("generation") if isinstance(closeout_binding.get("generation"), int) else 0,
            "owner_answer_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
            "stage_manifest_ref": _text(closeout_binding.get("stage_manifest_ref")),
            "owner_answer_current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
            "current_pointer_ref": _text(closeout_binding.get("current_pointer_ref")),
            "owner_answer_source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
            "owner_answer_idempotency_key": idempotency_key,
            "owner_answer_provider_attempt_ref": _text(closeout_binding.get("provider_attempt_ref")),
            "owner_answer_attempt_lease_ref": _text(closeout_binding.get("attempt_lease_ref")),
            "owner_answer_attempt_lease_status": _text(closeout_binding.get("attempt_lease_status")) or "active",
            "owner_answer_execution_authorization_decision_ref": _text(
                closeout_binding.get("execution_authorization_decision_ref")
            ),
            "owner_answer_closeout_refs": closeout_refs,
        },
    }
    if isinstance(next_action, Mapping):
        payload["next_action"] = dict(next_action)
        if surface_key := _text(next_action.get("surface_key")):
            payload["surface_key"] = surface_key
    _write_json(study_root / CURRENT_OWNER_DELTA_RELATIVE_PATH, payload)


def _write_current_pointer(
    *,
    study_root: Path,
    stage_status: str,
    terminal_outcome_kind: str,
    terminal_outcome_ref: str,
    closeout_binding: Mapping[str, Any],
) -> None:
    _write_json(
        study_root / CURRENT_POINTER_RELATIVE_PATH,
        {
            "surface_kind": "stage_current_pointer",
            "schema_version": 1,
            "current_stage": {
                "stage_id": STAGE_ID,
                "status": stage_status,
                "latest_attempt_id": _text(closeout_binding.get("provider_attempt_ref")),
                "stage_run_id": _text(closeout_binding.get("stage_run_id")),
                "terminal_outcome_kind": terminal_outcome_kind,
                "terminal_outcome_ref": terminal_outcome_ref,
                "source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
            },
            "closeout_binding": _manifest_closeout_binding(closeout_binding),
            "projection_only": True,
            "body_included": False,
            "authority_boundary": _authority_boundary(),
        },
    )


def _stage_native_closeout_binding(
    *,
    study_id: str,
    source_binding: Mapping[str, Any],
    owner_delta_result: Mapping[str, Any],
) -> dict[str, Any]:
    stage_run_id = _first_text(source_binding.get("stage_run_id"), owner_delta_result.get("stage_run_id"))
    stage_manifest_ref = _first_text(
        source_binding.get("stage_manifest_ref"),
        owner_delta_result.get("stage_manifest_ref"),
    )
    current_pointer_ref = _first_text(
        source_binding.get("current_pointer_ref"),
        owner_delta_result.get("current_pointer_ref"),
    )
    source_fingerprint = _first_text(
        source_binding.get("source_fingerprint"),
        owner_delta_result.get("source_fingerprint"),
    )
    work_unit_fingerprint = _first_text(
        owner_delta_result.get("source_fingerprint"),
        source_binding.get("work_unit_fingerprint"),
        source_binding.get("source_fingerprint"),
    )
    return {
        "surface_kind": "medical_paper_readiness_stage_native_closeout_binding",
        "trusted_opl_execution_authorization": bool(source_binding.get("trusted_opl_execution_authorization")),
        "bound_to_stage_run": stage_run_id is not None,
        "bound_to_stage_manifest": stage_manifest_ref is not None,
        "bound_to_current_pointer": current_pointer_ref is not None,
        "bound_to_source_fingerprint": source_fingerprint is not None,
        "provider_attempt_ref": _text(source_binding.get("provider_attempt_ref")),
        "attempt_id": _text(source_binding.get("provider_attempt_ref")),
        "attempt_lease_ref": _text(source_binding.get("attempt_lease_ref")),
        "attempt_lease_status": _text(source_binding.get("attempt_lease_status")) or "active",
        "execution_authorization_decision_ref": _text(source_binding.get("execution_authorization_decision_ref")),
        "stage_run_id": stage_run_id,
        "stage_run_ref": _first_text(source_binding.get("stage_run_ref"), stage_run_id),
        "stage_manifest_ref": stage_manifest_ref,
        "current_pointer_ref": current_pointer_ref,
        "closeout_refs": _text_list(source_binding.get("closeout_refs")),
        "source_fingerprint": source_fingerprint,
        "work_unit_fingerprint": work_unit_fingerprint,
        "idempotency_key": _first_text(
            source_binding.get("idempotency_key"),
            owner_delta_result.get("idempotency_key"),
            source_binding.get("source_fingerprint"),
        ),
        "generation": source_binding.get("generation") if isinstance(source_binding.get("generation"), int) else 0,
        "body_included": False,
    }


def _closeout_binding_for_receipt(
    *,
    closeout_binding: Mapping[str, Any],
    receipt_ref: str,
) -> dict[str, Any]:
    return {**_manifest_closeout_binding(closeout_binding), "receipt_ref": receipt_ref}


def _manifest_closeout_binding(closeout_binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "medical_paper_readiness_stage_native_closeout_binding",
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


def _terminal_kind(owner_delta_result: Mapping[str, Any]) -> str | None:
    result_kind = _text(owner_delta_result.get("result_kind"))
    if result_kind == "owner_receipt":
        return "owner_receipt"
    if result_kind in {
        "stable_typed_blocker",
        "quality_gate_receipt_with_stable_typed_blocker",
        "quality_gate_receipt",
    }:
        return "typed_blocker"
    return None


def _owner_result_refs(owner_delta_result: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    refs.extend(_text_list(owner_delta_result.get("quality_gate_receipt_refs")))
    refs.extend(_text_list(owner_delta_result.get("stable_typed_blocker_refs")))
    return list(dict.fromkeys(refs))


def _trusted(binding: Mapping[str, Any]) -> bool:
    return bool(
        binding.get("trusted_opl_execution_authorization")
        and _text(binding.get("provider_attempt_ref"))
        and _text(binding.get("attempt_lease_ref"))
        and _text(binding.get("execution_authorization_decision_ref"))
        and _text(binding.get("stage_run_id"))
        and _text(binding.get("stage_manifest_ref"))
        and _text(binding.get("current_pointer_ref"))
        and _text(binding.get("source_fingerprint"))
        and _text(binding.get("idempotency_key"))
    )


def _blocker_reason(owner_result: Mapping[str, Any], owner_delta_result: Mapping[str, Any]) -> str:
    action_result = _mapping(owner_result.get("guarded_operator_action_result"))
    typed_blocker = _mapping(owner_delta_result.get("typed_blocker"))
    return (
        _text(typed_blocker.get("blocker_id"))
        or _text(action_result.get("missing_reason"))
        or _text(owner_result.get("blocked_reason"))
        or "medical_paper_readiness_not_ready"
    )


def _readiness_ref(*, study_root: Path, owner_result: Mapping[str, Any]) -> str:
    return _text(owner_result.get("readiness_ref")) or str(
        readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)
    )


def _outcome_ref(terminal_kind: str) -> str:
    if terminal_kind == "owner_receipt":
        return OWNER_RECEIPT_RELATIVE_PATH.as_posix()
    return TYPED_BLOCKER_RELATIVE_PATH.as_posix()


def _materialized(*, terminal_kind: str, written_ref: str, closeout_binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "medical_paper_readiness_stage_native_closeout",
        "status": "materialized",
        "stage_id": STAGE_ID,
        "terminal_outcome_kind": terminal_kind,
        "written_ref": written_ref,
        "stage_manifest_ref": STAGE_MANIFEST_RELATIVE_PATH.as_posix(),
        "current_pointer_ref": CURRENT_POINTER_RELATIVE_PATH.as_posix(),
        "closeout_binding": _closeout_binding_for_receipt(
            closeout_binding=closeout_binding,
            receipt_ref=written_ref,
        ),
        "authority_boundary": _authority_boundary(),
    }


def _blocked(*, reason: str, binding: Mapping[str, Any], apply: bool) -> dict[str, Any]:
    return {
        "surface_kind": "medical_paper_readiness_stage_native_closeout",
        "status": "blocked" if apply else "dry_run_blocked",
        "blocked_reason": reason,
        "stage_id": STAGE_ID,
        "closeout_binding": dict(binding) if binding else None,
        "authority_boundary": _authority_boundary(),
    }


def _schema_refs() -> list[str]:
    return [
        "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
        "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
    ]


def _authority_boundary() -> dict[str, Any]:
    return {
        "owner": "MedAutoScience",
        "surface_owner": "MedAutoScience",
        "writes_stage_native_owner_answer": True,
        "writes_publication_eval_latest": False,
        "writes_controller_decision": False,
        "writes_current_package": False,
        "writes_paper_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _unlink_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


__all__ = ["materialize_stage_native_owner_answer"]

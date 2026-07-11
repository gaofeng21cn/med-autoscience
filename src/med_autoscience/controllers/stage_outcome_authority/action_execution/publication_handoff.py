from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_readiness
from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
    typed_blocker as opl_execution_authorization_typed_blocker,
)
from med_autoscience.profiles import WorkspaceProfile

STAGE_ID = "08-publication_package_handoff"
STAGE_ROOT_RELATIVE_PATH = Path("artifacts/stage_outputs") / STAGE_ID
HANDOFF_ROOT_RELATIVE_PATH = Path("artifacts/publication_handoff")
HANDOFF_RECEIPT_RELATIVE_PATH = HANDOFF_ROOT_RELATIVE_PATH / "owner_receipt.json"
TYPED_BLOCKER_RELATIVE_PATH = HANDOFF_ROOT_RELATIVE_PATH / "typed_blocker.json"


def execute_publication_handoff_owner_gate(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    dispatch_payload = _mapping(dispatch)
    study_root = profile.studies_root / study_id
    if not study_root.exists():
        return _blocked_execution(
            study_root=study_root,
            reason="study_root_missing",
            owner_result=None,
        )
    readiness = medical_paper_readiness.read_medical_paper_readiness_surface(
        study_root=study_root,
    )
    closeout_binding = _trusted_closeout_binding(
        dispatch=dispatch_payload,
    )
    if closeout_binding is None:
        return _blocked_execution(
            study_root=study_root,
            reason="opl_execution_authorization_required",
            owner_result=_authorization_required_result(study_root=study_root),
        )
    decision = _handoff_decision(
        study_root=study_root,
        readiness=readiness,
        closeout_binding=closeout_binding,
    )
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None if decision["status"] == "ready_for_human_submission_handoff" else decision["reason"],
            "owner_callable_surface": "publication_handoff_owner_gate.evaluate_terminal_handoff",
            "owner_result": {
                "surface_kind": "publication_handoff_owner_gate_result",
                "status": decision["status"],
                "decision": decision,
                "readiness_ref": str(medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)),
                "will_write_receipt": decision["status"] == "ready_for_human_submission_handoff",
                "will_write_typed_blocker": decision["status"] != "ready_for_human_submission_handoff",
                "authority_boundary": _authority_boundary(),
            },
            "quest_root": str(profile.runtime_root / study_id),
        }
    if decision["status"] == "ready_for_human_submission_handoff":
        owner_result = _write_handoff_receipt(
            study_id=study_id,
            study_root=study_root,
            decision=decision,
            readiness=readiness,
            closeout_binding=closeout_binding,
        )
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "publication_handoff_owner_gate.evaluate_terminal_handoff",
            "owner_result": owner_result,
            "quest_root": str(profile.runtime_root / study_id),
        }
    owner_result = _write_typed_blocker(
        study_id=study_id,
        study_root=study_root,
        decision=decision,
        readiness=readiness,
        closeout_binding=closeout_binding,
    )
    return _blocked_execution(
        study_root=study_root,
        reason=decision["reason"],
        owner_result=owner_result,
    )


def _blocked_execution(
    *,
    study_root: Path,
    reason: str,
    owner_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": reason,
        "owner_callable_surface": "publication_handoff_owner_gate.evaluate_terminal_handoff",
        "owner_result": dict(owner_result) if isinstance(owner_result, Mapping) else owner_result,
        "quest_root": str(study_root),
    }


def _authorization_required_result(*, study_root: Path) -> dict[str, Any]:
    return {
        "surface_kind": "publication_handoff_owner_gate_result",
        "status": "typed_blocker_or_stop_loss",
        "owner_receipt_ref": None,
        "typed_blocker_ref": None,
        "will_write_receipt": False,
        "will_write_typed_blocker": False,
        "typed_blocker": opl_execution_authorization_typed_blocker(),
        "readiness_ref": str(
            medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)
        ),
        "authority_boundary": _authority_boundary(),
    }


def _handoff_decision(
    *,
    study_root: Path,
    readiness: Mapping[str, Any],
    closeout_binding: Mapping[str, Any],
) -> dict[str, Any]:
    closeout_refs = _text_list(closeout_binding.get("closeout_refs"))
    missing_opl_refs = [
        key
        for key in (
            "provider_attempt_ref",
            "attempt_lease_ref",
            "execution_authorization_decision_ref",
            "stage_run_ref",
            "stage_manifest_ref",
            "current_pointer_ref",
            "source_fingerprint",
        )
        if _text(closeout_binding.get(key)) is None
    ]
    if not closeout_refs:
        missing_opl_refs.append("closeout_refs")
    if missing_opl_refs:
        return _decision(
            status="typed_blocker_or_stop_loss",
            reason="opl_stage_run_readback_refs_incomplete",
            next_owner="one-person-lab",
            next_action="opl_family_runtime_attempt_query",
            missing_refs=missing_opl_refs,
        )
    if not readiness:
        return _decision(
            status="typed_blocker_or_stop_loss",
            reason="medical_paper_readiness_missing",
            next_owner="MedAutoScience",
            next_action="materialize_medical_paper_readiness_surface",
            blocked_surfaces=["medical_paper_readiness"],
        )
    if _text(readiness.get("overall_status")) != "ready":
        next_action = _mapping(readiness.get("next_action"))
        return _decision(
            status="typed_blocker_or_stop_loss",
            reason="medical_paper_readiness_not_ready",
            next_owner="MedAutoScience",
            next_action=_text(next_action.get("action_id")) or "complete_medical_paper_readiness_surface",
            blocked_surfaces=[
                str(item["surface_key"])
                for item in _missing_readiness_surfaces(readiness)
                if _text(item.get("surface_key")) is not None
            ],
        )
    missing_handoff_refs = [
        ref
        for ref in (
            STAGE_ROOT_RELATIVE_PATH / "publication_package_manifest.json",
            STAGE_ROOT_RELATIVE_PATH / "publication_gate_receipt.json",
        )
        if not (study_root / ref).is_file()
    ]
    if missing_handoff_refs:
        return _decision(
            status="typed_blocker_or_stop_loss",
            reason="publication_handoff_required_refs_missing",
            next_owner="publication_gate_owner",
            next_action="publication_handoff_owner_gate",
            missing_refs=[ref.as_posix() for ref in missing_handoff_refs],
        )
    return _decision(
        status="ready_for_human_submission_handoff",
        reason="terminal_stage_and_medical_paper_readiness_ready",
        next_owner="human_gate",
        next_action="human_submission_decision",
    )


def _write_handoff_receipt(
    *,
    study_id: str,
    study_root: Path,
    decision: Mapping[str, Any],
    readiness: Mapping[str, Any],
    closeout_binding: Mapping[str, Any],
) -> dict[str, Any]:
    generated_at = _utc_now()
    artifact_refs = _handoff_artifact_refs(
        study_root=study_root,
        readiness=readiness,
        closeout_binding=closeout_binding,
    )
    receipt = _receipt_payload(
        study_root=study_root,
        study_id=study_id,
        artifact_refs=artifact_refs,
        decision=decision,
        readiness=readiness,
        generated_at=generated_at,
        closeout_binding=closeout_binding,
    )
    receipt_path = study_root / HANDOFF_RECEIPT_RELATIVE_PATH
    receipt_binding = _closeout_binding_for_receipt(
        closeout_binding=closeout_binding,
        receipt_ref=HANDOFF_RECEIPT_RELATIVE_PATH.as_posix(),
    )
    receipt["closeout_binding"] = receipt_binding
    _write_json(receipt_path, receipt)
    _unlink_if_exists(study_root / TYPED_BLOCKER_RELATIVE_PATH)
    return {
        "surface_kind": "publication_handoff_owner_gate_result",
        "status": "ready_for_human_submission_handoff",
        "owner_receipt_ref": str(receipt_path),
        "typed_blocker_ref": None,
        "closeout_binding": receipt_binding,
        "readiness_ref": str(medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)),
        "authority_boundary": _authority_boundary(),
    }


def _write_typed_blocker(
    *,
    study_id: str,
    study_root: Path,
    decision: Mapping[str, Any],
    readiness: Mapping[str, Any],
    closeout_binding: Mapping[str, Any],
) -> dict[str, Any]:
    blocker_path = study_root / TYPED_BLOCKER_RELATIVE_PATH
    blocker = _typed_blocker_payload(
        study_root=study_root,
        study_id=study_id,
        decision=decision,
        readiness=readiness,
        generated_at=_utc_now(),
        closeout_binding=closeout_binding,
    )
    blocker_binding = _closeout_binding_for_receipt(
        closeout_binding=closeout_binding,
        receipt_ref=TYPED_BLOCKER_RELATIVE_PATH.as_posix(),
    )
    blocker["closeout_binding"] = blocker_binding
    _write_json(blocker_path, blocker)
    _unlink_if_exists(study_root / HANDOFF_RECEIPT_RELATIVE_PATH)
    return {
        "surface_kind": "publication_handoff_owner_gate_result",
        "status": "typed_blocker_or_stop_loss",
        "owner_receipt_ref": None,
        "typed_blocker_ref": str(blocker_path),
        "closeout_binding": blocker_binding,
        "readiness_ref": str(medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)),
        "authority_boundary": _authority_boundary(),
    }


def _receipt_payload(
    *,
    study_root: Path,
    study_id: str,
    artifact_refs: list[str],
    decision: Mapping[str, Any],
    readiness: Mapping[str, Any],
    generated_at: str,
    closeout_binding: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_id = f"publication-handoff:{study_id}:{_fingerprint([artifact_refs, decision])[:16]}"
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
        "owner": "publication_gate_owner",
        "authority_type": "medical_owner_receipt",
        "receipt_ref": receipt_id,
        "schema_refs": _schema_refs(),
        "capability_refs": [
            "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/medical_owner_receipt",
        ],
        "domain_semantic_refs": {
            "owner_route_refs": [f"publication-handoff-owner-route:{study_id}:{STAGE_ID}"],
            "medical_owner_receipt_refs": [receipt_id],
        },
        "receipt_kind": "publication_handoff_owner_gate",
        "receipt_status": "ready_for_human_submission_handoff",
        "artifact_refs": artifact_refs,
        "produced_artifact_refs": [HANDOFF_RECEIPT_RELATIVE_PATH.as_posix()],
        "consumed_artifact_refs": [
            *artifact_refs,
            _readiness_ref(readiness=readiness, fallback_study_root=study_root),
        ],
        "next_owner_delta": {
            "owner": _text(decision.get("next_owner")) or "human_gate",
            "action": _text(decision.get("next_action")) or "human_submission_decision",
            "reason": _text(decision.get("reason")) or "terminal_stage_and_medical_paper_readiness_ready",
        },
        "idempotency_key": receipt_id,
        "intent_fingerprint": _fingerprint([artifact_refs, decision]),
        "source_fingerprint": _text(closeout_binding.get("source_fingerprint"))
        or _fingerprint([artifact_refs, readiness.get("ready_count"), readiness.get("required_count")]),
        "work_unit_fingerprint": _text(closeout_binding.get("work_unit_fingerprint")),
        "closeout_refs": _text_list(closeout_binding.get("closeout_refs")),
        "recorded_at": generated_at,
        "started_worker": False,
        "body_included": False,
        "refs_only": True,
        "legacy_body_copied": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
        "authority_boundary": _authority_boundary(),
    }


def _typed_blocker_payload(
    *,
    study_root: Path,
    study_id: str,
    decision: Mapping[str, Any],
    readiness: Mapping[str, Any],
    generated_at: str,
    closeout_binding: Mapping[str, Any],
) -> dict[str, Any]:
    blocker_id = _text(decision.get("reason")) or "publication_handoff_owner_gate_blocked"
    blocker_ref = f"publication-handoff-typed-blocker:{study_id}:{_fingerprint([decision, readiness])[:16]}"
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
        "owner": _text(decision.get("next_owner")) or "publication_gate_owner",
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
        "required_input": _text(decision.get("next_action")) or "complete_publication_handoff_owner_gate_inputs",
        "next_safe_action": _text(decision.get("next_action")) or "resolve_typed_blocker",
        "decision": dict(decision),
        "readiness_ref": _readiness_ref(readiness=readiness, fallback_study_root=study_root),
        "artifact_refs": [TYPED_BLOCKER_RELATIVE_PATH.as_posix()],
        "produced_artifact_refs": [TYPED_BLOCKER_RELATIVE_PATH.as_posix()],
        "source_fingerprint": _text(closeout_binding.get("source_fingerprint")),
        "work_unit_fingerprint": _text(closeout_binding.get("work_unit_fingerprint")),
        "closeout_refs": _text_list(closeout_binding.get("closeout_refs")),
        "recorded_at": generated_at,
        "body_included": False,
        "refs_only": True,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
        "authority_boundary": _authority_boundary(),
    }


def _handoff_artifact_refs(
    *,
    study_root: Path,
    readiness: Mapping[str, Any],
    closeout_binding: Mapping[str, Any],
) -> list[str]:
    refs = [
        _readiness_ref(readiness=readiness, fallback_study_root=study_root),
        (STAGE_ROOT_RELATIVE_PATH / "publication_package_manifest.json").as_posix(),
        (STAGE_ROOT_RELATIVE_PATH / "publication_gate_receipt.json").as_posix(),
        _text(closeout_binding.get("provider_attempt_ref")),
        _text(closeout_binding.get("attempt_lease_ref")),
        _text(closeout_binding.get("execution_authorization_decision_ref")),
        _text(closeout_binding.get("stage_run_ref")),
        _text(closeout_binding.get("stage_manifest_ref")),
        _text(closeout_binding.get("current_pointer_ref")),
        *_text_list(closeout_binding.get("closeout_refs")),
    ]
    return list(dict.fromkeys(ref for ref in refs if ref is not None))


def _missing_readiness_surfaces(readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in readiness.get("capability_surfaces") or []
        if isinstance(item, Mapping)
        and item.get("required_for_ready") is True
        and _text(item.get("status")) != "present"
    ]


def _decision(
    *,
    status: str,
    reason: str,
    next_owner: str,
    next_action: str,
    blocked_surfaces: list[str] | None = None,
    missing_refs: list[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "reason": reason,
        "next_owner": next_owner,
        "next_action": next_action,
        "publication_ready_authorized": False,
        "submission_ready_authorized": False,
        "current_package_write_allowed": False,
        "quality_verdict_authorized": False,
    }
    if blocked_surfaces:
        result["blocked_surfaces"] = blocked_surfaces
    if missing_refs:
        result["missing_refs"] = missing_refs
    return result


def _schema_refs() -> list[str]:
    return [
        "contracts/stage_run_kernel_profile.json#/stage_folder_manifest/closeout_contract",
        "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
    ]


def _authority_boundary() -> dict[str, Any]:
    return {
        "owner": "MedAutoScience",
        "surface_owner": "MedAutoScience",
        "writes_mas_truth": False,
        "writes_publication_eval_latest": False,
        "writes_controller_decision": False,
        "writes_current_package": False,
        "writes_memory_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
    }


def _trusted_closeout_binding(
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    authorization = first_trusted_opl_execution_authorization(
        dispatch.get("opl_execution_authorization"),
        dispatch.get("opl_provider_attempt"),
        dispatch.get("stage_attempt"),
        _mapping(dispatch.get("prompt_contract")).get("opl_execution_authorization"),
        _mapping(dispatch.get("prompt_contract")).get("opl_provider_attempt"),
        _mapping(dispatch.get("prompt_contract")).get("stage_attempt"),
        _mapping(dispatch.get("owner_route")).get("opl_execution_authorization"),
        _mapping(dispatch.get("owner_route")).get("opl_provider_attempt"),
        _mapping(dispatch.get("owner_route")).get("stage_attempt"),
    )
    if authorization is None:
        return None
    action_type = _first_text(
        dispatch.get("action_type"),
        _mapping(dispatch.get("prompt_contract")).get("action_type"),
        _mapping(dispatch.get("owner_route")).get("action_type"),
    )
    if action_type != "publication_handoff_owner_gate":
        return None
    closeout_refs = _closeout_refs(dispatch=dispatch, authorization=authorization)
    provider_attempt_ref = _text(authorization.get("provider_attempt_ref"))
    attempt_lease_ref = (
        _text(authorization.get("attempt_lease_ref"))
        or _text(authorization.get("lease_ref"))
        or _text(authorization.get("lease_id"))
    )
    execution_authorization_decision_ref = _text(
        authorization.get("execution_authorization_decision_ref")
    ) or _text(authorization.get("authorization_decision_ref"))
    source_fingerprint = _source_fingerprint(dispatch=dispatch, authorization=authorization)
    stage_run_id = _binding_text(
        dispatch,
        "stage_run_id",
        fallback=None,
    )
    return {
        "surface_kind": "publication_handoff_closeout_binding",
        "trusted_opl_execution_authorization": True,
        "bound_to_stage_run": stage_run_id is not None,
        "bound_to_stage_manifest": True,
        "bound_to_current_pointer": True,
        "bound_to_source_fingerprint": source_fingerprint is not None,
        "provider_attempt_ref": provider_attempt_ref,
        "attempt_id": provider_attempt_ref,
        "attempt_lease_ref": attempt_lease_ref,
        "attempt_lease_status": _text(authorization.get("attempt_lease_status")) or "active",
        "execution_authorization_decision_ref": execution_authorization_decision_ref,
        "stage_run_id": stage_run_id,
        "stage_run_ref": _binding_text(dispatch, "stage_run_ref", fallback=stage_run_id),
        "stage_manifest_ref": _binding_text(
            dispatch,
            "stage_manifest_ref",
            fallback=None,
        ),
        "current_pointer_ref": _binding_text(
            dispatch,
            "current_pointer_ref",
            fallback=None,
        ),
        "closeout_refs": closeout_refs,
        "source_fingerprint": source_fingerprint,
        "work_unit_fingerprint": _work_unit_fingerprint(dispatch=dispatch, source_fingerprint=source_fingerprint),
        "idempotency_key": _first_text(
            authorization.get("idempotency_key"),
            _mapping(dispatch.get("owner_route")).get("idempotency_key"),
            dispatch.get("idempotency_key"),
            _mapping(dispatch.get("prompt_contract")).get("idempotency_key"),
            _mapping(dispatch.get("closeout_binding")).get("idempotency_key"),
            _mapping(_mapping(dispatch.get("prompt_contract")).get("closeout_binding")).get("idempotency_key"),
            source_fingerprint,
        ),
        "body_included": False,
    }


def _closeout_binding_for_receipt(
    *,
    closeout_binding: Mapping[str, Any],
    receipt_ref: str,
) -> dict[str, Any]:
    return {
        **dict(closeout_binding),
        "receipt_ref": receipt_ref,
    }


def _closeout_refs(*, dispatch: Mapping[str, Any], authorization: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for candidate in (
        dispatch.get("closeout_refs"),
        _mapping(dispatch.get("prompt_contract")).get("closeout_refs"),
        _mapping(dispatch.get("owner_route")).get("closeout_refs"),
        _mapping(dispatch.get("closeout_binding")).get("closeout_refs"),
        _mapping(_mapping(dispatch.get("prompt_contract")).get("closeout_binding")).get("closeout_refs"),
    ):
        refs.extend(_text_list(candidate))
    for key in (
        "typed_closeout_ref",
        "typed_closeout_receipt_ref",
        "attempt_receipt_ref",
        "receipt_ref",
        "stage_packet_ref",
    ):
        if ref := _text(authorization.get(key)):
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _source_fingerprint(*, dispatch: Mapping[str, Any], authorization: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(dispatch.get("owner_route"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    closeout_binding = _mapping(dispatch.get("closeout_binding")) or _mapping(
        prompt_contract.get("closeout_binding")
    )
    return _first_text(
        authorization.get("source_fingerprint"),
        closeout_binding.get("source_fingerprint"),
        dispatch.get("source_fingerprint"),
        prompt_contract.get("source_fingerprint"),
        owner_route.get("source_fingerprint"),
        source_refs.get("source_fingerprint"),
        currentness_basis.get("source_fingerprint"),
    )


def _work_unit_fingerprint(
    *,
    dispatch: Mapping[str, Any],
    source_fingerprint: str | None,
) -> str | None:
    owner_route = _mapping(dispatch.get("owner_route"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return _first_text(
        dispatch.get("work_unit_fingerprint"),
        prompt_contract.get("work_unit_fingerprint"),
        owner_route.get("work_unit_fingerprint"),
        source_refs.get("work_unit_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        source_fingerprint,
    )


def _binding_text(dispatch: Mapping[str, Any], key: str, *, fallback: str | None) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    closeout_binding = _mapping(dispatch.get("closeout_binding")) or _mapping(
        prompt_contract.get("closeout_binding")
    )
    return _first_text(
        closeout_binding.get(key),
        dispatch.get(key),
        prompt_contract.get(key),
        _mapping(dispatch.get("owner_route")).get(key),
        fallback,
    )


def _readiness_ref(*, readiness: Mapping[str, Any], fallback_study_root: Path) -> str:
    return str(
        medical_paper_readiness.stable_medical_paper_readiness_path(
            study_root=Path(_text(readiness.get("study_root")) or fallback_study_root)
        )
    )


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


__all__ = ["execute_publication_handoff_owner_gate"]

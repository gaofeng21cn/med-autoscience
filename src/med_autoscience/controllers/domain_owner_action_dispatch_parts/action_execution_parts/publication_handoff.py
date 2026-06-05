from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_readiness
from med_autoscience.controllers import stage_artifact_index
from med_autoscience.profiles import WorkspaceProfile


STAGE_ID = "08-publication_package_handoff"
STAGE_ROOT_RELATIVE_PATH = Path("artifacts/stage_outputs") / STAGE_ID
HANDOFF_RECEIPT_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "handoff_owner_receipt.json"
STAGE_RECEIPT_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "receipts" / "owner_receipt.json"
TYPED_BLOCKER_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "receipts" / "typed_blocker.json"
STAGE_MANIFEST_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "stage_manifest.json"
CURRENT_OWNER_DELTA_RELATIVE_PATH = STAGE_ROOT_RELATIVE_PATH / "projection" / "current_owner_delta.json"


def execute_publication_handoff_owner_gate(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    del dispatch
    study_root = profile.studies_root / study_id
    if not study_root.exists():
        return _blocked_execution(
            study_root=study_root,
            reason="study_root_missing",
            owner_result=None,
        )
    index = stage_artifact_index.build_stage_artifact_index(
        study_id=study_id,
        study_root=study_root,
    )
    readiness = medical_paper_readiness.read_medical_paper_readiness_surface(
        study_root=study_root,
    )
    decision = _handoff_decision(study_root=study_root, index=index, readiness=readiness)
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
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            decision=decision,
            index=index,
            readiness=readiness,
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


def _handoff_decision(
    *,
    study_root: Path,
    index: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> dict[str, Any]:
    terminal_stage = _terminal_stage(index)
    if not terminal_stage:
        return _decision(
            status="typed_blocker_or_stop_loss",
            reason="terminal_publication_handoff_stage_missing",
            next_owner="MedAutoScience",
            next_action="materialize_stage_artifact_delta",
        )
    if _text(_mapping(index.get("current_stage")).get("stage_id")) != STAGE_ID:
        return _decision(
            status="typed_blocker_or_stop_loss",
            reason="terminal_publication_handoff_stage_not_current",
            next_owner=_text(_mapping(index.get("next_owner_action")).get("next_owner")) or "MedAutoScience",
            next_action=_text(_mapping(index.get("next_owner_action")).get("action_type")) or "materialize_stage_artifact_delta",
        )
    if _text(terminal_stage.get("artifact_status")) != "artifact_delta_present":
        return _decision(
            status="typed_blocker_or_stop_loss",
            reason=_text(_mapping(terminal_stage.get("artifact_classification")).get("fail_closed_reason"))
            or "terminal_publication_handoff_artifact_delta_missing",
            next_owner="MedAutoScience",
            next_action="materialize_stage_artifact_delta",
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
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    decision: Mapping[str, Any],
    index: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> dict[str, Any]:
    generated_at = _utc_now()
    artifact_refs = _terminal_artifact_refs(index)
    receipt = _receipt_payload(
        study_root=study_root,
        study_id=study_id,
        artifact_refs=artifact_refs,
        decision=decision,
        readiness=readiness,
        generated_at=generated_at,
    )
    receipt_path = study_root / HANDOFF_RECEIPT_RELATIVE_PATH
    stage_receipt_path = study_root / STAGE_RECEIPT_RELATIVE_PATH
    _write_json(receipt_path, receipt)
    _write_json(stage_receipt_path, receipt)
    _unlink_if_exists(study_root / TYPED_BLOCKER_RELATIVE_PATH)
    _update_stage_manifest(
        study_root=study_root,
        owner_receipt_refs=[
            "handoff_owner_receipt.json",
            "receipts/owner_receipt.json",
        ],
        typed_blocker_refs=[],
    )
    _write_current_owner_delta(
        study_root=study_root,
        owner="human_gate",
        action="human_submission_decision",
        reason="publication_handoff_owner_receipt_ready",
        source_ref=HANDOFF_RECEIPT_RELATIVE_PATH.as_posix(),
    )
    return {
        "surface_kind": "publication_handoff_owner_gate_result",
        "status": "ready_for_human_submission_handoff",
        "owner_receipt_ref": str(receipt_path),
        "stage_owner_receipt_ref": str(stage_receipt_path),
        "typed_blocker_ref": None,
        "readiness_ref": str(medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)),
        "authority_boundary": _authority_boundary(),
    }


def _write_typed_blocker(
    *,
    study_id: str,
    study_root: Path,
    decision: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> dict[str, Any]:
    blocker_path = study_root / TYPED_BLOCKER_RELATIVE_PATH
    blocker = _typed_blocker_payload(
        study_root=study_root,
        study_id=study_id,
        decision=decision,
        readiness=readiness,
        generated_at=_utc_now(),
    )
    _write_json(blocker_path, blocker)
    _update_stage_manifest(
        study_root=study_root,
        owner_receipt_refs=[],
        typed_blocker_refs=["receipts/typed_blocker.json"],
    )
    _write_current_owner_delta(
        study_root=study_root,
        owner=_text(decision.get("next_owner")) or "MedAutoScience",
        action=_text(decision.get("next_action")) or "resolve_typed_blocker",
        reason=_text(decision.get("reason")) or "publication_handoff_owner_gate_blocked",
        source_ref=TYPED_BLOCKER_RELATIVE_PATH.as_posix(),
    )
    return {
        "surface_kind": "publication_handoff_owner_gate_result",
        "status": "typed_blocker_or_stop_loss",
        "owner_receipt_ref": None,
        "typed_blocker_ref": str(blocker_path),
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
) -> dict[str, Any]:
    receipt_id = f"publication-handoff:{study_id}:{_fingerprint([artifact_refs, decision])[:16]}"
    return {
        "surface_kind": "mas_stage_owner_receipt",
        "schema_version": 1,
        "receipt_id": receipt_id,
        "study_id": study_id,
        "quest_id": study_id,
        "stage_id": STAGE_ID,
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
        "source_fingerprint": _fingerprint([artifact_refs, readiness.get("ready_count"), readiness.get("required_count")]),
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
    owner_receipt_refs: list[str],
    typed_blocker_refs: list[str],
) -> None:
    path = study_root / STAGE_MANIFEST_RELATIVE_PATH
    manifest = _read_json_object(path)
    if not manifest:
        return
    manifest["owner_receipt_refs"] = owner_receipt_refs
    manifest["typed_blocker_refs"] = typed_blocker_refs
    manifest["terminal_status"] = "blocked" if typed_blocker_refs else "completed"
    _write_json(path, manifest)


def _write_current_owner_delta(
    *,
    study_root: Path,
    owner: str,
    action: str,
    reason: str,
    source_ref: str,
) -> None:
    _write_json(
        study_root / CURRENT_OWNER_DELTA_RELATIVE_PATH,
        {
            "owner": owner,
            "action": action,
            "reason": reason,
            "source_ref": source_ref,
        },
    )


def _terminal_stage(index: Mapping[str, Any]) -> dict[str, Any]:
    for stage in index.get("stages") or []:
        if isinstance(stage, Mapping) and _text(stage.get("stage_id")) == STAGE_ID:
            return dict(stage)
    return {}


def _terminal_artifact_refs(index: Mapping[str, Any]) -> list[str]:
    terminal = _terminal_stage(index)
    refs = [
        _text(item.get("ref"))
        for item in terminal.get("observed_artifact_refs") or []
        if isinstance(item, Mapping)
    ]
    return [ref for ref in refs if ref is not None]


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
        "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
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


def _readiness_ref(*, readiness: Mapping[str, Any], fallback_study_root: Path) -> str:
    return str(
        medical_paper_readiness.stable_medical_paper_readiness_path(
            study_root=Path(_text(readiness.get("study_root")) or fallback_study_root)
        )
    )


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


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


__all__ = ["execute_publication_handoff_owner_gate"]

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_artifact_operating_contract import (
    CONSUMABILITY_REQUIRED_CHECKS,
    consumability_authority_boundary,
    consumability_failed_checks,
    consumability_insufficient_authority_refs,
    consumability_next_owner_delta,
)
from med_autoscience.controllers.mas_stage_semantic_receipts import (
    validate_mas_stage_semantic_receipt,
)


STAGE_RUN_KERNEL_PROFILE_REF = "contracts/stage_run_kernel_profile.json"


def stage_run_kernel_projection_from_stage_folder(
    stage_root: str | Path,
    *,
    manifest_ref: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(stage_root).expanduser().resolve()
    manifest_path = _manifest_path(root=root, manifest_ref=manifest_ref)
    manifest = _read_json_object(manifest_path)
    stage_id = _text(manifest.get("stage_id")) or root.name
    attempt_id = _text(manifest.get("attempt_id"))
    owner_receipt_path = _receipt_path(
        root=root,
        refs=_text_list(manifest.get("owner_receipt_refs")),
        default_name="owner_receipt.json",
    )
    typed_blocker_path = _receipt_path(
        root=root,
        refs=_text_list(manifest.get("typed_blocker_refs")),
        default_name="typed_blocker.json",
    )
    owner_receipt = _valid_owner_receipt(path=owner_receipt_path)
    typed_blocker = _valid_typed_blocker(path=typed_blocker_path)
    status, completion_authority, source_payload, source_path, source_kind = _terminal_authority(
        owner_receipt=owner_receipt,
        owner_receipt_path=owner_receipt_path,
        typed_blocker=typed_blocker,
        typed_blocker_path=typed_blocker_path,
    )
    if status is None:
        status = _non_terminal_status(manifest)
    artifact_consumability_gate = _artifact_consumability_gate(
        manifest=manifest,
        manifest_path=manifest_path,
        stage_id=stage_id,
        attempt_id=attempt_id,
        owner_receipt=owner_receipt,
        typed_blocker=typed_blocker,
    )
    current_owner_delta = _current_owner_delta(
        status=status,
        stage_id=stage_id,
        source_payload=source_payload,
        source_path=source_path,
        source_kind=source_kind,
        manifest_path=manifest_path,
    )
    return {
        "surface_kind": "stage_run_kernel_projection",
        "schema_version": 1,
        "profile_ref": STAGE_RUN_KERNEL_PROFILE_REF,
        "stage_id": stage_id,
        "stage_run_id": _text(manifest.get("stage_run_id")),
        "attempt_id": attempt_id,
        "generation": attempt_id or "declared",
        "work_unit": _text(manifest.get("work_unit")),
        "status": status,
        "completion_authority": completion_authority,
        "current_owner_delta": current_owner_delta,
        "manifest_ref": str(manifest_path),
        "owner_receipt_ref": str(owner_receipt_path) if owner_receipt_path else None,
        "typed_blocker_ref": str(typed_blocker_path) if typed_blocker_path else None,
        "closeout_binding": _closeout_binding_projection(
            manifest=manifest,
            source_payload=source_payload,
        ),
        "receipt_validation": _receipt_validation_projection(
            owner_receipt=owner_receipt,
            typed_blocker=typed_blocker,
        ),
        "artifact_consumability_gate": artifact_consumability_gate,
        "evidence_projection": _evidence_projection(manifest=manifest, source_payload=source_payload),
        "state_invariants": {
            "owner_receipt_or_typed_blocker_required": True,
            "artifact_consumability_gate_required": True,
            "file_presence_counts_as_completion": False,
            "manifest_hash_counts_as_consumable": False,
            "provider_completed_counts_as_completion": False,
            "latest_json_counts_as_completion": False,
            "latest_json_counts_as_transition_authority": False,
            "read_model_counts_as_transition_authority": False,
            "read_model_counts_as_consumable": False,
            "manifest_backed_receipt_or_blocker_required": True,
        },
        "authority": {
            "derived_projection": True,
            "writes_mas_truth": False,
            "writes_publication_eval_latest": False,
            "claims_publication_ready": False,
            "can_authorize_quality_verdict": False,
        },
        "body_included": False,
    }


def _artifact_consumability_gate(
    *,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    stage_id: str,
    attempt_id: str | None,
    owner_receipt: Mapping[str, Any] | None,
    typed_blocker: Mapping[str, Any] | None,
) -> dict[str, Any]:
    checks = {
        "role": bool(
            _text_list(manifest.get("required_outputs"))
            or _text_list(manifest.get("artifact_refs"))
            or _mapping_items(manifest.get("required_role_artifacts"))
        ),
        "hash": bool(_mapping_items(manifest.get("output_hashes"))),
        "source": bool(_text_list(manifest.get("present_outputs"))),
        "current_truth": _text(manifest.get("current_pointer_state")) == "current_pointer_promoted",
        "receipt_authority": owner_receipt is not None or typed_blocker is not None,
        "lineage": bool(
            _text_list(manifest.get("lineage_refs"))
            or _text(manifest.get("lineage_ref"))
            or _text(manifest.get("prov_ref"))
        ),
        "retention_restore": bool(
            _text_list(manifest.get("retention_refs"))
            or _text_list(manifest.get("restore_refs"))
            or _text(manifest.get("retention_ref"))
            or _text(manifest.get("restore_ref"))
        ),
        "domain_validation": bool(
            owner_receipt is not None
            or typed_blocker is not None
            or _text_list(manifest.get("domain_decision_receipt_refs"))
        ),
    }
    failed_checks = consumability_failed_checks(checks)
    return {
        "surface_kind": "stage_artifact_consumability_projection",
        "required_checks": list(CONSUMABILITY_REQUIRED_CHECKS),
        "status": "passed" if not failed_checks else "blocked",
        "fail_closed": bool(failed_checks),
        "checks": checks,
        "failed_checks": failed_checks,
        "next_owner_delta": consumability_next_owner_delta(
            stage_id=stage_id,
            attempt_id=attempt_id,
            failed_checks=failed_checks,
            source_ref=str(manifest_path),
        ),
        "insufficient_authority_refs": consumability_insufficient_authority_refs(),
        "authority_boundary": consumability_authority_boundary(),
        "body_included": False,
    }


def stage_run_kernel_projection_from_stage_state(
    *,
    selected_stage: Mapping[str, Any],
    study_root: str | Path | None = None,
) -> dict[str, Any] | None:
    stage_folder = _mapping(selected_stage.get("stage_folder_contract"))
    stage_folder_ref = _text(stage_folder.get("stage_folder_ref"))
    if stage_folder_ref is None:
        return None
    root = _resolve_ref(
        stage_folder_ref,
        base=Path(study_root).expanduser().resolve() if study_root else None,
    )
    manifest_ref = _text(stage_folder.get("manifest_ref"))
    manifest_path = (
        _resolve_ref(
            manifest_ref,
            base=Path(study_root).expanduser().resolve() if study_root else None,
        )
        if manifest_ref
        else None
    )
    if not root.exists() and (manifest_path is None or not manifest_path.exists()):
        return None
    return stage_run_kernel_projection_from_stage_folder(root, manifest_ref=manifest_path)


def _terminal_authority(
    *,
    owner_receipt: dict[str, Any] | None,
    owner_receipt_path: Path | None,
    typed_blocker: dict[str, Any] | None,
    typed_blocker_path: Path | None,
) -> tuple[str | None, str | None, dict[str, Any] | None, Path | None, str | None]:
    if typed_blocker is not None and typed_blocker_path is not None:
        return "TypedBlocked", "typed_blocker", typed_blocker, typed_blocker_path, "typed_blocker"
    if owner_receipt is not None and owner_receipt_path is not None:
        return "DomainAccepted", "owner_receipt", owner_receipt, owner_receipt_path, "owner_receipt"
    return None, None, None, None, None


def _non_terminal_status(manifest: Mapping[str, Any]) -> str:
    terminal_status = _text(manifest.get("terminal_status"))
    if terminal_status in {"success", "completed", "blocked", "failed", "deferred", "skipped"}:
        return "Terminalizing"
    if _text_list(manifest.get("present_outputs")):
        return "Running"
    if _text_list(manifest.get("input_refs")):
        return "InputsReady"
    return "Declared"


def _current_owner_delta(
    *,
    status: str,
    stage_id: str,
    source_payload: Mapping[str, Any] | None,
    source_path: Path | None,
    source_kind: str | None,
    manifest_path: Path,
) -> dict[str, Any]:
    if status == "DomainAccepted" and source_payload is not None and source_path is not None:
        delta = _mapping(source_payload.get("next_owner_delta"))
        return {
            "owner": _text(delta.get("owner")) or "MedAutoScience",
            "action": _text(delta.get("action")) or "advance_stage_from_owner_receipt",
            "reason": _text(delta.get("reason")) or "owner_receipt_consumed",
            "source_ref": str(source_path),
            "source_kind": source_kind,
        }
    if status == "TypedBlocked" and source_payload is not None and source_path is not None:
        return {
            "owner": _text(source_payload.get("owner")) or "MedAutoScience",
            "action": _text(source_payload.get("next_safe_action")) or "resolve_typed_blocker",
            "reason": _text(source_payload.get("blocker_id")) or "typed_blocker",
            "required_input": _text(source_payload.get("required_input")),
            "blocked_surface": _text(source_payload.get("blocked_surface")) or stage_id,
            "source_ref": str(source_path),
            "source_kind": source_kind,
        }
    return {
        "owner": "MedAutoScience",
        "action": "consume_closeout_and_emit_owner_receipt_or_typed_blocker",
        "reason": "manifest_backed_receipt_or_typed_blocker_required",
        "source_ref": str(manifest_path),
        "source_kind": "stage_manifest",
    }


def _receipt_validation_projection(
    *,
    owner_receipt: Mapping[str, Any] | None,
    typed_blocker: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "owner_receipt_status": _text(_mapping(owner_receipt).get("_validation_status")),
        "typed_blocker_status": _text(_mapping(typed_blocker).get("_validation_status")),
        "manifest_validity_is_semantic_receipt_validity": False,
        "receipt_body_read": False,
        "body_included": False,
    }


def _evidence_projection(
    *,
    manifest: Mapping[str, Any],
    source_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    latest_json_ref = _text(_mapping(source_payload).get("publication_eval_projection_ref"))
    result: dict[str, Any] = {
        "latest_json_ref": latest_json_ref,
        "latest_json_is_authority": False,
    }
    if latest_json_ref is None:
        result["outputs_present"] = _text_list(manifest.get("present_outputs"))
    return result


def _closeout_binding_projection(
    *,
    manifest: Mapping[str, Any],
    source_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    binding = _mapping(_mapping(source_payload).get("closeout_binding")) or _mapping(
        manifest.get("closeout_binding")
    )
    return {
        "surface_kind": "publication_handoff_closeout_binding_projection",
        "trusted_opl_execution_authorization": bool(
            binding.get("trusted_opl_execution_authorization")
        ),
        "bound_to_stage_run": bool(binding.get("bound_to_stage_run")),
        "bound_to_stage_manifest": bool(binding.get("bound_to_stage_manifest")),
        "bound_to_current_pointer": bool(binding.get("bound_to_current_pointer")),
        "bound_to_source_fingerprint": bool(binding.get("bound_to_source_fingerprint")),
        "provider_attempt_ref": _text(binding.get("provider_attempt_ref")),
        "stage_run_id": _text(binding.get("stage_run_id")) or _text(manifest.get("stage_run_id")),
        "stage_run_ref": _text(binding.get("stage_run_ref")) or _text(manifest.get("stage_run_ref")),
        "stage_manifest_ref": _text(binding.get("stage_manifest_ref"))
        or _text(manifest.get("stage_manifest_ref")),
        "current_pointer_ref": _text(binding.get("current_pointer_ref"))
        or _text(manifest.get("current_pointer_ref")),
        "closeout_refs": _text_list(binding.get("closeout_refs"))
        or _text_list(manifest.get("closeout_binding_refs")),
        "source_fingerprint": _text(binding.get("source_fingerprint"))
        or _text(manifest.get("source_fingerprint")),
        "work_unit_fingerprint": _text(binding.get("work_unit_fingerprint"))
        or _text(manifest.get("work_unit_fingerprint")),
        "receipt_ref": _text(binding.get("receipt_ref")),
        "body_included": False,
    }


def _valid_owner_receipt(*, path: Path | None) -> dict[str, Any] | None:
    payload = _read_json_object(path)
    if not payload:
        return None
    validation = validate_mas_stage_semantic_receipt(payload)
    if validation.get("status") != "accepted":
        return None
    return {**payload, "_validation_status": "accepted"}


def _valid_typed_blocker(*, path: Path | None) -> dict[str, Any] | None:
    payload = _read_json_object(path)
    if not payload:
        return None
    validation = validate_mas_stage_semantic_receipt(payload)
    if validation.get("status") != "typed_blocker":
        return None
    return {**payload, "_validation_status": "typed_blocker"}


def _manifest_path(*, root: Path, manifest_ref: str | Path | None) -> Path:
    if manifest_ref is not None:
        return Path(manifest_ref).expanduser().resolve()
    for name in ("stage_manifest.json", "stage_artifact_manifest.json", "manifest.json"):
        path = root / name
        if path.exists():
            return path.resolve()
    return (root / "stage_manifest.json").resolve()


def _receipt_path(*, root: Path, refs: list[str], default_name: str) -> Path | None:
    for ref in refs:
        path = _resolve_ref(ref, base=root)
        if path.exists():
            return path
    default_path = root / "receipts" / default_name
    if default_path.exists():
        return default_path.resolve()
    return None


def _resolve_ref(ref: str | Path, *, base: Path | None) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    if base is not None:
        return (base / path).resolve()
    return path.resolve()


def _read_json_object(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_items(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


__all__ = [
    "STAGE_RUN_KERNEL_PROFILE_REF",
    "stage_run_kernel_projection_from_stage_folder",
    "stage_run_kernel_projection_from_stage_state",
]

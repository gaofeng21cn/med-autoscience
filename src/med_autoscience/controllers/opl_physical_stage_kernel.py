from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.opl_artifact_operating_contract import (
    CONSUMABILITY_REQUIRED_CHECKS,
    consumability_authority_boundary,
    consumability_failed_checks,
    consumability_insufficient_authority_refs,
    consumability_next_owner_delta,
)

STAGE_ARTIFACT_RUNTIME_CONTRACT_REF = "contracts/opl-framework/stage-artifact-runtime-contract.json"


def physical_stage_kernel_projection(
    *,
    study_id: str,
    stage_ids: tuple[str, ...],
    domain_stage_pack: Mapping[str, Any],
) -> dict[str, Any]:
    locator = _locator(study_id=study_id, domain_stage_pack=domain_stage_pack)
    state_root = _opl_state_root()
    deliverable_root = _deliverable_root(state_root=state_root, locator=locator) if state_root else None
    current_pointer = _current_pointer(deliverable_root=deliverable_root)
    stages = {
        stage_id: _stage_projection(
            deliverable_root=deliverable_root,
            stage_id=stage_id,
            current_pointer=current_pointer,
        )
        for stage_id in stage_ids
    }
    observed = any(stage["status"] == "observed" for stage in stages.values())
    return {
        "surface_kind": "mas_opl_physical_stage_folder_kernel_projection",
        "contract_ref": STAGE_ARTIFACT_RUNTIME_CONTRACT_REF,
        "source_of_truth": "opl_physical_stage_folder_kernel",
        "status": "observed" if observed else "missing",
        "locator": locator,
        "state_root": str(state_root) if state_root else None,
        "deliverable_root": str(deliverable_root) if deliverable_root else None,
        "current_pointer_ref": str(deliverable_root / "current.json") if deliverable_root else None,
        "current_pointer": current_pointer,
        "body_included": False,
        "authority_boundary": {
            "opl_can_write_mas_truth": False,
            "opl_can_create_mas_owner_receipt": False,
            "mas_keeps_domain_authority": True,
        },
        "stages": stages,
    }


def stage_physical_kernel(
    physical_kernel: Mapping[str, Any],
    stage_id: str,
) -> dict[str, Any]:
    stages = physical_kernel.get("stages")
    if not isinstance(stages, Mapping):
        return {"status": "missing", "stage_id": stage_id}
    stage = stages.get(stage_id)
    return dict(stage) if isinstance(stage, Mapping) else {"status": "missing", "stage_id": stage_id}


def physical_artifact_classification(
    *,
    stage_folder_contract: Mapping[str, Any],
    physical_stage_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    current = sorted(str(item) for item in physical_stage_kernel.get("current_outputs") or [])
    missing_outputs = sorted(
        str(item)
        for item in physical_stage_kernel.get("required_outputs") or []
        if str(item) not in set(current)
    )
    promotion = _mapping(physical_stage_kernel.get("promotion"))
    semantic_validation = _mapping(physical_stage_kernel.get("semantic_validation"))
    consumability = _mapping(physical_stage_kernel.get("consumability"))
    lineage = _mapping(physical_stage_kernel.get("lineage"))
    retention = _mapping(physical_stage_kernel.get("retention"))
    pointer_current = promotion.get("state") == "current_pointer_promoted"
    semantically_accepted = semantic_validation.get("status") == "accepted"
    consumable = consumability.get("status") == "passed"
    status = "current" if current and not missing_outputs and pointer_current and semantically_accepted and consumable else "missing"
    fail_closed_reason = _physical_fail_closed_reason(
        missing_outputs=missing_outputs,
        promotion=promotion,
        semantic_validation=semantic_validation,
        consumability=consumability,
    )
    return {
        "surface_kind": "stage_artifact_classification",
        "contract_ref": f"{STAGE_ARTIFACT_RUNTIME_CONTRACT_REF}#/read_model_semantics",
        "source_of_truth": "opl_physical_stage_folder_kernel",
        "status": status,
        "current": current,
        "historical": [],
        "missing_manifest_or_receipt": [],
        "orphan": [],
        "broken": [],
        "missing": missing_outputs,
        "fail_closed": status != "current",
        "fail_closed_reason": None if status == "current" else fail_closed_reason,
        "manifest_ref": str(stage_folder_contract["manifest_ref"]),
        "receipt_ref": str(stage_folder_contract["receipt_ref"]),
        "current_pointer_basis": {
            "existing_artifacts": bool(current),
            "manifest_valid": bool(physical_stage_kernel.get("manifest_ref")),
            "receipt_accepted": bool(physical_stage_kernel.get("owner_receipt_refs")),
            "current_pointer_promoted": pointer_current,
            "semantic_receipt_valid": semantically_accepted,
            "consumability_passed": consumable,
        },
        "latest_attempt_id": physical_stage_kernel.get("latest_attempt_id"),
        "promotion": promotion,
        "semantic_validation": semantic_validation,
        "consumability": consumability,
        "lineage": lineage,
        "retention": retention,
        "legacy_declared_refs_fallback": False,
        "manifest_hash_refs": list(physical_stage_kernel.get("manifest_hash_refs") or []),
        "evidence_hash_refs": list(physical_stage_kernel.get("evidence_hash_refs") or []),
        "receipt_hash_refs": list(physical_stage_kernel.get("receipt_hash_refs") or []),
        "owner_receipt_refs": list(physical_stage_kernel.get("owner_receipt_refs") or []),
        "typed_blocker_refs": list(physical_stage_kernel.get("typed_blocker_refs") or []),
        "decision_receipt_refs": list(physical_stage_kernel.get("decision_receipt_refs") or []),
        "conformance_refs": dict(physical_stage_kernel.get("conformance_refs") or {}),
        "body_included": False,
    }


def _stage_projection(
    *,
    deliverable_root: Path | None,
    stage_id: str,
    current_pointer: Mapping[str, Any],
) -> dict[str, Any]:
    if deliverable_root is None:
        return _missing_stage(stage_id=stage_id, reason="missing_opl_state_dir")
    stage_root = _stage_root(deliverable_root=deliverable_root, stage_id=stage_id)
    if stage_root is None:
        return _missing_stage(stage_id=stage_id, reason="missing_stage_folder")
    latest_pointer = stage_root / "latest"
    latest_attempt_id = _read_text(latest_pointer)
    attempt_root = stage_root / "attempts" / latest_attempt_id if latest_attempt_id else None
    if attempt_root is None or not attempt_root.exists():
        return _missing_stage(stage_id=stage_id, reason="missing_latest_attempt")
    manifest_ref = attempt_root / "manifest.json"
    manifest = _read_json(manifest_ref)
    stage_ref = stage_root / "stage.json"
    attempt_ref = attempt_root / "attempt.json"
    manifest_hash_refs = _hash_refs(manifest.get("output_hashes") if manifest else None)
    evidence_hash_refs = _hash_refs(manifest.get("evidence_hashes") if manifest else None)
    receipt_hash_refs = _hash_refs(manifest.get("receipt_hashes") if manifest else None)
    owner_receipt_refs = _text_list(manifest.get("owner_receipt_refs") if manifest else None)
    typed_blocker_refs = _text_list(manifest.get("typed_blocker_refs") if manifest else None)
    decision_receipt_refs = _text_list(manifest.get("decision_receipt_refs") if manifest else None)
    receipt_file_ref = _first_receipt_file(attempt_root / "receipts")
    lineage_events = deliverable_root / "lineage" / "events.jsonl"
    lineage_graph = deliverable_root / "lineage" / "graph.json"
    required_outputs = _text_list(manifest.get("required_outputs") if manifest else None)
    present_outputs = _text_list(manifest.get("present_outputs") if manifest else None)
    restore_refs = _text_list(manifest.get("restore_refs") if manifest else None)
    retention_refs = _text_list(manifest.get("retention_refs") if manifest else None)
    promotion = _promotion_projection(
        stage_id=stage_id,
        latest_attempt_id=latest_attempt_id,
        current_pointer=current_pointer,
        required_outputs=required_outputs,
        present_outputs=present_outputs,
        manifest_ref=manifest_ref,
        owner_receipt_refs=owner_receipt_refs,
    )
    semantic_validation = _semantic_validation_projection(
        stage_id=stage_id,
        owner_receipt_refs=owner_receipt_refs,
        typed_blocker_refs=typed_blocker_refs,
        decision_receipt_refs=decision_receipt_refs,
    )
    lineage = _lineage_projection(
        lineage_events=lineage_events,
        lineage_graph=lineage_graph,
        manifest_ref=manifest_ref,
        owner_receipt_refs=owner_receipt_refs,
    )
    retention = _retention_projection(
        restore_refs=restore_refs,
        retention_refs=retention_refs,
        manifest_hash_refs=manifest_hash_refs,
    )
    consumability = _consumability_projection(
        stage_id=stage_id,
        attempt_id=latest_attempt_id,
        manifest_ref=manifest_ref,
        required_outputs=required_outputs,
        present_outputs=present_outputs,
        manifest_hash_refs=manifest_hash_refs,
        owner_receipt_refs=owner_receipt_refs,
        promotion=promotion,
        semantic_validation=semantic_validation,
        lineage=lineage,
        retention=retention,
    )
    return {
        "surface_kind": "mas_opl_physical_stage_folder_projection",
        "stage_id": stage_id,
        "status": "observed",
        "stage_folder_ref": str(stage_root),
        "stage_json_ref": str(stage_ref),
        "attempt_root": str(attempt_root),
        "attempt_json_ref": str(attempt_ref),
        "latest_attempt_id": latest_attempt_id,
        "latest_pointer_ref": str(latest_pointer),
        "current_pointer_ref": str(deliverable_root / "current.json"),
        "manifest_ref": str(manifest_ref),
        "receipt_ref": str(receipt_file_ref) if receipt_file_ref else None,
        "current_outputs": present_outputs,
        "required_outputs": required_outputs,
        "manifest_hash_refs": manifest_hash_refs,
        "evidence_hash_refs": evidence_hash_refs,
        "receipt_hash_refs": receipt_hash_refs,
        "owner_receipt_refs": owner_receipt_refs,
        "typed_blocker_refs": typed_blocker_refs,
        "decision_receipt_refs": decision_receipt_refs,
        "restore_refs": restore_refs,
        "retention_refs": retention_refs,
        "promotion": promotion,
        "semantic_validation": semantic_validation,
        "consumability": consumability,
        "lineage": lineage,
        "retention": retention,
        "conformance_refs": {
            "current_pointer_ref": str(deliverable_root / "current.json"),
            "latest_pointer_ref": str(latest_pointer),
            "stage_json_ref": str(stage_ref),
            "attempt_json_ref": str(attempt_ref),
            "manifest_ref": str(manifest_ref),
            "lineage_events_ref": str(lineage_events),
            "lineage_graph_ref": str(lineage_graph),
        },
        "body_included": False,
    }


def _current_pointer(*, deliverable_root: Path | None) -> dict[str, Any]:
    if deliverable_root is None:
        return {
            "status": "missing",
            "missing_reason": "missing_deliverable_root",
            "body_included": False,
        }
    pointer_ref = deliverable_root / "current.json"
    payload = _read_json(pointer_ref)
    if payload is None:
        return {
            "status": "missing",
            "pointer_ref": str(pointer_ref),
            "missing_reason": "missing_current_pointer",
            "body_included": False,
        }
    current_stage = _mapping(payload.get("current_stage"))
    return {
        "status": "observed",
        "pointer_ref": str(pointer_ref),
        "stage_id": _text(current_stage.get("stage_id")),
        "stage_status": _text(current_stage.get("status")),
        "latest_attempt_id": _text(current_stage.get("latest_attempt_id")),
        "body_included": False,
    }


def _promotion_projection(
    *,
    stage_id: str,
    latest_attempt_id: str,
    current_pointer: Mapping[str, Any],
    required_outputs: list[str],
    present_outputs: list[str],
    manifest_ref: Path,
    owner_receipt_refs: list[str],
) -> dict[str, Any]:
    missing_outputs = [item for item in required_outputs if item not in set(present_outputs)]
    pointer_stage_matches = _text(current_pointer.get("stage_id")) == stage_id
    pointer_attempt_matches = _text(current_pointer.get("latest_attempt_id")) == latest_attempt_id
    pointer_status = _text(current_pointer.get("stage_status"))
    if missing_outputs:
        state = "attempt_output_required"
    elif not manifest_ref.exists():
        state = "manifest_required"
    elif not owner_receipt_refs:
        state = "receipt_required"
    elif not pointer_stage_matches or not pointer_attempt_matches:
        state = "current_pointer_stale"
    elif pointer_status not in {"success", "blocked", "skipped", "deferred"}:
        state = "current_pointer_invalid_status"
    else:
        state = "current_pointer_promoted"
    return {
        "surface_kind": "opl_stage_current_pointer_promotion_projection",
        "state": state,
        "pointer_ref": _text(current_pointer.get("pointer_ref")),
        "pointer_stage_matches": pointer_stage_matches,
        "pointer_attempt_matches": pointer_attempt_matches,
        "pointer_terminal_status": pointer_status,
        "latest_attempt_id": latest_attempt_id,
        "missing_outputs": missing_outputs,
        "body_included": False,
    }


def _semantic_validation_projection(
    *,
    stage_id: str,
    owner_receipt_refs: list[str],
    typed_blocker_refs: list[str],
    decision_receipt_refs: list[str],
) -> dict[str, Any]:
    if typed_blocker_refs:
        status = "blocked"
        missing: list[str] = []
    else:
        missing = []
        if not owner_receipt_refs:
            missing.append("owner_receipt_refs")
        if _domain_receipt_required(stage_id) and not decision_receipt_refs:
            missing.append("domain_decision_receipt_refs")
        status = "accepted" if not missing else "missing_domain_receipt"
    return {
        "surface_kind": "mas_stage_semantic_receipt_validation",
        "status": status,
        "owner_receipt_refs": owner_receipt_refs,
        "typed_blocker_refs": typed_blocker_refs,
        "decision_receipt_refs": decision_receipt_refs,
        "missing": missing,
        "domain_validation_owner": "MedAutoScience",
        "manifest_validity_is_semantic_receipt_validity": False,
        "body_included": False,
    }


def _consumability_projection(
    *,
    stage_id: str,
    attempt_id: str,
    manifest_ref: Path,
    required_outputs: list[str],
    present_outputs: list[str],
    manifest_hash_refs: list[dict[str, str]],
    owner_receipt_refs: list[str],
    promotion: Mapping[str, Any],
    semantic_validation: Mapping[str, Any],
    lineage: Mapping[str, Any],
    retention: Mapping[str, Any],
) -> dict[str, Any]:
    checks = {
        "role": bool(required_outputs),
        "hash": bool(manifest_hash_refs),
        "source": bool(present_outputs),
        "current_truth": promotion.get("state") == "current_pointer_promoted",
        "receipt_authority": bool(owner_receipt_refs),
        "lineage": lineage.get("status") == "observed",
        "retention_restore": retention.get("status") == "covered",
        "domain_validation": semantic_validation.get("status") == "accepted",
    }
    failed = consumability_failed_checks(checks)
    return {
        "surface_kind": "stage_artifact_consumability_projection",
        "required_checks": list(CONSUMABILITY_REQUIRED_CHECKS),
        "status": "passed" if not failed else "blocked",
        "fail_closed": bool(failed),
        "checks": checks,
        "failed_checks": failed,
        "next_owner_delta": consumability_next_owner_delta(
            stage_id=stage_id,
            attempt_id=attempt_id,
            failed_checks=failed,
            source_ref=str(manifest_ref),
        ),
        "insufficient_authority_refs": consumability_insufficient_authority_refs(),
        "authority_boundary": consumability_authority_boundary(),
        "body_included": False,
    }


def _lineage_projection(
    *,
    lineage_events: Path,
    lineage_graph: Path,
    manifest_ref: Path,
    owner_receipt_refs: list[str],
) -> dict[str, Any]:
    missing = []
    if not lineage_events.exists():
        missing.append("lineage_events")
    if not lineage_graph.exists():
        missing.append("lineage_graph")
    if not manifest_ref.exists():
        missing.append("manifest")
    if not owner_receipt_refs:
        missing.append("owner_receipt_refs")
    return {
        "surface_kind": "stage_artifact_lineage_projection",
        "status": "observed" if not missing else "missing",
        "lineage_events_ref": str(lineage_events),
        "lineage_graph_ref": str(lineage_graph),
        "missing": missing,
        "event_model": "stage_attempt_manifest_receipt_current_pointer",
        "body_included": False,
    }


def _retention_projection(
    *,
    restore_refs: list[str],
    retention_refs: list[str],
    manifest_hash_refs: list[dict[str, str]],
) -> dict[str, Any]:
    covered = bool(manifest_hash_refs) and (bool(restore_refs) or bool(retention_refs))
    return {
        "surface_kind": "stage_artifact_retention_restore_projection",
        "status": "covered" if covered else "restore_contract_required",
        "restore_refs": restore_refs,
        "retention_refs": retention_refs,
        "hash_refs_present": bool(manifest_hash_refs),
        "cleanup_authorized": False,
        "required_before_cleanup": True,
        "body_included": False,
    }


def _physical_fail_closed_reason(
    *,
    missing_outputs: list[str],
    promotion: Mapping[str, Any],
    semantic_validation: Mapping[str, Any],
    consumability: Mapping[str, Any],
) -> str:
    if missing_outputs:
        return "missing_physical_stage_output"
    promotion_state = _text(promotion.get("state"))
    if promotion_state != "current_pointer_promoted":
        return promotion_state or "current_pointer_not_promoted"
    semantic_status = _text(semantic_validation.get("status"))
    if semantic_status != "accepted":
        return semantic_status or "semantic_receipt_not_accepted"
    failed_checks = _text_list(consumability.get("failed_checks"))
    if failed_checks:
        return "consumability_gate_failed:" + ",".join(failed_checks)
    return "physical_stage_kernel_not_current"


def _domain_receipt_required(stage_id: str) -> bool:
    return stage_id in {
        "01-study_intake",
        "03-data_asset_and_cohort_build",
        "05-evidence_synthesis",
        "06-manuscript_authoring",
        "07-independent_review_and_revision",
        "08-publication_package_handoff",
    }


def _missing_stage(*, stage_id: str, reason: str) -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_physical_stage_folder_projection",
        "stage_id": stage_id,
        "status": "missing",
        "missing_reason": reason,
        "body_included": False,
    }


def _locator(*, study_id: str, domain_stage_pack: Mapping[str, Any]) -> dict[str, str]:
    kernel = domain_stage_pack.get("physical_stage_folder_kernel")
    if not isinstance(kernel, Mapping):
        kernel = {}
    locator = kernel.get("locator")
    if not isinstance(locator, Mapping):
        locator = {}
    return {
        "domain_id": str(locator.get("domain_id") or "med-autoscience"),
        "program_id": str(locator.get("program_id") or "mas-paper-study"),
        "topic_id": str(locator.get("topic_id_template") or "{study_id}").replace("{study_id}", study_id),
        "deliverable_id": str(locator.get("deliverable_id") or "paper-study"),
    }


def _opl_state_root() -> Path | None:
    value = os.environ.get("OPL_STATE_DIR")
    if not value:
        return None
    return Path(value).expanduser().resolve()


def _deliverable_root(*, state_root: Path, locator: Mapping[str, str]) -> Path:
    return (
        state_root
        / "runtime-state"
        / "domains"
        / locator["domain_id"]
        / "deliverables"
        / locator["program_id"]
        / locator["topic_id"]
        / locator["deliverable_id"]
    )


def _stage_root(*, deliverable_root: Path, stage_id: str) -> Path | None:
    direct = deliverable_root / "stages" / stage_id
    if direct.exists():
        return direct
    stages_root = deliverable_root / "stages"
    if not stages_root.exists():
        return None
    for child in stages_root.iterdir():
        if not child.is_dir():
            continue
        folder_stage_id = child.name.split("-", 1)[1] if child.name[:2].isdigit() and "-" in child.name else child.name
        if folder_stage_id == stage_id:
            return child
    return None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text or None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _hash_refs(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        path = item.get("path")
        sha256 = item.get("sha256")
        if isinstance(path, str) and path.strip() and isinstance(sha256, str) and sha256.strip():
            refs.append(
                {
                    "kind": str(item.get("kind") or "content_hash"),
                    "path": path.strip(),
                    "sha256": sha256.strip(),
                }
            )
    return refs


def _first_receipt_file(receipts_root: Path) -> Path | None:
    if not receipts_root.exists():
        return None
    for path in sorted(receipts_root.rglob("*")):
        if path.is_file():
            return path
    return None


__all__ = [
    "STAGE_ARTIFACT_RUNTIME_CONTRACT_REF",
    "physical_artifact_classification",
    "physical_stage_kernel_projection",
    "stage_physical_kernel",
]

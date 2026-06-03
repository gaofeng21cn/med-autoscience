from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.opl_physical_stage_kernel import (
    STAGE_ARTIFACT_RUNTIME_CONTRACT_REF,
)

SURFACE_KIND = "opl_stage_current_pointer_promotion_audit"
SCHEMA_VERSION = "opl-stage-current-pointer-promotion-audit.v1"
TERMINAL_STATUSES = frozenset({"success", "blocked", "skipped", "deferred"})


def promotion_audit_from_stage_projection(
    stage_projection: Mapping[str, Any],
) -> dict[str, Any]:
    projection = dict(stage_projection)
    stage_id = _text(projection.get("stage_id"))
    latest_attempt_id = _text(projection.get("latest_attempt_id"))
    promotion = _mapping(projection.get("promotion"))
    current_pointer = _current_pointer_from_projection(projection, promotion)
    latest_pointer = {
        "attempt_id": latest_attempt_id,
        "ref": _text(projection.get("latest_pointer_ref")),
    }
    required_outputs = _text_list(projection.get("required_outputs"))
    present_outputs = _text_list(projection.get("current_outputs"))
    missing_outputs = _missing_outputs(
        required_outputs=required_outputs,
        present_outputs=present_outputs,
        promotion=promotion,
    )
    owner_receipt_refs = _text_list(projection.get("owner_receipt_refs"))
    typed_blocker_refs = _text_list(projection.get("typed_blocker_refs"))
    decision_receipt_refs = _text_list(projection.get("decision_receipt_refs"))
    semantic_validation = _mapping(projection.get("semantic_validation"))
    consumability = _mapping(projection.get("consumability"))
    lineage = _mapping(projection.get("lineage"))
    retention = _mapping(projection.get("retention"))
    orphan_outputs = _mapping_list(projection.get("orphan_outputs"))
    historical_tombstones = _mapping_list(projection.get("historical_pointer_tombstones"))
    reasons = _fail_closed_reasons(
        projection_status=_text(projection.get("status")),
        latest_attempt_id=latest_attempt_id,
        current_pointer=current_pointer,
        promotion=promotion,
        missing_outputs=missing_outputs,
        present_outputs=present_outputs,
        owner_receipt_refs=owner_receipt_refs,
        typed_blocker_refs=typed_blocker_refs,
        decision_receipt_refs=decision_receipt_refs,
        semantic_validation=semantic_validation,
        consumability=consumability,
        lineage=lineage,
        retention=retention,
        orphan_outputs=orphan_outputs,
        historical_tombstones=historical_tombstones,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "contract_ref": (
            "contracts/stage_artifact_kernel_adoption.json"
            "#/current_pointer_promotion_model"
        ),
        "stage_artifact_runtime_contract_ref": STAGE_ARTIFACT_RUNTIME_CONTRACT_REF,
        "source_of_truth": "opl_physical_stage_folder_kernel",
        "input_surface": _text(projection.get("surface_kind"))
        or "mas_opl_physical_stage_folder_projection",
        "stage_id": stage_id,
        "status": "promotable_current" if not reasons else "blocked",
        "fail_closed": bool(reasons),
        "fail_closed_reasons": reasons,
        "latest_pointer": latest_pointer,
        "current_pointer": current_pointer,
        "promotion": {
            "state": _text(promotion.get("state")),
            "ordered_steps": [
                "attempt_output",
                "manifest_valid",
                "receipt_accepted",
                "domain_decision_receipt_valid",
                "current_pointer_promoted",
                "projection_rebuilt",
            ],
            "projection_rebuild_required": True,
            "derived_projection_can_promote_pointer": False,
        },
        "partial_commit": {
            "observed": "partial_commit" in reasons,
            "present_outputs": present_outputs,
            "missing_outputs": missing_outputs,
        },
        "rollback_candidate": {
            "observed": "rollback_candidate" in reasons,
            "latest_attempt_id": latest_attempt_id,
            "current_attempt_id": _text(current_pointer.get("attempt_id")),
        },
        "orphan_outputs": orphan_outputs,
        "historical_pointer_tombstones": historical_tombstones,
        "semantic_validation": semantic_validation,
        "consumability": consumability,
        "lineage": lineage,
        "retention": retention,
        "refs": _refs(projection),
        "authority_boundary": _authority_boundary(),
        "body_included": False,
    }


def promotion_audit_from_deliverable_root(
    *,
    deliverable_root: str | Path,
    stage_id: str,
) -> dict[str, Any]:
    root = Path(deliverable_root).expanduser().resolve()
    stage_root = _stage_root(deliverable_root=root, stage_id=stage_id)
    current_pointer_ref = root / "current.json"
    current_pointer_payload = _read_json(current_pointer_ref)
    current_stage = _mapping(
        current_pointer_payload.get("current_stage") if current_pointer_payload else None
    )
    projection = _projection_from_stage_root(
        deliverable_root=root,
        stage_root=stage_root,
        stage_id=stage_id,
        current_pointer_ref=current_pointer_ref,
        current_stage=current_stage,
    )
    projection["orphan_outputs"] = _orphan_outputs(
        stage_root=stage_root,
        latest_attempt_id=_text(projection.get("latest_attempt_id")),
        current_attempt_id=_text(current_stage.get("latest_attempt_id")),
    )
    projection["historical_pointer_tombstones"] = _historical_pointer_tombstones(
        deliverable_root=root,
        stage_id=stage_id,
    )
    return promotion_audit_from_stage_projection(projection)


def _projection_from_stage_root(
    *,
    deliverable_root: Path,
    stage_root: Path | None,
    stage_id: str,
    current_pointer_ref: Path,
    current_stage: Mapping[str, Any],
) -> dict[str, Any]:
    if stage_root is None:
        return {
            "surface_kind": "mas_opl_physical_stage_folder_projection",
            "stage_id": stage_id,
            "status": "missing",
            "missing_reason": "missing_stage_folder",
            "current_pointer_ref": str(current_pointer_ref),
            "current_pointer": _current_pointer_payload(
                pointer_ref=current_pointer_ref,
                current_stage=current_stage,
            ),
            "promotion": {"state": "attempt_output_required"},
            "body_included": False,
        }
    latest_pointer = stage_root / "latest"
    latest_attempt_id = _read_text(latest_pointer)
    attempt_root = stage_root / "attempts" / latest_attempt_id if latest_attempt_id else None
    manifest_ref = attempt_root / "manifest.json" if attempt_root else stage_root / "attempts"
    manifest = _read_json(manifest_ref)
    required_outputs = _text_list(manifest.get("required_outputs") if manifest else None)
    present_outputs = _text_list(manifest.get("present_outputs") if manifest else None)
    owner_receipt_refs = _text_list(manifest.get("owner_receipt_refs") if manifest else None)
    typed_blocker_refs = _text_list(manifest.get("typed_blocker_refs") if manifest else None)
    decision_receipt_refs = _text_list(
        manifest.get("decision_receipt_refs") if manifest else None
    )
    output_hashes = _hash_refs(manifest.get("output_hashes") if manifest else None)
    restore_refs = _text_list(manifest.get("restore_refs") if manifest else None)
    retention_refs = _text_list(manifest.get("retention_refs") if manifest else None)
    receipt_ref = _first_receipt_file(attempt_root / "receipts") if attempt_root else None
    current_pointer = _current_pointer_payload(
        pointer_ref=current_pointer_ref,
        current_stage=current_stage,
    )
    promotion = _promotion_projection(
        stage_id=stage_id,
        latest_attempt_id=latest_attempt_id,
        current_pointer=current_pointer,
        required_outputs=required_outputs,
        present_outputs=present_outputs,
        manifest_ref=manifest_ref,
        owner_receipt_refs=owner_receipt_refs,
    )
    semantic_validation = _semantic_validation(
        owner_receipt_refs=owner_receipt_refs,
        typed_blocker_refs=typed_blocker_refs,
        decision_receipt_refs=decision_receipt_refs,
    )
    lineage = _lineage(
        deliverable_root=deliverable_root,
        manifest_ref=manifest_ref,
        owner_receipt_refs=owner_receipt_refs,
    )
    retention = _retention(
        manifest_hash_refs=output_hashes,
        restore_refs=restore_refs,
        retention_refs=retention_refs,
    )
    consumability = _consumability(
        required_outputs=required_outputs,
        present_outputs=present_outputs,
        manifest_hash_refs=output_hashes,
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
        "latest_attempt_id": latest_attempt_id,
        "latest_pointer_ref": str(latest_pointer),
        "attempt_root": str(attempt_root) if attempt_root else None,
        "manifest_ref": str(manifest_ref),
        "receipt_ref": str(receipt_ref) if receipt_ref else None,
        "current_pointer_ref": str(current_pointer_ref),
        "current_pointer": current_pointer,
        "current_outputs": present_outputs,
        "required_outputs": required_outputs,
        "owner_receipt_refs": owner_receipt_refs,
        "typed_blocker_refs": typed_blocker_refs,
        "decision_receipt_refs": decision_receipt_refs,
        "promotion": promotion,
        "semantic_validation": semantic_validation,
        "consumability": consumability,
        "lineage": lineage,
        "retention": retention,
        "body_included": False,
    }


def _promotion_projection(
    *,
    stage_id: str,
    latest_attempt_id: str | None,
    current_pointer: Mapping[str, Any],
    required_outputs: list[str],
    present_outputs: list[str],
    manifest_ref: Path,
    owner_receipt_refs: list[str],
) -> dict[str, Any]:
    missing_outputs = [item for item in required_outputs if item not in set(present_outputs)]
    pointer_stage_matches = _text(current_pointer.get("stage_id")) == stage_id
    pointer_attempt_matches = _text(current_pointer.get("attempt_id")) == latest_attempt_id
    pointer_status = _text(current_pointer.get("terminal_status"))
    if not latest_attempt_id or missing_outputs:
        state = "attempt_output_required"
    elif not manifest_ref.exists():
        state = "manifest_required"
    elif not owner_receipt_refs:
        state = "receipt_required"
    elif not pointer_stage_matches or not pointer_attempt_matches:
        state = "current_pointer_stale"
    elif pointer_status not in TERMINAL_STATUSES:
        state = "current_pointer_invalid_status"
    else:
        state = "current_pointer_promoted"
    return {
        "surface_kind": "opl_stage_current_pointer_promotion_projection",
        "state": state,
        "pointer_ref": _text(current_pointer.get("ref")),
        "pointer_stage_matches": pointer_stage_matches,
        "pointer_attempt_matches": pointer_attempt_matches,
        "pointer_terminal_status": pointer_status,
        "latest_attempt_id": latest_attempt_id,
        "missing_outputs": missing_outputs,
        "body_included": False,
    }


def _semantic_validation(
    *,
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
        if not decision_receipt_refs:
            missing.append("domain_decision_receipt_refs")
        status = "accepted" if not missing else "missing_domain_receipt"
    return {
        "surface_kind": "mas_stage_semantic_receipt_validation",
        "status": status,
        "missing": missing,
        "owner_receipt_refs": owner_receipt_refs,
        "typed_blocker_refs": typed_blocker_refs,
        "decision_receipt_refs": decision_receipt_refs,
        "body_included": False,
    }


def _lineage(
    *,
    deliverable_root: Path,
    manifest_ref: Path,
    owner_receipt_refs: list[str],
) -> dict[str, Any]:
    events_ref = deliverable_root / "lineage" / "events.jsonl"
    graph_ref = deliverable_root / "lineage" / "graph.json"
    missing = []
    if not events_ref.exists():
        missing.append("lineage_events")
    if not graph_ref.exists():
        missing.append("lineage_graph")
    if not manifest_ref.exists():
        missing.append("manifest")
    if not owner_receipt_refs:
        missing.append("owner_receipt_refs")
    return {
        "surface_kind": "stage_artifact_lineage_projection",
        "status": "observed" if not missing else "missing",
        "lineage_events_ref": str(events_ref),
        "lineage_graph_ref": str(graph_ref),
        "missing": missing,
        "body_included": False,
    }


def _retention(
    *,
    manifest_hash_refs: list[dict[str, str]],
    restore_refs: list[str],
    retention_refs: list[str],
) -> dict[str, Any]:
    covered = bool(manifest_hash_refs) and (bool(restore_refs) or bool(retention_refs))
    return {
        "surface_kind": "stage_artifact_retention_restore_projection",
        "status": "covered" if covered else "restore_contract_required",
        "restore_refs": restore_refs,
        "retention_refs": retention_refs,
        "hash_refs_present": bool(manifest_hash_refs),
        "cleanup_authorized": False,
        "body_included": False,
    }


def _consumability(
    *,
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
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "surface_kind": "stage_artifact_consumability_projection",
        "status": "passed" if not failed else "blocked",
        "checks": checks,
        "failed_checks": failed,
        "body_included": False,
    }


def _fail_closed_reasons(
    *,
    projection_status: str | None,
    latest_attempt_id: str | None,
    current_pointer: Mapping[str, Any],
    promotion: Mapping[str, Any],
    missing_outputs: list[str],
    present_outputs: list[str],
    owner_receipt_refs: list[str],
    typed_blocker_refs: list[str],
    decision_receipt_refs: list[str],
    semantic_validation: Mapping[str, Any],
    consumability: Mapping[str, Any],
    lineage: Mapping[str, Any],
    retention: Mapping[str, Any],
    orphan_outputs: list[dict[str, Any]],
    historical_tombstones: list[dict[str, Any]],
) -> list[str]:
    reasons: list[str] = []
    promotion_state = _text(promotion.get("state"))
    pointer_status = _text(current_pointer.get("terminal_status"))
    pointer_attempt_matches = _bool_or_none(promotion.get("pointer_attempt_matches"))
    pointer_stage_matches = _bool_or_none(promotion.get("pointer_stage_matches"))
    current_attempt_id = _text(current_pointer.get("attempt_id"))
    if projection_status != "observed":
        reasons.append("missing_stage_projection")
    if latest_attempt_id is None:
        reasons.append("latest_pointer_missing")
    if current_attempt_id is None:
        reasons.append("current_pointer_missing")
    if pointer_stage_matches is False or pointer_attempt_matches is False:
        reasons.append("current_pointer_stale")
    if pointer_status not in TERMINAL_STATUSES:
        reasons.append("current_pointer_invalid_status")
    if missing_outputs:
        reasons.append("partial_commit")
    if present_outputs and (missing_outputs or promotion_state in {"receipt_required", "manifest_required"}):
        reasons.append("partial_commit")
    if promotion_state in {
        "manifest_required",
        "receipt_required",
        "current_pointer_stale",
        "current_pointer_invalid_status",
        "missing_domain_receipt",
        "consumability_gate_failed",
    }:
        reasons.append(promotion_state)
    if not owner_receipt_refs and not typed_blocker_refs:
        reasons.append("receipt_required")
    if semantic_validation.get("status") == "missing_domain_receipt":
        reasons.append("missing_domain_receipt")
    if not decision_receipt_refs and not typed_blocker_refs:
        reasons.append("missing_domain_receipt")
    failed_checks = _text_list(consumability.get("failed_checks"))
    if failed_checks:
        reasons.append("consumability_gate_failed:" + ",".join(failed_checks))
    if lineage.get("status") == "missing":
        reasons.append("lineage_missing")
    if retention.get("status") == "restore_contract_required":
        reasons.append("retention_restore_required")
    if pointer_attempt_matches is False and (present_outputs or orphan_outputs):
        reasons.append("rollback_candidate")
    if orphan_outputs:
        reasons.append("orphan_output")
    if historical_tombstones:
        reasons.append("historical_pointer_tombstone")
    return _dedupe(reasons)


def _current_pointer_from_projection(
    projection: Mapping[str, Any],
    promotion: Mapping[str, Any],
) -> dict[str, Any]:
    pointer = _mapping(projection.get("current_pointer"))
    pointer_stage_id = _text(pointer.get("stage_id")) or (
        _text(projection.get("stage_id"))
        if promotion.get("pointer_stage_matches") is True
        else None
    )
    pointer_attempt_id = _text(pointer.get("attempt_id")) or _text(
        pointer.get("latest_attempt_id")
    )
    if pointer_attempt_id is None and promotion.get("pointer_attempt_matches") is True:
        pointer_attempt_id = _text(projection.get("latest_attempt_id"))
    terminal_status = (
        _text(pointer.get("terminal_status"))
        or _text(pointer.get("stage_status"))
        or _text(promotion.get("pointer_terminal_status"))
    )
    return {
        "ref": _text(pointer.get("ref"))
        or _text(pointer.get("pointer_ref"))
        or _text(projection.get("current_pointer_ref"))
        or _text(promotion.get("pointer_ref")),
        "stage_id": pointer_stage_id,
        "attempt_id": pointer_attempt_id,
        "terminal_status": terminal_status,
        "matches_stage": _bool_or_none(promotion.get("pointer_stage_matches")),
        "matches_latest": _bool_or_none(promotion.get("pointer_attempt_matches")),
        "status_is_terminal": terminal_status in TERMINAL_STATUSES,
    }


def _current_pointer_payload(
    *,
    pointer_ref: Path,
    current_stage: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "ref": str(pointer_ref),
        "stage_id": _text(current_stage.get("stage_id")),
        "attempt_id": _text(current_stage.get("latest_attempt_id")),
        "terminal_status": _text(current_stage.get("status")),
    }


def _missing_outputs(
    *,
    required_outputs: list[str],
    present_outputs: list[str],
    promotion: Mapping[str, Any],
) -> list[str]:
    promoted_missing = _text_list(promotion.get("missing_outputs"))
    if promoted_missing:
        return promoted_missing
    present = set(present_outputs)
    return [item for item in required_outputs if item not in present]


def _orphan_outputs(
    *,
    stage_root: Path | None,
    latest_attempt_id: str | None,
    current_attempt_id: str | None,
) -> list[dict[str, Any]]:
    if stage_root is None:
        return []
    attempts_root = stage_root / "attempts"
    if not attempts_root.exists():
        return []
    protected = {item for item in (latest_attempt_id, current_attempt_id) if item}
    orphans: list[dict[str, Any]] = []
    for attempt_root in sorted(path for path in attempts_root.iterdir() if path.is_dir()):
        attempt_id = attempt_root.name
        if attempt_id in protected:
            continue
        manifest_ref = attempt_root / "manifest.json"
        present_outputs = _attempt_present_outputs(manifest_ref)
        if not present_outputs:
            continue
        orphans.append(
            {
                "attempt_id": attempt_id,
                "attempt_root": str(attempt_root),
                "manifest_ref": str(manifest_ref),
                "present_outputs": present_outputs,
                "body_included": False,
            }
        )
    return orphans


def _historical_pointer_tombstones(
    *,
    deliverable_root: Path,
    stage_id: str,
) -> list[dict[str, Any]]:
    tombstones: list[dict[str, Any]] = []
    if not deliverable_root.exists():
        return tombstones
    for path in sorted(deliverable_root.rglob("*.json")):
        path_text = str(path)
        if "tombstone" not in path_text and "tombstones" not in path_text:
            continue
        if "current" not in path.name and "pointer" not in path.name:
            payload = _read_json(path)
            surface = _text(payload.get("surface_kind") if payload else None)
            if surface != "historical_current_pointer_tombstone":
                continue
        else:
            payload = _read_json(path)
        payload = payload or {}
        payload_stage_id = _text(payload.get("stage_id"))
        if payload_stage_id is not None and payload_stage_id != stage_id:
            continue
        tombstones.append(
            {
                "ref": str(path),
                "stage_id": payload_stage_id or stage_id,
                "attempt_id": _text(payload.get("attempt_id")),
                "body_included": False,
            }
        )
    return tombstones


def _attempt_present_outputs(manifest_ref: Path) -> list[str]:
    manifest = _read_json(manifest_ref)
    if manifest is None:
        return []
    present = _text_list(manifest.get("present_outputs"))
    if present:
        return present
    return _text_list(manifest.get("current_outputs"))


def _refs(projection: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage_folder_ref": _text(projection.get("stage_folder_ref")),
        "latest_pointer_ref": _text(projection.get("latest_pointer_ref")),
        "current_pointer_ref": _text(projection.get("current_pointer_ref")),
        "manifest_ref": _text(projection.get("manifest_ref")),
        "receipt_ref": _text(projection.get("receipt_ref")),
        "body_included": False,
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "read_only": True,
        "writes_current_pointer": False,
        "writes_mas_truth": False,
        "writes_paper_or_eval": False,
        "writes_controller_decisions": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_publication_ready": False,
    }


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


def _first_receipt_file(receipts_root: Path) -> Path | None:
    if not receipts_root.exists():
        return None
    for path in sorted(receipts_root.rglob("*")):
        if path.is_file():
            return path
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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _bool_or_none(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "TERMINAL_STATUSES",
    "promotion_audit_from_deliverable_root",
    "promotion_audit_from_stage_projection",
]

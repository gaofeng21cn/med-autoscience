from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

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
    stages = {
        stage_id: _stage_projection(deliverable_root=deliverable_root, stage_id=stage_id)
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
    status = "current" if current and not missing_outputs else "missing"
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
        "fail_closed_reason": None if status == "current" else "missing_physical_stage_output",
        "manifest_ref": str(stage_folder_contract["manifest_ref"]),
        "receipt_ref": str(stage_folder_contract["receipt_ref"]),
        "current_pointer_basis": {
            "existing_artifacts": bool(current),
            "manifest_valid": bool(physical_stage_kernel.get("manifest_ref")),
            "receipt_accepted": bool(physical_stage_kernel.get("owner_receipt_refs")),
        },
        "latest_attempt_id": physical_stage_kernel.get("latest_attempt_id"),
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


def _stage_projection(*, deliverable_root: Path | None, stage_id: str) -> dict[str, Any]:
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
    manifest_hash_refs = _hash_refs(manifest.get("output_hashes") if manifest else None)
    evidence_hash_refs = _hash_refs(manifest.get("evidence_hashes") if manifest else None)
    receipt_hash_refs = _hash_refs(manifest.get("receipt_hashes") if manifest else None)
    owner_receipt_refs = _text_list(manifest.get("owner_receipt_refs") if manifest else None)
    receipt_file_ref = _first_receipt_file(attempt_root / "receipts")
    lineage_events = deliverable_root / "lineage" / "events.jsonl"
    lineage_graph = deliverable_root / "lineage" / "graph.json"
    return {
        "surface_kind": "mas_opl_physical_stage_folder_projection",
        "stage_id": stage_id,
        "status": "observed",
        "stage_folder_ref": str(stage_root),
        "attempt_root": str(attempt_root),
        "latest_attempt_id": latest_attempt_id,
        "latest_pointer_ref": str(latest_pointer),
        "current_pointer_ref": str(deliverable_root / "current.json"),
        "manifest_ref": str(manifest_ref),
        "receipt_ref": str(receipt_file_ref) if receipt_file_ref else None,
        "current_outputs": _text_list(manifest.get("present_outputs") if manifest else None),
        "required_outputs": _text_list(manifest.get("required_outputs") if manifest else None),
        "manifest_hash_refs": manifest_hash_refs,
        "evidence_hash_refs": evidence_hash_refs,
        "receipt_hash_refs": receipt_hash_refs,
        "owner_receipt_refs": owner_receipt_refs,
        "typed_blocker_refs": _text_list(manifest.get("typed_blocker_refs") if manifest else None),
        "decision_receipt_refs": _text_list(manifest.get("decision_receipt_refs") if manifest else None),
        "conformance_refs": {
            "current_pointer_ref": str(deliverable_root / "current.json"),
            "latest_pointer_ref": str(latest_pointer),
            "manifest_ref": str(manifest_ref),
            "lineage_events_ref": str(lineage_events),
            "lineage_graph_ref": str(lineage_graph),
        },
        "body_included": False,
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

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from med_autoscience.controllers import data_assets, startup_data_readiness


MUTATION_LOG_SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mutations_root(workspace_root: Path) -> Path:
    return data_assets._data_assets_root(workspace_root) / "mutations"


def _mutation_log_path(*, workspace_root: Path, timestamp: str, action: str) -> Path:
    stamp = timestamp.replace(":", "").replace("+00:00", "Z")
    mutation_id = uuid4().hex[:8]
    return _mutations_root(workspace_root) / f"{stamp}_{action}_{mutation_id}.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refresh_data_assets(*, workspace_root: Path) -> dict[str, Any]:
    init = data_assets.init_data_assets(workspace_root=workspace_root)
    public_validation = data_assets.validate_public_registry(workspace_root=workspace_root)
    impact_report = data_assets.assess_data_asset_impact(workspace_root=workspace_root)
    startup_report = startup_data_readiness.startup_data_readiness(workspace_root=workspace_root)
    status = data_assets.data_assets_status(workspace_root=workspace_root)
    return {
        "init": init,
        "status": status,
        "public_validation": public_validation,
        "impact_report": {
            "study_count": impact_report.get("study_count"),
            "report_path": str(data_assets._impact_report_path(workspace_root)),
        },
        "startup_data_readiness": startup_report,
    }


def _serialize_error(exc: Exception) -> dict[str, str]:
    return {
        "type": type(exc).__name__,
        "message": str(exc),
    }


def _normalize_public_dataset(dataset: object) -> dict[str, Any]:
    payload = dataset if isinstance(dataset, dict) else {}
    status = payload.get("status")
    if status is not None:
        if not isinstance(status, str) or status not in data_assets.PUBLIC_DATASET_ALLOWED_STATUSES:
            raise ValueError(f"upsert_public_dataset received invalid status: {status}")
    roles = payload.get("roles")
    if roles is not None:
        if not isinstance(roles, list):
            raise ValueError("upsert_public_dataset requires dataset.roles as a list when provided")
        invalid_roles = sorted(
            {
                role
                for role in roles
                if isinstance(role, str) and role not in data_assets.PUBLIC_DATASET_ALLOWED_ROLES
            }
        )
        if invalid_roles:
            raise ValueError("upsert_public_dataset received invalid roles: " + ", ".join(invalid_roles))
        if any(not isinstance(role, str) for role in roles):
            raise ValueError("upsert_public_dataset requires dataset.roles to contain only strings")
    normalized = data_assets._normalize_public_dataset_entry(dataset)
    dataset_id = normalized.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("upsert_public_dataset requires dataset.dataset_id")
    return normalized


def _load_public_registry_for_mutation(workspace_root: Path) -> dict[str, Any]:
    data_assets.init_data_assets(workspace_root=workspace_root)
    return data_assets._load_public_registry(workspace_root)


def _upsert_public_dataset(*, workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    dataset = _normalize_public_dataset(payload.get("dataset"))
    registry = _load_public_registry_for_mutation(workspace_root)
    datasets = [item for item in registry.get("datasets", []) if isinstance(item, dict)]
    replaced = False
    for index, item in enumerate(datasets):
        if item.get("dataset_id") == dataset["dataset_id"]:
            datasets[index] = dataset
            replaced = True
            break
    if not replaced:
        datasets.append(dataset)
    registry["datasets"] = datasets
    data_assets._write_json(data_assets._public_registry_path(workspace_root), registry)
    return {
        "kind": "public_registry_upsert",
        "dataset_id": dataset["dataset_id"],
        "replaced_existing": replaced,
        "registry_path": str(data_assets._public_registry_path(workspace_root)),
        "written_dataset": dataset,
    }


def _update_public_dataset_status(*, workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    dataset_id = payload.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("update_public_dataset_status requires dataset_id")
    status = payload.get("status")
    if not isinstance(status, str) or status not in data_assets.PUBLIC_DATASET_ALLOWED_STATUSES:
        raise ValueError("update_public_dataset_status requires a valid status")
    registry = _load_public_registry_for_mutation(workspace_root)
    datasets = [item for item in registry.get("datasets", []) if isinstance(item, dict)]
    matched: dict[str, Any] | None = None
    for item in datasets:
        if item.get("dataset_id") == dataset_id:
            matched = item
            break
    if matched is None:
        raise FileNotFoundError(f"Public dataset not found: {dataset_id}")
    matched["status"] = status
    rationale = payload.get("rationale")
    if isinstance(rationale, str):
        matched["rationale"] = rationale
    append_notes = payload.get("append_notes")
    if isinstance(append_notes, list):
        notes = list(matched.get("notes") or [])
        for item in append_notes:
            if isinstance(item, str):
                notes.append(item)
        matched["notes"] = notes
    registry["datasets"] = datasets
    normalized = data_assets._normalize_public_registry_payload(registry)
    data_assets._write_json(data_assets._public_registry_path(workspace_root), normalized)
    written_dataset = next(
        item for item in normalized["datasets"] if isinstance(item, dict) and item.get("dataset_id") == dataset_id
    )
    return {
        "kind": "public_registry_status_update",
        "dataset_id": dataset_id,
        "status": status,
        "registry_path": str(data_assets._public_registry_path(workspace_root)),
        "written_dataset": written_dataset,
    }


def _record_public_dataset_discovery(*, workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    status = payload.get("status")
    if not isinstance(status, str) or status not in data_assets.PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES:
        raise ValueError("record_public_dataset_discovery requires a valid status")
    last_scouted_on = payload.get("last_scouted_on")
    if last_scouted_on is not None and not isinstance(last_scouted_on, str):
        raise ValueError("record_public_dataset_discovery requires last_scouted_on to be a string when provided")
    scope = payload.get("scope")
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("record_public_dataset_discovery requires scope")
    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list) or any(not isinstance(item, str) for item in notes):
            raise ValueError("record_public_dataset_discovery requires notes to be a list of strings when provided")

    registry = _load_public_registry_for_mutation(workspace_root)
    discovery = data_assets._normalize_public_registry_discovery(
        {
            "status": status,
            "last_scouted_on": last_scouted_on,
            "scope": scope,
            "notes": notes or [],
        }
    )
    registry["discovery"] = discovery
    normalized = data_assets._normalize_public_registry_payload(registry)
    data_assets._write_json(data_assets._public_registry_path(workspace_root), normalized)
    return {
        "kind": "public_registry_discovery_update",
        "discovery": normalized["discovery"],
        "registry_path": str(data_assets._public_registry_path(workspace_root)),
    }


def _upsert_private_release_manifest(*, workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    family_id = payload.get("family_id")
    version_id = payload.get("version_id")
    manifest = payload.get("manifest")
    if not isinstance(family_id, str) or not family_id:
        raise ValueError("upsert_private_release_manifest requires family_id")
    if not isinstance(version_id, str) or not version_id:
        raise ValueError("upsert_private_release_manifest requires version_id")
    if not isinstance(manifest, dict):
        raise ValueError("upsert_private_release_manifest requires manifest")
    dataset_id = manifest.get("dataset_id")
    raw_snapshot = manifest.get("raw_snapshot")
    generated_by = manifest.get("generated_by")
    main_outputs = manifest.get("main_outputs")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("upsert_private_release_manifest requires manifest.dataset_id")
    if not isinstance(raw_snapshot, str) or not raw_snapshot:
        raise ValueError("upsert_private_release_manifest requires manifest.raw_snapshot")
    if not isinstance(generated_by, str) or not generated_by:
        raise ValueError("upsert_private_release_manifest requires manifest.generated_by")
    normalized_main_outputs = data_assets._normalize_string_map(main_outputs)
    if not normalized_main_outputs:
        raise ValueError("upsert_private_release_manifest requires manifest.main_outputs")
    version_root = workspace_root / "datasets" / family_id / version_id
    if not version_root.exists():
        raise FileNotFoundError(f"Release root does not exist: {family_id}/{version_id}")
    missing_outputs = sorted(
        output_name
        for output_name, relative_path in normalized_main_outputs.items()
        if not (version_root / relative_path).is_file()
    )
    if missing_outputs:
        raise FileNotFoundError("Missing declared main outputs: " + ", ".join(missing_outputs))
    manifest_payload: dict[str, Any] = {
        "dataset_id": dataset_id,
        "version": version_id,
        "raw_snapshot": raw_snapshot,
        "generated_by": generated_by,
        "main_outputs": normalized_main_outputs,
        "notes": manifest.get("notes") if isinstance(manifest.get("notes"), list) else [],
        "release_contract": manifest.get("release_contract") if isinstance(manifest.get("release_contract"), dict) else {},
    }
    if isinstance(manifest.get("source_release"), dict):
        manifest_payload["source_release"] = manifest["source_release"]
    supersedes_versions = data_assets._normalize_string_list(manifest.get("supersedes_versions"))
    if supersedes_versions:
        manifest_payload["supersedes_versions"] = supersedes_versions
    manifest_path = version_root / "dataset_manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {
        "kind": "private_release_manifest_upsert",
        "family_id": family_id,
        "version_id": version_id,
        "manifest_path": str(manifest_path),
        "written_manifest": manifest_payload,
    }


def _apply_mutation(*, workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    if action == "refresh_all":
        return {"kind": "refresh_all"}
    if action == "upsert_public_dataset":
        return _upsert_public_dataset(workspace_root=workspace_root, payload=payload)
    if action == "update_public_dataset_status":
        return _update_public_dataset_status(workspace_root=workspace_root, payload=payload)
    if action == "record_public_dataset_discovery":
        return _record_public_dataset_discovery(workspace_root=workspace_root, payload=payload)
    if action == "upsert_private_release_manifest":
        return _upsert_private_release_manifest(workspace_root=workspace_root, payload=payload)
    raise ValueError(f"Unsupported data-asset update action: {action}")


def apply_data_asset_update(*, workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dictionary")
    action = payload.get("action")
    if not isinstance(action, str) or not action:
        raise ValueError("payload.action is required")
    timestamp = utc_now()
    log_path = _mutation_log_path(workspace_root=workspace_root, timestamp=timestamp, action=action)
    log_payload: dict[str, Any] = {
        "schema_version": MUTATION_LOG_SCHEMA_VERSION,
        "recorded_at": timestamp,
        "workspace_root": str(workspace_root),
        "action": action,
        "payload": payload,
        "status": "started",
    }
    _write_json(log_path, log_payload)
    try:
        mutation = _apply_mutation(workspace_root=workspace_root, payload=payload)
    except Exception as exc:
        log_payload["status"] = "mutation_failed"
        log_payload["error"] = _serialize_error(exc)
        _write_json(log_path, log_payload)
        raise
    try:
        refresh = refresh_data_assets(workspace_root=workspace_root)
    except Exception as exc:
        log_payload["status"] = "refresh_failed"
        log_payload["mutation"] = mutation
        log_payload["refresh_error"] = _serialize_error(exc)
        _write_json(log_path, log_payload)
        raise
    log_payload["status"] = "applied"
    log_payload["mutation"] = mutation
    log_payload["refresh"] = {
        "status": refresh["status"],
        "impact_report": refresh["impact_report"],
        "startup_data_readiness": refresh["startup_data_readiness"],
    }
    _write_json(log_path, log_payload)
    return {
        "status": "applied",
        "action": action,
        "workspace_root": str(workspace_root),
        "mutation": mutation,
        "refresh": refresh,
        "mutation_log_path": str(log_path),
    }

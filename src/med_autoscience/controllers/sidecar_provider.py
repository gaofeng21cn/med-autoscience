from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from med_autoscience.adapters import sidecar_provider as adapter
from med_autoscience.sidecars import get_provider


SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _resolve_instance_id(
    *,
    provider_id: str,
    payload: dict[str, object] | None,
    explicit_instance_id: str | None,
) -> str | None:
    spec = get_provider(provider_id)
    resolved_from_payload = spec.resolve_instance_id(payload or {})
    if spec.instance_key_name is None:
        if explicit_instance_id:
            raise ValueError(f"{provider_id} sidecar does not accept instance_id")
        return None

    if explicit_instance_id:
        normalized_explicit = str(explicit_instance_id).strip()
        if resolved_from_payload and resolved_from_payload != normalized_explicit:
            raise ValueError(
                f"{provider_id} sidecar requires explicit instance_id to match {spec.instance_key_name} from payload"
            )
        return normalized_explicit

    if resolved_from_payload:
        return resolved_from_payload
    raise ValueError(f"{provider_id} sidecar requires {spec.instance_key_name}")


def _validate_user_confirmation(provider_id: str, payload: dict[str, object]) -> dict[str, object]:
    value = payload.get("user_confirmation")
    if not isinstance(value, dict):
        raise ValueError(f"{provider_id} sidecar provisioning requires user_confirmation")
    if value.get("confirmed") is not True:
        raise ValueError(f"{provider_id} sidecar provisioning requires user_confirmation.confirmed=true")
    confirmed_by = value.get("confirmed_by")
    confirmed_at = value.get("confirmed_at")
    if not isinstance(confirmed_by, str) or not confirmed_by.strip():
        raise ValueError(f"{provider_id} sidecar provisioning requires user_confirmation.confirmed_by")
    if not isinstance(confirmed_at, str) or not confirmed_at.strip():
        raise ValueError(f"{provider_id} sidecar provisioning requires user_confirmation.confirmed_at")
    return value


def _load_sidecar_manifest(handoff_root: Path, provider_id: str) -> dict[str, object]:
    manifest = adapter.load_json(handoff_root / "sidecar_manifest.json")
    if not isinstance(manifest, dict):
        raise ValueError(f"{provider_id} sidecar handoff requires a valid sidecar_manifest.json")
    return manifest


def _validate_import_manifest(
    *,
    provider_id: str,
    manifest: dict[str, object],
    input_contract_hash: str,
    required_handoff_files: tuple[str, ...],
) -> None:
    if manifest.get("provider") != provider_id:
        raise ValueError(f"{provider_id} sidecar import requires sidecar_manifest.json provider={provider_id}")
    if manifest.get("status") != "result_ready":
        raise ValueError(f"{provider_id} sidecar import requires sidecar_manifest.json status=result_ready")
    if manifest.get("input_contract_hash") != input_contract_hash:
        raise ValueError(f"{provider_id} sidecar import requires sidecar_manifest.json to match the frozen input contract hash")
    artifacts_generated = manifest.get("artifacts_generated")
    required = set(required_handoff_files)
    if not isinstance(artifacts_generated, list) or not required.issubset({item for item in artifacts_generated if isinstance(item, str)}):
        raise ValueError(
            f"{provider_id} sidecar import requires sidecar_manifest.json artifacts_generated to cover all required handoff files"
        )


def recommend_sidecar(
    *,
    quest_root: Path,
    provider_id: str,
    payload: dict[str, object],
    instance_id: str | None = None,
) -> dict[str, object]:
    spec = get_provider(provider_id)
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_instance_id = _resolve_instance_id(provider_id=provider_id, payload=payload, explicit_instance_id=instance_id)
    recommendation_payload = spec.evaluate_recommendation(payload)
    result = {
        **recommendation_payload,
        "provider": provider_id,
        "domain_id": spec.domain_id,
        "quest_root": str(resolved_quest_root),
        "instance_id": resolved_instance_id,
    }
    if recommendation_payload["status"] == "recommended":
        persisted = dict(result)
        persisted["status"] = "awaiting_user_confirmation"
        persisted["recorded_at"] = utc_now()
        adapter.dump_json(
            adapter.recommendation_path(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id),
            persisted,
        )
    return result


def provision_sidecar(
    *,
    quest_root: Path,
    provider_id: str,
    payload: dict[str, object],
    instance_id: str | None = None,
) -> dict[str, object]:
    spec = get_provider(provider_id)
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    contract_payload = dict(payload)
    user_confirmation = _validate_user_confirmation(provider_id, contract_payload)
    contract_payload.pop("user_confirmation", None)
    normalized_contract = spec.normalize_input_contract(contract_payload)
    resolved_instance_id = _resolve_instance_id(
        provider_id=provider_id,
        payload=normalized_contract,
        explicit_instance_id=instance_id,
    )

    recommendation = adapter.load_json(
        adapter.recommendation_path(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)
    )
    if not isinstance(recommendation, dict) or recommendation.get("status") != "awaiting_user_confirmation":
        raise ValueError(f"{provider_id} sidecar provisioning requires an awaiting_user_confirmation recommendation gate")

    input_contract_hash = adapter.build_contract_hash(normalized_contract)
    input_contract_path = adapter.input_contract_path(
        resolved_quest_root,
        provider_id=provider_id,
        instance_id=resolved_instance_id,
    )
    existing_contract = adapter.load_json(input_contract_path)
    if isinstance(existing_contract, dict):
        existing_hash = adapter.build_contract_hash(existing_contract)
        if existing_hash != input_contract_hash:
            raise ValueError(f"{provider_id.upper()} sidecar contract drift detected for the existing frozen input contract")

    adapter.dump_json(input_contract_path, normalized_contract)
    handoff_root = adapter.handoff_root(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)
    handoff_root.mkdir(parents=True, exist_ok=True)
    state_payload = {
        "schema_version": SCHEMA_VERSION,
        "sidecar_id": provider_id,
        "provider": provider_id,
        "domain_id": spec.domain_id,
        "status": "contract_frozen",
        "quest_root": str(resolved_quest_root),
        "sidecar_root": str(adapter.sidecar_root(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)),
        "handoff_root": str(handoff_root),
        "instance_id": resolved_instance_id,
        "input_contract_hash": input_contract_hash,
        "input_contract_path": str(input_contract_path),
        "user_confirmation": user_confirmation,
        "updated_at": utc_now(),
    }
    state_path = adapter.state_path(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)
    adapter.dump_json(state_path, state_payload)
    return {
        "status": "contract_frozen",
        "provider": provider_id,
        "quest_root": str(resolved_quest_root),
        "sidecar_root": str(adapter.sidecar_root(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)),
        "handoff_root": str(handoff_root),
        "instance_id": resolved_instance_id,
        "input_contract_hash": input_contract_hash,
        "input_contract_path": str(input_contract_path),
        "state_path": str(state_path),
    }


def import_sidecar_result(
    *,
    quest_root: Path,
    provider_id: str,
    instance_id: str | None = None,
) -> dict[str, object]:
    spec = get_provider(provider_id)
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_instance_id = _resolve_instance_id(provider_id=provider_id, payload=None, explicit_instance_id=instance_id)
    input_contract_path = adapter.input_contract_path(
        resolved_quest_root,
        provider_id=provider_id,
        instance_id=resolved_instance_id,
    )
    input_contract = adapter.load_json(input_contract_path)
    if not isinstance(input_contract, dict):
        raise FileNotFoundError(f"Frozen {provider_id} input contract not found: {input_contract_path}")
    input_contract_hash = adapter.build_contract_hash(input_contract)
    handoff_root = adapter.handoff_root(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)
    missing = [name for name in spec.required_handoff_files if not (handoff_root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required {provider_id} handoff files: " + ", ".join(missing))

    manifest = _load_sidecar_manifest(handoff_root, provider_id)
    _validate_import_manifest(
        provider_id=provider_id,
        manifest=manifest,
        input_contract_hash=input_contract_hash,
        required_handoff_files=spec.required_handoff_files,
    )

    artifact_root = adapter.artifact_root(
        resolved_quest_root,
        domain_id=spec.domain_id,
        provider_id=provider_id,
        instance_id=resolved_instance_id,
    )
    adapter.copy_file(source=input_contract_path, destination=artifact_root / "input_contract.json")
    for name in spec.required_handoff_files:
        adapter.copy_file(source=handoff_root / name, destination=artifact_root / name)

    extra_manifest_fields = spec.finalize_import(
        resolved_quest_root,
        artifact_root,
        manifest,
        input_contract,
        input_contract_hash,
        resolved_instance_id,
    )
    imported_manifest = dict(manifest)
    imported_manifest.update(
        {
            "schema_version": SCHEMA_VERSION,
            "provider": provider_id,
            "input_contract_path": str(artifact_root / "input_contract.json"),
            "source_sidecar_root": str(adapter.sidecar_root(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)),
            "instance_id": resolved_instance_id,
            "imported_at": utc_now(),
            **extra_manifest_fields,
        }
    )
    imported_manifest_path = artifact_root / "sidecar_manifest.json"
    adapter.dump_json(imported_manifest_path, imported_manifest)
    return {
        "status": "imported",
        "provider": provider_id,
        "quest_root": str(resolved_quest_root),
        "sidecar_root": str(adapter.sidecar_root(resolved_quest_root, provider_id=provider_id, instance_id=resolved_instance_id)),
        "artifact_root": str(artifact_root),
        "instance_id": resolved_instance_id,
        "imported_manifest_path": str(imported_manifest_path),
        "input_contract_hash": input_contract_hash,
    }


def resolve_sidecar_artifacts(
    *,
    quest_root: Path,
    provider_id: str,
    instance_id: str | None = None,
) -> dict[str, object]:
    spec = get_provider(provider_id)
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_instance_id = _resolve_instance_id(provider_id=provider_id, payload=None, explicit_instance_id=instance_id)
    artifact_root = adapter.artifact_root(
        resolved_quest_root,
        domain_id=spec.domain_id,
        provider_id=provider_id,
        instance_id=resolved_instance_id,
    )
    input_contract_path = artifact_root / "input_contract.json"
    if not input_contract_path.is_file():
        return {
            "status": "absent",
            "provider": provider_id,
            "quest_root": str(resolved_quest_root),
            "artifact_root": str(artifact_root),
            "instance_id": resolved_instance_id,
            "artifacts": {},
        }

    required_paths = {"input_contract.json": input_contract_path}
    for name in spec.required_handoff_files:
        path = artifact_root / name
        if not path.is_file():
            raise FileNotFoundError(f"Imported {provider_id} artifact missing from audit surface: {path}")
        required_paths[name] = path
    return {
        "status": "imported",
        "provider": provider_id,
        "quest_root": str(resolved_quest_root),
        "artifact_root": str(artifact_root),
        "instance_id": resolved_instance_id,
        "artifacts": {name: str(path) for name, path in required_paths.items()},
    }

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


COMMON_EXECUTION_REF_FAMILIES = {
    "input_fingerprint_ref",
    "dependency_profile_ref",
    "prepared_run_context_ref",
}
ARTIFACT_AUTHORITY_FALSE_FLAGS = {
    "counts_as_paper_truth",
    "counts_as_owner_receipt",
    "can_authorize_publication_readiness",
    "can_claim_domain_ready",
    "can_claim_quality_verdict",
    "can_claim_artifact_authority",
    "can_claim_production_ready",
    "can_claim_runtime_ready",
    "can_schedule_runtime",
    "can_write_domain_truth",
    "can_write_runtime_state",
    "can_write_memory_body",
    "can_mutate_artifact_body",
    "can_sign_owner_receipt",
    "can_create_typed_blocker",
    "can_write_publication_eval",
    "can_write_controller_decisions",
    "can_write_current_package",
    "can_write_paper_or_package",
    "can_write_study_truth",
    "can_write_owner_receipt",
    "can_write_typed_blocker",
    "can_write_human_gate",
}


def build_scholarskills_materialized_package_input(
    *,
    capability_id: str,
    required_ref_families: Iterable[str],
    execution_receipt_path: Path | str | None,
    materialized_package_manifest_path: Path | str | None,
) -> dict[str, Any]:
    manifest_path = _optional_json_path(materialized_package_manifest_path)
    receipt_path = _optional_json_path(execution_receipt_path)
    manifest: dict[str, Any] = {}
    if manifest_path:
        manifest = _read_json_mapping(
            manifest_path, label="materialized_package_manifest_path"
        )
        embedded_receipt_ref = _text(manifest.get("execution_receipt_candidate_path"))
        embedded_receipt_ref = embedded_receipt_ref or _text(
            manifest.get("execution_receipt_path")
        )
        if embedded_receipt_ref and receipt_path is None:
            receipt_path = _resolve_ref_path(
                embedded_receipt_ref, base=manifest_path.parent
            )

    receipt: dict[str, Any] = {}
    if receipt_path:
        receipt = _read_json_mapping(receipt_path, label="execution_receipt_path")
    embedded_receipt = _mapping(manifest.get("execution_receipt_candidate"))
    if embedded_receipt and not receipt:
        receipt = embedded_receipt

    observed_module_ids = _dedupe_texts(
        [
            _text(manifest.get("module_id")),
            _text(receipt.get("module_id")),
        ]
    )
    mismatched_module_ids = [
        module_id for module_id in observed_module_ids if module_id != capability_id
    ]
    if mismatched_module_ids:
        raise ValueError(
            "OPL ScholarSkills materialized package module_id mismatch: "
            + ", ".join(mismatched_module_ids)
        )

    required_ref_family_list = _text_list(list(required_ref_families))
    raw_refs = _materialized_package_refs(
        required_ref_families=required_ref_family_list,
        manifest=manifest,
        receipt=receipt,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
    )
    authority_flags = _merge_mappings(
        manifest.get("authority_flags"),
        receipt.get("authority_flags"),
    )
    authority_flags.update(_top_level_authority_claims(manifest))
    authority_flags.update(_top_level_authority_claims(receipt))
    _raise_for_truthy_authority_flags(
        authority_flags,
        label="OPL ScholarSkills materialized package authority flags",
    )

    written_files = _dedupe_texts(
        [
            *_text_list(manifest.get("written_files")),
            *_text_list(receipt.get("written_files")),
        ]
    )
    forbidden_collisions = _forbidden_materialized_package_written_refs(written_files)
    if forbidden_collisions:
        raise ValueError(
            "OPL ScholarSkills materialized package reports forbidden authority writes: "
            + ", ".join(forbidden_collisions)
        )
    candidate_artifacts = _candidate_artifacts(
        required_ref_families=required_ref_family_list,
        raw_refs=raw_refs,
        manifest=manifest,
        receipt=receipt,
    )
    if not (manifest or receipt or raw_refs):
        return {}
    return {
        "execution_receipt": receipt,
        "execution_receipt_refs": raw_refs,
        "materialized_package_consumption": {
            "surface_kind": "mas_scholarskills_materialized_package_consumption",
            "schema_version": 1,
            "refs_only": True,
            "manifest_path": str(manifest_path) if manifest_path else None,
            "execution_receipt_path": str(receipt_path) if receipt_path else None,
            "module_id": _text(receipt.get("module_id"))
            or _text(manifest.get("module_id"))
            or capability_id,
            "sha256": _text(receipt.get("sha256"))
            or _text(manifest.get("sha256"))
            or None,
            "candidate_artifacts": candidate_artifacts,
            "candidate_artifact_count": len(candidate_artifacts),
            "candidate_artifact_missing_inputs": _dedupe_texts(
                missing
                for artifact in candidate_artifacts
                for missing in _text_list(artifact.get("missing_inputs"))
            ),
            "authority_flags": {
                key: value
                for key, value in authority_flags.items()
                if isinstance(value, bool)
            },
            "authority_flags_false": True,
            "written_files": written_files,
            "forbidden_written_file_collisions": forbidden_collisions,
            "mas_consumer_written_files": [],
            "counts_as_paper_truth": False,
            "counts_as_owner_receipt": False,
            "can_authorize_publication_readiness": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_write_current_package": False,
            "can_write_paper_or_package": False,
            "can_write_study_truth": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
        },
    }


def build_candidate_artifact_owner_request_items(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for artifact in _mapping_list(payload.get("candidate_artifacts")):
        items.append(
            {
                "kind": _text(artifact.get("kind")),
                "ref": _text(artifact.get("ref")) or None,
                "sha256": _text(artifact.get("sha256")) or None,
                "authority": False,
                "authority_flags_false": artifact.get("authority_flags_false") is True,
                "readiness_notes": _text_list(artifact.get("readiness_notes")),
                "missing_inputs": _text_list(artifact.get("missing_inputs")),
                "body_included": artifact.get("body_included") is True,
                "body_carried_to_owner_request": False,
                "counts_as_paper_truth": False,
                "counts_as_owner_receipt": False,
                "can_authorize_publication_readiness": False,
            }
        )
    return items


def _candidate_artifacts(
    *,
    required_ref_families: list[str],
    raw_refs: Mapping[str, str],
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for payload in (manifest, receipt):
        artifacts.extend(_candidate_artifacts_from_payload(payload))
    artifacts.extend(_candidate_artifacts_from_refs(raw_refs, required_ref_families))
    return _dedupe_candidate_artifacts(artifacts)


def _candidate_artifacts_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for key in (
        "candidate_artifacts",
        "candidate_artifact_refs",
        "artifact_refs",
        "candidate_artifact_bodies",
        "artifact_bodies",
    ):
        artifacts.extend(_candidate_artifacts_from_value(payload.get(key), source_key=key))
    return artifacts


def _candidate_artifacts_from_value(value: object, *, source_key: str) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        if _looks_like_artifact(value):
            return [_normalize_candidate_artifact(value, default_kind=source_key)]
        artifacts: list[dict[str, Any]] = []
        for kind, item in value.items():
            if isinstance(item, Mapping):
                artifacts.append(
                    _normalize_candidate_artifact(item, default_kind=_text(kind))
                )
            else:
                artifacts.append(
                    _normalize_candidate_artifact(
                        {"kind": kind, _artifact_value_key(source_key): item},
                        default_kind=_text(kind),
                    )
                )
        return artifacts
    if isinstance(value, list | tuple):
        return [
            _normalize_candidate_artifact(item, default_kind=source_key)
            for item in value
            if isinstance(item, Mapping)
        ]
    return []


def _candidate_artifacts_from_refs(
    refs: Mapping[str, str],
    required_ref_families: Iterable[str],
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for family in required_ref_families:
        ref = _text(refs.get(family))
        if not ref or family in COMMON_EXECUTION_REF_FAMILIES:
            continue
        artifacts.append(
            _normalize_candidate_artifact(
                {"kind": _artifact_kind_from_family(family), "ref": ref},
                default_kind=family,
            )
        )
    return artifacts


def _normalize_candidate_artifact(
    value: Mapping[str, Any],
    *,
    default_kind: str,
) -> dict[str, Any]:
    authority_flags = _merge_mappings(
        value.get("authority_flags"),
        _top_level_authority_claims(value),
    )
    kind = _text(value.get("kind")) or _text(value.get("artifact_kind")) or default_kind
    if not kind:
        raise ValueError("OPL ScholarSkills candidate artifact missing kind")
    _raise_for_truthy_authority_flags(
        authority_flags,
        label=f"OPL ScholarSkills candidate artifact authority flags ({kind})",
    )
    written_files = _text_list(value.get("written_files"))
    forbidden_collisions = _forbidden_materialized_package_written_refs(written_files)
    if forbidden_collisions:
        raise ValueError(
            "OPL ScholarSkills candidate artifact reports forbidden authority writes "
            f"({kind}): " + ", ".join(forbidden_collisions)
        )
    body = value.get("body")
    if body is None:
        body = value.get("artifact_body")
    ref = (
        _text(value.get("ref"))
        or _text(value.get("artifact_ref"))
        or _text(value.get("path"))
        or _text(value.get("uri"))
    )
    sha256 = _text(value.get("sha256")) or _text(value.get("body_sha256"))
    if not sha256 and body is not None:
        sha256 = _sha256(body)
    if sha256 and not sha256.startswith("sha256:"):
        sha256 = f"sha256:{sha256}"
    if not (ref or sha256):
        raise ValueError(
            f"OPL ScholarSkills candidate artifact missing ref or sha256: {kind}"
        )
    return {
        "kind": kind,
        "ref": ref or None,
        "sha256": sha256 or None,
        "authority": False,
        "authority_flags": {
            key: value
            for key, value in authority_flags.items()
            if isinstance(value, bool)
        },
        "authority_flags_false": True,
        "readiness_notes": _text_list(value.get("readiness_notes"))
        or _text_list(value.get("readiness_note")),
        "missing_inputs": _text_list(value.get("missing_inputs")),
        "body_included": body is not None,
        "body_carried_to_owner_request": False,
        "written_files": written_files,
        "forbidden_written_file_collisions": forbidden_collisions,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }


def _dedupe_candidate_artifacts(
    artifacts: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for artifact in artifacts:
        key = (
            _text(artifact.get("kind")),
            _text(artifact.get("ref")),
            _text(artifact.get("sha256")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(artifact))
    return result


def _looks_like_artifact(value: Mapping[str, Any]) -> bool:
    return any(
        key in value
        for key in (
            "kind",
            "artifact_kind",
            "ref",
            "artifact_ref",
            "path",
            "uri",
            "sha256",
            "body",
            "artifact_body",
        )
    )


def _artifact_value_key(source_key: str) -> str:
    if source_key in {"candidate_artifact_bodies", "artifact_bodies"}:
        return "body"
    return "ref"


def _artifact_kind_from_family(family: str) -> str:
    return family.removesuffix("_ref")


def _materialized_package_refs(
    *,
    required_ref_families: Iterable[str],
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
    manifest_path: Path | None,
    receipt_path: Path | None,
) -> dict[str, str]:
    refs: dict[str, str] = {}
    if receipt_path:
        refs["execution_receipt_ref"] = str(receipt_path)
    elif manifest_path:
        refs["execution_receipt_ref"] = str(manifest_path)
    execution_receipt_ref = _text(receipt.get("execution_receipt_ref"))
    execution_receipt_ref = execution_receipt_ref or _text(
        manifest.get("execution_receipt_ref")
    )
    if execution_receipt_ref:
        refs["execution_receipt_ref"] = execution_receipt_ref
    for payload in (manifest, receipt):
        refs.update(_mapping(payload.get("execution_receipt_refs")))
        refs.update(_mapping(payload.get("refs")))
        artifact_manifest_path = _text(payload.get("artifact_manifest_path"))
        if artifact_manifest_path and "artifact_manifest_ref" not in refs:
            refs["artifact_manifest_ref"] = artifact_manifest_path
            refs.setdefault(
                _module_manifest_family(required_ref_families),
                artifact_manifest_path,
            )
    return {key: value for key, value in refs.items() if _text(value)}


def _module_manifest_family(required_ref_families: Iterable[str]) -> str:
    for family in _text_list(list(required_ref_families)):
        if family.endswith("_manifest_ref"):
            return family
    return "artifact_manifest_ref"


def _optional_json_path(value: Path | str | None) -> Path | None:
    text = _text(value)
    return Path(text).expanduser().resolve() if text else None


def _resolve_ref_path(value: str, *, base: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _read_json_mapping(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return dict(payload)


def _forbidden_materialized_package_written_refs(values: list[str]) -> list[str]:
    forbidden: list[str] = []
    for value in values:
        normalized = value.replace("\\", "/")
        if (
            normalized.endswith("/artifacts/publication_eval/latest.json")
            or normalized == "artifacts/publication_eval/latest.json"
            or normalized.endswith("/artifacts/controller_decisions/latest.json")
            or normalized == "artifacts/controller_decisions/latest.json"
            or "/current_package/" in normalized
            or normalized.endswith("/current_package")
            or normalized == "paper"
            or normalized.endswith("/paper")
            or "/paper/" in normalized
            or normalized == "package"
            or normalized.endswith("/package")
            or "/package/" in normalized
            or "/typed_blocker" in normalized
            or "/human_gate" in normalized
            or "/owner_receipt" in normalized
        ):
            forbidden.append(value)
    return forbidden


def _top_level_authority_claims(payload: Mapping[str, Any]) -> dict[str, bool]:
    return {
        key: value
        for key in ARTIFACT_AUTHORITY_FALSE_FLAGS
        if isinstance((value := payload.get(key)), bool)
    }


def _raise_for_truthy_authority_flags(
    flags: Mapping[str, Any],
    *,
    label: str,
) -> None:
    truthy = [key for key, value in flags.items() if value is True]
    if truthy:
        raise ValueError(f"{label} must be false: " + ", ".join(sorted(truthy)))


def _sha256(value: object) -> str:
    if isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _dedupe_texts(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _merge_mappings(*values: object) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        result.update(_mapping(value))
    return result


def _text_list(value: object) -> list[str]:
    if isinstance(value, (str, Path)):
        text = _text(value)
        return [text] if text else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()

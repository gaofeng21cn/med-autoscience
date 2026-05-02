from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "artifact_runtime_proof"


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _hash_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _authority() -> dict[str, Any]:
    return {
        "proof_can_authorize_scientific_quality": False,
        "scientific_quality_authority": "publication_eval_and_controller_decisions",
        "derived_artifact_can_authorize_submission": False,
        "derived_artifact_can_be_quality_authority": False,
        "derived_artifact_can_be_edit_source": False,
    }


def _blocked_proof(
    *,
    study_root: Path,
    manifest_path: Path,
    blockers: list[dict[str, Any]],
    refs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "rebuild_status": "blocked",
        "current_package_from_canonical_source": False,
        "blockers": blockers,
        "refs": {
            "study_root": str(study_root),
            "delivery_manifest_path": str(manifest_path),
            **(refs or {}),
        },
        "authority": _authority(),
    }


def _source_ref_text(item: object) -> str | None:
    if isinstance(item, str):
        return _text(item)
    if not isinstance(item, Mapping):
        return None
    for key in ("relative_path", "path", "ref", "source_ref"):
        text = _text(item.get(key))
        if text is not None:
            return text
    return _text(item.get("source_path"))


def _canonical_source_ref_texts(manifest: Mapping[str, Any]) -> list[str]:
    source_refs: list[str] = []
    for field_name in ("source_relative_paths", "canonical_source_refs", "source_refs"):
        for item in _list(manifest.get(field_name)):
            text = _source_ref_text(item)
            if text is not None:
                source_refs.append(text)
        if source_refs:
            return source_refs

    for item in _list(manifest.get("copied_files")):
        text = _source_ref_text(item)
        if text is not None:
            source_refs.append(text)
    return source_refs


def _relative_label_for_path(*, path: Path, source_root: Path, paper_root: Path | None, study_root: Path) -> str:
    resolved = path.expanduser().resolve()
    for root in (source_root, paper_root, study_root):
        if root is None:
            continue
        try:
            return resolved.relative_to(root.expanduser().resolve()).as_posix()
        except ValueError:
            continue
    return str(resolved)


def _resolve_source_ref(
    *,
    ref: str,
    study_root: Path,
    source_root: Path,
    paper_root: Path | None,
) -> tuple[str, Path]:
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        return _relative_label_for_path(
            path=resolved,
            source_root=source_root,
            paper_root=paper_root,
            study_root=study_root,
        ), resolved

    candidates = [source_root / candidate]
    if paper_root is not None:
        candidates.append(paper_root / candidate)
    candidates.append(study_root / candidate)
    for path in candidates:
        resolved = path.expanduser().resolve()
        if resolved.is_file():
            return candidate.as_posix(), resolved
    return candidate.as_posix(), candidates[0].expanduser().resolve()


def _source_signature(
    *,
    study_root: Path,
    source_root: Path,
    paper_root: Path | None,
    source_refs: list[str],
) -> tuple[str | None, list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    missing_refs: list[str] = []
    seen_labels: set[str] = set()
    for ref in source_refs:
        label, path = _resolve_source_ref(
            ref=ref,
            study_root=study_root,
            source_root=source_root,
            paper_root=paper_root,
        )
        if label in seen_labels:
            continue
        seen_labels.add(label)
        if not path.is_file():
            missing_refs.append(label)
            continue
        stat = path.stat()
        entries.append(
            {
                "path": label,
                "source_path": str(path),
                "size": stat.st_size,
                "sha256": _hash_file_bytes(path),
            }
        )
    if missing_refs or not entries:
        return None, entries, sorted(missing_refs)
    payload = [
        {
            "path": item["path"],
            "size": item["size"],
            "sha256": item["sha256"],
        }
        for item in sorted(entries, key=lambda value: str(value["path"]))
    ]
    signature = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return signature, sorted(entries, key=lambda value: str(value["path"])), []


def _stable_blocking_refs(value: object) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in _list(value):
        if isinstance(item, Mapping):
            compact = {str(key): item[key] for key in sorted(item) if str(item.get(key) or "").strip()}
            if compact:
                refs.append(compact)
            continue
        text = str(item or "").strip()
        if text:
            refs.append({"ref": text})
    return refs


def build_artifact_runtime_proof(study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    manifest_path = resolved_study_root / "manuscript" / "delivery_manifest.json"
    if not manifest_path.exists():
        return _blocked_proof(
            study_root=resolved_study_root,
            manifest_path=manifest_path,
            blockers=[{"code": "delivery_manifest_missing"}],
        )

    try:
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _blocked_proof(
            study_root=resolved_study_root,
            manifest_path=manifest_path,
            blockers=[{"code": "delivery_manifest_invalid"}],
        )
    if not isinstance(manifest_payload, Mapping):
        return _blocked_proof(
            study_root=resolved_study_root,
            manifest_path=manifest_path,
            blockers=[{"code": "delivery_manifest_invalid"}],
        )

    manifest = manifest_payload
    surface_roles = _mapping(manifest.get("surface_roles"))
    source_payload = _mapping(manifest.get("source"))
    targets = _mapping(manifest.get("targets"))
    source_root_text = _text(surface_roles.get("controller_authorized_package_source_root"))
    paper_root_text = _text(surface_roles.get("controller_authorized_paper_root")) or _text(source_payload.get("paper_root"))
    source_root = Path(source_root_text).expanduser().resolve() if source_root_text is not None else None
    paper_root = Path(paper_root_text).expanduser().resolve() if paper_root_text is not None else None
    recorded_source_signature = _text(manifest.get("source_signature"))
    recorded_authority_source_signature = _text(manifest.get("authority_source_signature")) or recorded_source_signature
    blocking_artifact_refs = _stable_blocking_refs(manifest.get("blocking_artifact_refs"))
    current_package_root = _text(surface_roles.get("human_facing_current_package_root")) or _text(
        targets.get("current_package_root")
    )
    current_package_zip = _text(surface_roles.get("human_facing_current_package_zip")) or _text(
        targets.get("current_package_zip")
    )

    refs: dict[str, Any] = {
        "controller_authorized_package_source_root": str(source_root) if source_root is not None else None,
        "controller_authorized_paper_root": str(paper_root) if paper_root is not None else None,
        "current_package_root": current_package_root,
        "current_package_zip": current_package_zip,
        "delivery_source_signature": recorded_source_signature,
        "authority_source_signature": recorded_authority_source_signature,
        "blocking_artifact_refs": blocking_artifact_refs,
    }
    blockers: list[dict[str, Any]] = []
    if source_root is None:
        blockers.append({"code": "controller_authorized_package_source_root_missing"})
    if recorded_source_signature is None:
        blockers.append({"code": "source_signature_missing"})
    if blocking_artifact_refs:
        blockers.append(
            {
                "code": "blocking_artifact_refs_present",
                "blocking_artifact_refs": blocking_artifact_refs,
            }
        )
    if (
        recorded_source_signature is not None
        and recorded_authority_source_signature is not None
        and recorded_source_signature != recorded_authority_source_signature
    ):
        blockers.append(
            {
                "code": "authority_source_signature_mismatch",
                "delivery_source_signature": recorded_source_signature,
                "authority_source_signature": recorded_authority_source_signature,
            }
        )

    if source_root is None:
        return _blocked_proof(
            study_root=resolved_study_root,
            manifest_path=manifest_path,
            blockers=blockers,
            refs=refs,
        )

    source_refs = _canonical_source_ref_texts(manifest)
    refs["canonical_source_refs"] = source_refs
    if not source_refs:
        blockers.append({"code": "canonical_source_refs_missing"})

    evaluated_source_signature, source_entries, missing_refs = _source_signature(
        study_root=resolved_study_root,
        source_root=source_root,
        paper_root=paper_root,
        source_refs=source_refs,
    )
    refs["source_signature"] = evaluated_source_signature
    refs["canonical_source_entries"] = source_entries
    if missing_refs:
        refs["missing_source_refs"] = missing_refs
        blockers.append({"code": "canonical_source_ref_missing", "missing_source_refs": missing_refs})
    if (
        evaluated_source_signature is not None
        and recorded_source_signature is not None
        and evaluated_source_signature != recorded_source_signature
    ):
        blockers.append(
            {
                "code": "source_signature_mismatch",
                "evaluated_source_signature": evaluated_source_signature,
                "delivery_source_signature": recorded_source_signature,
            }
        )

    if blockers:
        return _blocked_proof(
            study_root=resolved_study_root,
            manifest_path=manifest_path,
            blockers=blockers,
            refs=refs,
        )

    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "rebuild_status": "current",
        "current_package_from_canonical_source": True,
        "blockers": [],
        "refs": {
            "study_root": str(resolved_study_root),
            "delivery_manifest_path": str(manifest_path),
            **refs,
        },
        "authority": _authority(),
    }

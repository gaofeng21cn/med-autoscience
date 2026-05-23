from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.authority_write_route import (
    blocked_authority_write_payload,
    resolve_authority_write_route_context,
)
from med_autoscience.controllers.submission_package_layout import (
    audit_path,
    reproducibility_path,
    resolve_submission_manifest_path,
)
from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.publication_profiles import normalize_publication_profile

from .delivery_context import FORMAL_PAPER_DELIVERY_RELATIVE_PATHS
from .delivery_io import (
    clear_directory_contents,
    copy_file,
    dump_json,
    utc_now,
    write_text,
)
from .delivery_rendering import (
    build_current_package_readme,
    build_preview_general_delivery_readme,
)
from .delivery_context import (
    _resolve_delivery_context,
    build_authority_source_relative_root,
    build_charter_contract_linkage,
    build_submission_source_root,
    can_sync_study_delivery,
)
from .delivery_descriptions import (
    _copy_optional_file,
    _copy_optional_tree,
    _iter_relative_files,
)
from .delivery_io import build_zip_from_directory

def _resolve_submission_source_path(*, paper_root: Path, source_root: Path, relative_path: Path) -> Path:
    if relative_path in FORMAL_PAPER_DELIVERY_RELATIVE_PATHS:
        return paper_root / relative_path
    return source_root / relative_path


def _hash_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS = frozenset(
    {
        Path("README.md"),
    }
)

CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS: dict[Path, frozenset[str]] = {
    Path("evidence_ledger.json"): frozenset({"updated_at"}),
    Path("audit/evidence_ledger.json"): frozenset({"updated_at"}),
    **{Path("reproducibility") / name: frozenset({"package_role"}) for name in ("source_signature.json", "source_relative_paths.json", "analysis_manifest.json")},
}


def _submission_projection_target_relative_path(relative_path: Path) -> Path:
    if relative_path == Path("submission_manifest.json"):
        return Path("audit") / "submission_manifest.json"
    if relative_path == Path("evidence_ledger.json"):
        return Path("audit") / "evidence_ledger.json"
    if relative_path == Path("review") / "review_ledger.json":
        return Path("audit") / "review_ledger.json"
    if relative_path == Path("controller") / "study_charter.json":
        return Path("audit") / "study_charter.json"
    if relative_path == Path("reproducibility") / "source_signature.json":
        return Path("reproducibility") / "source_signature.json"
    if relative_path == Path("reproducibility") / "source_relative_paths.json":
        return Path("reproducibility") / "source_relative_paths.json"
    if relative_path == Path("reproducibility") / "analysis_manifest.json":
        return Path("reproducibility") / "analysis_manifest.json"
    return relative_path


def _submission_projection_target_path(*, relative_path: Path, current_package_root: Path) -> Path:
    return current_package_root / _submission_projection_target_relative_path(relative_path)


def _submission_source_relative_paths(*, paper_root: Path, source_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_source_root = Path(source_root).expanduser().resolve()
    canonical_target_paths = {
        _submission_projection_target_relative_path(relative_path)
        for relative_path in FORMAL_PAPER_DELIVERY_RELATIVE_PATHS
        if (resolved_paper_root / relative_path).exists()
    }
    relative_paths = [
        relative_path
        for relative_path in _iter_relative_files(resolved_source_root)
        if _submission_projection_target_relative_path(relative_path) not in canonical_target_paths
    ]
    relative_paths.extend(
        relative_path
        for relative_path in FORMAL_PAPER_DELIVERY_RELATIVE_PATHS
        if (resolved_paper_root / relative_path).exists()
    )
    deduped = {path.as_posix(): path for path in relative_paths}
    return tuple(sorted(deduped.values(), key=lambda item: item.as_posix()))


def _submission_source_signature(*, paper_root: Path, source_root: Path, relative_paths: tuple[Path, ...]) -> str:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_source_root = Path(source_root).expanduser().resolve()
    fingerprint_payload = []
    for relative_path in relative_paths:
        source = _resolve_submission_source_path(
            paper_root=resolved_paper_root,
            source_root=resolved_source_root,
            relative_path=relative_path,
        )
        stat = source.stat()
        fingerprint_payload.append(
            {
                "path": relative_path.as_posix(),
                "size": stat.st_size,
                "sha256": _hash_file_bytes(source),
            }
        )
    canonical = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_json_file(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _normalize_projection_json_payload(*, relative_path: Path, payload: Any) -> Any:
    volatile_keys = CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS.get(relative_path)
    if not volatile_keys or not isinstance(payload, dict):
        return payload
    return {key: value for key, value in payload.items() if key not in volatile_keys}


def _submission_projection_file_matches_source(
    *,
    relative_path: Path,
    source: Path,
    target: Path,
) -> bool:
    if not target.exists():
        return False
    if relative_path in CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS:
        return True
    if _hash_file_bytes(source) == _hash_file_bytes(target):
        return True
    if relative_path not in CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS:
        return False
    source_payload = _load_json_file(source)
    target_payload = _load_json_file(target)
    if source_payload is None or target_payload is None:
        return False
    return _normalize_projection_json_payload(
        relative_path=relative_path,
        payload=source_payload,
    ) == _normalize_projection_json_payload(
        relative_path=relative_path,
        payload=target_payload,
    )


def _submission_projection_matches_source(
    *,
    paper_root: Path,
    source_root: Path,
    current_package_root: Path,
    relative_paths: tuple[Path, ...],
) -> bool:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_source_root = Path(source_root).expanduser().resolve()
    resolved_current_package_root = Path(current_package_root).expanduser().resolve()
    for relative_path in relative_paths:
        source = _resolve_submission_source_path(
            paper_root=resolved_paper_root,
            source_root=resolved_source_root,
            relative_path=relative_path,
        )
        target = _submission_projection_target_path(
            relative_path=relative_path,
            current_package_root=resolved_current_package_root,
        )
        if not _submission_projection_file_matches_source(
            relative_path=relative_path,
            source=source,
            target=target,
        ):
            return False
    return True


def _submission_delivery_blocking_artifact_refs(
    *,
    status: str,
    stale_reason: str | None,
    delivery_manifest_path: Path,
    missing_source_paths: list[str],
) -> list[dict[str, Any]]:
    if status == "current":
        return []
    refs: list[dict[str, Any]] = []
    if delivery_manifest_path.exists():
        refs.append(
            {
                "blocker": "stale_study_delivery_mirror",
                "artifact_path": str(delivery_manifest_path),
                "artifact_role": "study_delivery_mirror",
                "stale_reason": stale_reason,
            }
        )
    for path in missing_source_paths:
        refs.append(
            {
                "blocker": "stale_study_delivery_mirror",
                "artifact_path": path,
                "artifact_role": "missing_delivery_source",
                "stale_reason": stale_reason,
            }
        )
    return refs


def _submission_delivery_handshake(
    *,
    status: str,
    evaluated_source_signature: str | None,
    authority_source_signature: str | None,
    delivery_source_signature: str | None,
    blocking_artifact_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": status,
        "evaluated_source_signature": evaluated_source_signature,
        "authority_source_signature": authority_source_signature,
        "delivery_source_signature": delivery_source_signature,
        "blocking_artifact_refs": blocking_artifact_refs,
        "replay_after_repair": status != "current",
    }


def describe_submission_delivery(
    *,
    paper_root: Path,
    publication_profile: str = "general_medical_journal",
) -> dict[str, Any]:
    if not can_sync_study_delivery(paper_root=paper_root):
        return {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": None,
            "current_package_zip": None,
            "missing_source_paths": [],
            "evaluated_source_signature": None,
            "authority_source_signature": None,
            "delivery_source_signature": None,
            "source_signature": None,
            "blocking_artifact_refs": [],
            "gate_freshness_handshake": _submission_delivery_handshake(
                status="not_applicable",
                evaluated_source_signature=None,
                authority_source_signature=None,
                delivery_source_signature=None,
                blocking_artifact_refs=[],
            ),
        }

    context = _resolve_delivery_context(Path(paper_root).expanduser().resolve())
    resolved_paper_root = context["paper_root"]
    study_root = context["study_root"]
    manuscript_root = study_root / "manuscript"
    delivery_manifest_path = manuscript_root / "delivery_manifest.json"
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    if not delivery_manifest_path.exists():
        return {
            "applicable": True,
            "status": "missing",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": [],
            "evaluated_source_signature": None,
            "authority_source_signature": None,
            "delivery_source_signature": None,
            "source_signature": None,
            "blocking_artifact_refs": [],
            "gate_freshness_handshake": _submission_delivery_handshake(
                status="missing",
                evaluated_source_signature=None,
                authority_source_signature=None,
                delivery_source_signature=None,
                blocking_artifact_refs=[],
            ),
        }
    try:
        manifest = json.loads(delivery_manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "delivery_manifest_invalid",
            "delivery_manifest_path": str(delivery_manifest_path),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": [],
            "evaluated_source_signature": None,
            "authority_source_signature": None,
            "delivery_source_signature": None,
            "source_signature": None,
            "blocking_artifact_refs": [],
            "gate_freshness_handshake": _submission_delivery_handshake(
                status="invalid",
                evaluated_source_signature=None,
                authority_source_signature=None,
                delivery_source_signature=None,
                blocking_artifact_refs=[],
            ),
        }
    if not isinstance(manifest, dict):
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "delivery_manifest_invalid",
            "delivery_manifest_path": str(delivery_manifest_path),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": [],
            "evaluated_source_signature": None,
            "authority_source_signature": None,
            "delivery_source_signature": None,
            "source_signature": None,
            "blocking_artifact_refs": [],
            "gate_freshness_handshake": _submission_delivery_handshake(
                status="invalid",
                evaluated_source_signature=None,
                authority_source_signature=None,
                delivery_source_signature=None,
                blocking_artifact_refs=[],
            ),
        }

    expected_source_root = build_submission_source_root(
        paper_root=resolved_paper_root,
        publication_profile=normalized_publication_profile,
    )
    expected_manifest_path = resolve_submission_manifest_path(expected_source_root)
    if not expected_manifest_path.exists():
        missing_source_paths = sorted(
            {
                str(Path(item.get("source_path")).expanduser())
                for item in (manifest.get("copied_files") or [])
                if isinstance(item, dict) and str(item.get("source_path") or "").strip()
            }
        )
        blocking_artifact_refs = _submission_delivery_blocking_artifact_refs(
            status="stale_source_missing",
            stale_reason="current_submission_source_missing",
            delivery_manifest_path=delivery_manifest_path,
            missing_source_paths=missing_source_paths,
        )
        return {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "current_submission_source_missing",
            "delivery_manifest_path": str(delivery_manifest_path),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": missing_source_paths,
            "evaluated_source_signature": None,
            "authority_source_signature": str(manifest.get("authority_source_signature") or "").strip() or None,
            "delivery_source_signature": str(manifest.get("source_signature") or "").strip() or None,
            "source_signature": None,
            "blocking_artifact_refs": blocking_artifact_refs,
            "gate_freshness_handshake": _submission_delivery_handshake(
                status="stale_source_missing",
                evaluated_source_signature=None,
                authority_source_signature=str(manifest.get("authority_source_signature") or "").strip() or None,
                delivery_source_signature=str(manifest.get("source_signature") or "").strip() or None,
                blocking_artifact_refs=blocking_artifact_refs,
            ),
        }

    recorded_surface_roles = manifest.get("surface_roles") or {}
    recorded_source_root = (
        str((recorded_surface_roles or {}).get("controller_authorized_package_source_root") or "").strip()
        or str(((manifest.get("source") or {}) if isinstance(manifest.get("source"), dict) else {}).get("package_source_root") or "").strip()
    )
    source_relative_paths = _submission_source_relative_paths(
        paper_root=resolved_paper_root,
        source_root=expected_source_root,
    )
    source_signature = _submission_source_signature(
        paper_root=resolved_paper_root,
        source_root=expected_source_root,
        relative_paths=source_relative_paths,
    )
    recorded_source_signature = str(manifest.get("source_signature") or "").strip() or None
    recorded_authority_source_signature = (
        str(manifest.get("authority_source_signature") or "").strip()
        or recorded_source_signature
    )
    missing_source_paths = sorted(
        {
            str(Path(item.get("source_path")).expanduser().resolve())
            for item in (manifest.get("copied_files") or [])
            if isinstance(item, dict)
            and str(item.get("source_path") or "").strip()
            and not Path(str(item.get("source_path"))).expanduser().exists()
        }
    )
    if missing_source_paths:
        status = "stale_source_missing"
        stale_reason = "delivery_manifest_sources_missing"
    elif not current_package_root.exists() or not current_package_zip.exists():
        status = "stale_projection_missing"
        stale_reason = "delivery_projection_missing"
    elif recorded_source_root and recorded_source_root != str(expected_source_root.resolve()):
        status = "stale_source_mismatch"
        stale_reason = "delivery_manifest_source_mismatch"
    elif not _submission_projection_matches_source(
        paper_root=resolved_paper_root,
        source_root=expected_source_root,
        current_package_root=current_package_root,
        relative_paths=source_relative_paths,
    ):
        status = "stale_source_changed"
        stale_reason = "delivery_manifest_source_changed"
    else:
        status = "current"
        stale_reason = None
    blocking_artifact_refs = _submission_delivery_blocking_artifact_refs(
        status=status,
        stale_reason=stale_reason,
        delivery_manifest_path=delivery_manifest_path,
        missing_source_paths=missing_source_paths,
    )
    return {
        "applicable": True,
        "status": status,
        "stale_reason": stale_reason,
        "delivery_manifest_path": str(delivery_manifest_path),
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
        "missing_source_paths": missing_source_paths,
        "evaluated_source_signature": source_signature,
        "authority_source_signature": recorded_authority_source_signature,
        "delivery_source_signature": recorded_source_signature,
        "source_signature": source_signature,
        "blocking_artifact_refs": blocking_artifact_refs,
        "gate_freshness_handshake": _submission_delivery_handshake(
            status=status,
            evaluated_source_signature=source_signature,
            authority_source_signature=recorded_authority_source_signature,
            delivery_source_signature=recorded_source_signature,
            blocking_artifact_refs=blocking_artifact_refs,
        ),
    }


def materialize_submission_delivery_stale_notice(
    *,
    paper_root: Path,
    stale_reason: str,
    missing_source_paths: list[str] | None = None,
    publication_profile: str = "general_medical_journal",
    authority_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not can_sync_study_delivery(paper_root=paper_root):
        return {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_status_path": None,
            "current_package_root": None,
            "current_package_zip": None,
            "missing_source_paths": [],
            "cleared_paths": [],
        }

    context = _resolve_delivery_context(Path(paper_root).expanduser().resolve())
    resolved_paper_root = context["paper_root"]
    study_root = context["study_root"]
    study_id = context["study_id"]
    manuscript_root = study_root / "manuscript"
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    delivery_manifest_path = manuscript_root / "delivery_manifest.json"
    delivery_status_path = manuscript_root / "delivery_status.json"
    _resolved_route_context, authority_route_gate = resolve_authority_write_route_context(
        action="submission_notice_materialize",
        context=authority_route_context or route_context,
        default_paths=[current_package_root, current_package_zip, delivery_status_path],
    )
    if not bool(authority_route_gate.get("authorized")):
        return blocked_authority_write_payload(
            gate=authority_route_gate,
            paper_root=str(resolved_paper_root),
            study_root=str(study_root),
            delivery_status_path=str(delivery_status_path),
        )
    cleared_paths = clear_directory_contents(manuscript_root, keep_names=("delivery_manifest.json",))
    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []

    expected_source_root = build_submission_source_root(
        paper_root=resolved_paper_root,
        publication_profile=normalized_publication_profile,
    )
    source_relative_root = build_authority_source_relative_root(
        paper_root=resolved_paper_root,
        source_root=expected_source_root,
    )
    manuscript_root.mkdir(parents=True, exist_ok=True)
    current_package_root.mkdir(parents=True, exist_ok=True)
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=resolved_paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        review_ledger_path=resolved_paper_root / "review" / "review_ledger.json",
    )
    preview_file_count = 0
    for name in ("manuscript.docx", "paper.pdf"):
        if _copy_optional_file(
            source=expected_source_root / name,
            target=manuscript_root / name,
            category="preview_delivery_root",
            copied_files=copied_files,
        ):
            preview_file_count += 1
            copy_file(
                source=manuscript_root / name,
                target=current_package_root / name,
                category="preview_current_package",
                copied_files=copied_files,
            )
    source_manifest_path = resolve_submission_manifest_path(expected_source_root)
    if _copy_optional_file(
        source=source_manifest_path,
        target=audit_path(manuscript_root, "submission_manifest"),
        category="preview_delivery_root",
        copied_files=copied_files,
    ):
        preview_file_count += 1
        copy_file(
            source=audit_path(manuscript_root, "submission_manifest"),
            target=audit_path(current_package_root, "submission_manifest"),
            category="preview_current_package",
            copied_files=copied_files,
        )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "build" / "review_manuscript.md",
            target=current_package_root / "review_manuscript.md",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "build" / "compile_report.json",
            target=current_package_root / "compile_report.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "review" / "submission_checklist.json",
            target=current_package_root / "submission_checklist.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "paper_bundle_manifest.json",
            target=current_package_root / "paper_bundle_manifest.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "figures" / "figure_catalog.json",
            target=current_package_root / "figures" / "figure_catalog.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += _copy_optional_tree(
        source_root=resolved_paper_root / "figures" / "generated",
        target_root=current_package_root / "figures",
        category="preview_current_package",
        copied_files=copied_files,
        ignore_suffixes=(".layout.json",),
        ignore_filenames=("README.md",),
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "tables" / "table_catalog.json",
            target=current_package_root / "tables" / "table_catalog.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += _copy_optional_tree(
        source_root=resolved_paper_root / "tables" / "generated",
        target_root=current_package_root / "tables",
        category="preview_current_package",
        copied_files=copied_files,
        ignore_filenames=("README.md",),
    )
    write_text(
        manuscript_root / "README.md",
        build_preview_general_delivery_readme(
            study_id=study_id,
            stale_reason=stale_reason,
            source_relative_root=source_relative_root,
        ),
    )
    generated_files.append(
        {
            "category": "preview_delivery_readme",
            "path": str((manuscript_root / "README.md").resolve()),
        }
    )
    current_package_readme_path = current_package_root / "README.md"
    write_text(
        current_package_readme_path,
        build_current_package_readme(
            study_id=study_id,
            stage="submission_preview",
            source_relative_root=source_relative_root,
            status_line="audit preview only; not submission-ready",
            charter_contract_linkage=charter_contract_linkage,
        ),
    )
    generated_files.append(
        {
            "category": "preview_current_package",
            "path": str(current_package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(source_root=current_package_root, output_path=current_package_zip)
    generated_files.append(
        {
            "category": "preview_current_package",
            "path": str(current_package_zip.resolve()),
        }
    )
    status_payload = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "study_id": study_id,
        "publication_profile": normalized_publication_profile,
        "status": "stale_source_missing",
        "stale_reason": stale_reason,
        "preview_mode": "authority_audit_preview",
        "submission_ready": False,
        "preview_file_count": preview_file_count,
        "source": {
            "paper_root": str(resolved_paper_root),
            "expected_package_source_root": str(expected_source_root),
        },
        "charter_contract_linkage": charter_contract_linkage,
        "active_delivery_manifest_path": str(delivery_manifest_path) if delivery_manifest_path.exists() else None,
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
        "missing_source_paths": list(missing_source_paths or []),
        "cleared_paths": cleared_paths,
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    generated_files.append(
        {
            "category": "preview_delivery_status",
            "path": str(delivery_status_path.resolve()),
        }
    )
    dump_json(delivery_status_path, status_payload)
    return {
        "applicable": True,
        **status_payload,
        "delivery_status_path": str(delivery_status_path),
        "authority_route_gate": authority_route_gate,
    }


__all__ = [name for name in globals() if not name.startswith("__")]

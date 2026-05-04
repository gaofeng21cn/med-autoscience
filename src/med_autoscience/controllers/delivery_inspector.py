from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import study_delivery_sync
from med_autoscience.controllers.submission_package_layout import (
    AUDIT_DIRNAME,
    REPRODUCIBILITY_DIRNAME,
    SUBMISSION_PACKAGE_LAYOUT_VERSION,
    V2_AUDIT_RELATIVE_PATHS,
    V2_REPRODUCIBILITY_RELATIVE_PATHS,
    has_legacy_root_audit_files,
    resolve_submission_manifest_path,
)
from med_autoscience.journal_requirements import journal_submission_package_root
from med_autoscience.profiles import WorkspaceProfile


_LEGACY_ROOT_AUDIT_LABELS = {
    "submission_manifest": Path("submission_manifest.json"),
    "evidence_ledger": Path("evidence_ledger.json"),
    "review_ledger": Path("review") / "review_ledger.json",
    "study_charter": Path("controller") / "study_charter.json",
}


def _path_string(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _status_for_required_paths(package_root: Path, relative_paths: Mapping[str, Path]) -> dict[str, Any]:
    present = sorted(key for key, relative_path in relative_paths.items() if (package_root / relative_path).exists())
    missing = sorted(key for key, relative_path in relative_paths.items() if not (package_root / relative_path).exists())
    if not package_root.exists():
        status = "missing"
    elif not missing:
        status = "complete"
    elif present:
        status = "partial"
    else:
        status = "missing"
    return {
        "status": status,
        "present": present,
        "missing": missing,
    }


def _legacy_root_file_status(package_root: Path) -> dict[str, Any]:
    present = sorted(
        key for key, relative_path in _LEGACY_ROOT_AUDIT_LABELS.items() if (package_root / relative_path).exists()
    )
    return {
        "status": "present" if present else "absent",
        "present": present,
    }


def _layout_status(*, package_root: Path, audit_completeness: Mapping[str, Any]) -> str:
    if not package_root.exists():
        return "missing"
    legacy_present = has_legacy_root_audit_files(package_root)
    v2_present = (package_root / AUDIT_DIRNAME).is_dir() or (package_root / REPRODUCIBILITY_DIRNAME).is_dir()
    if v2_present:
        return "v2"
    if legacy_present:
        return "legacy"
    if audit_completeness.get("status") == "complete":
        return "v2"
    return "unknown"


def _read_source_signature(package_root: Path) -> str | None:
    reproducibility_signature = package_root / V2_REPRODUCIBILITY_RELATIVE_PATHS["source_signature"]
    reproducibility_payload = _load_json_object(reproducibility_signature)
    signature = str(reproducibility_payload.get("source_signature") or "").strip()
    if signature:
        return signature
    manifest_payload = _load_json_object(resolve_submission_manifest_path(package_root))
    signature = str(manifest_payload.get("source_signature") or "").strip()
    if signature:
        return signature
    source_contract = manifest_payload.get("source_contract")
    if isinstance(source_contract, dict):
        signature = str(source_contract.get("source_signature") or "").strip()
        if signature:
            return signature
    return None


def _inspect_package(*, package_root: Path, role: str) -> dict[str, Any]:
    resolved_root = Path(package_root).expanduser().resolve()
    audit_completeness = _status_for_required_paths(resolved_root, V2_AUDIT_RELATIVE_PATHS)
    reproducibility_completeness = _status_for_required_paths(resolved_root, V2_REPRODUCIBILITY_RELATIVE_PATHS)
    legacy_status = _legacy_root_file_status(resolved_root)
    return {
        "role": role,
        "root": str(resolved_root),
        "exists": resolved_root.exists(),
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION if _layout_status(
            package_root=resolved_root,
            audit_completeness=audit_completeness,
        ) == "v2" else None,
        "layout_status": _layout_status(package_root=resolved_root, audit_completeness=audit_completeness),
        "submission_manifest_path": str(resolve_submission_manifest_path(resolved_root)),
        "audit_root": str(resolved_root / AUDIT_DIRNAME),
        "reproducibility_root": str(resolved_root / REPRODUCIBILITY_DIRNAME),
        "audit_completeness": audit_completeness,
        "reproducibility_completeness": reproducibility_completeness,
        "legacy_root_file_status": legacy_status,
        "source_signature": _read_source_signature(resolved_root),
    }


def _inspect_zip(zip_path: Path) -> dict[str, Any]:
    resolved_zip = Path(zip_path).expanduser().resolve()
    result: dict[str, Any] = {
        "path": str(resolved_zip),
        "exists": resolved_zip.exists(),
        "size_bytes": resolved_zip.stat().st_size if resolved_zip.exists() else None,
        "root_audit_entries": [],
    }
    if not resolved_zip.exists():
        return result
    try:
        with zipfile.ZipFile(resolved_zip) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        result["status"] = "invalid"
        return result
    legacy_entries = sorted(
        relative_path.as_posix()
        for relative_path in _LEGACY_ROOT_AUDIT_LABELS.values()
        if relative_path.as_posix() in names
    )
    result["status"] = "readable"
    result["root_audit_entries"] = legacy_entries
    return result


def _inspect_journal_packages(*, study_root: Path) -> list[dict[str, Any]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    candidates: list[tuple[Path, str, str]] = []
    for parent, role in (
        (resolved_study_root / "submission_packages", "journal_specific_package"),
        (resolved_study_root / "manuscript" / "journal_packages", "journal_specific_manuscript_mirror"),
        (resolved_study_root / "manuscript" / "journal_package_mirrors", "journal_specific_manuscript_mirror"),
    ):
        if not parent.exists():
            continue
        candidates.extend((child, child.name, role) for child in sorted(parent.iterdir()) if child.is_dir())

    packages: list[dict[str, Any]] = []
    seen_roots: set[Path] = set()
    for root, journal_slug, role in candidates:
        resolved_root = root.resolve()
        if resolved_root in seen_roots:
            continue
        seen_roots.add(resolved_root)
        package = _inspect_package(package_root=resolved_root, role=role)
        zip_candidates = sorted(resolved_root.glob("*_submission_package.zip"))
        if not zip_candidates and role == "journal_specific_package":
            zip_candidates = [resolved_root / f"{journal_slug}_submission_package.zip"]
        package["journal_slug"] = journal_slug
        package["zip"] = _inspect_zip(zip_candidates[0]) if zip_candidates else None
        packages.append(package)
    return packages


def _resolve_study_root(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
) -> Path:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")
    if study_root is not None:
        return Path(study_root).expanduser().resolve()
    assert study_id is not None
    return (profile.studies_root / study_id).expanduser().resolve()


def _freshness_verdict(
    *,
    delivery_status: str,
    source_package: Mapping[str, Any],
    human_package: Mapping[str, Any],
) -> str:
    package_statuses = {str(source_package.get("layout_status")), str(human_package.get("layout_status"))}
    if "legacy" in package_statuses:
        return "legacy"
    if delivery_status == "current":
        return "current"
    if delivery_status in {"missing", "not_applicable"} or "missing" in package_statuses:
        return "missing"
    if delivery_status.startswith("stale") or delivery_status in {"invalid", "incomplete"}:
        return "stale"
    return "unknown"


def inspect_study_delivery(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    publication_profile: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = _resolve_study_root(profile=profile, study_id=study_id, study_root=study_root)
    resolved_publication_profile = publication_profile or profile.default_publication_profile
    manuscript_root = resolved_study_root / "manuscript"
    delivery_manifest = _load_json_object(manuscript_root / "delivery_manifest.json")
    surface_roles = (
        delivery_manifest.get("surface_roles")
        if isinstance(delivery_manifest.get("surface_roles"), dict)
        else {}
    )
    source_block = (
        delivery_manifest.get("source")
        if isinstance(delivery_manifest.get("source"), dict)
        else {}
    )
    paper_root = Path(
        str(
            surface_roles.get("controller_authorized_paper_root")
            or source_block.get("paper_root")
            or resolved_study_root / "paper"
        )
    ).expanduser().resolve()
    recorded_source_root = str(
        surface_roles.get("controller_authorized_package_source_root")
        or source_block.get("package_source_root")
        or ""
    ).strip()
    source_root = (
        Path(recorded_source_root).expanduser().resolve()
        if recorded_source_root
        else study_delivery_sync.build_submission_source_root(
            paper_root=paper_root,
            publication_profile=resolved_publication_profile,
        )
    )
    human_root = Path(
        str(surface_roles.get("human_facing_current_package_root") or manuscript_root / "current_package")
    ).expanduser().resolve()
    current_package_zip = Path(
        str(surface_roles.get("human_facing_current_package_zip") or manuscript_root / "current_package.zip")
    ).expanduser().resolve()
    source_package = _inspect_package(package_root=source_root, role="controller_authorized_source")
    human_package = _inspect_package(package_root=human_root, role="human_facing_mirror")

    try:
        delivery_status = study_delivery_sync.describe_submission_delivery(
            paper_root=paper_root,
            publication_profile=resolved_publication_profile,
        )
    except (FileNotFoundError, ValueError):
        delivery_status = {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "evaluated_source_signature": None,
            "authority_source_signature": None,
            "delivery_source_signature": None,
            "gate_freshness_handshake": {
                "status": "not_applicable",
            },
        }

    status = str(delivery_status.get("status") or "unknown")
    verdict = _freshness_verdict(
        delivery_status=status,
        source_package=source_package,
        human_package=human_package,
    )
    source_signature = {
        "evaluated": delivery_status.get("evaluated_source_signature"),
        "authority": delivery_status.get("authority_source_signature"),
        "delivery": delivery_status.get("delivery_source_signature"),
        "source_package": source_package.get("source_signature"),
        "human_package": human_package.get("source_signature"),
    }
    return {
        "surface": "delivery_inspector",
        "schema_version": 1,
        "mutation_policy": {
            "read_only": True,
            "writes_package": False,
        },
        "authority": {
            "surface_role": "observability_only",
            "can_authorize_publication_quality": False,
            "can_authorize_submission_dispatch": False,
            "can_mutate_delivery_packages": False,
        },
        "profile_ref": _path_string(Path(profile_ref).expanduser().resolve()) if profile_ref is not None else None,
        "study_id": resolved_study_root.name,
        "study_root": str(resolved_study_root),
        "paper_root": str(paper_root),
        "publication_profile": resolved_publication_profile,
        "source_package": source_package,
        "human_package": human_package,
        "zip": _inspect_zip(current_package_zip),
        "journal_packages": _inspect_journal_packages(study_root=resolved_study_root),
        "source_signature": source_signature,
        "freshness": {
            "verdict": verdict,
            "delivery_status": status,
            "stale_reason": delivery_status.get("stale_reason"),
            "gate_freshness_handshake": delivery_status.get("gate_freshness_handshake"),
        },
        "next_sync_command": (
            "medautosci study delivery-sync "
            f"--paper-root {paper_root} "
            f"--stage submission_minimal "
            f"--publication-profile {resolved_publication_profile}"
        ),
        "wording": {
            "source": "submission_minimal = controller-authorized source",
            "mirror": "current_package = human-facing mirror",
            "legacy_upgrade": "Legacy layout upgrades on the next authorized sync.",
        },
    }


def compact_delivery_inspection(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": payload.get("surface"),
        "schema_version": payload.get("schema_version"),
        "mutation_policy": payload.get("mutation_policy"),
        "study_id": payload.get("study_id"),
        "freshness": payload.get("freshness"),
        "source_package": {
            "root": (payload.get("source_package") or {}).get("root")
            if isinstance(payload.get("source_package"), dict)
            else None,
            "layout_status": (payload.get("source_package") or {}).get("layout_status")
            if isinstance(payload.get("source_package"), dict)
            else None,
            "role": (payload.get("source_package") or {}).get("role")
            if isinstance(payload.get("source_package"), dict)
            else None,
        },
        "human_package": {
            "root": (payload.get("human_package") or {}).get("root")
            if isinstance(payload.get("human_package"), dict)
            else None,
            "layout_status": (payload.get("human_package") or {}).get("layout_status")
            if isinstance(payload.get("human_package"), dict)
            else None,
            "role": (payload.get("human_package") or {}).get("role")
            if isinstance(payload.get("human_package"), dict)
            else None,
        },
        "zip": payload.get("zip"),
        "journal_package_count": len(payload.get("journal_packages") or []),
        "next_sync_command": payload.get("next_sync_command"),
        "wording": payload.get("wording"),
    }


def render_delivery_inspection_markdown(payload: Mapping[str, Any]) -> str:
    source_package = payload.get("source_package") if isinstance(payload.get("source_package"), dict) else {}
    human_package = payload.get("human_package") if isinstance(payload.get("human_package"), dict) else {}
    freshness = payload.get("freshness") if isinstance(payload.get("freshness"), dict) else {}
    zip_payload = payload.get("zip") if isinstance(payload.get("zip"), dict) else {}
    wording = payload.get("wording") if isinstance(payload.get("wording"), dict) else {}
    lines = [
        "# Delivery Inspection",
        "",
        f"- Study: `{payload.get('study_id')}`",
        f"- Verdict: `{freshness.get('verdict')}`",
        f"- Delivery status: `{freshness.get('delivery_status')}`",
        f"- Mutation policy: `read_only=true`",
        f"- {wording.get('source') or 'submission_minimal = controller-authorized source'}",
        f"- {wording.get('mirror') or 'current_package = human-facing mirror'}",
        f"- {wording.get('legacy_upgrade') or 'Legacy layout upgrades on the next authorized sync.'}",
        "",
        "## Source Package",
        "",
        f"- Root: `{source_package.get('root')}`",
        f"- Layout: `{source_package.get('layout_status')}`",
        f"- Audit: `{(source_package.get('audit_completeness') or {}).get('status')}`",
        f"- Reproducibility: `{(source_package.get('reproducibility_completeness') or {}).get('status')}`",
        "",
        "## Human Package",
        "",
        f"- Root: `{human_package.get('root')}`",
        f"- Layout: `{human_package.get('layout_status')}`",
        f"- Audit: `{(human_package.get('audit_completeness') or {}).get('status')}`",
        f"- Reproducibility: `{(human_package.get('reproducibility_completeness') or {}).get('status')}`",
        f"- Zip: `{zip_payload.get('path')}`",
        "",
        "## Next Sync",
        "",
        f"`{payload.get('next_sync_command')}`",
        "",
    ]
    journal_packages = payload.get("journal_packages") if isinstance(payload.get("journal_packages"), list) else []
    if journal_packages:
        lines.extend(["## Journal Packages", ""])
        for package in journal_packages:
            if not isinstance(package, dict):
                continue
            lines.append(
                f"- `{package.get('journal_slug')}`: `{package.get('layout_status')}` at `{package.get('root')}`"
            )
        lines.append("")
    return "\n".join(lines)

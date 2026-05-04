from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


SUBMISSION_PACKAGE_LAYOUT_VERSION = "submission-package.v2"

AUDIT_DIRNAME = "audit"
REPRODUCIBILITY_DIRNAME = "reproducibility"

SUBMISSION_MANIFEST_BASENAME = "submission_manifest.json"
EVIDENCE_LEDGER_BASENAME = "evidence_ledger.json"
REVIEW_LEDGER_BASENAME = "review_ledger.json"
STUDY_CHARTER_BASENAME = "study_charter.json"

SOURCE_SIGNATURE_BASENAME = "source_signature.json"
SOURCE_RELATIVE_PATHS_BASENAME = "source_relative_paths.json"
ANALYSIS_MANIFEST_BASENAME = "analysis_manifest.json"

LEGACY_ROOT_AUDIT_RELATIVE_PATHS = frozenset(
    {
        Path(SUBMISSION_MANIFEST_BASENAME),
        Path(EVIDENCE_LEDGER_BASENAME),
        Path("review") / REVIEW_LEDGER_BASENAME,
        Path("controller") / STUDY_CHARTER_BASENAME,
    }
)

V2_AUDIT_RELATIVE_PATHS = {
    "submission_manifest": Path(AUDIT_DIRNAME) / SUBMISSION_MANIFEST_BASENAME,
    "evidence_ledger": Path(AUDIT_DIRNAME) / EVIDENCE_LEDGER_BASENAME,
    "review_ledger": Path(AUDIT_DIRNAME) / REVIEW_LEDGER_BASENAME,
    "study_charter": Path(AUDIT_DIRNAME) / STUDY_CHARTER_BASENAME,
}

V2_REPRODUCIBILITY_RELATIVE_PATHS = {
    "source_signature": Path(REPRODUCIBILITY_DIRNAME) / SOURCE_SIGNATURE_BASENAME,
    "source_relative_paths": Path(REPRODUCIBILITY_DIRNAME) / SOURCE_RELATIVE_PATHS_BASENAME,
    "analysis_manifest": Path(REPRODUCIBILITY_DIRNAME) / ANALYSIS_MANIFEST_BASENAME,
}


def audit_root(package_root: Path) -> Path:
    return Path(package_root) / AUDIT_DIRNAME


def reproducibility_root(package_root: Path) -> Path:
    return Path(package_root) / REPRODUCIBILITY_DIRNAME


def audit_path(package_root: Path, key: str) -> Path:
    return Path(package_root) / V2_AUDIT_RELATIVE_PATHS[key]


def reproducibility_path(package_root: Path, key: str) -> Path:
    return Path(package_root) / V2_REPRODUCIBILITY_RELATIVE_PATHS[key]


def legacy_submission_manifest_path(package_root: Path) -> Path:
    return Path(package_root) / SUBMISSION_MANIFEST_BASENAME


def submission_manifest_path(package_root: Path) -> Path:
    return audit_path(package_root, "submission_manifest")


def resolve_submission_manifest_path(package_root: Path) -> Path:
    v2_path = submission_manifest_path(package_root)
    if v2_path.exists():
        return v2_path
    return legacy_submission_manifest_path(package_root)


def has_legacy_root_audit_files(package_root: Path) -> bool:
    resolved_root = Path(package_root)
    return any((resolved_root / relative_path).exists() for relative_path in LEGACY_ROOT_AUDIT_RELATIVE_PATHS)


def _path_label(path: Path, *, workspace_root: Path | None) -> str:
    resolved = Path(path).expanduser().resolve()
    if workspace_root is None:
        return str(resolved)
    try:
        return resolved.relative_to(Path(workspace_root).expanduser().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def build_package_layout_block(
    *,
    package_root: Path,
    workspace_root: Path | None = None,
    package_role: str | None = None,
    source_package_root: Path | None = None,
    human_package_root: Path | None = None,
    source_signature: str | None = None,
    legacy_input_status: str | None = None,
) -> dict[str, Any]:
    root = Path(package_root)
    block: dict[str, Any] = {
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_root": _path_label(root, workspace_root=workspace_root),
        "audit_root": _path_label(audit_root(root), workspace_root=workspace_root),
        "reproducibility_root": _path_label(reproducibility_root(root), workspace_root=workspace_root),
        "audit_paths": {
            key: _path_label(root / relative_path, workspace_root=workspace_root)
            for key, relative_path in V2_AUDIT_RELATIVE_PATHS.items()
        },
        "reproducibility_paths": {
            key: _path_label(root / relative_path, workspace_root=workspace_root)
            for key, relative_path in V2_REPRODUCIBILITY_RELATIVE_PATHS.items()
        },
    }
    if package_role:
        block["package_role"] = package_role
    if source_package_root is not None:
        block["source_package_root"] = _path_label(source_package_root, workspace_root=workspace_root)
    if human_package_root is not None:
        block["human_package_root"] = _path_label(human_package_root, workspace_root=workspace_root)
    if source_signature:
        block["source_signature"] = source_signature
    if legacy_input_status:
        block["legacy_input_status"] = legacy_input_status
    return block


def build_submission_delivery_layout_block(
    *,
    source_package_root: Path,
    human_package_root: Path,
    source_signature: str,
    package_role: str,
) -> dict[str, Any]:
    return build_package_layout_block(
        package_root=human_package_root,
        source_package_root=source_package_root,
        human_package_root=human_package_root,
        source_signature=source_signature,
        package_role=package_role,
        legacy_input_status="v2_generated",
    )


def build_submission_delivery_signature_block(
    *,
    source_signature: str,
    source_relative_paths: Iterable[Any],
    source_package_root: Path,
    human_package_root: Path,
    package_role: str,
) -> dict[str, Any]:
    return {
        "source_signature": source_signature,
        "evaluated_source_signature": source_signature,
        "authority_source_signature": source_signature,
        "source_relative_paths": [
            path.as_posix() if hasattr(path, "as_posix") else str(path)
            for path in source_relative_paths
        ],
        "delivery_layout": build_submission_delivery_layout_block(
            source_package_root=source_package_root,
            human_package_root=human_package_root,
            source_signature=source_signature,
            package_role=package_role,
        ),
    }


def build_source_signature_document(
    *,
    source_signature: str,
    source_contract: dict[str, Any] | None = None,
    package_role: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_role": package_role,
        "source_signature": source_signature,
        "source_contract": source_contract or {},
    }


def build_source_relative_paths_document(
    *,
    source_relative_paths: Iterable[str],
    source_files: Iterable[dict[str, Any]] = (),
    package_role: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_role": package_role,
        "source_relative_paths": sorted({str(path) for path in source_relative_paths if str(path).strip()}),
        "source_files": list(source_files),
    }


def build_analysis_manifest_document(
    *,
    analysis_manifest_source: str | None = None,
    analysis_manifest_present: bool = False,
    package_role: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_role": package_role,
        "analysis_manifest_present": analysis_manifest_present,
        "analysis_manifest_source": analysis_manifest_source,
    }

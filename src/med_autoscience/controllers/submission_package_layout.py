from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping


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
SOFTWARE_ENVIRONMENT_BASENAME = "software_environment.json"
ARTIFACT_LINEAGE_GRAPH_BASENAME = "artifact_lineage_graph.json"

ARTIFACT_LINEAGE_CHAIN = (
    "canonical_source",
    "analysis_result",
    "evidence_ledger",
    "claim_map",
    "manuscript_table_figure",
    "submission_package",
)

ARTIFACT_LINEAGE_NODE_AUTHORITIES = {
    "canonical_source": "canonical_source_authority",
    "analysis_result": "analysis_output_projection",
    "evidence_ledger": "paper_evidence_authority",
    "claim_map": "claim_evidence_projection",
    "manuscript_table_figure": "generated_delivery_projection",
    "submission_package": "controller_authorized_delivery_projection",
}

DERIVED_PROJECTION_BOUNDARIES = {
    "edit_source": False,
    "quality_authority": False,
    "dispatch_authority": False,
}

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
    "software_environment": Path(REPRODUCIBILITY_DIRNAME) / SOFTWARE_ENVIRONMENT_BASENAME,
    "artifact_lineage_graph": Path(REPRODUCIBILITY_DIRNAME) / ARTIFACT_LINEAGE_GRAPH_BASENAME,
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


def _reproducibility_ref(key: str) -> str:
    return V2_REPRODUCIBILITY_RELATIVE_PATHS[key].as_posix()


def build_package_layout_block(
    *,
    package_root: Path,
    workspace_root: Path | None = None,
    package_role: str | None = None,
    source_package_root: Path | None = None,
    human_package_root: Path | None = None,
    source_signature: str | None = None,
    legacy_input_status: str | None = None,
    extra_audit_paths: Mapping[str, Path] | None = None,
    extra_reproducibility_paths: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    root = Path(package_root)
    audit_relative_paths = {
        **V2_AUDIT_RELATIVE_PATHS,
        **{str(key): Path(value) for key, value in (extra_audit_paths or {}).items()},
    }
    reproducibility_relative_paths = {
        **V2_REPRODUCIBILITY_RELATIVE_PATHS,
        **{str(key): Path(value) for key, value in (extra_reproducibility_paths or {}).items()},
    }
    block: dict[str, Any] = {
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_root": _path_label(root, workspace_root=workspace_root),
        "audit_root": _path_label(audit_root(root), workspace_root=workspace_root),
        "reproducibility_root": _path_label(reproducibility_root(root), workspace_root=workspace_root),
        "audit_paths": {
            key: _path_label(root / relative_path, workspace_root=workspace_root)
            for key, relative_path in audit_relative_paths.items()
        },
        "reproducibility_paths": {
            key: _path_label(root / relative_path, workspace_root=workspace_root)
            for key, relative_path in reproducibility_relative_paths.items()
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
        "source_signature_sha256": source_signature,
        "source_contract": source_contract or {},
        "artifact_lineage_graph_ref": _reproducibility_ref("artifact_lineage_graph"),
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
    analysis_results: Iterable[Mapping[str, Any]] = (),
    software_environment_ref: str | None = None,
    artifact_lineage_graph_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_role": package_role,
        "analysis_manifest_present": analysis_manifest_present,
        "analysis_manifest_source": analysis_manifest_source,
        "analysis_results": [dict(item) for item in analysis_results],
        "software_environment_ref": software_environment_ref or _reproducibility_ref("software_environment"),
        "artifact_lineage_graph_ref": artifact_lineage_graph_ref
        or _reproducibility_ref("artifact_lineage_graph"),
    }


def build_analysis_results_from_source_contract(
    source_contract: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    source_files = (source_contract or {}).get("source_files") if source_contract is not None else None
    if not isinstance(source_files, list):
        return []
    results: list[dict[str, Any]] = []
    for item in source_files:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if not path.endswith("build/compile_report.json"):
            continue
        sha256 = str(item.get("sha256") or "").strip()
        if not sha256:
            continue
        results.append(
            {
                "result_id": "analysis_outputs",
                "source_ref": path,
                "sha256": sha256,
            }
        )
    return results


def build_software_environment_document(
    *,
    package_role: str,
    environment_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_role": package_role,
        "environment_ref_status": "repo_runtime",
        "environment_refs": dict(
            environment_refs
            or {
                "runtime": "Codex-default host-agent runtime",
                "verification_entry": "scripts/run-pytest-clean.sh",
                "project": "med-autoscience",
            }
        ),
        "artifact_lineage_graph_ref": _reproducibility_ref("artifact_lineage_graph"),
    }


def build_artifact_lineage_graph_document(
    *,
    package_role: str,
    source_signature: str,
    source_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_paths = (source_contract or {}).get("source_paths") if source_contract is not None else None
    source_files = (source_contract or {}).get("source_files") if source_contract is not None else None
    return {
        "schema_version": 1,
        "layout_version": SUBMISSION_PACKAGE_LAYOUT_VERSION,
        "package_role": package_role,
        "lineage_chain": list(ARTIFACT_LINEAGE_CHAIN),
        "source_signature": source_signature,
        "source_signature_sha256": source_signature,
        "source_refs": list(source_paths) if isinstance(source_paths, list) else [],
        "source_files": list(source_files) if isinstance(source_files, list) else [],
        "nodes": [
            {
                "node_id": node_id,
                "authority": ARTIFACT_LINEAGE_NODE_AUTHORITIES[node_id],
            }
            for node_id in ARTIFACT_LINEAGE_CHAIN
        ],
        "edges": [
            {"from": source, "to": target}
            for source, target in zip(ARTIFACT_LINEAGE_CHAIN, ARTIFACT_LINEAGE_CHAIN[1:])
        ],
        "refs": {
            "source_signature": _reproducibility_ref("source_signature"),
            "analysis_manifest": _reproducibility_ref("analysis_manifest"),
            "software_environment": _reproducibility_ref("software_environment"),
            "submission_manifest": f"{AUDIT_DIRNAME}/{SUBMISSION_MANIFEST_BASENAME}",
            "evidence_ledger": f"{AUDIT_DIRNAME}/{EVIDENCE_LEDGER_BASENAME}",
        },
        "derived_projection_boundaries": dict(DERIVED_PROJECTION_BOUNDARIES),
    }

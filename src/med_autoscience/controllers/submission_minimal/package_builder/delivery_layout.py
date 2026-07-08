from pathlib import Path
from typing import Any

from med_autoscience.controllers.submission_package_layout import (
    build_analysis_results_from_source_contract,
    build_analysis_manifest_document,
    build_artifact_lineage_graph_document,
    build_package_layout_block,
    build_software_environment_document,
    build_source_relative_paths_document,
    build_source_signature_document,
    reproducibility_path,
)

from ..shared_base import dump_json


def apply_controller_authorized_delivery_layout(
    *,
    manifest: dict[str, Any],
    target_submission_root: Path,
    workspace_root: Path,
    source_contract: dict[str, Any],
) -> None:
    manifest["source_signature"] = source_contract["source_signature"]
    manifest["source_contract"] = source_contract
    manifest["delivery_layout"] = build_package_layout_block(
        package_root=target_submission_root,
        workspace_root=workspace_root,
        package_role="controller_authorized_package_source",
        source_package_root=target_submission_root,
        source_signature=source_contract["source_signature"],
        legacy_input_status="v2_generated",
    )


def write_submission_reproducibility_documents(
    *,
    target_submission_root: Path,
    source_contract: dict[str, Any],
) -> None:
    dump_json(
        reproducibility_path(target_submission_root, "source_signature"),
        build_source_signature_document(
            source_signature=source_contract["source_signature"],
            source_contract=source_contract,
            package_role="controller_authorized_package_source",
        ),
    )
    dump_json(
        reproducibility_path(target_submission_root, "source_relative_paths"),
        build_source_relative_paths_document(
            source_relative_paths=source_contract.get("source_paths") or [],
            source_files=source_contract.get("source_files") or [],
            package_role="controller_authorized_package_source",
        ),
    )


def write_submission_lineage_reproducibility_bundle(
    *,
    target_submission_root: Path,
    source_contract: dict[str, Any],
) -> None:
    analysis_results = build_analysis_results_from_source_contract(source_contract)
    dump_json(
        reproducibility_path(target_submission_root, "software_environment"),
        build_software_environment_document(
            package_role="controller_authorized_package_source",
        ),
    )
    dump_json(
        reproducibility_path(target_submission_root, "analysis_manifest"),
        build_analysis_manifest_document(
            analysis_manifest_source=None,
            analysis_manifest_present=bool(analysis_results),
            package_role="controller_authorized_package_source",
            analysis_results=analysis_results,
        ),
    )
    dump_json(
        reproducibility_path(target_submission_root, "artifact_lineage_graph"),
        build_artifact_lineage_graph_document(
            package_role="controller_authorized_package_source",
            source_signature=source_contract["source_signature"],
            source_contract=source_contract,
        ),
    )

from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import paper_artifacts


def resolve_latest_paper_root(quest_root: Path) -> Path:
    return paper_artifacts.resolve_latest_paper_root(quest_root)


def resolve_paper_bundle_manifest(quest_root: Path) -> Path | None:
    return paper_artifacts.resolve_paper_bundle_manifest(quest_root)


def resolve_submission_minimal_manifest(paper_bundle_manifest_path: Path | None) -> Path | None:
    return paper_artifacts.resolve_submission_minimal_manifest(paper_bundle_manifest_path)


def resolve_artifact_manifest(main_result: dict[str, Any]) -> Path | None:
    return paper_artifacts.resolve_artifact_manifest(main_result)


def resolve_submission_minimal_output_paths(
    *,
    paper_bundle_manifest_path: Path | None,
    submission_minimal_manifest: dict[str, Any] | None,
) -> tuple[Path | None, Path | None]:
    return paper_artifacts.resolve_submission_minimal_output_paths(
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        submission_minimal_manifest=submission_minimal_manifest,
    )

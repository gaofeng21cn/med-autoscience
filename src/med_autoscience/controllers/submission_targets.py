from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.adapters.deepscientist import paper_bundle
from med_autoscience.controllers import submission_minimal
from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.submission_targets import (
    SubmissionTarget,
    SubmissionTargetContract,
    resolve_submission_target_contract,
)


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _serialize_target(target: SubmissionTarget) -> dict[str, Any]:
    return dict(asdict(target))


def _resolve_profile(profile_path: Path | None) -> tuple[Path | None, WorkspaceProfile | None]:
    if profile_path is None:
        return None, None
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    return resolved_profile_path, load_profile(resolved_profile_path)


def _resolve_quest_root(quest_root: Path | None) -> Path | None:
    if quest_root is None:
        return None
    return Path(quest_root).expanduser().resolve()


def _resolve_study_root(
    *,
    study_root: Path | None,
    quest_root: Path | None,
    profile: WorkspaceProfile | None,
) -> Path | None:
    if study_root is not None:
        return Path(study_root).expanduser().resolve()
    if quest_root is None or profile is None:
        return None

    quest_payload = _load_yaml_dict(quest_root / "quest.yaml")
    quest_id = str(quest_payload.get("quest_id") or quest_root.name).strip()
    candidate = (profile.studies_root / quest_id).resolve()
    if not (candidate / "study.yaml").exists():
        raise FileNotFoundError(f"could not resolve study_root from profile and quest: {candidate}")
    return candidate


def _resolve_contract(
    *,
    profile_path: Path | None = None,
    study_root: Path | None = None,
    quest_root: Path | None = None,
) -> tuple[Path | None, WorkspaceProfile | None, Path | None, Path | None, SubmissionTargetContract]:
    resolved_profile_path, profile = _resolve_profile(profile_path)
    resolved_quest_root = _resolve_quest_root(quest_root)
    resolved_study_root = _resolve_study_root(
        study_root=study_root,
        quest_root=resolved_quest_root,
        profile=profile,
    )
    contract = resolve_submission_target_contract(
        profile=profile,
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
    )
    return resolved_profile_path, profile, resolved_study_root, resolved_quest_root, contract


def resolve_submission_targets(
    *,
    profile_path: Path | None = None,
    study_root: Path | None = None,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    resolved_profile_path, _, resolved_study_root, resolved_quest_root, contract = _resolve_contract(
        profile_path=profile_path,
        study_root=study_root,
        quest_root=quest_root,
    )
    return {
        "schema_version": 1,
        "status": "resolved",
        "profile_path": str(resolved_profile_path) if resolved_profile_path is not None else None,
        "study_root": str(resolved_study_root) if resolved_study_root is not None else None,
        "quest_root": str(resolved_quest_root) if resolved_quest_root is not None else None,
        "targets": [_serialize_target(target) for target in contract.targets],
        "primary_target": _serialize_target(contract.primary_target),
        "unresolved_target_count": len(contract.unresolved_targets),
        "unresolved_targets": [_serialize_target(target) for target in contract.unresolved_targets],
        "export_publication_profiles": list(contract.export_publication_profiles),
    }


def _resolve_paper_root(*, paper_root: Path | None, quest_root: Path | None) -> Path:
    if paper_root is not None:
        return Path(paper_root).expanduser().resolve()
    if quest_root is None:
        raise ValueError("export_submission_targets requires --paper-root or --quest-root")
    return paper_bundle.resolve_latest_paper_root(quest_root)


def export_submission_targets(
    *,
    paper_root: Path | None = None,
    profile_path: Path | None = None,
    study_root: Path | None = None,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    resolved_profile_path, _, resolved_study_root, resolved_quest_root, contract = _resolve_contract(
        profile_path=profile_path,
        study_root=study_root,
        quest_root=quest_root,
    )
    resolved_paper_root = _resolve_paper_root(paper_root=paper_root, quest_root=resolved_quest_root)

    exported_profiles: dict[str, dict[str, Any]] = {}
    blocked_target_count = 0
    target_results: list[dict[str, Any]] = []
    for target in contract.targets:
        item = _serialize_target(target)
        if not target.package_required:
            item["export_status"] = "skipped_package_not_required"
            target_results.append(item)
            continue
        if target.resolution_status != "resolved_profile" or not target.publication_profile:
            blocked_target_count += 1
            item["export_status"] = "blocked_needs_journal_resolution"
            target_results.append(item)
            continue
        if target.publication_profile not in exported_profiles:
            exported_profiles[target.publication_profile] = submission_minimal.create_submission_minimal_package(
                paper_root=resolved_paper_root,
                publication_profile=target.publication_profile,
                citation_style=target.citation_style or "auto",
            )
            item["export_status"] = "exported"
        else:
            item["export_status"] = "already_exported_in_batch"
        item["export_result"] = exported_profiles[target.publication_profile]
        target_results.append(item)

    return {
        "schema_version": 1,
        "status": "blocked" if blocked_target_count else "exported",
        "profile_path": str(resolved_profile_path) if resolved_profile_path is not None else None,
        "study_root": str(resolved_study_root) if resolved_study_root is not None else None,
        "quest_root": str(resolved_quest_root) if resolved_quest_root is not None else None,
        "paper_root": str(resolved_paper_root),
        "primary_target": _serialize_target(contract.primary_target),
        "blocked_target_count": blocked_target_count,
        "exported_publication_profiles": list(exported_profiles),
        "targets": target_results,
    }

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.controllers.study_workspace_status_parts import (
    AUTHORITY_BOUNDARY,
    CURRENT_PAPER_INPUTS,
    MIGRATION_HISTORY_ROOT_RELPATH,
    MIGRATION_MANIFEST_ROOT_RELPATH,
    PAPER_CLEAN_ROOM_DESCRIPTOR_RELPATH,
    PRODUCT_VIEW_DIRS,
    STAGE_INDEX_SCHEMA,
    STAGE_OUTPUTS_RELPATH,
    STAGE_REQUIRED_DIRS,
    SURFACE_KIND,
    TARGET_STATE_REFERENCE_DOC,
    USER_ENTRY_REFS,
    workspace_taxonomy,
)


def run_study_workspace_status(
    *,
    profile_path: Path,
    study_ids: Iterable[str] | None = None,
    apply: bool,
) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    selected_study_ids = _resolve_study_ids(profile=profile, study_ids=study_ids)
    recorded_at = _utc_now()
    studies = [
        _study_status(
            profile=profile,
            study_id=study_id,
            study_root_override=None,
            recorded_at=recorded_at,
        )
        for study_id in selected_study_ids
    ]
    if apply:
        for study in studies:
            if not study["blockers"]:
                _materialize_study_workspace_status(study=study, recorded_at=recorded_at)
        studies = [
            _study_status(
                profile=profile,
                study_id=study_id,
                study_root_override=None,
                recorded_at=recorded_at,
            )
            for study_id in selected_study_ids
        ]
        for study in studies:
            if not study["blockers"]:
                _materialize_study_workspace_status(study=study, recorded_at=recorded_at)
        studies = [
            _study_status(
                profile=profile,
                study_id=study_id,
                study_root_override=None,
                recorded_at=recorded_at,
            )
            for study_id in selected_study_ids
        ]
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "workspace_taxonomy": workspace_taxonomy(profile),
        "study_count": len(studies),
        "studies": studies,
        "next_required_actions": _workspace_next_actions(studies),
    }


def build_study_workspace_status(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    recorded_at: str | None = None,
    apply: bool = False,
    study_root: Path | None = None,
) -> dict[str, Any]:
    timestamp = _text(recorded_at) or _utc_now()
    study = _study_status(
        profile=profile,
        study_id=study_id,
        study_root_override=study_root,
        recorded_at=timestamp,
    )
    if apply and not study["blockers"]:
        _materialize_study_workspace_status(study=study, recorded_at=timestamp)
        study = _study_status(
            profile=profile,
            study_id=study_id,
            study_root_override=study_root,
            recorded_at=timestamp,
        )
        if not study["blockers"]:
            _materialize_study_workspace_status(study=study, recorded_at=timestamp)
            study = _study_status(
                profile=profile,
                study_id=study_id,
                study_root_override=study_root,
                recorded_at=timestamp,
            )
    return study


def _study_status(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root_override: Path | None,
    recorded_at: str,
) -> dict[str, Any]:
    expected_study_root = (profile.studies_root / study_id).expanduser().resolve()
    study_root = (study_root_override or expected_study_root).expanduser().resolve()
    runtime_quest_root = (profile.runtime_root / study_id).expanduser().resolve()
    study_yaml_path = study_root / "study.yaml"
    study_config = _read_yaml_mapping(study_yaml_path)
    current_inputs = _current_paper_inputs(profile=profile, study_root=study_root)
    product_views = _product_views(study_root)
    missing_required_inputs = [
        surface["surface_id"]
        for surface in current_inputs
        if surface["required"] is True and surface["present"] is not True
    ]
    entry_surfaces = _entry_surfaces(study_root)
    missing_entry_surfaces = [
        surface["surface_id"]
        for surface in entry_surfaces
        if surface["required"] is True and surface["materialized_by_controller"] is True and surface["present"] is not True
    ]
    stage_payload = _stage_index_payload(study_id=study_id, study_root=study_root)
    stage_index = stage_payload["stage_index"]
    stage_validation = stage_payload["validation"]
    blockers = _blockers(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        expected_study_root=expected_study_root,
        runtime_quest_root=runtime_quest_root,
        study_yaml_path=study_yaml_path,
        current_inputs=current_inputs,
        missing_required_inputs=missing_required_inputs,
        stage_validation=stage_validation,
    )
    status = _status(
        blockers=blockers,
        missing_entry_surfaces=missing_entry_surfaces,
        materialization_gaps=stage_validation["materialization_gaps"],
    )
    package_status = _current_package_status(
        study_root=study_root,
        current_inputs=current_inputs,
        recorded_at=recorded_at,
    )
    paper_clean_room_status = _paper_clean_room_rebuild_status(study_root=study_root)
    validation = {
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "canonical_study_root": str(study_root) == str(expected_study_root),
        "canonical_study_root_role": "single_user_and_machine_entry",
        "study_yaml_present": study_yaml_path.exists(),
        "runtime_quest_root_role": "runtime_execution_state_and_provenance",
        "runtime_quest_root_is_user_entry": False,
        "runtime_quest_root_is_current_paper_truth": False,
        "archive_roots_are_current_truth": False,
        "legacy_runtime_residue_is_current_truth": False,
        "product_views_current_surface": product_views,
        "missing_required_inputs": missing_required_inputs,
        "missing_entry_surfaces": missing_entry_surfaces,
        "stage_native": stage_validation,
        "blockers": blockers,
    }
    next_action = _next_action(
        blockers=blockers,
        missing_required_inputs=missing_required_inputs,
        package_status=package_status,
        stage_index=stage_index,
        paper_clean_room_status=paper_clean_room_status,
    )
    current_truth_map = {
        "schema_version": 1,
        "surface_kind": "study_workspace_current_truth_map",
        "study_id": study_id,
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "study_config": _source_ref(profile=profile, study_root=study_root, path=study_yaml_path),
        "paper_inputs": current_inputs,
        "product_views": product_views,
        "stage_index_ref": USER_ENTRY_REFS["stage_index"].as_posix(),
        "current_stage": stage_index.get("current_stage"),
        "package_status": package_status,
        "paper_clean_room_rebuild": paper_clean_room_status,
    }
    legacy_provenance_map = _legacy_provenance_map(
        profile=profile,
        study_root=study_root,
        runtime_quest_root=runtime_quest_root,
    )
    target_path_map = _target_path_map(study_root=study_root, stage_index=stage_index, current_inputs=current_inputs)
    materialization_plan = _materialization_plan(
        entry_surfaces=entry_surfaces,
        missing_entry_surfaces=missing_entry_surfaces,
        stage_validation=stage_validation,
        blockers=blockers,
    )
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "status": status,
        "recorded_at": recorded_at,
        "study_id": study_id,
        "study_root": str(study_root),
        "canonical_study_root": str(expected_study_root),
        "runtime_quest_root": str(runtime_quest_root),
        "study_title": _text(study_config.get("title")) if study_config else None,
        "study_archetype": _text(study_config.get("study_archetype")) if study_config else None,
        "manuscript_family": _text(study_config.get("manuscript_family")) if study_config else None,
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "workspace_taxonomy": workspace_taxonomy(profile),
        "stage_index": stage_index,
        "validation": validation,
        "blockers": blockers,
        "current_truth_map": current_truth_map,
        "legacy_provenance_map": legacy_provenance_map,
        "target_path_map": target_path_map,
        "materialization_plan": materialization_plan,
        "entry_surfaces": entry_surfaces,
        "next_action": next_action,
        "descriptor_path": str(study_root / MIGRATION_MANIFEST_ROOT_RELPATH / "validation_result.json"),
        "manifest_root": str(study_root / MIGRATION_MANIFEST_ROOT_RELPATH),
        "history_path": str(study_root / MIGRATION_HISTORY_ROOT_RELPATH / f"{_history_stamp(recorded_at)}.json"),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _current_paper_inputs(*, profile: WorkspaceProfile, study_root: Path) -> list[dict[str, Any]]:
    return [
        _selected_surface_ref(
            profile=profile,
            study_root=study_root,
            surface_id=surface_id,
            canonical_relpath=canonical_relpath,
            candidate_relpaths=candidate_relpaths,
            required=required,
        )
        for surface_id, canonical_relpath, candidate_relpaths, required in CURRENT_PAPER_INPUTS
    ]


def _selected_surface_ref(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    surface_id: str,
    canonical_relpath: Path,
    candidate_relpaths: tuple[Path, ...],
    required: bool,
) -> dict[str, Any]:
    candidates = [
        _source_ref(profile=profile, study_root=study_root, path=study_root / candidate_relpath)
        for candidate_relpath in candidate_relpaths
    ]
    selected = next((candidate for candidate in candidates if candidate["present"] is True), None)
    source = selected or candidates[0]
    return {
        "surface_id": surface_id,
        "required": required,
        "present": selected is not None,
        "valid": selected is not None and not _is_non_current_truth_source(profile=profile, path=Path(source["path"])),
        "canonical_relative_path": canonical_relpath.as_posix(),
        "selected_source_path": source["path"],
        "selected_source_relative_path": source["relative_path"],
        "candidate_sources": candidates,
        "sha256": source.get("sha256") if selected else None,
    }


def _product_views(study_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "surface_id": relpath.as_posix().replace("/", "_") or "study_root",
            "relative_path": relpath.as_posix(),
            "path": str(study_root / relpath),
            "present": (study_root / relpath).exists(),
            "role": "current_product_view",
            "current_truth": True,
        }
        for relpath in PRODUCT_VIEW_DIRS
    ]


def _stage_index_payload(*, study_id: str, study_root: Path) -> dict[str, Any]:
    stage_outputs_root = study_root / STAGE_OUTPUTS_RELPATH
    stage_roots = _discover_stage_roots(stage_outputs_root)
    stage_refs = [_stage_ref(study_root=study_root, stage_root=stage_root) for stage_root in stage_roots]
    current_stage = _select_current_stage(stage_refs)
    current_stage_id = current_stage["stage_id"] if current_stage else None
    stage_index = {
        "schema_version": STAGE_INDEX_SCHEMA,
        "study_id": study_id,
        "canonical_study_root": f"studies/{study_id}",
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "current_stage_id": current_stage_id,
        "current_stage": current_stage,
        "stage_outputs_root": STAGE_OUTPUTS_RELPATH.as_posix(),
        "stages": stage_refs,
    }
    validation = _stage_validation(stage_outputs_root=stage_outputs_root, stages=stage_refs, current_stage=current_stage)
    return {
        "stage_index": stage_index,
        "validation": validation,
    }


def _discover_stage_roots(stage_outputs_root: Path) -> list[Path]:
    if not stage_outputs_root.is_dir():
        return []
    return [
        path
        for path in sorted(stage_outputs_root.iterdir())
        if path.is_dir() and not path.name.startswith("_") and not path.name.startswith(".")
    ]


def _stage_ref(*, study_root: Path, stage_root: Path) -> dict[str, Any]:
    rel_root = _relative_path(path=stage_root, root=study_root)
    manifest = stage_root / "stage_manifest.json"
    owner_receipt = stage_root / "receipts" / "owner_receipt.json"
    typed_blocker = stage_root / "receipts" / "typed_blocker.json"
    current_owner_delta = stage_root / "projection" / "current_owner_delta.json"
    missing_required_dirs = [
        relpath.as_posix()
        for relpath in STAGE_REQUIRED_DIRS
        if not (stage_root / relpath).is_dir()
    ]
    status = "typed_blocked" if typed_blocker.exists() else "receipt_recorded" if owner_receipt.exists() else "open_or_incomplete"
    if not manifest.exists():
        status = "missing_manifest"
    return {
        "stage_id": stage_root.name,
        "stage_root": rel_root,
        "manifest": f"{rel_root}/stage_manifest.json",
        "manifest_present": manifest.exists(),
        "status": status,
        "receipt_ref": f"{rel_root}/receipts/owner_receipt.json" if owner_receipt.exists() else None,
        "typed_blocker_ref": f"{rel_root}/receipts/typed_blocker.json" if typed_blocker.exists() else None,
        "current_owner_delta_ref": f"{rel_root}/projection/current_owner_delta.json" if current_owner_delta.exists() else None,
        "lineage_ref": f"{rel_root}/lineage/prov.json" if (stage_root / "lineage" / "prov.json").exists() else None,
        "missing_required_dirs": missing_required_dirs,
        "product_refs": _stage_product_refs(stage_id=stage_root.name),
    }


def _stage_product_refs(*, stage_id: str) -> list[str]:
    refs = ["paper/draft.md", "paper/claim_evidence_map.json", "evidence/evidence_ledger.json"]
    if "publication" in stage_id or "handoff" in stage_id or "package" in stage_id:
        refs.append("publication/current_package/STATUS.json")
    return refs


def _select_current_stage(stages: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    if not stages:
        return None
    with_owner_delta = [stage for stage in stages if stage.get("current_owner_delta_ref")]
    if with_owner_delta:
        return with_owner_delta[-1]
    with_answer = [stage for stage in stages if stage.get("receipt_ref") or stage.get("typed_blocker_ref")]
    if with_answer:
        return with_answer[-1]
    return stages[-1]


def _stage_validation(
    *,
    stage_outputs_root: Path,
    stages: list[Mapping[str, Any]],
    current_stage: Mapping[str, Any] | None,
) -> dict[str, Any]:
    blockers: list[str] = []
    materialization_gaps: list[str] = []
    if not stage_outputs_root.is_dir():
        blockers.append("stage_outputs_root_missing")
    if not stages:
        blockers.append("stage_native_stage_folder_missing")
    if current_stage is None:
        blockers.append("current_stage_missing")
    else:
        if current_stage.get("manifest_present") is not True:
            blockers.append(f"current_stage_manifest_missing:{current_stage.get('stage_id')}")
        if not current_stage.get("receipt_ref") and not current_stage.get("typed_blocker_ref"):
            blockers.append(f"current_stage_owner_receipt_or_typed_blocker_missing:{current_stage.get('stage_id')}")
        if not current_stage.get("current_owner_delta_ref"):
            materialization_gaps.append(f"current_stage_owner_delta_projection_missing:{current_stage.get('stage_id')}")
    for stage in stages:
        for relpath in stage.get("missing_required_dirs") or []:
            materialization_gaps.append(f"stage_required_dir_missing:{stage.get('stage_id')}:{relpath}")
    return {
        "stage_outputs_root_present": stage_outputs_root.is_dir(),
        "stage_count": len(stages),
        "current_stage_id": current_stage.get("stage_id") if current_stage else None,
        "blockers": blockers,
        "materialization_gaps": materialization_gaps,
        "fail_closed": bool(blockers),
    }


def _entry_surfaces(study_root: Path) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for surface_id, relpath in USER_ENTRY_REFS.items():
        surfaces.append(
            {
                "surface_id": surface_id,
                "required": True,
                "materialized_by_controller": surface_id != "study_config",
                "path": str(study_root / relpath),
                "relative_path": relpath.as_posix(),
                "present": (study_root / relpath).exists(),
            }
        )
    return surfaces


def _current_package_status(
    *,
    study_root: Path,
    current_inputs: list[Mapping[str, Any]],
    recorded_at: str,
) -> dict[str, Any]:
    status_path = study_root / USER_ENTRY_REFS["current_package_status"]
    candidate_roots = [
        study_root / "publication" / "current_package",
        study_root / "artifacts" / "submission_minimal" / "current",
        study_root / "manuscript" / "current_package",
        study_root / "artifacts" / "delivery" / "paper",
    ]
    candidates = [
        {
            "path": str(path),
            "relative_path": _relative_path(path=path, root=study_root),
            "present": path.exists(),
            "role": "package_candidate_or_projection",
        }
        for path in candidate_roots
    ]
    manuscript_ready = all(
        item.get("present") is True
        for item in current_inputs
        if item.get("surface_id") in {"current_manuscript", "evidence_ledger", "review_ledger"}
    )
    return {
        "schema_version": 1,
        "surface_kind": "study_current_package_status",
        "status": "not_ready",
        "reason": "current_package_not_promoted_by_publication_gate",
        "recorded_at": recorded_at,
        "status_path": str(status_path),
        "current_package_root": str(study_root / "publication" / "current_package"),
        "candidate_package_refs": candidates,
        "current_paper_inputs_ready": manuscript_ready,
        "promotion_allowed": False,
        "submission_package_regenerated": False,
    }


def _paper_clean_room_rebuild_status(*, study_root: Path) -> dict[str, Any]:
    descriptor_path = study_root / PAPER_CLEAN_ROOM_DESCRIPTOR_RELPATH
    payload = _read_json_mapping(descriptor_path)
    status = _text(payload.get("status")) if payload else None
    return {
        "schema_version": 1,
        "surface_kind": "paper_clean_room_rebuild_status_ref",
        "descriptor_ref": PAPER_CLEAN_ROOM_DESCRIPTOR_RELPATH.as_posix(),
        "descriptor_path": str(descriptor_path),
        "present": descriptor_path.exists(),
        "status": status,
        "ready": status == "ready",
        "clean_workspace_root": payload.get("clean_workspace_root") if payload else None,
        "verified_input_root": payload.get("verified_input_root") if payload else None,
        "workspace_blockers": payload.get("workspace_blockers") if payload else None,
        "missing_required_refs": payload.get("missing_required_refs") if payload else None,
    }


def _legacy_provenance_map(*, profile: WorkspaceProfile, study_root: Path, runtime_quest_root: Path) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    roots = [
        (runtime_quest_root, "runtime_execution_state_and_provenance"),
        (study_root / ".ds", "legacy_study_residue_provenance"),
        (study_root / "_archive", "study_archive_non_current_provenance"),
        (workspace_root / "archive", "workspace_archive_provenance"),
        (workspace_root / "runtime" / "archives", "legacy_runtime_archive_provenance"),
        (profile.med_deepscientist_runtime_root.expanduser().resolve(), "historical_fixture_or_archive_import"),
    ]
    return {
        "schema_version": 1,
        "surface_kind": "study_workspace_legacy_provenance_map",
        "roots": [
            {
                "path": str(path),
                "relative_path": _relative_path(path=path, root=workspace_root),
                "role": role,
                "present": path.exists(),
                "current_truth": False,
                "user_entry": False,
                "decision": "retain_as_provenance_only",
            }
            for path, role in roots
        ],
    }


def _target_path_map(
    *,
    study_root: Path,
    stage_index: Mapping[str, Any],
    current_inputs: list[Mapping[str, Any]],
) -> dict[str, Any]:
    product_view_targets = [
        {
            "surface_id": relpath.as_posix().replace("/", "_"),
            "target_path": str(study_root / relpath),
            "target_relative_path": relpath.as_posix(),
            "decision": "ensure_current_product_view_directory",
        }
        for relpath in PRODUCT_VIEW_DIRS
    ]
    stage_dir_targets: list[dict[str, Any]] = []
    for stage in stage_index.get("stages") or []:
        stage_root = Path(str(stage["stage_root"]))
        for relpath in STAGE_REQUIRED_DIRS:
            stage_dir_targets.append(
                {
                    "surface_id": f"stage_required_dir:{stage['stage_id']}:{relpath.as_posix()}",
                    "target_path": str(study_root / stage_root / relpath),
                    "target_relative_path": (stage_root / relpath).as_posix(),
                    "decision": "ensure_stage_native_directory_without_fabricating_receipts",
                }
            )
    current_artifact_targets = [
        {
            "surface_id": str(item["surface_id"]),
            "target_path": str(study_root / str(item["canonical_relative_path"])),
            "target_relative_path": str(item["canonical_relative_path"]),
            "selected_source_relative_path": item.get("selected_source_relative_path"),
            "present": item.get("present"),
            "decision": "use_existing_current_product_view"
            if item.get("present") is True and item.get("selected_source_relative_path") == item.get("canonical_relative_path")
            else "record_current_ref_without_mutating_product_view",
        }
        for item in current_inputs
    ]
    return {
        "schema_version": 1,
        "surface_kind": "study_workspace_target_path_map",
        "targets": [
            {
                "surface_id": surface_id,
                "target_path": str(study_root / relpath),
                "target_relative_path": relpath.as_posix(),
                "decision": "materialize_or_refresh_user_entry_surface",
            }
            for surface_id, relpath in USER_ENTRY_REFS.items()
            if surface_id != "study_config"
        ]
        + current_artifact_targets
        + product_view_targets
        + stage_dir_targets
        + [
            {
                "surface_id": "migration_manifest",
                "target_path": str(study_root / MIGRATION_MANIFEST_ROOT_RELPATH),
                "target_relative_path": MIGRATION_MANIFEST_ROOT_RELPATH.as_posix(),
                "decision": "record_current_truth_legacy_target_plan_and_validation",
            }
        ],
    }


def _materialization_plan(
    *,
    entry_surfaces: list[Mapping[str, Any]],
    missing_entry_surfaces: list[str],
    stage_validation: Mapping[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    stage_dir_writes = [
        gap.removeprefix("stage_required_dir_missing:")
        for gap in stage_validation.get("materialization_gaps", [])
        if str(gap).startswith("stage_required_dir_missing:")
    ]
    return {
        "schema_version": 1,
        "surface_kind": "study_workspace_materialization_plan",
        "status": "blocked" if blockers else "ready_to_materialize" if missing_entry_surfaces or stage_dir_writes else "already_materialized",
        "missing_entry_surfaces": missing_entry_surfaces,
        "stage_materialization_gaps": list(stage_validation.get("materialization_gaps", [])),
        "blockers": blockers,
        "write_policy": {
            "write_user_entry_surfaces": not blockers,
            "write_stage_native_directories": not blockers,
            "write_paper_body": False,
            "write_runtime_truth": False,
            "write_publication_eval": False,
            "write_controller_decisions": False,
            "promote_current_package": False,
            "fabricate_stage_receipt_or_blocker": False,
        },
        "planned_writes": [
            surface["relative_path"]
            for surface in entry_surfaces
            if surface.get("surface_id") in missing_entry_surfaces or not surface.get("present")
        ]
        + [f"artifacts/stage_outputs/{item}" for item in stage_dir_writes],
    }


def _blockers(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    expected_study_root: Path,
    runtime_quest_root: Path,
    study_yaml_path: Path,
    current_inputs: list[Mapping[str, Any]],
    missing_required_inputs: list[str],
    stage_validation: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if not study_root.exists():
        blockers.append("canonical_study_root_missing")
    if study_root != expected_study_root:
        blockers.append("study_root_not_under_profile_studies_root")
    if _same_or_under(study_root, runtime_quest_root):
        blockers.append("runtime_quest_root_cannot_be_canonical_study_root")
    if _is_non_current_truth_source(profile=profile, path=study_root):
        blockers.append("archive_or_legacy_root_cannot_be_canonical_study_root")
    if not study_yaml_path.exists():
        blockers.append("study_yaml_missing")
    for surface_id in missing_required_inputs:
        blockers.append(f"{surface_id}_missing")
    for item in current_inputs:
        if item.get("present") is True and item.get("valid") is not True:
            blockers.append(f"current_truth_source_is_provenance:{item.get('surface_id')}")
    blockers.extend(str(item) for item in stage_validation.get("blockers", []))
    return _dedupe(blockers)


def _status(*, blockers: list[str], missing_entry_surfaces: list[str], materialization_gaps: list[str]) -> str:
    if blockers:
        return "blocked"
    if missing_entry_surfaces or materialization_gaps:
        return "needs_materialization"
    return "ready"


def _next_action(
    *,
    blockers: list[str],
    missing_required_inputs: list[str],
    package_status: Mapping[str, Any],
    stage_index: Mapping[str, Any],
    paper_clean_room_status: Mapping[str, Any],
) -> dict[str, Any]:
    if blockers:
        return {
            "action_id": "resolve_study_workspace_status_blockers",
            "owner": "MedAutoScience",
            "status": "blocked",
            "blockers": blockers,
            "current_stage_id": stage_index.get("current_stage_id"),
        }
    if missing_required_inputs:
        return {
            "action_id": "resolve_missing_current_paper_inputs",
            "owner": "MedAutoScience",
            "status": "blocked",
            "missing_required_inputs": missing_required_inputs,
            "current_stage_id": stage_index.get("current_stage_id"),
        }
    if paper_clean_room_status.get("present") is True and paper_clean_room_status.get("ready") is not True:
        return {
            "action_id": "resolve_paper_clean_room_rebuild_blockers",
            "owner": "MedAutoScience",
            "status": "blocked",
            "clean_room_status": paper_clean_room_status.get("status"),
            "clean_room_descriptor_ref": PAPER_CLEAN_ROOM_DESCRIPTOR_RELPATH.as_posix(),
            "current_stage_id": stage_index.get("current_stage_id"),
        }
    if paper_clean_room_status.get("ready") is True:
        return {
            "action_id": "run_medical_publication_surface_from_clean_room",
            "owner": "MedAutoScience",
            "status": "ready_for_owner_action",
            "source_surface": PAPER_CLEAN_ROOM_DESCRIPTOR_RELPATH.as_posix(),
            "stage_index_ref": USER_ENTRY_REFS["stage_index"].as_posix(),
            "current_stage_id": stage_index.get("current_stage_id"),
            "current_package_status": package_status.get("status"),
        }
    return {
        "action_id": "paper_clean_room_rebuild_required",
        "owner": "MedAutoScience",
        "status": "ready_for_owner_action",
        "target_surface": "artifacts/supervision/paper_clean_room_rebuild/latest.json",
        "stage_index_ref": USER_ENTRY_REFS["stage_index"].as_posix(),
        "current_stage_id": stage_index.get("current_stage_id"),
        "current_package_status": package_status.get("status"),
    }


def _materialize_study_workspace_status(*, study: Mapping[str, Any], recorded_at: str) -> None:
    study_root = Path(str(study["study_root"]))
    stage_index = dict(study["stage_index"])
    current_stage = dict(stage_index.get("current_stage") or {})
    package_status = dict(study["current_truth_map"]["package_status"])
    next_action = dict(study["next_action"])
    blockers_payload = _blockers_payload(study=study, recorded_at=recorded_at)
    descriptor = {
        **dict(study),
        "status": "ready",
        "entry_surface_materialized_at": recorded_at,
    }
    for relpath in PRODUCT_VIEW_DIRS:
        (study_root / relpath).mkdir(parents=True, exist_ok=True)
    _materialize_stage_required_dirs(study=study)
    _write_text(study_root / USER_ENTRY_REFS["study_status"], _render_status_markdown(study=study))
    _write_text(
        study_root / USER_ENTRY_REFS["paper_metadata"],
        yaml.safe_dump(_paper_yaml_payload(study=study), allow_unicode=True, sort_keys=False),
    )
    _write_json(study_root / USER_ENTRY_REFS["current_stage"], current_stage)
    _write_json(study_root / USER_ENTRY_REFS["next_action"], next_action)
    _write_json(study_root / USER_ENTRY_REFS["stage_index"], stage_index)
    _write_json(study_root / USER_ENTRY_REFS["blockers"], blockers_payload)
    _write_json(study_root / USER_ENTRY_REFS["current_package_status"], package_status)
    _write_json(study_root / MIGRATION_MANIFEST_ROOT_RELPATH / "current_truth_map.json", study["current_truth_map"])
    _write_json(study_root / MIGRATION_MANIFEST_ROOT_RELPATH / "legacy_provenance_map.json", study["legacy_provenance_map"])
    _write_json(study_root / MIGRATION_MANIFEST_ROOT_RELPATH / "target_path_map.json", study["target_path_map"])
    _write_json(study_root / MIGRATION_MANIFEST_ROOT_RELPATH / "materialization_plan.json", study["materialization_plan"])
    _write_json(study_root / MIGRATION_MANIFEST_ROOT_RELPATH / "validation_result.json", descriptor)
    _write_json(study_root / MIGRATION_HISTORY_ROOT_RELPATH / f"{_history_stamp(recorded_at)}.json", descriptor)


def _materialize_stage_required_dirs(*, study: Mapping[str, Any]) -> None:
    study_root = Path(str(study["study_root"]))
    for stage in study["stage_index"].get("stages") or []:
        stage_root = study_root / str(stage["stage_root"])
        for relpath in STAGE_REQUIRED_DIRS:
            (stage_root / relpath).mkdir(parents=True, exist_ok=True)


def _blockers_payload(*, study: Mapping[str, Any], recorded_at: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": "study_workspace_blockers",
        "study_id": study["study_id"],
        "recorded_at": recorded_at,
        "status": "blocked" if study["blockers"] else "clear",
        "blockers": list(study["blockers"]),
        "stage_blockers": list(study["validation"]["stage_native"].get("blockers", [])),
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
    }


def _paper_yaml_payload(*, study: Mapping[str, Any]) -> dict[str, Any]:
    refs = {
        item["surface_id"]: item
        for item in study["current_truth_map"]["paper_inputs"]
        if isinstance(item, Mapping)
    }
    return {
        "schema_version": 1,
        "surface_kind": "paper_metadata",
        "study_id": study["study_id"],
        "title": study.get("study_title"),
        "study_archetype": study.get("study_archetype"),
        "manuscript_family": study.get("manuscript_family"),
        "canonical_study_root": study["study_root"],
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "stage_index_ref": USER_ENTRY_REFS["stage_index"].as_posix(),
        "current_stage_id": study["stage_index"].get("current_stage_id"),
        "current_refs": {
            key: refs[key]["selected_source_relative_path"]
            for key in (
                "current_manuscript",
                "evidence_ledger",
                "review_ledger",
                "claim_evidence_map",
                "medical_manuscript_blueprint",
                "figure_catalog",
                "table_catalog",
            )
            if key in refs and refs[key].get("present") is True
        },
        "package_status_ref": USER_ENTRY_REFS["current_package_status"].as_posix(),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _render_status_markdown(*, study: Mapping[str, Any]) -> str:
    refs = {
        item["surface_id"]: item
        for item in study["current_truth_map"]["paper_inputs"]
        if isinstance(item, Mapping)
    }
    package_status = study["current_truth_map"]["package_status"]
    next_action = study["next_action"]
    lines = [
        f"# {study['study_id']}",
        "",
        f"- Status: `{study['status']}`",
        f"- Canonical study root: `{study['study_root']}`",
        f"- Runtime/provenance root: `{study['runtime_quest_root']}`",
        f"- Target-state reference: `{TARGET_STATE_REFERENCE_DOC}`",
        f"- Current stage: `{study['stage_index'].get('current_stage_id')}`",
        f"- Stage index: `{USER_ENTRY_REFS['stage_index'].as_posix()}`",
        f"- Current manuscript: `{_selected_ref(refs, 'current_manuscript')}`",
        f"- Evidence ledger: `{_selected_ref(refs, 'evidence_ledger')}`",
        f"- Review ledger: `{_selected_ref(refs, 'review_ledger')}`",
        f"- Current package: `{package_status.get('status')}`",
        f"- Next action: `{next_action.get('action_id')}`",
        "",
        "Runtime, legacy `.ds`, MDS archive, and submission mirrors are provenance or projections, not the user-facing paper root.",
        "",
    ]
    return "\n".join(lines)


def _selected_ref(refs: Mapping[str, Mapping[str, Any]], surface_id: str) -> str:
    ref = refs.get(surface_id) or {}
    if ref.get("present") is True:
        return str(ref.get("selected_source_relative_path") or ref.get("selected_source_path") or "")
    return "missing"


def _workspace_next_actions(studies: list[Mapping[str, Any]]) -> list[str]:
    actions: list[str] = []
    for study in studies:
        action = _text((study.get("next_action") or {}).get("action_id") if isinstance(study.get("next_action"), Mapping) else None)
        if action and action not in actions:
            actions.append(action)
    return actions


def _resolve_study_ids(*, profile: WorkspaceProfile, study_ids: Iterable[str] | None) -> tuple[str, ...]:
    selected = tuple(item for raw in (study_ids or ()) if (item := _text(raw)) is not None)
    available_study_ids = _discover_study_ids(profile)
    if selected:
        known = set(available_study_ids)
        for study_id in selected:
            if study_id not in known:
                known_text = ", ".join(sorted(known)) or "<none>"
                raise ValueError(f"Unknown study workspace study_id: {study_id}; known study_ids: {known_text}")
        return selected
    return available_study_ids


def _discover_study_ids(profile: WorkspaceProfile) -> tuple[str, ...]:
    studies_root = profile.studies_root.expanduser().resolve()
    if not studies_root.is_dir():
        return ()
    return tuple(path.name for path in sorted(studies_root.iterdir()) if path.is_dir() and (path / "study.yaml").exists())


def _source_ref(*, profile: WorkspaceProfile, study_root: Path, path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    present = resolved.exists()
    return {
        "path": str(resolved),
        "relative_path": _relative_path(path=resolved, root=study_root),
        "workspace_relative_path": _relative_path(path=resolved, root=profile.workspace_root.expanduser().resolve()),
        "present": present,
        "kind": "directory" if resolved.is_dir() else "file",
        "sha256": _sha256(resolved) if resolved.is_file() else None,
    }


def _relative_path(*, path: Path, root: Path) -> str:
    try:
        return path.expanduser().resolve().relative_to(root.expanduser().resolve()).as_posix()
    except ValueError:
        return str(path.expanduser().resolve())


def _same_or_under(path: Path, root: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(root.expanduser().resolve())
        return True
    except ValueError:
        return False


def _is_non_current_truth_source(*, profile: WorkspaceProfile, path: Path) -> bool:
    resolved = path.expanduser().resolve()
    workspace_root = profile.workspace_root.expanduser().resolve()
    non_current_roots = (
        profile.runtime_root.expanduser().resolve(),
        profile.med_deepscientist_runtime_root.expanduser().resolve(),
        workspace_root / "archive",
        workspace_root / "runtime" / "archives",
    )
    if any(_same_or_under(resolved, root) for root in non_current_roots):
        return True
    parts = set(resolved.parts)
    return ".ds" in parts or "_archive" in parts


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _history_stamp(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("+", "").replace(".", "")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


__all__ = [
    "AUTHORITY_BOUNDARY",
    "SURFACE_KIND",
    "TARGET_STATE_REFERENCE_DOC",
    "build_study_workspace_status",
    "run_study_workspace_status",
]

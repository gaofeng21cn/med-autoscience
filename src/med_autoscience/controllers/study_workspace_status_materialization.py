from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.study_workspace_status_parts import (
    AUTHORITY_BOUNDARY,
    MIGRATION_HISTORY_ROOT_RELPATH,
    MIGRATION_MANIFEST_ROOT_RELPATH,
    PAPER_CLEAN_ROOM_DESCRIPTOR_RELPATH,
    PRODUCT_VIEW_DIRS,
    STAGE_OUTPUTS_RELPATH,
    STAGE_REQUIRED_DIRS,
    TARGET_STATE_REFERENCE_DOC,
    USER_ENTRY_REFS,
    WORKSPACE_ENTRY_REFS,
    WORKSPACE_INDEX_SCHEMA,
    WORKSPACE_MIGRATION_STAGE_ID,
    WORKSPACE_STATUS_SCHEMA,
    workspace_taxonomy,
)


def materialize_study_workspace_status(*, study: Mapping[str, Any], recorded_at: str) -> None:
    study_root = Path(str(study["study_root"]))
    stage_index = dict(study["stage_index"])
    current_stage = dict(stage_index.get("current_stage") or {})
    package_status = dict(study["current_truth_map"]["package_status"])
    next_action = dict(study["next_action"])
    blockers_payload = _blockers_payload(study=study, recorded_at=recorded_at)
    descriptor = {
        **dict(study),
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


def materialize_study_workspace_status_if_safe(*, study: Mapping[str, Any], recorded_at: str) -> None:
    if hard_blockers(study):
        return
    materialize_study_workspace_status(study=study, recorded_at=recorded_at)


def materialize_workspace_migration_stage_if_needed(*, study: Mapping[str, Any], recorded_at: str) -> None:
    blockers = [str(item) for item in study.get("blockers") or []]
    if not blockers:
        return
    if hard_blockers(study):
        return
    stage_blockers = set(str(item) for item in study["validation"]["stage_native"].get("blockers", []))
    if not stage_blockers.intersection(
        {
            "stage_outputs_root_missing",
            "stage_native_stage_folder_missing",
            "current_stage_missing",
        }
    ):
        return
    study_root = Path(str(study["study_root"]))
    stage_root = study_root / STAGE_OUTPUTS_RELPATH / WORKSPACE_MIGRATION_STAGE_ID
    for relpath in STAGE_REQUIRED_DIRS:
        (stage_root / relpath).mkdir(parents=True, exist_ok=True)
    blocker_payload = _workspace_migration_typed_blocker(study=study, recorded_at=recorded_at)
    manifest_payload = _workspace_migration_stage_manifest(study=study, recorded_at=recorded_at)
    projection_payload = _workspace_migration_owner_delta(study=study, recorded_at=recorded_at)
    lineage_payload = _workspace_migration_lineage(study=study, recorded_at=recorded_at)
    _write_json(stage_root / "stage_manifest.json", manifest_payload)
    _write_json(stage_root / "inputs" / "consumed_artifact_refs.json", _migration_consumed_refs(study=study))
    _write_json(stage_root / "outputs" / "migration_status.json", blocker_payload)
    _write_json(stage_root / "role_artifacts" / "validator_closeout.json", blocker_payload)
    _write_json(stage_root / "receipts" / "typed_blocker.json", blocker_payload)
    _write_json(stage_root / "lineage" / "prov.json", lineage_payload)
    _write_json(stage_root / "projection" / "current_owner_delta.json", projection_payload)


def hard_blockers(study: Mapping[str, Any]) -> list[str]:
    stage_blockers = set(str(item) for item in study["validation"]["stage_native"].get("blockers", []))
    materializable_stage_blockers = {
        "stage_outputs_root_missing",
        "stage_native_stage_folder_missing",
        "current_stage_missing",
        "workspace_target_state_migration_required",
    }
    materializable_truth_blockers = {
        "current_manuscript_missing",
        "evidence_ledger_missing",
        "review_ledger_missing",
    }
    blockers = [str(item) for item in study.get("blockers") or []]
    hard: list[str] = []
    for blocker in blockers:
        if blocker in stage_blockers and blocker in materializable_stage_blockers:
            continue
        if blocker in materializable_truth_blockers:
            continue
        hard.append(blocker)
    return hard


def materialize_workspace_surfaces(
    *,
    profile: WorkspaceProfile,
    profile_path: Path,
    studies: list[Mapping[str, Any]],
    recorded_at: str,
) -> None:
    workspace_root = profile.workspace_root.expanduser().resolve()
    descriptor = workspace_descriptor(
        profile=profile,
        profile_path=profile_path,
        studies=studies,
        recorded_at=recorded_at,
    )
    index = workspace_index(profile=profile, studies=studies, recorded_at=recorded_at)
    _write_text(workspace_root / WORKSPACE_ENTRY_REFS["workspace_status"], _render_workspace_status(index=index))
    _write_text(
        workspace_root / WORKSPACE_ENTRY_REFS["workspace_descriptor"],
        yaml.safe_dump(descriptor, allow_unicode=True, sort_keys=False),
    )
    _write_json(workspace_root / WORKSPACE_ENTRY_REFS["workspace_index"], index)
    _write_json(workspace_root / WORKSPACE_ENTRY_REFS["reports_studies_index"], index)
    _write_json(
        workspace_root / WORKSPACE_ENTRY_REFS["reports_latest_status"],
        {
            "schema_version": WORKSPACE_STATUS_SCHEMA,
            "surface_kind": "workspace_latest_status",
            "recorded_at": recorded_at,
            "workspace_root": str(workspace_root),
            "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
            "study_count": len(studies),
            "status_counts": _workspace_status_counts(studies),
            "next_required_actions": _workspace_next_actions(studies),
            "workspace_index_ref": WORKSPACE_ENTRY_REFS["workspace_index"].as_posix(),
        },
    )


def workspace_descriptor(
    *,
    profile: WorkspaceProfile,
    profile_path: Path,
    studies: list[Mapping[str, Any]],
    recorded_at: str,
) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    return {
        "schema_version": WORKSPACE_STATUS_SCHEMA,
        "surface_kind": "workspace_descriptor",
        "name": profile.name,
        "recorded_at": recorded_at,
        "profile_path": str(profile_path),
        "workspace_root": str(workspace_root),
        "studies_root": str(profile.studies_root.expanduser().resolve()),
        "runtime_root": str(profile.runtime_root.expanduser().resolve()),
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "workspace_taxonomy": workspace_taxonomy(profile),
        "study_count": len(studies),
        "canonical_study_root_pattern": "studies/<study_id>",
        "runtime_root_role": "runtime_execution_state_logs_receipts_provenance",
        "archive_roots_current_truth": False,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def workspace_index(
    *,
    profile: WorkspaceProfile,
    studies: list[Mapping[str, Any]],
    recorded_at: str,
) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    return {
        "schema_version": WORKSPACE_INDEX_SCHEMA,
        "surface_kind": "workspace_index",
        "recorded_at": recorded_at,
        "workspace_root": str(workspace_root),
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "study_count": len(studies),
        "status_counts": _workspace_status_counts(studies),
        "studies": [_workspace_study_entry(profile=profile, study=study) for study in studies],
        "runtime_boundary": {
            "runtime_root": str(profile.runtime_root.expanduser().resolve()),
            "role": "runtime_execution_state_logs_receipts_provenance",
            "user_entry": False,
            "current_paper_truth": False,
        },
        "archive_boundary": {
            "archive_roots_are_current_truth": False,
            "legacy_runtime_residue_is_current_truth": False,
        },
    }


def _workspace_migration_typed_blocker(*, study: Mapping[str, Any], recorded_at: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": "study_workspace_migration_typed_blocker",
        "blocker_id": "workspace_target_state_migration_required",
        "status": "typed_blocked",
        "recorded_at": recorded_at,
        "study_id": study["study_id"],
        "stage_id": WORKSPACE_MIGRATION_STAGE_ID,
        "owner": "MedAutoScience",
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "original_blockers": list(study.get("blockers") or []),
        "hard_blockers": hard_blockers(study),
        "next_required_action": "resolve_study_workspace_status_blockers",
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "message": (
            "Study root has been given a Stage Native migration blocker so users can inspect a canonical "
            "workspace, but this does not close any scientific stage or promote a publication package."
        ),
    }


def _workspace_migration_stage_manifest(*, study: Mapping[str, Any], recorded_at: str) -> dict[str, Any]:
    stage_root = f"{STAGE_OUTPUTS_RELPATH.as_posix()}/{WORKSPACE_MIGRATION_STAGE_ID}"
    return {
        "schema_version": 1,
        "surface_kind": "stage_manifest",
        "stage_id": WORKSPACE_MIGRATION_STAGE_ID,
        "status": "typed_blocked",
        "recorded_at": recorded_at,
        "study_id": study["study_id"],
        "stage_root": stage_root,
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "inputs_ref": f"{stage_root}/inputs/consumed_artifact_refs.json",
        "outputs_ref": f"{stage_root}/outputs/migration_status.json",
        "typed_blocker_ref": f"{stage_root}/receipts/typed_blocker.json",
        "current_owner_delta_ref": f"{stage_root}/projection/current_owner_delta.json",
        "lineage_ref": f"{stage_root}/lineage/prov.json",
        "product_refs": [
            "STUDY_STATUS.md",
            "control/stage_index.json",
            "control/next_action.json",
            "publication/current_package/STATUS.json",
        ],
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _workspace_migration_owner_delta(*, study: Mapping[str, Any], recorded_at: str) -> dict[str, Any]:
    stage_root = f"{STAGE_OUTPUTS_RELPATH.as_posix()}/{WORKSPACE_MIGRATION_STAGE_ID}"
    return {
        "schema_version": 1,
        "surface_kind": "stage_current_owner_delta",
        "recorded_at": recorded_at,
        "study_id": study["study_id"],
        "stage_id": WORKSPACE_MIGRATION_STAGE_ID,
        "status": "typed_blocked",
        "latest_owner_answer_kind": "typed_blocker",
        "latest_owner_answer_ref": f"{stage_root}/receipts/typed_blocker.json",
        "next_action": {
            "action_id": "resolve_study_workspace_status_blockers",
            "owner": "MedAutoScience",
            "status": "blocked",
            "blockers": list(study.get("blockers") or []),
        },
    }


def _workspace_migration_lineage(*, study: Mapping[str, Any], recorded_at: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": "study_workspace_migration_lineage",
        "recorded_at": recorded_at,
        "study_id": study["study_id"],
        "source": "med_autoscience.controllers.study_workspace_status",
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "runtime_root_role": "runtime_execution_state_logs_receipts_provenance",
        "archive_roots_current_truth": False,
        "paper_body_mutated": False,
        "publication_package_promoted": False,
    }


def _migration_consumed_refs(*, study: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": "stage_consumed_artifact_refs",
        "study_id": study["study_id"],
        "stage_id": WORKSPACE_MIGRATION_STAGE_ID,
        "refs": [
            "study.yaml",
            "brief.md",
            "protocol.md",
            "runtime_binding.yaml",
        ],
        "current_truth_map_ref": f"{MIGRATION_MANIFEST_ROOT_RELPATH.as_posix()}/current_truth_map.json",
        "legacy_provenance_map_ref": f"{MIGRATION_MANIFEST_ROOT_RELPATH.as_posix()}/legacy_provenance_map.json",
    }


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


def _workspace_study_entry(*, profile: WorkspaceProfile, study: Mapping[str, Any]) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    study_root = Path(str(study["study_root"]))
    runtime_root = Path(str(study["runtime_quest_root"]))
    current_stage = study["stage_index"].get("current_stage") or {}
    return {
        "study_id": study["study_id"],
        "status": study["status"],
        "canonical_study_root": _relative_path(path=study_root, root=workspace_root),
        "runtime_provenance_root": _relative_path(path=runtime_root, root=workspace_root),
        "current_stage_id": study["stage_index"].get("current_stage_id"),
        "current_stage_root": current_stage.get("stage_root"),
        "current_stage_status": current_stage.get("status"),
        "stage_index_ref": "control/stage_index.json",
        "next_action_ref": "control/next_action.json",
        "study_status_ref": "STUDY_STATUS.md",
        "paper_entry_ref": "paper/draft.md",
        "publication_package_status_ref": "publication/current_package/STATUS.json",
        "package_status": study["current_truth_map"]["package_status"].get("status"),
        "blockers": list(study.get("blockers") or []),
        "runtime_root_is_current_paper_truth": False,
        "archive_roots_are_current_truth": False,
    }


def _workspace_status_counts(studies: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for study in studies:
        status = str(study.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _render_workspace_status(*, index: Mapping[str, Any]) -> str:
    lines = [
        "# Workspace Status",
        "",
        f"- Target-state reference: `{TARGET_STATE_REFERENCE_DOC}`",
        f"- Workspace root: `{index.get('workspace_root')}`",
        f"- Study count: `{index.get('study_count')}`",
        f"- Workspace index: `{WORKSPACE_ENTRY_REFS['workspace_index'].as_posix()}`",
        "",
        "Studies:",
    ]
    for study in index.get("studies") or []:
        lines.append(
            "- "
            f"`{study.get('study_id')}`: status=`{study.get('status')}`, "
            f"stage=`{study.get('current_stage_id')}`, root=`{study.get('canonical_study_root')}`"
        )
    lines.extend(
        [
            "",
            "Runtime roots and archive roots are provenance surfaces only; current study inspection starts under `studies/<study_id>/`.",
            "",
        ]
    )
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


def _relative_path(*, path: Path, root: Path) -> str:
    try:
        return path.expanduser().resolve().relative_to(root.expanduser().resolve()).as_posix()
    except ValueError:
        return str(path.expanduser().resolve())


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _history_stamp(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("+", "").replace(".", "")


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "hard_blockers",
    "materialize_study_workspace_status",
    "materialize_study_workspace_status_if_safe",
    "materialize_workspace_migration_stage_if_needed",
    "materialize_workspace_surfaces",
    "workspace_descriptor",
    "workspace_index",
]

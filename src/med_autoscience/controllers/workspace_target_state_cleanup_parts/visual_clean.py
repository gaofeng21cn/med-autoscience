from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers.workspace_target_state_cleanup_parts.shared import (
    add_symlink_target,
    blocker_slug,
    decision_counts,
    dedupe,
    logical_abs,
    path_kind,
    path_present,
    relative_ref,
)


SCHEMA_VERSION = "mas.workspace_target_state_cleanup.v1"
STUDY_LEGACY_SURFACES_RELPATH = Path("_archive") / "legacy_surfaces"
OPS_LEGACY_SURFACES_RELPATH = Path("archive") / "legacy_ops_surfaces"

STUDY_ACTIVE_ROOTS = {
    "STUDY_STATUS.md": "study_status",
    "study.yaml": "study_identity_truth",
    "paper.yaml": "paper_metadata_truth",
    "control": "control_read_model_projection",
    "artifacts": "stage_native_artifact_authority",
    "paper": "current_paper_product_view",
    "analysis": "current_analysis_product_view",
    "evidence": "current_evidence_product_view",
    "publication": "current_publication_product_view",
    "_archive": "study_archive_provenance",
}

STUDY_ACTIVE_LOCATOR_TAILS = {
    "runtime_binding.yaml": {
        "role": "active_runtime_binding_locator_tail",
        "reason": "runtime_binding.yaml remains an active MAS runtime locator until the runtime-binding control-surface migration lands",
    },
}

OPS_ACTIVE_ROOTS = {
    "medautoscience": "canonical_mas_workspace_ops_entry",
    "mas": "progress_portal_container",
    "data_assets": "workspace_data_asset_ops",
}

OPS_ACTIVE_MEDAUTOSCIENCE_CHILDREN = {
    ".venv": "workspace_python_environment",
    "bin": "canonical_mas_workspace_wrappers",
    "config.env": "canonical_mas_workspace_config",
    "config.env.example": "canonical_mas_workspace_config_example",
    "profiles": "workspace_profiles",
    "README.md": "canonical_mas_workspace_ops_readme",
    "compatibility_inventory.md": "workspace_compatibility_inventory",
    "lightweight_collaboration.md": "workspace_collaboration_notes",
}

OPS_ACTIVE_MAS_CHILDREN = {
    "progress": "progress_portal_static_html_projection",
}

OPS_LEGACY_ARCHIVE_ROOTS = {
    "deepscientist",
    "framework_refs",
    "med-deepscientist",
    "med-the study team",
    "studies",
    "med-deepscientist.TOMBSTONE.json",
}

OPS_MEDAUTOSCIENCE_LEGACY_CHILDREN = {
    "logs",
    "python_pycache",
}

OPS_MEDAUTOSCIENCE_LEGACY_BIN_ENTRIES = {
    "legacy-control-surface-clean-migration",
}

OPS_MEDAUTOSCIENCE_ACTIVE_BIN_ENTRIES = {
    "_shared.sh",
    "bootstrap",
    "show-profile",
    "enter-study",
    "study-progress",
    "study-state-matrix",
    "domain-health-diagnostic",
    "owner-route-reconcile",
    "domain-action-request-materialize",
    "domain-owner-action-dispatch",
    "maintain-runtime-storage",
    "storage-audit",
    "publication-gate",
    "medical-surface",
    "figure-loop-guard",
    "resolve-submission-targets",
    "resolve-journal-shortlist",
    "init-portfolio-memory",
    "portfolio-memory-status",
    "init-workspace-literature",
    "workspace-literature-status",
    "prepare-external-research",
    "external-research-status",
    "export-submission",
    "sync-delivery",
}

OPS_MAS_LEGACY_CHILDREN = {
    "README.md",
    "behavior_equivalence_gate.yaml",
    "bin",
    "config.env",
    "config.env.example",
    "live-console",
}

OPS_LEGACY_SUFFIXES = (
    ".bak",
    ".bak-",
    ".old",
    ".orig",
    ".tmp",
)

STUDY_LEGACY_ARCHIVE_ROOTS = {
    ".ds",
    "brief.md",
    "protocol.md",
    "data_input",
    "experiments",
    "literature",
    "manuscript",
    "notes",
    "portfolio",
    "submission_packages",
    "tests",
    "tmp",
    "CHECKLIST.md",
    "PLAN.md",
    "STOP_LOSS_MEMORY.md",
}


def study_visual_cleanup_plan(
    *,
    workspace_root: Path,
    archive_stamp: str,
    enabled: bool,
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    studies_root = workspace_root / "studies"
    if not enabled or not studies_root.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "study_visual_cleanup_plan",
            "enabled": enabled,
            "archive_stamp": archive_stamp,
            "study_count": 0,
            "study_actions": [],
            "study_action_counts": {},
            "blockers": [],
        }
    for study_root in sorted((path for path in studies_root.iterdir() if path.is_dir()), key=lambda item: item.name):
        study_id = study_root.name
        target_root = study_root / STUDY_LEGACY_SURFACES_RELPATH / archive_stamp
        for entry in sorted(study_root.iterdir(), key=lambda path: path.name):
            name = entry.name
            if name in STUDY_ACTIVE_ROOTS:
                actions.append(
                    _study_action(
                        workspace_root=workspace_root,
                        study_id=study_id,
                        source=entry,
                        role=STUDY_ACTIVE_ROOTS[name],
                        decision="keep_active_study_root",
                    )
                )
                continue
            if name in STUDY_ACTIVE_LOCATOR_TAILS:
                tail = STUDY_ACTIVE_LOCATOR_TAILS[name]
                actions.append(
                    _study_action(
                        workspace_root=workspace_root,
                        study_id=study_id,
                        source=entry,
                        role=str(tail["role"]),
                        decision="keep_active_locator_tail",
                        blocker_id="runtime_binding_control_surface_migration_pending",
                        reason=str(tail["reason"]),
                    )
                )
                continue
            if name in STUDY_LEGACY_ARCHIVE_ROOTS:
                actions.append(
                    _study_action(
                        workspace_root=workspace_root,
                        study_id=study_id,
                        source=entry,
                        role="study_legacy_surface_not_current_truth",
                        decision="archive",
                        target=target_root / name,
                    )
                )
                continue
            actions.append(
                _study_action(
                    workspace_root=workspace_root,
                    study_id=study_id,
                    source=entry,
                    role="unclassified_study_root_entry",
                    decision="blocked_unclassified_study_root",
                    blocker_id=f"unclassified_study_root_entry_{study_id}_{blocker_slug(name)}",
                )
            )
    blockers = [
        str(action["blocker_id"])
        for action in actions
        if action.get("decision") == "blocked_unclassified_study_root" and action.get("blocker_id")
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "study_visual_cleanup_plan",
        "enabled": True,
        "archive_stamp": archive_stamp,
        "study_count": len({str(action.get("study_id") or "") for action in actions if action.get("study_id")}),
        "study_actions": actions,
        "study_action_counts": decision_counts(actions),
        "expected_study_root_entries_after_apply": _expected_study_root_entries(actions),
        "blockers": dedupe(blockers),
    }


def ops_visual_cleanup_plan(
    *,
    workspace_root: Path,
    archive_stamp: str,
    enabled: bool,
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    ops_root = workspace_root / "ops"
    if not enabled or not ops_root.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "ops_visual_cleanup_plan",
            "enabled": enabled,
            "archive_stamp": archive_stamp,
            "ops_actions": [],
            "ops_action_counts": {},
            "expected_ops_entries_after_apply": [],
            "blockers": [],
        }

    target_root = workspace_root / OPS_LEGACY_SURFACES_RELPATH / archive_stamp
    for entry in sorted(ops_root.iterdir(), key=lambda path: path.name):
        name = entry.name
        if name in OPS_ACTIVE_ROOTS:
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role=OPS_ACTIVE_ROOTS[name],
                    decision="keep_active_ops_root",
                )
            )
            if name == "medautoscience" and entry.is_dir():
                actions.extend(
                    _ops_medautoscience_child_actions(
                        workspace_root=workspace_root,
                        medautoscience_root=entry,
                        target_root=target_root / "medautoscience",
                    )
                )
            if name == "mas" and entry.is_dir():
                actions.extend(
                    _ops_mas_child_actions(
                        workspace_root=workspace_root,
                        mas_root=entry,
                        target_root=target_root / "mas",
                    )
                )
            continue
        if name in OPS_LEGACY_ARCHIVE_ROOTS or _is_legacy_backup_name(name):
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role="legacy_ops_surface_not_current_truth",
                    decision="archive",
                    target=target_root / name,
                )
            )
            continue
        actions.append(
            _ops_action(
                workspace_root=workspace_root,
                source=entry,
                role="unclassified_ops_root_entry",
                decision="blocked_unclassified_ops_root",
                    blocker_id=f"unclassified_ops_root_entry_{blocker_slug(name)}",
            )
        )
    blockers = [
        str(action["blocker_id"])
        for action in actions
        if action.get("decision") == "blocked_unclassified_ops_root" and action.get("blocker_id")
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "ops_visual_cleanup_plan",
        "enabled": True,
        "archive_stamp": archive_stamp,
        "ops_actions": actions,
        "ops_action_counts": decision_counts(actions),
        "expected_ops_entries_after_apply": _expected_ops_entries(actions),
        "blockers": dedupe(blockers),
    }


def apply_study_visual_cleanup_plan(study_visual_plan: dict[str, Any]) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    for action in study_visual_plan.get("study_actions") or []:
        if action.get("decision") != "archive":
            continue
        source = Path(str(action["absolute_path"]))
        target = Path(str(action["target_absolute_path"]))
        applied.append(_apply_archive_action(action=action, source=source, target=target))
    return applied


def apply_ops_visual_cleanup_plan(ops_visual_plan: dict[str, Any]) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    for action in ops_visual_plan.get("ops_actions") or []:
        if action.get("decision") != "archive":
            continue
        source = Path(str(action["absolute_path"]))
        target = Path(str(action["target_absolute_path"]))
        applied.append(_apply_archive_action(action=action, source=source, target=target))
    return applied


def _ops_medautoscience_child_actions(
    *,
    workspace_root: Path,
    medautoscience_root: Path,
    target_root: Path,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for entry in sorted(medautoscience_root.iterdir(), key=lambda path: path.name):
        name = entry.name
        if name in OPS_ACTIVE_MEDAUTOSCIENCE_CHILDREN:
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role=OPS_ACTIVE_MEDAUTOSCIENCE_CHILDREN[name],
                    decision="keep_active_ops_child",
                )
            )
            if name == "bin" and entry.is_dir():
                actions.extend(
                    _ops_medautoscience_bin_actions(
                        workspace_root=workspace_root,
                        bin_root=entry,
                        target_root=target_root / "bin",
                    )
                )
            continue
        if name in OPS_MEDAUTOSCIENCE_LEGACY_CHILDREN or _is_legacy_backup_name(name):
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role="legacy_medautoscience_ops_child_not_current_truth",
                    decision="archive",
                    target=target_root / name,
                )
            )
            continue
        actions.append(
            _ops_action(
                workspace_root=workspace_root,
                source=entry,
                role="unclassified_ops_root_entry",
                decision="blocked_unclassified_ops_root",
                blocker_id=f"unclassified_ops_root_entry_medautoscience_{blocker_slug(name)}",
            )
        )
    return actions


def _ops_medautoscience_bin_actions(
    *,
    workspace_root: Path,
    bin_root: Path,
    target_root: Path,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for entry in sorted(bin_root.iterdir(), key=lambda path: path.name):
        name = entry.name
        if name in OPS_MEDAUTOSCIENCE_ACTIVE_BIN_ENTRIES:
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role="canonical_mas_workspace_wrapper",
                    decision="keep_active_ops_child",
                )
            )
            continue
        if name in OPS_MEDAUTOSCIENCE_LEGACY_BIN_ENTRIES or _is_legacy_backup_name(name):
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role="legacy_medautoscience_wrapper_not_current_entry",
                    decision="archive",
                    target=target_root / name,
                )
            )
            continue
        actions.append(
            _ops_action(
                workspace_root=workspace_root,
                source=entry,
                role="unclassified_medautoscience_wrapper",
                decision="blocked_unclassified_ops_root",
                blocker_id=f"unclassified_ops_root_entry_medautoscience_bin_{blocker_slug(name)}",
            )
        )
    return actions


def _ops_mas_child_actions(
    *,
    workspace_root: Path,
    mas_root: Path,
    target_root: Path,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for entry in sorted(mas_root.iterdir(), key=lambda path: path.name):
        name = entry.name
        if name in OPS_ACTIVE_MAS_CHILDREN:
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role=OPS_ACTIVE_MAS_CHILDREN[name],
                    decision="keep_active_ops_child",
                )
            )
            continue
        if name in OPS_MAS_LEGACY_CHILDREN or _is_legacy_backup_name(name) or name == ".DS_Store":
            actions.append(
                _ops_action(
                    workspace_root=workspace_root,
                    source=entry,
                    role="legacy_mas_bridge_surface_not_current_entry",
                    decision="archive",
                    target=target_root / name,
                )
            )
            continue
        actions.append(
            _ops_action(
                workspace_root=workspace_root,
                source=entry,
                role="unclassified_ops_root_entry",
                decision="blocked_unclassified_ops_root",
                blocker_id=f"unclassified_ops_root_entry_mas_{blocker_slug(name)}",
            )
        )
    return actions


def _apply_archive_action(*, action: dict[str, Any], source: Path, target: Path) -> dict[str, Any]:
    if not path_present(source):
        return {**dict(action), "applied": False, "skip_reason": "source_missing"}
    if path_present(target):
        if source.is_dir() and target.is_dir():
            _merge_directory(source=source, target=target)
            return {**dict(action), "applied": True, "merge_target_existed": True}
        return {**dict(action), "applied": False, "skip_reason": "target_exists"}
    target.parent.mkdir(parents=True, exist_ok=True)
    source.rename(target)
    return {**dict(action), "applied": True}


def _merge_directory(*, source: Path, target: Path) -> None:
    for child in sorted(source.iterdir(), key=lambda item: item.name):
        destination = target / child.name
        if path_present(destination):
            if child.is_dir() and destination.is_dir():
                _merge_directory(source=child, target=destination)
                continue
            raise FileExistsError(f"target path already exists: {destination}")
        child.rename(destination)
    source.rmdir()


def _study_action(
    *,
    workspace_root: Path,
    study_id: str,
    source: Path,
    role: str,
    decision: str,
    target: Path | None = None,
    blocker_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    source_abs = logical_abs(source)
    payload = {
        "study_id": study_id,
        "source_relative_path": source.name,
        "workspace_relative_path": relative_ref(workspace_root, source_abs),
        "absolute_path": str(source_abs),
        "exists": path_present(source),
        "kind": path_kind(source),
        "role": role,
        "decision": decision,
        "current_truth": decision in {"keep_active_study_root", "keep_active_locator_tail"},
        "user_entry": decision == "keep_active_study_root",
        "applied": False,
    }
    add_symlink_target(payload, source)
    if target is not None:
        payload["target_relative_path"] = relative_ref(source.parent, target)
        payload["target_workspace_relative_path"] = relative_ref(workspace_root, target)
        payload["target_absolute_path"] = str(target)
        payload["target_exists"] = path_present(target)
    if blocker_id:
        payload["blocker_id"] = blocker_id
    if reason:
        payload["reason"] = reason
    return payload


def _ops_action(
    *,
    workspace_root: Path,
    source: Path,
    role: str,
    decision: str,
    target: Path | None = None,
    blocker_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    source_abs = logical_abs(source)
    payload = {
        "source_relative_path": relative_ref(workspace_root / "ops", source_abs),
        "workspace_relative_path": relative_ref(workspace_root, source_abs),
        "absolute_path": str(source_abs),
        "exists": path_present(source),
        "kind": path_kind(source),
        "role": role,
        "decision": decision,
        "current_truth": decision in {"keep_active_ops_root", "keep_active_ops_child"},
        "applied": False,
    }
    add_symlink_target(payload, source)
    if target is not None:
        payload["target_relative_path"] = relative_ref(workspace_root, target)
        payload["target_absolute_path"] = str(target)
        payload["target_exists"] = path_present(target)
    if blocker_id:
        payload["blocker_id"] = blocker_id
    if reason:
        payload["reason"] = reason
    return payload


def _expected_study_root_entries(actions: list[dict[str, Any]]) -> dict[str, list[str]]:
    by_study: dict[str, set[str]] = {}
    for action in actions:
        study_id = str(action.get("study_id") or "")
        if not study_id:
            continue
        entries = by_study.setdefault(study_id, set(STUDY_ACTIVE_ROOTS))
        if action.get("decision") in {
            "keep_active_study_root",
            "keep_active_locator_tail",
            "blocked_unclassified_study_root",
        }:
            entries.add(str(action.get("source_relative_path") or ""))
    return {study_id: sorted(entries) for study_id, entries in sorted(by_study.items())}


def _expected_ops_entries(actions: list[dict[str, Any]]) -> list[str]:
    entries: set[str] = set()
    for action in actions:
        source = str(action.get("source_relative_path") or "")
        if not source or "/" in source:
            continue
        if action.get("decision") in {"keep_active_ops_root", "blocked_unclassified_ops_root"}:
            entries.add(source)
    return sorted(entries)


def _is_legacy_backup_name(name: str) -> bool:
    return any(name.endswith(suffix) or suffix in name for suffix in OPS_LEGACY_SUFFIXES)


__all__ = [
    "apply_ops_visual_cleanup_plan",
    "apply_study_visual_cleanup_plan",
    "ops_visual_cleanup_plan",
    "study_visual_cleanup_plan",
]

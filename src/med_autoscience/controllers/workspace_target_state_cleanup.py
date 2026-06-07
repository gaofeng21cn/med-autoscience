from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.controllers.study_workspace_status_parts import TARGET_STATE_REFERENCE_DOC
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
from med_autoscience.controllers.workspace_target_state_cleanup_parts.visual_clean import (
    apply_ops_visual_cleanup_plan,
    apply_study_visual_cleanup_plan,
    ops_visual_cleanup_plan,
    study_visual_cleanup_plan,
)


SURFACE_KIND = "workspace_target_state_cleanup"
SCHEMA_VERSION = "mas.workspace_target_state_cleanup.v1"
MANIFEST_ROOT_RELPATH = Path("archive") / "root_cleanup_manifest"
LEGACY_ROOT_SURFACES_RELPATH = Path("archive") / "legacy_root_surfaces"
REPORT_RELPATH = Path("reports") / "workspace_target_state_cleanup.json"

PATH_REF_EXTENSIONS = {
    ".cfg",
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

PATH_REF_ROOT_FILES = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("WORKSPACE_AUTOSCIENCE_RULES.md"),
    Path("WORKSPACE_STATUS.md"),
    Path("workspace.yaml"),
    Path("workspace_index.json"),
)

STUDY_ACTIVE_SOURCE_FILES = {
    "study.yaml",
    "paper.yaml",
    "brief.md",
    "protocol.md",
}

OPS_ACTIVE_SOURCE_SUFFIXES = {
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".yaml",
    ".yml",
}

ANALYSIS_ACTIVE_SOURCE_DIRS = {
    "scripts",
    "runbooks",
    "runbook",
    "src",
}

ANALYSIS_ACTIVE_SOURCE_FILENAMES = {
    "README.md",
    "PLAN.md",
    "CHECKLIST.md",
    "analysis_plan.md",
    "clean_room_runbook.md",
    "clean_room_analysis_surface.md",
    "paper_facing_evidence_contract.md",
}

PROVENANCE_REF_EXCLUDED_PARTS = {
    "_archive",
    "_repo_compare",
    "artifacts",
    "framework_refs",
    "lineage",
    "logs",
    "outputs",
    "package_refs",
    "publication",
    "receipts",
    "reports",
    "results",
    "role_artifacts",
    "runtime",
}

PROVENANCE_REF_EXCLUDED_FILENAMES = {
    "latest.json",
    "publication_eval.json",
    "publication_eval.latest.json",
    "controller_decisions.json",
    "controller_decisions.latest.json",
    "evidence_ledger.json",
    "review_ledger.json",
    "revision_log.json",
    "owner_receipt.json",
    "typed_blocker.json",
    "stage_manifest.json",
    "current_owner_delta.json",
}

PATH_REF_RULES = (
    ("datasets_segment", re.compile(r"(?<!data/)datasets/"), "data/datasets/"),
    ("portfolio_segment", re.compile(r"(?<!memory/)portfolio/"), "memory/portfolio/"),
    ("portfolio_leaf", re.compile(r"(?<!memory/)portfolio(?=[\"'`\\s\\n\\r])"), "memory/portfolio"),
    (
        "root_refs_segment",
        re.compile(r"(^|[\\s`'\"(:\\[])refs/"),
        r"\1archive/legacy_root_surfaces/refs/",
    ),
    (
        "relative_refs_segment",
        re.compile(r"(?<!legacy_root_surfaces/)\.\./\.\./refs/"),
        "../../archive/legacy_root_surfaces/refs/",
    ),
    (
        "relative3_refs_segment",
        re.compile(r"(?<!legacy_root_surfaces/)\.\./\.\./\.\./refs/"),
        "../../../archive/legacy_root_surfaces/refs/",
    ),
    (
        "dm_cvd_refs_segment",
        re.compile(r"DM-CVD-Mortality-Risk/refs/"),
        "DM-CVD-Mortality-Risk/archive/legacy_root_surfaces/refs/",
    ),
    (
        "workspace_venv_ref",
        re.compile(r"\$\{WORKSPACE_ROOT\}/\.venv"),
        "${WORKSPACE_ROOT}/ops/medautoscience/.venv",
    ),
)

ACTIVE_ROOTS = {
    "AGENTS.md": "workspace_agent_instructions",
    "README.md": "workspace_user_entry",
    "WORKSPACE_AUTOSCIENCE_RULES.md": "workspace_agent_rules",
    "WORKSPACE_STATUS.md": "workspace_status",
    "workspace.yaml": "workspace_descriptor",
    "workspace_index.json": "workspace_index",
    "data": "shared_data_root",
    "literature": "literature_root",
    "memory": "workspace_memory_root",
    "studies": "canonical_studies_root",
    "runtime": "runtime_execution_state_logs_receipts_provenance",
    "reports": "workspace_reports",
    "archive": "workspace_archive_provenance",
    "ops": "workspace_operations",
}

DIRECTORY_MOVES = {
    "artifacts": Path("runtime") / "artifacts",
    "datasets": Path("data") / "datasets",
    "portfolio": Path("memory") / "portfolio",
    ".venv": Path("ops") / "medautoscience" / ".venv",
}

DIRECTORY_MOVE_BLOCKERS = {
    "datasets": "legacy_datasets_refs_remaining",
    "portfolio": "legacy_portfolio_refs_remaining",
    ".venv": "legacy_root_venv_ref_remaining",
}

LEGACY_ARCHIVE_ROOTS = {
    ".tmp",
    "analysis",
    "assets",
    "paper",
    "refs",
    "contracts",
    "docs",
    "experiments",
    "tests",
    "storage_audit",
    "inbox",
    "pipeline",
    "ppt",
    "raw data",
    "registry",
}

DEV_SCAFFOLD_ARCHIVE_ROOTS = {
    ".codex",
    ".gitignore",
    ".worktrees",
    ".python-version",
    "RTK.md",
    "hermes_runtime_binding.yaml",
    "pyproject.toml",
    "uv.lock",
}

ACTIVE_BLOCKED_ROOTS: dict[str, dict[str, str]] = {}


def run_workspace_target_state_cleanup(
    *,
    profile_path: Path,
    apply: bool,
    rewrite_refs: bool = True,
    visual_clean: bool = False,
) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    recorded_at = _utc_now()
    workspace_root = profile.workspace_root.expanduser().resolve()
    archive_stamp = _stamp(recorded_at)
    path_ref_plan = _path_ref_plan(
        workspace_root=workspace_root,
        profile=profile,
        profile_path=resolved_profile_path,
        archive_stamp=archive_stamp,
    )
    root_plan = _root_plan(
        workspace_root=workspace_root,
        recorded_at=recorded_at,
        archive_stamp=archive_stamp,
        path_ref_plan=path_ref_plan,
    )
    study_visual_plan = study_visual_cleanup_plan(
        workspace_root=workspace_root,
        archive_stamp=archive_stamp,
        enabled=visual_clean,
    )
    ops_visual_plan = ops_visual_cleanup_plan(
        workspace_root=workspace_root,
        archive_stamp=archive_stamp,
        enabled=visual_clean,
    )

    applied_path_ref_updates: list[dict[str, Any]] = []
    applied_root_actions: list[dict[str, Any]] = []
    applied_study_visual_actions: list[dict[str, Any]] = []
    applied_ops_visual_actions: list[dict[str, Any]] = []
    if apply:
        _ensure_target_roots(workspace_root)
        if rewrite_refs:
            applied_path_ref_updates = _apply_path_ref_plan(path_ref_plan)
            profile = load_profile(resolved_profile_path)
            path_ref_plan = _path_ref_plan(
                workspace_root=workspace_root,
                profile=profile,
                profile_path=resolved_profile_path,
                archive_stamp=archive_stamp,
            )
            root_plan = _root_plan(
                workspace_root=workspace_root,
                recorded_at=recorded_at,
                archive_stamp=archive_stamp,
                path_ref_plan=path_ref_plan,
            )
            study_visual_plan = study_visual_cleanup_plan(
                workspace_root=workspace_root,
                archive_stamp=archive_stamp,
                enabled=visual_clean,
            )
            ops_visual_plan = ops_visual_cleanup_plan(
                workspace_root=workspace_root,
                archive_stamp=archive_stamp,
                enabled=visual_clean,
            )
        applied_root_actions = _apply_root_plan(root_plan)
        if visual_clean:
            applied_study_visual_actions = apply_study_visual_cleanup_plan(study_visual_plan)
            applied_ops_visual_actions = apply_ops_visual_cleanup_plan(ops_visual_plan)

    post_path_ref_plan = (
        _path_ref_plan(
            workspace_root=workspace_root,
            profile=profile,
            profile_path=resolved_profile_path,
            archive_stamp=archive_stamp,
        )
        if apply
        else path_ref_plan
    )
    post_root_plan = (
        _root_plan(
            workspace_root=workspace_root,
            recorded_at=recorded_at,
            archive_stamp=archive_stamp,
            path_ref_plan=post_path_ref_plan,
        )
        if apply
        else root_plan
    )
    post_study_visual_plan = (
        study_visual_cleanup_plan(
            workspace_root=workspace_root,
            archive_stamp=archive_stamp,
            enabled=visual_clean,
        )
        if apply
        else study_visual_plan
    )
    post_ops_visual_plan = (
        ops_visual_cleanup_plan(
            workspace_root=workspace_root,
            archive_stamp=archive_stamp,
            enabled=visual_clean,
        )
        if apply
        else ops_visual_plan
    )
    manifest = _manifest(
        profile=profile,
        profile_path=resolved_profile_path,
        recorded_at=recorded_at,
        mode="apply" if apply else "dry_run",
        archive_stamp=archive_stamp,
        path_ref_plan=post_path_ref_plan,
        root_plan=post_root_plan,
        study_visual_plan=post_study_visual_plan,
        ops_visual_plan=post_ops_visual_plan,
        applied_path_ref_updates=applied_path_ref_updates,
        applied_root_actions=applied_root_actions,
        applied_study_visual_actions=applied_study_visual_actions,
        applied_ops_visual_actions=applied_ops_visual_actions,
        visual_clean=visual_clean,
    )
    if apply:
        _write_manifest(workspace_root=workspace_root, manifest=manifest, recorded_at=recorded_at)
    return manifest


def _path_ref_plan(
    *,
    workspace_root: Path,
    profile: WorkspaceProfile,
    profile_path: Path,
    archive_stamp: str,
) -> dict[str, Any]:
    candidates = _path_ref_candidates(workspace_root=workspace_root, profile_path=profile_path)
    file_updates: list[dict[str, Any]] = []
    for file_path in candidates:
        relpath = relative_ref(workspace_root, file_path)
        text = _read_text_or_none(file_path)
        if text is None:
            continue
        rewritten = _rewrite_text_refs(text, archive_stamp=archive_stamp)
        if rewritten == text:
            continue
        replacement_counts = _replacement_counts(text=text)
        file_updates.append(
            {
                "path": relpath,
                "absolute_path": str(file_path),
                "replacement_count": sum(replacement_counts.values()),
                "replacement_counts": replacement_counts,
                "decision": "rewrite_path_refs",
                "applied": False,
            }
        )
    blockers = _path_ref_blockers(file_updates=file_updates)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_path_ref_migration_plan",
        "archive_stamp": archive_stamp,
        "candidate_policy": {
            "root_files": [path.as_posix() for path in PATH_REF_ROOT_FILES],
            "study_active_source_files": sorted(STUDY_ACTIVE_SOURCE_FILES),
            "ops_active_source_suffixes": sorted(OPS_ACTIVE_SOURCE_SUFFIXES),
            "analysis_active_source_dirs": sorted(ANALYSIS_ACTIVE_SOURCE_DIRS),
            "analysis_active_source_filenames": sorted(ANALYSIS_ACTIVE_SOURCE_FILENAMES),
            "excluded_provenance_parts": sorted(PROVENANCE_REF_EXCLUDED_PARTS),
            "excluded_provenance_filenames": sorted(PROVENANCE_REF_EXCLUDED_FILENAMES),
        },
        "candidate_file_count": len(candidates),
        "candidate_files": [relative_ref(workspace_root, path) for path in candidates],
        "replacement_rules": [
            {"rule_id": rule_id, "to": target}
            for rule_id, _, target in _path_ref_replacement_rules(archive_stamp=archive_stamp)
        ],
        "file_update_count": len(file_updates),
        "file_updates": file_updates,
        "blockers": blockers,
        "migration_complete": not blockers,
        "profile_refs": _profile_ref_status(workspace_root=workspace_root, profile=profile),
    }


def _root_plan(
    *,
    workspace_root: Path,
    recorded_at: str,
    archive_stamp: str,
    path_ref_plan: dict[str, Any],
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    target_root = LEGACY_ROOT_SURFACES_RELPATH / archive_stamp
    top_entries = sorted(workspace_root.iterdir(), key=lambda path: path.name)
    path_ref_blockers = set(path_ref_plan.get("blockers") or [])
    for entry in top_entries:
        name = entry.name
        if name == ".git":
            continue
        if name in ACTIVE_ROOTS:
            actions.append(_action(entry, role=ACTIVE_ROOTS[name], decision="keep_active_root"))
            continue
        if name in DIRECTORY_MOVES:
            blocker_id = DIRECTORY_MOVE_BLOCKERS.get(name)
            if blocker_id and blocker_id in path_ref_blockers:
                actions.append(
                    _action(
                        entry,
                        role="legacy_compatibility_root",
                        decision="blocked_until_path_refs_rewritten",
                        target=workspace_root / DIRECTORY_MOVES[name],
                        blocker_id=blocker_id,
                    )
                )
            else:
                actions.append(
                    _action(
                        entry,
                        role="move_to_target_workspace_root",
                        decision="move",
                        target=workspace_root / DIRECTORY_MOVES[name],
                    )
                )
            continue
        if name in LEGACY_ARCHIVE_ROOTS:
            actions.append(
                _action(
                    entry,
                    role="legacy_root_surface_not_current_truth",
                    decision="archive",
                    target=workspace_root / target_root / name,
                )
            )
            continue
        if name in DEV_SCAFFOLD_ARCHIVE_ROOTS:
            actions.append(
                _action(
                    entry,
                    role="legacy_dev_scaffold_not_workspace_truth",
                    decision="archive",
                    target=workspace_root / target_root / "dev_scaffold" / name,
                )
            )
            continue
        if name in ACTIVE_BLOCKED_ROOTS:
            blocked = ACTIVE_BLOCKED_ROOTS[name]
            actions.append(
                _action(
                    entry,
                    role=str(blocked["role"]),
                    decision="blocked_active_caller",
                    blocker_id=str(blocked["blocker_id"]),
                    reason=str(blocked["reason"]),
                )
            )
            continue
        if name.isdigit():
            actions.append(
                _action(
                    entry,
                    role="legacy_numeric_scratch_root_not_current_truth",
                    decision="archive",
                    target=workspace_root / target_root / "numeric_scratch" / name,
                )
            )
            continue
        actions.append(
            _action(
                entry,
                role="unclassified_root_entry",
                decision="blocked_unclassified_root",
                blocker_id=f"unclassified_root_entry_{blocker_slug(name)}",
            )
        )
    blockers = [
        str(action["blocker_id"])
        for action in actions
        if action.get("decision") in {"blocked_active_caller", "blocked_unclassified_root", "blocked_until_path_refs_rewritten"}
        and action.get("blocker_id")
    ]
    blockers.extend(str(item) for item in path_ref_blockers)
    root_entries_after_apply = _expected_root_entries(actions)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_root_cleanup_plan",
        "recorded_at": recorded_at,
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "archive_stamp": archive_stamp,
        "root_actions": actions,
        "root_action_counts": decision_counts(actions),
        "expected_root_entries_after_apply": root_entries_after_apply,
        "blockers": dedupe(blockers),
    }


def _apply_path_ref_plan(path_ref_plan: dict[str, Any]) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    archive_stamp = str(path_ref_plan["archive_stamp"])
    for update in path_ref_plan.get("file_updates") or []:
        file_path = Path(str(update["absolute_path"]))
        original = file_path.read_text(encoding="utf-8")
        rewritten = _rewrite_text_refs(original, archive_stamp=archive_stamp)
        if rewritten == original:
            continue
        file_path.write_text(rewritten, encoding="utf-8")
        applied.append({**dict(update), "applied": True})
    return applied


def _apply_root_plan(root_plan: dict[str, Any]) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    for action in root_plan.get("root_actions") or []:
        decision = str(action.get("decision") or "")
        if decision not in {"move", "archive"}:
            continue
        source = Path(str(action["absolute_path"]))
        target = Path(str(action["target_absolute_path"]))
        if not path_present(source):
            applied.append({**dict(action), "applied": False, "skip_reason": "source_missing"})
            continue
        if decision == "move" and action.get("source_relative_path") == "artifacts":
            _migrate_root_artifacts(source=source, target=target)
            applied.append({**dict(action), "applied": True, "migration_kind": "root_artifacts_to_runtime_artifacts"})
            continue
        if path_present(target):
            if source.is_dir() and target.is_dir():
                _merge_directory(source=source, target=target)
                applied.append({**dict(action), "applied": True, "merge_target_existed": True})
                continue
            applied.append({**dict(action), "applied": False, "skip_reason": "target_exists"})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        applied.append({**dict(action), "applied": True})
    return applied


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


def _migrate_root_artifacts(*, source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for child in sorted(source.iterdir(), key=lambda item: item.name):
        if child.name == "runtime" and child.is_dir():
            _merge_directory(source=child, target=target)
            continue
        destination = target / child.name
        if path_present(destination):
            if child.is_dir() and destination.is_dir():
                _merge_directory(source=child, target=destination)
                continue
            raise FileExistsError(f"target path already exists: {destination}")
        child.rename(destination)
    source.rmdir()


def _manifest(
    *,
    profile: WorkspaceProfile,
    profile_path: Path,
    recorded_at: str,
    mode: str,
    archive_stamp: str,
    path_ref_plan: dict[str, Any],
    root_plan: dict[str, Any],
    study_visual_plan: dict[str, Any],
    ops_visual_plan: dict[str, Any],
    applied_path_ref_updates: list[dict[str, Any]],
    applied_root_actions: list[dict[str, Any]],
    applied_study_visual_actions: list[dict[str, Any]],
    applied_ops_visual_actions: list[dict[str, Any]],
    visual_clean: bool,
) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    validation = _validation(
        path_ref_plan=path_ref_plan,
        root_plan=root_plan,
        study_visual_plan=study_visual_plan,
        ops_visual_plan=ops_visual_plan,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "mode": mode,
        "status": "ready" if validation["pass"] else "typed_blocked",
        "recorded_at": recorded_at,
        "profile_path": str(profile_path),
        "workspace_root": str(workspace_root),
        "target_state_reference_doc": TARGET_STATE_REFERENCE_DOC,
        "archive_stamp": archive_stamp,
        "visual_clean_enabled": visual_clean,
        "authority_boundary": {
            "paper_body_mutation_allowed": False,
            "publication_eval_write_allowed": False,
            "controller_decision_write_allowed": False,
            "runtime_truth_write_allowed": False,
            "current_package_promotion_allowed": False,
            "root_physical_move_allowed": True,
            "path_ref_rewrite_allowed": True,
            "destructive_delete_allowed": False,
        },
        "current_truth_map": {
            "workspace_root": str(workspace_root),
            "canonical_studies_root": "studies",
            "runtime_root": "runtime/quests",
            "workspace_runtime_artifacts_root": "runtime/artifacts",
            "workspace_index": "workspace_index.json",
            "study_user_entry_pattern": "studies/<study_id>",
        },
        "legacy_provenance_map": _legacy_provenance_map(
            root_plan=root_plan,
            applied_root_actions=applied_root_actions,
            ops_visual_plan=ops_visual_plan,
            applied_ops_visual_actions=applied_ops_visual_actions,
        ),
        "target_path_map": _target_path_map(
            root_plan=root_plan,
            applied_root_actions=applied_root_actions,
            ops_visual_plan=ops_visual_plan,
            applied_ops_visual_actions=applied_ops_visual_actions,
        ),
        "path_ref_migration": path_ref_plan,
        "root_cleanup": root_plan,
        "study_visual_cleanup": study_visual_plan,
        "ops_visual_cleanup": ops_visual_plan,
        "applied_path_ref_updates": applied_path_ref_updates,
        "applied_root_actions": applied_root_actions,
        "applied_study_visual_actions": applied_study_visual_actions,
        "applied_ops_visual_actions": applied_ops_visual_actions,
        "validation": validation,
    }


def _validation(
    *,
    path_ref_plan: dict[str, Any],
    root_plan: dict[str, Any],
    study_visual_plan: dict[str, Any],
    ops_visual_plan: dict[str, Any],
) -> dict[str, Any]:
    blockers = dedupe(
        [
            *path_ref_plan.get("blockers", []),
            *root_plan.get("blockers", []),
            *study_visual_plan.get("blockers", []),
            *ops_visual_plan.get("blockers", []),
        ]
    )
    non_terminal_blockers = [
        blocker
        for blocker in blockers
        if blocker
        not in {
            "workspace_python_wrapper_uses_root_venv",
        }
    ]
    return {
        "pass": not non_terminal_blockers,
        "blockers": blockers,
        "non_terminal_blockers": non_terminal_blockers,
        "runtime_archive_current_truth": False,
        "runtime_quests_current_paper_truth": False,
        "root_paper_current_truth": False,
        "canonical_study_root_pattern": "studies/<study_id>",
        "active_runtime_provenance_roots": [
            action["source_relative_path"]
            for action in root_plan.get("root_actions") or []
            if action.get("decision") == "blocked_active_caller"
        ],
        "study_visual_clean_enabled": bool(study_visual_plan.get("enabled")),
        "ops_visual_clean_enabled": bool(ops_visual_plan.get("enabled")),
        "study_visual_locator_tails": [
            {
                "study_id": action.get("study_id"),
                "source": action.get("source_relative_path"),
                "role": action.get("role"),
                "blocker_id": action.get("blocker_id"),
            }
            for action in study_visual_plan.get("study_actions") or []
            if action.get("decision") == "keep_active_locator_tail"
        ],
        "legacy_ops_current_truth": False,
    }


def _write_manifest(*, workspace_root: Path, manifest: dict[str, Any], recorded_at: str) -> None:
    stamp = _stamp(recorded_at)
    manifest_root = workspace_root / MANIFEST_ROOT_RELPATH
    _write_json(manifest_root / "latest.json", manifest)
    _write_json(manifest_root / "history" / f"{stamp}.json", manifest)
    _write_json(workspace_root / REPORT_RELPATH, manifest)


def _legacy_provenance_map(
    *,
    root_plan: dict[str, Any],
    applied_root_actions: list[dict[str, Any]],
    ops_visual_plan: dict[str, Any],
    applied_ops_visual_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mapped = []
    all_actions = [
        *applied_root_actions,
        *(root_plan.get("root_actions") or []),
        *applied_ops_visual_actions,
        *(ops_visual_plan.get("ops_actions") or []),
    ]
    for action in all_actions:
        if action.get("decision") in {"archive", "blocked_active_caller", "blocked_until_path_refs_rewritten"}:
            mapped.append(
                {
                    "source": action.get("workspace_relative_path") or action.get("source_relative_path"),
                    "role": action.get("role"),
                    "current_truth": False,
                    "decision": action.get("decision"),
                    "target": action.get("target_relative_path"),
                    "blocker_id": action.get("blocker_id"),
                }
            )
    return mapped


def _target_path_map(
    *,
    root_plan: dict[str, Any],
    applied_root_actions: list[dict[str, Any]],
    ops_visual_plan: dict[str, Any],
    applied_ops_visual_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mapped = []
    all_actions = [
        *applied_root_actions,
        *(root_plan.get("root_actions") or []),
        *applied_ops_visual_actions,
        *(ops_visual_plan.get("ops_actions") or []),
    ]
    for action in all_actions:
        if action.get("target_relative_path"):
            mapped.append(
                {
                    "source": action.get("workspace_relative_path") or action.get("source_relative_path"),
                    "target": action.get("target_relative_path"),
                    "decision": action.get("decision"),
                    "role": action.get("role"),
                }
            )
    return mapped


def _path_ref_blockers(*, file_updates: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for update in file_updates:
        path = str(update["path"])
        replacements = int(update.get("replacement_count") or 0)
        if replacements <= 0:
            continue
        counts = dict(update.get("replacement_counts") or {})
        if counts.get("datasets_segment"):
            blockers.append("legacy_datasets_refs_remaining")
        if counts.get("portfolio_segment") or counts.get("portfolio_leaf"):
            blockers.append("legacy_portfolio_refs_remaining")
        if counts.get("root_refs_segment") or counts.get("relative_refs_segment") or counts.get("relative3_refs_segment") or counts.get("dm_cvd_refs_segment"):
            blockers.append("legacy_refs_refs_remaining")
        if counts.get("workspace_venv_ref"):
            blockers.append("legacy_root_venv_ref_remaining")
        if path:
            blockers.append("path_ref_migration_pending")
    return dedupe(blockers)


def _profile_ref_status(*, workspace_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "portfolio_root": _profile_root_ref(workspace_root=workspace_root, path=profile.portfolio_root),
        "studies_root": _profile_root_ref(workspace_root=workspace_root, path=profile.studies_root),
        "runtime_root": _profile_root_ref(workspace_root=workspace_root, path=profile.runtime_root),
    }


def _profile_root_ref(*, workspace_root: Path, path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    return {
        "absolute_path": str(resolved),
        "workspace_relative_path": relative_ref(workspace_root, resolved),
        "exists": resolved.exists(),
    }


def _ensure_target_roots(workspace_root: Path) -> None:
    for relpath in (
        Path("data"),
        Path("literature"),
        Path("memory"),
        Path("reports"),
        Path("archive"),
        MANIFEST_ROOT_RELPATH,
        LEGACY_ROOT_SURFACES_RELPATH,
    ):
        (workspace_root / relpath).mkdir(parents=True, exist_ok=True)


def _path_ref_candidates(*, workspace_root: Path, profile_path: Path) -> list[Path]:
    candidates: list[Path] = []
    for relpath in PATH_REF_ROOT_FILES:
        candidate = workspace_root / relpath
        if candidate.is_file():
            candidates.append(candidate)
    if profile_path.exists():
        candidates.append(profile_path)
    candidates.extend(_ops_active_source_files(workspace_root / "ops"))
    candidates.extend(_study_active_source_files(workspace_root / "studies"))
    return list(_dedupe_paths(candidates))


def _ops_active_source_files(ops_root: Path) -> list[Path]:
    if not ops_root.exists():
        return []
    return [
        path
        for path in sorted(ops_root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file() and _is_ops_active_source_file(path)
    ]


def _study_active_source_files(studies_root: Path) -> list[Path]:
    if not studies_root.exists():
        return []
    files: list[Path] = []
    for study_root in sorted((path for path in studies_root.iterdir() if path.is_dir()), key=lambda item: item.name):
        for filename in sorted(STUDY_ACTIVE_SOURCE_FILES):
            candidate = study_root / filename
            if candidate.is_file():
                files.append(candidate)
        analysis_root = study_root / "analysis"
        if analysis_root.exists():
            files.extend(
                path
                for path in sorted(analysis_root.rglob("*"), key=lambda item: item.as_posix())
                if path.is_file() and _is_analysis_active_source_file(path, analysis_root=analysis_root)
            )
    return files


def _is_ops_active_source_file(path: Path) -> bool:
    if _has_ignored_part(path):
        return False
    if any(part in PROVENANCE_REF_EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name == ".DS_Store":
        return False
    if path.suffix.lower() in OPS_ACTIVE_SOURCE_SUFFIXES:
        return True
    return path.parent.name == "bin" and "." not in path.name


def _is_analysis_active_source_file(path: Path, *, analysis_root: Path) -> bool:
    if _has_ignored_part(path):
        return False
    rel_parts = path.relative_to(analysis_root).parts
    if any(part in PROVENANCE_REF_EXCLUDED_PARTS for part in rel_parts):
        return False
    if path.name in PROVENANCE_REF_EXCLUDED_FILENAMES:
        return False
    if path.name in ANALYSIS_ACTIVE_SOURCE_FILENAMES:
        return True
    if path.suffix.lower() in {".py", ".sh", ".toml", ".yaml", ".yml"}:
        return bool(set(rel_parts[:-1]) & ANALYSIS_ACTIVE_SOURCE_DIRS)
    return False


def _has_ignored_part(path: Path) -> bool:
    return any(part in {".git", ".venv", "__pycache__"} for part in path.parts)


def _dedupe_paths(paths: list[Path]):
    seen: set[Path] = set()
    for path in paths:
        if path.suffix.lower() not in PATH_REF_EXTENSIONS and "." in path.name:
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        yield path


def _path_ref_replacement_rules(*, archive_stamp: str):
    archive_refs_root = f"archive/legacy_root_surfaces/{archive_stamp}/refs/"
    return [
        (
            rule_id,
            pattern,
            target.replace("archive/legacy_root_surfaces/refs/", archive_refs_root),
        )
        for rule_id, pattern, target in PATH_REF_RULES
    ]


def _rewrite_text_refs(text: str, *, archive_stamp: str) -> str:
    rewritten = text
    for _, pattern, target in _path_ref_replacement_rules(archive_stamp=archive_stamp):
        rewritten = pattern.sub(target, rewritten)
    return rewritten


def _replacement_counts(*, text: str) -> dict[str, int]:
    return {rule_id: len(pattern.findall(text)) for rule_id, pattern, _ in PATH_REF_RULES}


def _read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _action(
    source: Path,
    *,
    role: str,
    decision: str,
    target: Path | None = None,
    blocker_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    source_abs = logical_abs(source)
    workspace_root = source_abs.parent
    payload = {
        "source_relative_path": source.name,
        "absolute_path": str(source_abs),
        "exists": path_present(source),
        "kind": path_kind(source),
        "role": role,
        "decision": decision,
        "current_truth": decision == "keep_active_root",
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


def _expected_root_entries(actions: list[dict[str, Any]]) -> list[str]:
    entries = set(ACTIVE_ROOTS)
    for action in actions:
        if action.get("decision") in {"keep_active_root", "blocked_active_caller", "blocked_until_path_refs_rewritten", "blocked_unclassified_root"}:
            entries.add(str(action.get("source_relative_path") or ""))
    entries.discard("")
    return sorted(entries)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stamp(recorded_at: str) -> str:
    text = recorded_at.replace("+00:00", "Z")
    return re.sub(r"[^0-9A-Za-z]+", "", text)

__all__ = ["run_workspace_target_state_cleanup"]

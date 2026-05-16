from __future__ import annotations

import tomllib
from collections.abc import Sequence
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any, Iterable, Mapping

from med_autoscience.controllers.workspace_init_parts.retired_entries import (
    retired_file_cleanup_reason,
    retired_workspace_service_paths,
)
from med_autoscience.profiles import load_profile


SURFACE_KIND = "workspace_legacy_physical_cleanup_audit"
APPLY_SURFACE_KIND = "workspace_legacy_physical_cleanup_apply"
LEGACY_ROOT_RELPATH = Path("ops") / "med-deepscientist"
ARCHIVE_ROOT_RELPATH = Path("runtime") / "archives" / "legacy_mds"
CLEANUP_ROOT_RELPATH = Path("artifacts") / "runtime" / "legacy_physical_cleanup"
SCAN_GLOB_PATTERNS = (
    "artifacts/runtime/monolith_migration/latest.json",
    "artifacts/runtime/monolith_migration/history/*.json",
    "runtime/quests/*/quest.yaml",
    "runtime/quests/*/.ds/runtime_state.json",
    "studies/*/runtime_binding.yaml",
    "studies/*/manuscript/delivery_manifest.json",
    "studies/*/paper/delivery_manifest.json",
    "studies/*/paper/current_package/delivery_manifest.json",
    "studies/*/submission_minimal/delivery_manifest.json",
    "studies/*/artifacts/controller_decisions/latest.json",
    "studies/*/artifacts/publication_eval/latest.json",
    "studies/*/artifacts/controller/confirmation/latest.json",
    "studies/*/artifacts/controller_confirmation_summary.json",
)
PROVENANCE_REWRITE_GLOB_PATTERNS = (
    "AGENTS.md",
    "README.md",
    "artifacts/runtime/lifecycle_migration/**/*.json",
    "storage_audit/**/*.json",
    "studies/*/PLAN.md",
    "studies/*/study.yaml",
    "studies/*/manuscript/**/evidence_ledger.json",
    "studies/*/paper/**/evidence_ledger.json",
    "studies/*/artifacts/autonomy/ai_doctor_requests/*.json",
    "studies/*/artifacts/eval_hygiene/**/*.json",
    "studies/*/artifacts/runtime/runtime_supervision/**/*.json",
    "docs/superpowers/*.md",
    "docs/superpowers/**/*.md",
)
STRING_REPLACEMENT_KEYS = (
    "runtime_quests_root",
    "runtime_root",
    "legacy_root",
    "legacy_root_rel_slash",
    "legacy_root_rel",
)
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}
TEXT_FILE_SUFFIXES = {
    ".csv",
    ".env",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def build_workspace_legacy_physical_cleanup_audit(*, profile_path: Path) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    workspace_root = profile.workspace_root.expanduser().resolve()
    legacy_root = workspace_root / LEGACY_ROOT_RELPATH
    recorded_at = datetime.now(timezone.utc).isoformat()
    profile_payload = tomllib.loads(resolved_profile_path.read_text(encoding="utf-8"))
    profile_refs = _profile_reference_items(
        profile_payload=profile_payload,
        profile_path=resolved_profile_path,
        workspace_root=workspace_root,
        legacy_root=legacy_root,
    )
    workspace_refs = _workspace_reference_items(
        workspace_root=workspace_root,
        legacy_root=legacy_root,
    )
    all_refs = profile_refs + workspace_refs
    reference_counts = _count_by_key(all_refs, "reference_class")
    hard_blockers = sorted(
        {
            str(ref["cleanup_blocker"])
            for ref in all_refs
            if ref.get("cleanup_blocker")
        }
    )
    service_wrappers = _retired_service_wrapper_items(workspace_root)
    active_runtime_uses_legacy_root = _path_is_under(Path(profile.runtime_root), legacy_root) or _path_is_under(
        profile.managed_runtime_home,
        legacy_root,
    )
    replacement_ready = not active_runtime_uses_legacy_root and profile.managed_runtime_backend_id != "med_deepscientist"
    legacy_root_exists = legacy_root.exists()
    physical_root_allowed = legacy_root_exists and replacement_ready and not hard_blockers
    legacy_root_action = (
        "delete_safe_after_optional_external_snapshot"
        if physical_root_allowed
        else "blocked_archive_or_tombstone_required"
        if legacy_root_exists
        else "already_absent"
    )
    blockers = list(hard_blockers)
    if active_runtime_uses_legacy_root:
        blockers.append("active_profile_runtime_root_still_points_to_legacy_root")
    if legacy_root_exists and not all_refs:
        blockers = [item for item in blockers if item != "legacy_root_has_retained_references"]
    report: dict[str, Any] = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "audit_only",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(workspace_root),
        "authority_boundary": {
            "read_only": True,
            "writes_workspace": False,
            "paper_package_mutation": False,
            "publication_gate_mutation": False,
            "controller_decision_mutation": False,
            "runtime_sqlite_mutation": False,
            "physical_cleanup_performed": False,
        },
        "replacement_proof": {
            "active_runtime_root": str(profile.runtime_root),
            "active_managed_runtime_home": str(profile.managed_runtime_home),
            "active_runtime_uses_legacy_root": active_runtime_uses_legacy_root,
            "managed_runtime_backend_id": profile.managed_runtime_backend_id,
            "replacement_ready_for_cleanup_audit": replacement_ready,
        },
        "legacy_root_candidate": {
            "path": str(legacy_root),
            "exists": legacy_root_exists,
            "candidate_action": legacy_root_action,
            "physical_cleanup_allowed": physical_root_allowed,
            "blockers": sorted(set(blockers)),
            "reference_counts": reference_counts,
            "targeted_scan_patterns": list(SCAN_GLOB_PATTERNS),
            "provenance_rewrite_scan_patterns": list(PROVENANCE_REWRITE_GLOB_PATTERNS),
        },
        "reference_inventory": all_refs,
        "retired_workspace_service_wrappers": {
            "candidate_count": len(service_wrappers),
            "cleanup_ready_count": sum(1 for item in service_wrappers if item["candidate_action"] == "delete_safe"),
            "items": service_wrappers,
        },
        "next_required_action": _next_required_action(
            legacy_root_exists=legacy_root_exists,
            physical_root_allowed=physical_root_allowed,
            blockers=blockers,
            service_wrappers=service_wrappers,
        ),
        "opl_handoff_expectation": {
            "generic_runtime_owner": "one-person-lab",
            "mas_cleanup_role": "domain_authority_reference_audit_and_owner_receipt",
            "required_before_deleting_legacy_root": [
                "replacement proof remains available",
                "profile/runtime/artifact provenance refs are archived or tombstoned",
                "current truth and delivery refs no longer point at legacy physical paths",
                "focused cleanup tests and git diff --check pass",
            ],
        },
    }
    return report


def apply_workspace_legacy_physical_cleanup(*, profile_path: Path, apply: bool) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    pre_audit = build_workspace_legacy_physical_cleanup_audit(profile_path=resolved_profile_path)
    workspace_root = Path(str(pre_audit["workspace_root"]))
    legacy_root = Path(str(pre_audit["legacy_root_candidate"]["path"]))
    recorded_at = _utc_now()
    archive_root = _archive_root_for_apply(
        legacy_root=legacy_root,
        workspace_root=workspace_root,
        recorded_at=recorded_at,
    )
    replacement_map = _replacement_map(legacy_root=legacy_root, archive_root=archive_root)
    candidate_files = _candidate_rewrite_files(pre_audit)
    rewrite_plan = _build_rewrite_plan(
        candidate_files=candidate_files,
        replacements=replacement_map,
        workspace_root=workspace_root,
    )
    can_apply = _can_apply_archive_cleanup(pre_audit)
    report: dict[str, Any] = {
        "schema_version": 1,
        "surface_kind": APPLY_SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(workspace_root),
        "authority_boundary": {
            "reference_rewrite_only": True,
            "paper_package_mutation": False,
            "publication_gate_mutation": False,
            "paper_content_mutation": False,
            "runtime_sqlite_mutation": False,
            "generic_runtime_implementation": False,
        },
        "pre_audit_summary": {
            "legacy_root_exists": pre_audit["legacy_root_candidate"]["exists"],
            "physical_cleanup_allowed": pre_audit["legacy_root_candidate"]["physical_cleanup_allowed"],
            "blockers": list(pre_audit["legacy_root_candidate"]["blockers"]),
            "reference_counts": dict(pre_audit["legacy_root_candidate"]["reference_counts"]),
            "next_required_action": pre_audit["next_required_action"],
        },
        "archive_plan": {
            "legacy_root": str(legacy_root),
            "archive_root": str(archive_root),
            "legacy_root_exists": legacy_root.exists(),
            "archive_parent": str(archive_root.parent),
            "move_required": legacy_root.exists(),
            "preserves_content_by_move": legacy_root.exists(),
            "missing_root_tombstone_required": not legacy_root.exists(),
        },
        "replacement_map": {key: {"old": old, "new": new} for key, (old, new) in replacement_map.items()},
        "rewrite_plan": rewrite_plan,
        "can_apply": can_apply,
        "apply_blockers": [] if can_apply else _apply_blockers(pre_audit),
        "writes_performed": False,
    }
    if not apply:
        return report
    if not can_apply:
        report["status"] = "blocked"
        return report
    archive_result = _archive_legacy_root(
        legacy_root=legacy_root,
        archive_root=archive_root,
        recorded_at=str(report["recorded_at"]),
    )
    changed_files = _apply_rewrite_plan(rewrite_plan)
    post_audit = build_workspace_legacy_physical_cleanup_audit(profile_path=resolved_profile_path)
    report.update(
        {
            "status": "applied",
            "writes_performed": True,
            "archive_result": archive_result,
            "changed_files": changed_files,
            "post_audit_summary": {
                "legacy_root_exists": post_audit["legacy_root_candidate"]["exists"],
                "physical_cleanup_allowed": post_audit["legacy_root_candidate"]["physical_cleanup_allowed"],
                "blockers": list(post_audit["legacy_root_candidate"]["blockers"]),
                "reference_counts": dict(post_audit["legacy_root_candidate"]["reference_counts"]),
                "next_required_action": post_audit["next_required_action"],
            },
        }
    )
    _write_cleanup_report(report=report, workspace_root=workspace_root)
    return report


def _profile_reference_items(
    *,
    profile_payload: Mapping[str, Any],
    profile_path: Path,
    workspace_root: Path,
    legacy_root: Path,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in ("runtime_root", "managed_runtime_home", "med_deepscientist_runtime_root"):
        value = profile_payload.get(key)
        if isinstance(value, str):
            resolved = _resolve_path(value, profile_dir=profile_path.parent)
            if _path_is_under(resolved, legacy_root):
                reference_class = "active_profile_ref" if key in {"runtime_root", "managed_runtime_home"} else "legacy_profile_ref"
                items.append(
                    _reference_item(
                        path=profile_path,
                        workspace_root=workspace_root,
                        matched_value=str(resolved),
                        reference_class=reference_class,
                        cleanup_blocker=(
                            "active_profile_runtime_root_still_points_to_legacy_root"
                            if reference_class == "active_profile_ref"
                            else "legacy_root_has_retained_references"
                        ),
                    )
                )
    for table_name in ("source_provenance", "historical_fixture_ref", "explicit_archive_import_ref"):
        table = profile_payload.get(table_name)
        if not isinstance(table, Mapping):
            continue
        for key, value in table.items():
            if isinstance(value, str):
                resolved = _resolve_path(value, profile_dir=profile_path.parent)
                if _path_is_under(resolved, legacy_root):
                    items.append(
                        _reference_item(
                            path=profile_path,
                            workspace_root=workspace_root,
                            matched_value=str(resolved),
                            reference_class=f"profile_{table_name}",
                            cleanup_blocker="legacy_root_has_retained_references",
                            field=f"{table_name}.{key}",
                        )
                    )
    return items


def _can_apply_archive_cleanup(audit: Mapping[str, Any]) -> bool:
    replacement = audit.get("replacement_proof")
    if not isinstance(replacement, Mapping):
        return False
    if replacement.get("replacement_ready_for_cleanup_audit") is not True:
        return False
    wrappers = audit.get("retired_workspace_service_wrappers")
    if isinstance(wrappers, Mapping) and int(wrappers.get("cleanup_ready_count") or 0) > 0:
        return False
    return True


def _apply_blockers(audit: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    replacement = audit.get("replacement_proof")
    if not isinstance(replacement, Mapping) or replacement.get("replacement_ready_for_cleanup_audit") is not True:
        blockers.append("replacement_proof_not_ready")
    wrappers = audit.get("retired_workspace_service_wrappers")
    if isinstance(wrappers, Mapping) and int(wrappers.get("cleanup_ready_count") or 0) > 0:
        blockers.append("retired_workspace_service_wrappers_must_be_deleted_first")
    return blockers


def _replacement_map(*, legacy_root: Path, archive_root: Path) -> dict[str, tuple[str, str]]:
    legacy_rel = str(LEGACY_ROOT_RELPATH)
    archive_rel = str(archive_root)
    try:
        archive_rel = str(archive_root.relative_to(legacy_root.parents[1]))
    except ValueError:
        pass
    return {
        "runtime_quests_root": (str(legacy_root / "runtime" / "quests"), str(archive_root / "runtime" / "quests")),
        "runtime_root": (str(legacy_root / "runtime"), str(archive_root / "runtime")),
        "legacy_root": (str(legacy_root), str(archive_root)),
        "legacy_root_rel_slash": (f"{legacy_rel}/", f"{archive_rel}/"),
        "legacy_root_rel": (legacy_rel, archive_rel),
    }


def _candidate_rewrite_files(audit: Mapping[str, Any]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for item in audit.get("reference_inventory") or []:
        if not isinstance(item, Mapping):
            continue
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            continue
        path = Path(raw_path)
        if path in seen:
            continue
        seen.add(path)
        files.append(path)
    return files


def _build_rewrite_plan(
    *,
    candidate_files: Sequence[Path],
    replacements: Mapping[str, tuple[str, str]],
    workspace_root: Path,
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    ordered_replacements = [replacements[key] for key in STRING_REPLACEMENT_KEYS]
    for path in candidate_files:
        if not path.exists() or not path.is_file():
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rewritten = _rewrite_text(original, ordered_replacements)
        if rewritten == original:
            continue
        plan.append(
            {
                "path": str(path),
                "relpath": str(_relative_path(path, workspace_root)),
                "candidate_action": "rewrite_legacy_path_to_archive_ref",
                "replacements_applied": [
                    {"old": old, "new": new}
                    for old, new in ordered_replacements
                    if old in original
                ],
            }
        )
    return plan


def _apply_rewrite_plan(plan: Sequence[Mapping[str, Any]]) -> list[str]:
    changed: list[str] = []
    for item in plan:
        raw_path = item.get("path")
        replacements = item.get("replacements_applied")
        if not isinstance(raw_path, str) or not isinstance(replacements, list):
            continue
        path = Path(raw_path)
        text = path.read_text(encoding="utf-8")
        ordered = [
            (str(replacement["old"]), str(replacement["new"]))
            for replacement in replacements
            if isinstance(replacement, Mapping)
        ]
        rewritten = _rewrite_text(text, ordered)
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")
            changed.append(str(path))
    return changed


def _rewrite_text(text: str, replacements: Iterable[tuple[str, str]]) -> str:
    rewritten = text
    for old, new in replacements:
        rewritten = rewritten.replace(old, new)
    return rewritten


def _archive_legacy_root(*, legacy_root: Path, archive_root: Path, recorded_at: str) -> dict[str, Any]:
    archive_root.parent.mkdir(parents=True, exist_ok=True)
    if legacy_root.exists():
        if archive_root.exists():
            raise FileExistsError(f"archive root already exists: {archive_root}")
        shutil.move(str(legacy_root), str(archive_root))
        status = "moved"
    elif archive_root.exists() and _existing_tombstone_archive_root(legacy_root=legacy_root) == archive_root:
        status = "existing_archive_reused"
    else:
        archive_root.mkdir(parents=True, exist_ok=True)
        status = "legacy_root_absent_tombstone_created"
    tombstone_path = legacy_root.parent / "med-deepscientist.TOMBSTONE.json"
    tombstone_payload = {
        "schema_version": 1,
        "surface_kind": "legacy_mds_physical_root_tombstone",
        "recorded_at": recorded_at,
        "legacy_root": str(legacy_root),
        "archive_root": str(archive_root),
        "status": status,
        "active_runtime_owner": "mas_runtime_core",
        "legacy_role": "archived_historical_fixture_ref",
    }
    tombstone_path.parent.mkdir(parents=True, exist_ok=True)
    tombstone_path.write_text(_json_dumps(tombstone_payload), encoding="utf-8")
    return {"status": status, "archive_root": str(archive_root), "tombstone_path": str(tombstone_path)}


def _archive_root_for_apply(*, legacy_root: Path, workspace_root: Path, recorded_at: str) -> Path:
    existing = _existing_tombstone_archive_root(legacy_root=legacy_root)
    if existing is not None:
        return existing
    stamp = _history_stamp(recorded_at)
    return workspace_root / ARCHIVE_ROOT_RELPATH / stamp / "med-deepscientist"


def _existing_tombstone_archive_root(*, legacy_root: Path) -> Path | None:
    tombstone_path = legacy_root.parent / "med-deepscientist.TOMBSTONE.json"
    if not tombstone_path.exists():
        return None
    try:
        payload = json.loads(tombstone_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    archive_root = payload.get("archive_root")
    if not isinstance(archive_root, str) or not archive_root.strip():
        return None
    return Path(archive_root)


def _write_cleanup_report(*, report: Mapping[str, Any], workspace_root: Path) -> None:
    root = workspace_root / CLEANUP_ROOT_RELPATH
    history_root = root / "history"
    history_root.mkdir(parents=True, exist_ok=True)
    stamp = _history_stamp(str(report["recorded_at"]))
    history_path = history_root / f"{stamp}.json"
    latest_path = root / "latest.json"
    payload = dict(report)
    payload["history_path"] = str(history_path)
    payload["latest_path"] = str(latest_path)
    history_path.write_text(_json_dumps(payload), encoding="utf-8")
    latest_path.write_text(_json_dumps(payload), encoding="utf-8")


def _workspace_reference_items(*, workspace_root: Path, legacy_root: Path) -> list[dict[str, Any]]:
    needles = _legacy_needles(legacy_root)
    items: list[dict[str, Any]] = []
    for file_path in _iter_scan_files(workspace_root=workspace_root, legacy_root=legacy_root):
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        matched_value = next((needle for needle in needles if needle and needle in content), None)
        if matched_value is None:
            continue
        reference_class = _classify_reference_path(file_path, workspace_root=workspace_root)
        items.append(
            _reference_item(
                path=file_path,
                workspace_root=workspace_root,
                matched_value=matched_value,
                reference_class=reference_class,
                cleanup_blocker=_cleanup_blocker_for_reference(reference_class),
            )
        )
    return items


def _iter_scan_files(*, workspace_root: Path, legacy_root: Path) -> Iterable[Path]:
    yielded: set[Path] = set()
    for pattern in (*SCAN_GLOB_PATTERNS, *PROVENANCE_REWRITE_GLOB_PATTERNS):
        for path in workspace_root.glob(pattern):
            if path in yielded or not path.is_file():
                continue
            if _should_skip_scan_path(path=path, workspace_root=workspace_root, legacy_root=legacy_root):
                continue
            if not path.suffix or path.suffix.lower() in TEXT_FILE_SUFFIXES:
                yielded.add(path)
                yield path


def _classify_reference_path(path: Path, *, workspace_root: Path) -> str:
    relpath = _relative_path(path, workspace_root)
    parts = relpath.parts
    name = path.name
    if relpath == Path("AGENTS.md"):
        return "workspace_guidance_provenance_ref"
    if relpath == Path("README.md"):
        return "workspace_readme_provenance_ref"
    if parts[:3] == ("artifacts", "runtime", "monolith_migration"):
        return "migration_ledger_provenance_ref"
    if parts[:3] == ("artifacts", "runtime", "lifecycle_migration"):
        return "lifecycle_migration_provenance_ref"
    if parts and parts[0] == "storage_audit":
        return "storage_audit_provenance_ref"
    if len(parts) >= 5 and parts[0] == "studies" and parts[2:5] == (
        "artifacts",
        "runtime",
        "runtime_supervision",
    ):
        return "runtime_supervision_provenance_ref"
    if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "superpowers":
        return "historical_superpowers_doc_ref"
    if len(parts) >= 2 and parts[0] == "studies" and name in {"PLAN.md", "study.yaml"}:
        return "study_guidance_or_config_provenance_ref"
    if "evidence_ledger.json" in parts:
        return "paper_evidence_ledger_provenance_ref"
    if len(parts) >= 4 and parts[0] == "studies" and parts[2:4] == ("artifacts", "autonomy"):
        return "autonomy_request_provenance_ref"
    if len(parts) >= 4 and parts[0] == "studies" and parts[2:4] == ("artifacts", "eval_hygiene"):
        return "eval_hygiene_provenance_ref"
    if name in {"delivery_manifest.json", "latest.json"} and "controller_decisions" in parts:
        return "current_truth_or_controller_ref"
    if name == "delivery_manifest.json" or "current_package" in parts or "submission_minimal" in parts:
        return "current_truth_or_delivery_ref"
    if name in {"runtime_binding.yaml", "quest.yaml", "runtime_state.json"}:
        return "runtime_binding_or_snapshot_ref"
    if parts and parts[0] == "artifacts":
        return "artifact_or_controller_ref"
    return "workspace_reference_ref"


def _should_skip_scan_path(*, path: Path, workspace_root: Path, legacy_root: Path) -> bool:
    if _path_is_under(path, legacy_root):
        return True
    if _path_is_under(path, workspace_root / ARCHIVE_ROOT_RELPATH):
        return True
    if _path_is_under(path, workspace_root / CLEANUP_ROOT_RELPATH):
        return True
    if path.name == "med-deepscientist.TOMBSTONE.json":
        return True
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True
    relpath = _relative_path(path, workspace_root)
    parts = relpath.parts
    if ".ds" in parts:
        ds_index = parts.index(".ds")
        if len(parts) > ds_index + 1 and parts[ds_index + 1] in {
            "bash_exec",
            "codex_history",
            "codex_homes",
            "runs",
            "worktrees",
        }:
            return True
    return False


def _cleanup_blocker_for_reference(reference_class: str) -> str:
    if reference_class in {"current_truth_or_controller_ref", "current_truth_or_delivery_ref"}:
        return "current_truth_or_delivery_refs_still_point_to_legacy_root"
    if reference_class == "active_profile_ref":
        return "active_profile_runtime_root_still_points_to_legacy_root"
    return "legacy_root_has_retained_references"


def _retired_service_wrapper_items(workspace_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in retired_workspace_service_paths(workspace_root):
        reason = retired_file_cleanup_reason(path)
        items.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "cleanup_reason": reason,
                "candidate_action": (
                    "delete_safe"
                    if reason is not None
                    else "already_absent"
                    if not path.exists()
                    else "manual_review"
                ),
            }
        )
    return items


def _reference_item(
    *,
    path: Path,
    workspace_root: Path,
    matched_value: str,
    reference_class: str,
    cleanup_blocker: str,
    field: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path),
        "relpath": str(_relative_path(path, workspace_root)),
        "matched_value": matched_value,
        "reference_class": reference_class,
        "cleanup_blocker": cleanup_blocker,
    }
    if field is not None:
        item["field"] = field
    return item


def _legacy_needles(legacy_root: Path) -> tuple[str, ...]:
    root = str(legacy_root)
    runtime_root = str(legacy_root / "runtime")
    quests_root = str(legacy_root / "runtime" / "quests")
    return (quests_root, runtime_root, root, "/ops/med-deepscientist/", "ops/med-deepscientist")


def _resolve_path(raw_path: str, *, profile_dir: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = profile_dir / candidate
    return candidate.resolve()


def _path_is_under(path: Path, root: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(root.expanduser().resolve())
        return True
    except ValueError:
        return False


def _relative_path(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def _count_by_key(items: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _next_required_action(
    *,
    legacy_root_exists: bool,
    physical_root_allowed: bool,
    blockers: list[str],
    service_wrappers: list[Mapping[str, Any]],
) -> str:
    if legacy_root_exists and physical_root_allowed:
        return "delete_legacy_root_with_focused_verification"
    if legacy_root_exists and blockers:
        return "archive_or_tombstone_references_before_physical_delete"
    if blockers:
        return "rewrite_stale_legacy_refs_to_archive_or_tombstone"
    if any(item.get("candidate_action") == "delete_safe" for item in service_wrappers):
        return "delete_retired_workspace_service_wrappers"
    return "no_legacy_physical_cleanup_required"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_stamp(recorded_at: str) -> str:
    return recorded_at.replace("+00:00", "Z").replace("+0000", "Z").replace("-", "").replace(":", "").replace(".", "")


def _json_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n"


__all__ = [
    "apply_workspace_legacy_physical_cleanup",
    "build_workspace_legacy_physical_cleanup_audit",
]

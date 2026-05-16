from __future__ import annotations

import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.controllers.workspace_init_parts.retired_entries import (
    retired_file_cleanup_reason,
    retired_workspace_service_paths,
)
from med_autoscience.profiles import load_profile


SURFACE_KIND = "workspace_legacy_physical_cleanup_audit"
LEGACY_ROOT_RELPATH = Path("ops") / "med-deepscientist"
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
    for pattern in SCAN_GLOB_PATTERNS:
        for path in workspace_root.glob(pattern):
            if path in yielded or not path.is_file():
                continue
            if _path_is_under(path, legacy_root) or any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if not path.suffix or path.suffix.lower() in TEXT_FILE_SUFFIXES:
                yielded.add(path)
                yield path


def _classify_reference_path(path: Path, *, workspace_root: Path) -> str:
    relpath = _relative_path(path, workspace_root)
    parts = relpath.parts
    name = path.name
    if parts[:3] == ("artifacts", "runtime", "monolith_migration"):
        return "migration_ledger_provenance_ref"
    if name in {"delivery_manifest.json", "latest.json"} and "controller_decisions" in parts:
        return "current_truth_or_controller_ref"
    if name == "delivery_manifest.json" or "current_package" in parts or "submission_minimal" in parts:
        return "current_truth_or_delivery_ref"
    if name in {"runtime_binding.yaml", "quest.yaml", "runtime_state.json"}:
        return "runtime_binding_or_snapshot_ref"
    if parts and parts[0] == "artifacts":
        return "artifact_or_controller_ref"
    return "workspace_reference_ref"


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
    if any(item.get("candidate_action") == "delete_safe" for item in service_wrappers):
        return "delete_retired_workspace_service_wrappers"
    return "no_legacy_physical_cleanup_required"


__all__ = ["build_workspace_legacy_physical_cleanup_audit"]

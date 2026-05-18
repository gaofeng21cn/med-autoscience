from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
from typing import Any

from . import runtime_lifecycle_read_model
from .runtime_lifecycle_migration_parts import quest_git_cutover
from .runtime_lifecycle_contract import (
    FILE_AUTHORITY_SURFACES,
    MIGRATION_RUN_MODES,
    SCHEMA_VERSION,
    SQLITE_GITIGNORE_PATTERNS,
    WORKSPACE_CLASSIFICATIONS,
    validate_migration_ledger,
)


SURFACE_KIND = "runtime_lifecycle_migration_ledger"
LATEST_SURFACE_KIND = "runtime_lifecycle_migration_latest"
QUEST_GIT_INVENTORY_SURFACE_KIND = "quest_git_inventory"
QUEST_GIT_SCAN_ROOTS = (
    (Path("runtime") / "quests", "workspace_runtime_quests"),
    (Path("ops") / "med-deepscientist" / "runtime" / "quests", "med_deepscientist_runtime_quests"),
    (Path(".ds") / "worktrees", "legacy_ds_worktrees"),
)


def build_migration_ledger(
    *,
    workspace_root: Path,
    mode: str,
    workspace_classification: str,
    migration_run_id: str | None = None,
    quest_git_cutover_status: Mapping[str, Any] | None = None,
    quest_git_inventory: Iterable[Mapping[str, Any]] = (),
    legacy_import_retirement: Mapping[str, Any] | None = None,
    skipped_reasons: Iterable[str] = (),
    next_required_action: str | None = None,
    write: bool = False,
    write_lifecycle_export: bool = False,
    output_root: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    normalized_mode = _require_choice("mode", mode, MIGRATION_RUN_MODES)
    normalized_classification = _require_choice(
        "workspace_classification",
        workspace_classification,
        WORKSPACE_CLASSIFICATIONS,
    )
    started_at = _utc_now()
    run_id = migration_run_id or f"runtime-lifecycle-{_artifact_slug(started_at)}"
    ledger_root = (
        Path(output_root).expanduser().resolve()
        if output_root is not None
        else resolved_workspace_root / "artifacts" / "runtime" / "lifecycle_migration"
    )
    storage_audit = _read_json_mapping(resolved_workspace_root / "storage_audit" / "latest.json")
    inventory = runtime_lifecycle_read_model.build_lifecycle_inventory(workspace_root=resolved_workspace_root)
    git_tracking_check = _git_tracking_check(resolved_workspace_root)
    authority_surfaces = _authority_surfaces_checked(resolved_workspace_root)
    errors: list[dict[str, Any]] = []
    quest_git_cutover_record = quest_git_cutover.read_latest_quest_git_cutover_record(ledger_root=ledger_root)
    lifecycle_exports = _lifecycle_exports(
        workspace_root=resolved_workspace_root,
        ledger_root=ledger_root,
        enabled=write_lifecycle_export,
        errors=errors,
    )
    quest_git_inventory_items = tuple(quest_git_inventory)
    if not quest_git_inventory_items:
        quest_git_inventory_items = tuple(
            quest_git_cutover.merge_quest_git_cutover_record_items(
                inventory_items=build_quest_git_inventory(workspace_root=resolved_workspace_root)["items"],
                cutover_record=quest_git_cutover_record,
            )
        )
    if quest_git_cutover_status is None and quest_git_cutover_record:
        quest_git_cutover_status = quest_git_cutover.quest_git_cutover_status_from_record(quest_git_cutover_record)
    git_lifecycle_cutover = _git_lifecycle_cutover(
        quest_git_cutover_status=quest_git_cutover_status,
        quest_git_inventory=quest_git_inventory_items,
        legacy_import_retirement=legacy_import_retirement,
    )
    skipped_items = [
        *_skipped_items(
            skipped_reasons=tuple(skipped_reasons),
            git_tracking_check=git_tracking_check,
            storage_audit=storage_audit,
        ),
        *_quest_git_skipped_items(git_lifecycle_cutover["quest_git_inventory"]),
    ]
    payload: dict[str, Any] = {
        "surface_kind": SURFACE_KIND,
        "migration_run_id": run_id,
        "workspace_root": str(resolved_workspace_root),
        "workspace_id": resolved_workspace_root.name,
        "started_at": started_at,
        "finished_at": _utc_now(),
        "mode": normalized_mode,
        "schema_version": SCHEMA_VERSION,
        "tool_versions": {
            "runtime_lifecycle_contract_schema_version": SCHEMA_VERSION,
            "runtime_lifecycle_ledger_surface": SURFACE_KIND,
        },
        "workspace_classification": normalized_classification,
        "quest_classifications": _quest_classifications(storage_audit),
        "bucket_baseline": _bucket_baseline(storage_audit),
        "planned_actions": _planned_actions(storage_audit),
        "applied_actions": _applied_actions(storage_audit),
        "skipped_items": skipped_items,
        "lifecycle_exports": lifecycle_exports,
        "restore_proofs": _restore_proofs(storage_audit),
        "git_tracking_check": git_tracking_check,
        "git_lifecycle_cutover": git_lifecycle_cutover,
        "quest_git_cutover_record": quest_git_cutover_record,
        "authority_surfaces_checked": authority_surfaces,
        "errors": errors,
        "next_required_action": next_required_action
        or _default_next_required_action(
            skipped_items=skipped_items,
            inventory=inventory,
            git_lifecycle_cutover=git_lifecycle_cutover,
        ),
        "lifecycle_inventory": inventory,
    }
    payload["validation"] = validate_migration_ledger(payload)
    if write:
        payload["ledger_paths"] = _write_ledger(ledger_root=ledger_root, payload=payload)
    return payload


def build_quest_git_inventory(*, workspace_root: Path) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    storage_audit = _read_json_mapping(resolved_workspace_root / "storage_audit" / "latest.json")
    items_by_active_path: dict[str, dict[str, Any]] = {}
    _merge_quest_git_inventory_items(
        items_by_active_path,
        _active_quest_git_inventory_items(workspace_root=resolved_workspace_root),
    )
    _merge_quest_git_inventory_items(
        items_by_active_path,
        _restore_proof_quest_git_inventory_items(
            workspace_root=resolved_workspace_root,
            storage_audit=storage_audit,
        ),
    )

    items = sorted(items_by_active_path.values(), key=lambda item: (str(item.get("source") or ""), str(item.get("active_path") or "")))
    active_git_count = sum(1 for item in items if item["quest_git_present_in_active_path"])
    retired_count = sum(1 for item in items if item["quest_git_active_path_retired"])
    pending_count = sum(1 for item in items if item["status"] == "pending")
    return {
        "surface_kind": QUEST_GIT_INVENTORY_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "workspace_root": str(resolved_workspace_root),
        "generated_at": _utc_now(),
        "scan_roots": [
            {"path": str(resolved_workspace_root / relative_root), "source": source}
            for relative_root, source in QUEST_GIT_SCAN_ROOTS
        ],
        "items": items,
        "summary": {
            "item_count": len(items),
            "active_git_count": active_git_count,
            "retired_count": retired_count,
            "pending_count": pending_count,
        },
    }


def _active_quest_git_inventory_items(*, workspace_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for relative_root, source in QUEST_GIT_SCAN_ROOTS:
        quests_root = workspace_root / relative_root
        if not quests_root.is_dir():
            continue
        for git_path in sorted(path for path in quests_root.glob("*/.git") if path.exists()):
            active_path = git_path.parent
            items.append(
                _quest_git_inventory_item(
                    {
                        "source": source,
                        "quest_id": active_path.name,
                        "active_path": str(active_path),
                        "git_path": str(git_path),
                        "quest_git_present_in_active_path": True,
                        "quest_git_active_path_retired": False,
                        "status": "pending",
                        "action": "audit_only",
                        "skipped_reason": "active_quest_git_present",
                    }
                )
            )
    return items


def _restore_proof_quest_git_inventory_items(
    *,
    workspace_root: Path,
    storage_audit: Mapping[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for proof in _restore_proofs(storage_audit):
        quest_root = str(proof.get("quest_root") or "").strip()
        if not quest_root:
            continue
        active_path = _resolved_path_text(quest_root, workspace_root=workspace_root)
        archive_ref = str(proof.get("archive_path") or "").strip() or None
        proof_status = str(proof.get("status") or "").strip()
        items.append(
            _quest_git_inventory_item(
                {
                    "source": "restore_proof_archive_ref",
                    "study_id": proof.get("study_id"),
                    "quest_id": proof.get("quest_id") or Path(active_path).name,
                    "active_path": active_path,
                    "git_path": str(Path(active_path) / ".git"),
                    "quest_git_present_in_active_path": (Path(active_path) / ".git").exists(),
                    "archive_ref": archive_ref,
                    "restore_proof_path": proof.get("restore_proof_path"),
                    "projection_equivalence": proof_status or None,
                }
            )
        )
    return items


def _merge_quest_git_inventory_items(
    items_by_active_path: dict[str, dict[str, Any]],
    items: Iterable[Mapping[str, Any]],
) -> None:
    for item in items:
        normalized = _quest_git_inventory_item(item)
        active_path = str(normalized.get("active_path") or "")
        if not active_path:
            continue
        if active_path in items_by_active_path:
            items_by_active_path[active_path].update(
                {
                    "archive_ref": normalized.get("archive_ref"),
                    "restore_proof_path": normalized.get("restore_proof_path"),
                    "projection_equivalence": normalized.get("projection_equivalence"),
                }
            )
        else:
            items_by_active_path[active_path] = normalized


def cutover_quest_git_active_paths(
    *,
    workspace_root: Path,
    mode: str = "dry_run",
    migration_run_id: str | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    return quest_git_cutover.cutover_quest_git_active_paths(
        workspace_root=workspace_root,
        inventory_builder=lambda root: build_quest_git_inventory(workspace_root=root),
        schema_version=SCHEMA_VERSION,
        mode=mode,
        migration_run_id=migration_run_id,
        output_root=output_root,
    )


def validate_legacy_import_retirement(payload: Mapping[str, Any]) -> dict[str, Any]:
    required_true_fields = (
        "current_projects_cutover_verified",
        "old_readers_equivalent",
        "restore_import_diagnostic_retained",
        "default_legacy_reader_removed",
    )
    missing_true_fields = [field for field in required_true_fields if payload.get(field) is not True]
    disallowed_default_callers = [
        str(caller)
        for caller in payload.get("default_callers", ())
        if str(caller).strip() and str(caller).strip() not in {"none", "legacy_restore_import_diagnostic"}
    ]
    return {
        "allowed": not missing_true_fields and not disallowed_default_callers,
        "missing_true_fields": missing_true_fields,
        "disallowed_default_callers": disallowed_default_callers,
        "retained_scope": "legacy_restore_import_diagnostic",
    }


def _git_lifecycle_cutover(
    *,
    quest_git_cutover_status: Mapping[str, Any] | None,
    quest_git_inventory: tuple[Mapping[str, Any], ...],
    legacy_import_retirement: Mapping[str, Any] | None,
) -> dict[str, Any]:
    inventory = [_quest_git_inventory_item(item) for item in quest_git_inventory]
    unresolved = [
        item
        for item in inventory
        if item["quest_git_present_in_active_path"] or not item["quest_git_active_path_retired"]
    ]
    status_payload = dict(quest_git_cutover_status or {})
    explicit_verified = status_payload.get("status") == "verified" or status_payload.get("verified") is True
    cutover_verified = bool(explicit_verified and not unresolved)
    legacy_import_payload = dict(legacy_import_retirement or {})
    retirement_validation = validate_legacy_import_retirement(legacy_import_payload)
    retirement_allowed = cutover_verified and bool(retirement_validation["allowed"])
    if retirement_allowed:
        next_required_action = "Q6 complete: retain explicit archive import diagnostic only."
    elif cutover_verified:
        next_required_action = "Complete Q6 legacy import retirement guard before closing old reader paths."
    else:
        next_required_action = "Complete Q1-Q5 quest Git writer/read-model cutover, import/archive proof, and active-path retirement ledger."
    return {
        "surface_kind": "quest_git_lifecycle_cutover",
        "status": "verified" if cutover_verified else "pending",
        "quest_git_active_path_retired": cutover_verified,
        "quest_git_inventory": inventory,
        "unresolved_active_git_paths": unresolved,
        "legacy_import_retirement": {
            "allowed": retirement_allowed,
            "validation": retirement_validation,
            "requested": legacy_import_payload,
        },
        "next_required_action": next_required_action,
    }


def _quest_git_inventory_item(item: Mapping[str, Any]) -> dict[str, Any]:
    quest_id = _text(item.get("quest_id"))
    active_path = _quest_git_active_path_text(item)
    git_path = _quest_git_path_text(item, active_path=active_path)
    git_present = _quest_git_present(item, git_path=git_path)
    active_path_retired = _quest_git_active_path_retired(item, git_present=git_present)
    status = _quest_git_status(item, git_present=git_present, active_path_retired=active_path_retired)
    skipped_reason = _quest_git_skipped_reason(item, status=status, git_present=git_present)
    return {
        "source": item.get("source"),
        "quest_id": quest_id or (Path(active_path).name if active_path else None),
        "study_id": item.get("study_id"),
        "active_path": active_path or None,
        "git_path": git_path or None,
        "quest_git_present_in_active_path": git_present,
        "quest_git_active_path_retired": bool(active_path_retired),
        "archive_ref": item.get("archive_ref"),
        "restore_proof_path": item.get("restore_proof_path"),
        "projection_equivalence": item.get("projection_equivalence"),
        "status": status,
        "action": item.get("action") or ("audit_only" if status == "pending" else "none"),
        "skipped_reason": skipped_reason,
    }


def _quest_git_active_path_text(item: Mapping[str, Any]) -> str:
    return str(item.get("active_path") or item.get("quest_root") or "").strip()


def _quest_git_path_text(item: Mapping[str, Any], *, active_path: str) -> str:
    return str(item.get("git_path") or (f"{active_path}/.git" if active_path else "")).strip()


def _quest_git_present(item: Mapping[str, Any], *, git_path: str) -> bool:
    if "quest_git_present_in_active_path" in item:
        return bool(item.get("quest_git_present_in_active_path"))
    return bool(git_path and Path(git_path).expanduser().exists())


def _quest_git_active_path_retired(item: Mapping[str, Any], *, git_present: bool) -> bool:
    value = item.get("quest_git_active_path_retired")
    return not git_present if value is None else bool(value)


def _quest_git_status(
    item: Mapping[str, Any],
    *,
    git_present: bool,
    active_path_retired: bool,
) -> str:
    status = str(item.get("status") or "").strip()
    return status or ("pending" if git_present or not active_path_retired else "retired")


def _quest_git_skipped_reason(item: Mapping[str, Any], *, status: str, git_present: bool) -> Any:
    reason = item.get("skipped_reason")
    if reason or status != "pending":
        return reason
    return "active_quest_git_present" if git_present else "active_path_retirement_unverified"


def _quest_git_skipped_items(inventory: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    skipped: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str]] = set()
    for item in inventory:
        if not item.get("quest_git_present_in_active_path") and item.get("quest_git_active_path_retired") is True:
            continue
        reason = str(item.get("skipped_reason") or "active_path_retirement_unverified")
        key = (item.get("quest_id"), item.get("study_id"), reason)
        if key in seen:
            continue
        seen.add(key)
        skipped.append(
            {
                "scope": "quest_git",
                "quest_id": item.get("quest_id"),
                "study_id": item.get("study_id"),
                "reason": reason,
                "action": "audit_only",
            }
        )
    return skipped


def _lifecycle_exports(
    *,
    workspace_root: Path,
    ledger_root: Path,
    enabled: bool,
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not enabled:
        return []
    output_path = ledger_root / "lifecycle_exports" / "workspace_storage_audit.latest.json"
    try:
        export = runtime_lifecycle_read_model.export_lifecycle_projection(
            surface="workspace_storage_audit",
            export_format="json",
            workspace_root=workspace_root,
            output_path=output_path,
        )
    except Exception as exc:  # pragma: no cover - defensive surface for operator ledgers.
        errors.append(
            {
                "surface": "workspace_storage_audit",
                "error_kind": type(exc).__name__,
                "error": str(exc),
            }
        )
        return []
    return [
        {
            "surface": "workspace_storage_audit",
            "export_format": "json",
            "export_path": export["output_path"],
            "source_db_path": export["source_db_path"],
            "source_payload_sha256": export["source_payload_sha256"],
            "legacy_restore_import_used": export["legacy_restore_import_used"],
        }
    ]


def _bucket_baseline(storage_audit: Mapping[str, Any]) -> dict[str, Any]:
    if not storage_audit:
        return {
            "source": "storage_audit/latest.json",
            "status": "missing",
            "summary": {},
            "buckets": [],
        }
    categories = _mapping(storage_audit.get("categories"))
    buckets: list[dict[str, Any]] = []
    for name in sorted(categories):
        category = _mapping(categories.get(name))
        buckets.append(
            {
                "bucket_name": name,
                "bytes_before": _int(category.get("bytes")),
                "estimated_release_bytes": _int(category.get("estimated_release_bytes")),
                "actual_release_bytes": _int(category.get("actual_release_bytes")),
                "candidate_action": category.get("candidate_action"),
            }
        )
    return {
        "source": str(storage_audit.get("latest_report_path") or "storage_audit/latest.json"),
        "status": "ready",
        "recorded_at": storage_audit.get("recorded_at"),
        "mode": storage_audit.get("mode"),
        "summary": dict(_mapping(storage_audit.get("summary"))),
        "buckets": buckets,
    }


def _planned_actions(storage_audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    categories = _mapping(storage_audit.get("categories"))
    actions: list[dict[str, Any]] = []
    for name in sorted(categories):
        category = _mapping(categories.get(name))
        estimated_release_bytes = _int(category.get("estimated_release_bytes"))
        candidate_action = str(category.get("candidate_action") or "")
        if estimated_release_bytes <= 0 or candidate_action in {"", "keep-online"}:
            continue
        actions.append(
            {
                "bucket_name": name,
                "candidate_action": candidate_action,
                "estimated_release_bytes": estimated_release_bytes,
                "mode": storage_audit.get("mode") or "unknown",
            }
        )
    return actions


def _applied_actions(storage_audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    if storage_audit.get("mode") != "apply":
        return []
    categories = _mapping(storage_audit.get("categories"))
    actions: list[dict[str, Any]] = []
    for name in sorted(categories):
        category = _mapping(categories.get(name))
        actual_release_bytes = _int(category.get("actual_release_bytes"))
        if actual_release_bytes <= 0:
            continue
        actions.append(
            {
                "bucket_name": name,
                "candidate_action": category.get("candidate_action"),
                "actual_release_bytes": actual_release_bytes,
            }
        )
    return actions


def _restore_proofs(storage_audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    runtime_category = _mapping(_mapping(storage_audit.get("categories")).get("runtime"))
    studies = runtime_category.get("studies")
    if not isinstance(studies, list):
        return []
    proofs: list[dict[str, Any]] = []
    for study in studies:
        if not isinstance(study, Mapping):
            continue
        compaction = _mapping(study.get("restore_proof_compaction"))
        if not compaction:
            compaction = _mapping(_mapping(study.get("apply_result")).get("restore_proof_compaction"))
        restore_proof = _mapping(compaction.get("restore_proof"))
        archive_ref = _mapping(compaction.get("archive_ref"))
        restore_proof_path = str(compaction.get("restore_proof_path") or archive_ref.get("restore_proof_path") or "").strip()
        if not restore_proof_path and not restore_proof:
            continue
        proofs.append(
            {
                "study_id": study.get("study_id"),
                "quest_id": study.get("quest_id"),
                "quest_root": study.get("quest_root"),
                "status": restore_proof.get("status") or compaction.get("status") or "unknown",
                "restore_proof_path": restore_proof_path or None,
                "archive_path": archive_ref.get("archive_path") or restore_proof.get("archive_path"),
                "archive_sha256": archive_ref.get("sha256") or restore_proof.get("archive_sha256"),
                "source_file_count": _int(archive_ref.get("source_file_count") or restore_proof.get("source_file_count")),
                "verified_file_count": _int(restore_proof.get("verified_file_count")),
            }
        )
    return proofs


def _resolved_path_text(value: str, *, workspace_root: Path) -> str:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    return str(path.resolve())


def _quest_classifications(storage_audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    runtime_category = _mapping(_mapping(storage_audit.get("categories")).get("runtime"))
    studies = runtime_category.get("studies")
    if not isinstance(studies, list):
        return []
    result: list[dict[str, Any]] = []
    for study in studies:
        if not isinstance(study, Mapping):
            continue
        quest_runtime = _mapping(study.get("quest_runtime"))
        runtime = _mapping(study.get("runtime"))
        result.append(
            {
                "study_id": study.get("study_id"),
                "quest_id": study.get("quest_id"),
                "quest_root": study.get("quest_root"),
                "audit_status": study.get("status"),
                "runtime_status": quest_runtime.get("status"),
                "active_run_id": quest_runtime.get("active_run_id"),
                "classification": _classify_quest(study),
                "bytes_before": _int(runtime.get("bytes")),
                "candidate_action": runtime.get("candidate_action"),
                "estimated_release_bytes": _int(runtime.get("estimated_release_bytes")),
                "actual_release_bytes": _int(runtime.get("actual_release_bytes")),
            }
        )
    return result


def _classify_quest(study: Mapping[str, Any]) -> str:
    quest_runtime = _mapping(study.get("quest_runtime"))
    runtime_status = str(quest_runtime.get("status") or "").lower()
    audit_status = str(study.get("status") or "").lower()
    if runtime_status in {"running", "live", "active"}:
        return "live_active"
    if runtime_status in {"paused", "parked", "stopped"} or audit_status == "skipped_stopped_only":
        return "parked_controller_stop"
    if runtime_status in {"completed", "failed", "cancelled", "canceled"} and audit_status == "audited":
        return "stopped_cold"
    return "pinned_or_unknown_owner"


def _skipped_items(
    *,
    skipped_reasons: tuple[str, ...],
    git_tracking_check: Mapping[str, Any],
    storage_audit: Mapping[str, Any],
) -> list[dict[str, Any]]:
    reasons = [reason for reason in skipped_reasons if str(reason).strip()]
    if git_tracking_check.get("is_dirty"):
        reasons.append("dirty_workspace")
    if git_tracking_check.get("sidecar_gitignore_ok") is False:
        reasons.append("db_gitignore_missing")
    skipped: list[dict[str, Any]] = [
        {
            "scope": "workspace",
            "reason": reason,
            "action": "apply_blocked",
        }
        for reason in dict.fromkeys(reasons)
    ]
    for quest in _quest_classifications(storage_audit):
        if quest.get("classification") != "stopped_cold":
            skipped.append(
                {
                    "scope": "quest",
                    "quest_id": quest.get("quest_id"),
                    "study_id": quest.get("study_id"),
                    "reason": quest.get("classification"),
                    "action": "audit_only",
                }
            )
    return skipped


def _git_tracking_check(workspace_root: Path) -> dict[str, Any]:
    git_root = _git_output(["rev-parse", "--show-toplevel"], cwd=workspace_root)
    if git_root is None:
        return {
            "git_available": False,
            "workspace_root": str(workspace_root),
            "status_line_count": 0,
            "is_dirty": False,
            "sidecar_gitignore_ok": False,
            "sqlite_sidecars": [],
        }
    status_output = _git_output(["status", "--porcelain=v1"], cwd=workspace_root) or ""
    status_lines = [line for line in status_output.splitlines() if line.strip()]
    sidecars = [
        Path("artifacts/runtime/runtime_lifecycle.sqlite"),
        Path("artifacts/runtime/runtime_lifecycle.sqlite-wal"),
        Path("artifacts/runtime/runtime_lifecycle.sqlite-shm"),
    ]
    checks = [_sidecar_check(workspace_root=workspace_root, relative_path=path) for path in sidecars]
    return {
        "git_available": True,
        "git_root": git_root.strip(),
        "workspace_root": str(workspace_root),
        "status_line_count": len(status_lines),
        "status_samples": status_lines[:50],
        "is_dirty": bool(status_lines),
        "sqlite_gitignore_patterns": list(SQLITE_GITIGNORE_PATTERNS),
        "sidecar_gitignore_ok": all(check["ignored"] for check in checks),
        "sqlite_sidecars": checks,
    }


def _sidecar_check(*, workspace_root: Path, relative_path: Path) -> dict[str, Any]:
    ignored = _git_returncode(["check-ignore", str(relative_path)], cwd=workspace_root) == 0
    tracked = _git_returncode(["ls-files", "--error-unmatch", str(relative_path)], cwd=workspace_root) == 0
    path = workspace_root / relative_path
    return {
        "path": str(path),
        "relative_path": str(relative_path),
        "exists": path.exists(),
        "ignored": ignored,
        "tracked": tracked,
    }


def _authority_surfaces_checked(workspace_root: Path) -> list[dict[str, Any]]:
    studies_root = workspace_root / "studies"
    study_roots = sorted(path for path in studies_root.iterdir() if path.is_dir()) if studies_root.is_dir() else []
    return [
        {
            "surface": surface,
            "candidates_checked": [
                {
                    "path": str(path),
                    "exists": path.exists(),
                    "kind": "dir" if path.is_dir() else "file" if path.is_file() else "missing",
                }
                for path in _authority_candidate_paths(workspace_root, study_roots, surface)
            ],
        }
        for surface in FILE_AUTHORITY_SURFACES
    ]


def _authority_candidate_paths(workspace_root: Path, study_roots: list[Path], surface: str) -> list[Path]:
    if surface == "runtime_binding.yaml":
        return [workspace_root / "runtime_binding.yaml", workspace_root / "ops" / "medautoscience" / "runtime_binding.yaml"]
    if surface == ".ds/runtime_state.json":
        return [workspace_root / "ops" / "med-deepscientist" / "runtime" / ".ds" / "runtime_state.json"]
    if surface == "study_runtime_status":
        return [study / "artifacts" / "runtime" / "study_runtime_status" / "latest.json" for study in study_roots]
    if surface == "runtime_watch/latest.json":
        return [study / "artifacts" / "reports" / "runtime_watch" / "latest.json" for study in study_roots]
    if surface == "publication_eval/latest.json":
        return [study / "artifacts" / "publication_eval" / "latest.json" for study in study_roots]
    if surface == "controller_decisions/latest.json":
        return [study / "artifacts" / "controller_decisions" / "latest.json" for study in study_roots]
    if surface == "runtime_escalation_record.json":
        return [study / "artifacts" / "runtime" / "runtime_escalation_record.json" for study in study_roots]
    if surface == "dataset_manifest":
        return [workspace_root / "datasets" / "master" / "dataset_manifest.yaml"]
    if surface == "restore_index":
        return [workspace_root / "restore_index.json"]
    if surface == "paper":
        return [study / "paper" for study in study_roots]
    if surface == "manuscript/current_package":
        return [study / "manuscript" / "current_package" for study in study_roots]
    if surface == "current_package.zip":
        return [study / "manuscript" / "current_package.zip" for study in study_roots]
    return [workspace_root / surface]


def _write_ledger(*, ledger_root: Path, payload: Mapping[str, Any]) -> dict[str, str]:
    ledger_root.mkdir(parents=True, exist_ok=True)
    run_path = ledger_root / f"{payload['migration_run_id']}.json"
    latest_path = ledger_root / "latest.json"
    ledger_paths = {"ledger_path": str(run_path), "latest_path": str(latest_path)}
    run_payload = dict(payload)
    run_payload["ledger_paths"] = ledger_paths
    _write_json(run_path, run_payload)
    latest_pointer = {
        "surface_kind": LATEST_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "migration_run_id": payload["migration_run_id"],
        "workspace_root": payload["workspace_root"],
        "ledger_path": str(run_path),
        "finished_at": payload["finished_at"],
    }
    _write_json(latest_path, latest_pointer)
    return ledger_paths


def _default_next_required_action(
    *,
    skipped_items: list[dict[str, Any]],
    inventory: Mapping[str, Any],
    git_lifecycle_cutover: Mapping[str, Any],
) -> str:
    if git_lifecycle_cutover.get("status") != "verified":
        return str(git_lifecycle_cutover.get("next_required_action"))
    legacy_import = _mapping(git_lifecycle_cutover.get("legacy_import_retirement"))
    if legacy_import.get("allowed") is not True:
        return str(git_lifecycle_cutover.get("next_required_action"))
    reasons = {str(item.get("reason")) for item in skipped_items}
    if "db_gitignore_missing" in reasons:
        return "Backfill workspace .gitignore SQLite sidecar patterns, then rerun dry-run ledger before apply."
    if "dirty_workspace" in reasons:
        return "Resolve or explicitly classify existing workspace changes before apply."
    if inventory.get("status") != "ready":
        return "Run storage-audit dry-run to create the runtime lifecycle SQLite sidecar."
    return "Generate rollback plan and restore proof before any apply action."


def _read_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _git_output(args: list[str], *, cwd: Path) -> str | None:
    try:
        completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _git_returncode(args: list[str], *, cwd: Path) -> int:
    try:
        completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return 127
    return completed.returncode


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_choice(name: str, value: str, choices: Iterable[str]) -> str:
    normalized = str(value or "").strip()
    allowed = tuple(choices)
    if normalized not in allowed:
        raise ValueError(f"{name} must be one of {allowed}: {value!r}")
    return normalized


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+0000", "Z").replace("+00:00", "Z")


__all__ = [
    "SURFACE_KIND",
    "build_migration_ledger",
    "build_quest_git_inventory",
    "cutover_quest_git_active_paths",
    "validate_legacy_import_retirement",
]

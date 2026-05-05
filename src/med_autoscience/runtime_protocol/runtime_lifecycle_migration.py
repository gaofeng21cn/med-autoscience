from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
from typing import Any

from . import runtime_lifecycle_read_model
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


def build_migration_ledger(
    *,
    workspace_root: Path,
    mode: str,
    workspace_classification: str,
    migration_run_id: str | None = None,
    skipped_reasons: Iterable[str] = (),
    next_required_action: str | None = None,
    write: bool = False,
    write_compat_export: bool = False,
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
    compatibility_exports = _compatibility_exports(
        workspace_root=resolved_workspace_root,
        ledger_root=ledger_root,
        enabled=write_compat_export,
        errors=errors,
    )
    skipped_items = _skipped_items(
        skipped_reasons=tuple(skipped_reasons),
        git_tracking_check=git_tracking_check,
        storage_audit=storage_audit,
    )
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
        "compatibility_exports": compatibility_exports,
        "restore_proofs": [],
        "git_tracking_check": git_tracking_check,
        "authority_surfaces_checked": authority_surfaces,
        "errors": errors,
        "next_required_action": next_required_action
        or _default_next_required_action(skipped_items=skipped_items, inventory=inventory),
        "lifecycle_inventory": inventory,
    }
    payload["validation"] = validate_migration_ledger(payload)
    if write:
        payload["ledger_paths"] = _write_ledger(ledger_root=ledger_root, payload=payload)
    return payload


def _compatibility_exports(
    *,
    workspace_root: Path,
    ledger_root: Path,
    enabled: bool,
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not enabled:
        return []
    output_path = ledger_root / "compat_exports" / "workspace_storage_audit.latest.json"
    try:
        export = runtime_lifecycle_read_model.export_compatibility_projection(
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
            "compatibility_fallback_used": export["compatibility_fallback_used"],
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
    _write_json(run_path, payload)
    latest_pointer = {
        "surface_kind": LATEST_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "migration_run_id": payload["migration_run_id"],
        "workspace_root": payload["workspace_root"],
        "ledger_path": str(run_path),
        "finished_at": payload["finished_at"],
    }
    _write_json(latest_path, latest_pointer)
    return {"ledger_path": str(run_path), "latest_path": str(latest_path)}


def _default_next_required_action(*, skipped_items: list[dict[str, Any]], inventory: Mapping[str, Any]) -> str:
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


__all__ = ["SURFACE_KIND", "build_migration_ledger"]

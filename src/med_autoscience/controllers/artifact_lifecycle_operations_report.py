from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any
import os
import time

from med_autoscience.controllers.artifact_lifecycle_inventory import (
    ARTIFACT_ROLES,
    classify_artifact,
)
from med_autoscience.controllers.artifact_lifecycle_operations_report_parts.scan_policy import (
    CLASSIFIED_SCAN_MODE as _CLASSIFIED_SCAN_MODE,
    DEEP_STATISTICAL_SCAN_MODE as _DEEP_STATISTICAL_SCAN_MODE,
    DEFAULT_ARTIFACT_SAMPLE_LIMIT as _DEFAULT_ARTIFACT_SAMPLE_LIMIT,
    DEFAULT_MAX_FILES as _DEFAULT_MAX_FILES,
    DEFAULT_MAX_SECONDS as _DEFAULT_MAX_SECONDS,
    HARD_SKIPPED_DIR_NAMES as _HARD_SKIPPED_DIR_NAMES,
    NOISE_SCAN_MODE as _NOISE_SCAN_MODE,
    SKIPPED_SCAN_MODE as _SKIPPED_SCAN_MODE,
    SNAPSHOT_SCAN_MODE as _SNAPSHOT_SCAN_MODE,
    STATISTICAL_DIR_BUCKETS as _STATISTICAL_DIR_BUCKETS,
    STATISTICAL_RELATIVE_DIR_BUCKETS as _STATISTICAL_RELATIVE_DIR_BUCKETS,
    STATISTICAL_ROLE_LIFECYCLE_BY_BUCKET as _STATISTICAL_ROLE_LIFECYCLE_BY_BUCKET,
    STATISTICAL_STUDY_ARTIFACT_DIR_BUCKETS as _STATISTICAL_STUDY_ARTIFACT_DIR_BUCKETS,
    build_scan_policy as _build_scan_policy,
)
from med_autoscience.controllers.artifact_lifecycle_operations_report_parts.markdown import (
    render_lifecycle_operations_report_markdown,
)
from med_autoscience.controllers.artifact_lifecycle_operations_report_parts.operational_summary import (
    build_lifecycle_operational_summary,
)
from med_autoscience.runtime_protocol.workspace_artifacts import workspace_runtime_artifact_path
from med_autoscience.controllers.artifact_lifecycle_operations_report_parts.study_projection import (
    PROJECTION_SURFACES as _PROJECTION_SURFACES,
    aggregate_historical_backfill_plan_count as _aggregate_historical_backfill_plan_count,
    aggregate_projection_completeness as _aggregate_projection_completeness,
    build_study_projection_reports as _build_study_projection_reports,
    historical_backfill_plan_count as _historical_backfill_plan_count,
    projection_role_catalog as _projection_role_catalog,
    workspace_projection_completeness as _workspace_projection_completeness,
)
from med_autoscience.controllers.artifact_retention_operations_plan import (
    aggregate_artifact_retention_operations_plans,
    build_artifact_retention_operations_plan,
    compact_artifact_retention_operations_plan,
    retention_policy_catalog,
)
from med_autoscience.controllers.storage_governance_policy_kernel import build_storage_governance_policy_projection
from med_autoscience.controllers.storage_governance_history import build_storage_governance_history_projection


SCHEMA_VERSION = 1
SURFACE_KIND = "artifact_lifecycle_report"
_SOURCE_BUCKETS = (
    "runtime",
    "dataset",
    "cache",
    "delivery_projection",
    "audit_log",
    "canonical_source",
    "cold_archive",
    "other",
)


def run_lifecycle_operations_report(
    *,
    workspace_roots: Iterable[str | Path],
    deep: bool = False,
    max_files: int | None = None,
    max_seconds: float | None = None,
) -> dict[str, Any]:
    resolved_roots = sorted(_as_path(root) for root in workspace_roots)
    scan_policy = _build_scan_policy(deep=deep, max_files=max_files, max_seconds=max_seconds)
    workspaces = [_workspace_report(root, scan_policy=scan_policy) for root in resolved_roots]
    mutation_policy = _mutation_policy()
    summary = _aggregate_summary(workspaces)
    source_totals = _aggregate_source_totals(workspaces)
    retention_plan = _aggregate_retention_plan(workspaces)
    report = {
        "surface": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "report_kind": "artifact_lifecycle_operations_report",
        "workspace_count": len(workspaces),
        "mutation_policy": mutation_policy,
        "retention_policy_catalog": retention_policy_catalog(),
        "scan_policy": {
            "classified_scan_mode": _CLASSIFIED_SCAN_MODE,
            "noise_scan_mode": _NOISE_SCAN_MODE,
            "hard_skipped_directories": sorted(_HARD_SKIPPED_DIR_NAMES),
            "statistical_directories": sorted(_STATISTICAL_DIR_BUCKETS),
            **scan_policy,
        },
        "projection_role_catalog": _projection_role_catalog(),
        "summary": summary,
        "source_totals": source_totals,
        "retention_plan": retention_plan,
        "projection_completeness": _aggregate_projection_completeness(workspaces),
        "operational_summary": build_lifecycle_operational_summary(
            summary=summary,
            source_totals=source_totals,
            retention_plan=retention_plan,
            workspaces=workspaces,
            mutation_policy=mutation_policy,
        ),
        "historical_backfill_plan_count": _aggregate_historical_backfill_plan_count(workspaces),
        "workspaces": workspaces,
    }
    report["storage_governance_history"] = build_storage_governance_history_projection(
        workspaces=workspaces,
        summary=summary,
        source_totals=source_totals,
    )
    report["storage_governance_policy"] = build_storage_governance_policy_projection(lifecycle_report=report)
    return report


def _mutation_policy() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_workspace": False,
        "physical_cleanup_owned_by": "one-person-lab",
        "physical_cleanup_performed": False,
    }


def _workspace_report(workspace_root: Path, *, scan_policy: Mapping[str, Any]) -> dict[str, Any]:
    scan = _scan_workspace(workspace_root, scan_policy=scan_policy)
    study_roots = _discover_study_roots(workspace_root=workspace_root, paths=scan["classified_paths"])
    artifacts = _classify_workspace_artifacts(
        workspace_root=workspace_root,
        paths=scan["classified_paths"],
        study_roots=study_roots,
    )
    statistical_directories = scan["statistical_directories"]
    skipped_directories = scan["skipped_directories"]
    studies = _build_study_projection_reports(
        workspace_root=workspace_root,
        study_roots=study_roots,
        artifacts=artifacts,
        as_path=_as_path,
        is_relative_to=_is_relative_to,
        rel=_rel,
    )
    retention_plan = build_artifact_retention_operations_plan(
        workspace_root=workspace_root,
        artifacts=[*artifacts, *statistical_directories],
    )
    return {
        "workspace_root": str(workspace_root),
        "exists": workspace_root.exists(),
        "classified_artifact_count": len(artifacts),
        "statistical_directory_count": len(statistical_directories),
        "skipped_directory_count": len(skipped_directories),
        "summary": _workspace_summary(
            artifacts=artifacts,
            statistical_directories=statistical_directories,
        ),
        "source_totals": _workspace_source_totals(
            artifacts=artifacts,
            statistical_directories=statistical_directories,
        ),
        "retention_plan": compact_artifact_retention_operations_plan(retention_plan),
        "projection_completeness": _workspace_projection_completeness(studies),
        "historical_backfill_plan_count": _historical_backfill_plan_count(studies),
        "studies": studies,
        "artifact_listing": "bounded",
        "artifact_sample": artifacts[:_DEFAULT_ARTIFACT_SAMPLE_LIMIT],
        "artifact_sample_limit": _DEFAULT_ARTIFACT_SAMPLE_LIMIT,
        "artifact_sample_truncated": len(artifacts) > _DEFAULT_ARTIFACT_SAMPLE_LIMIT,
        "classified_scan_truncated": bool(scan.get("classified_scan_truncated")),
        "statistical_directories": statistical_directories,
        "skipped_directories": skipped_directories,
    }


def _scan_workspace(workspace_root: Path, *, scan_policy: Mapping[str, Any]) -> dict[str, Any]:
    classified_paths: list[Path] = []
    statistical_directories: list[dict[str, Any]] = []
    skipped_directories: list[dict[str, Any]] = []
    classified_scan_truncated = False
    classified_scan_deadline = time.monotonic() + float(scan_policy.get("max_seconds") or _DEFAULT_MAX_SECONDS)
    classified_scan_max_files = int(scan_policy.get("max_files") or _DEFAULT_MAX_FILES)
    deep_scan_enabled = bool(scan_policy.get("deep_scan_enabled"))
    if not workspace_root.exists():
        return {
            "classified_paths": classified_paths,
            "statistical_directories": statistical_directories,
            "skipped_directories": skipped_directories,
            "classified_scan_truncated": classified_scan_truncated,
        }
    for current_root, dirnames, filenames in os.walk(workspace_root):
        current_path = Path(current_root)
        if not _should_descend_directory(
            current_path,
            workspace_root=workspace_root,
            deep=deep_scan_enabled,
        ):
            dirnames[:] = []
            continue
        dirnames[:] = _kept_child_directories(
            current_path=current_path,
            dirnames=dirnames,
            workspace_root=workspace_root,
            scan_policy=scan_policy,
            statistical_directories=statistical_directories,
            skipped_directories=skipped_directories,
        )
        if _should_scan_classified_files(
            current_path,
            workspace_root=workspace_root,
            deep=deep_scan_enabled,
        ):
            classified_scan_truncated = _append_classified_files(
                current_path=current_path,
                filenames=filenames,
                classified_paths=classified_paths,
                deep=deep_scan_enabled,
                max_files=classified_scan_max_files,
                deadline=classified_scan_deadline,
            )
        if classified_scan_truncated:
            dirnames[:] = []
            break
    return {
        "classified_paths": sorted(classified_paths),
        "statistical_directories": sorted(
            statistical_directories,
            key=lambda item: str(item.get("workspace_relative_path") or ""),
        ),
        "skipped_directories": sorted(
            skipped_directories,
            key=lambda item: str(item.get("workspace_relative_path") or ""),
        ),
        "classified_scan_truncated": classified_scan_truncated,
    }


def _kept_child_directories(
    *,
    current_path: Path,
    dirnames: list[str],
    workspace_root: Path,
    scan_policy: Mapping[str, Any],
    statistical_directories: list[dict[str, Any]],
    skipped_directories: list[dict[str, Any]],
) -> list[str]:
    kept_dirnames: list[str] = []
    for dirname in sorted(dirnames):
        directory = current_path / dirname
        source_bucket = _statistical_source_bucket(directory, workspace_root=workspace_root)
        if source_bucket is not None:
            statistical_directories.append(
                _statistical_directory_report(
                    directory=directory,
                    workspace_root=workspace_root,
                    source_bucket=source_bucket,
                    scan_policy=scan_policy,
                )
            )
        elif dirname in _HARD_SKIPPED_DIR_NAMES:
            skipped_directories.append(_skipped_directory_report(directory, workspace_root=workspace_root))
        else:
            kept_dirnames.append(dirname)
    return kept_dirnames


def _skipped_directory_report(directory: Path, *, workspace_root: Path) -> dict[str, Any]:
    return {
        "path": str(directory.resolve()),
        "workspace_relative_path": _rel(directory, workspace_root),
        "scan_mode": _SKIPPED_SCAN_MODE,
        "source_bucket": "other",
        "reason": "noise_directory_skipped",
    }


def _append_classified_files(
    *,
    current_path: Path,
    filenames: list[str],
    classified_paths: list[Path],
    deep: bool,
    max_files: int,
    deadline: float,
) -> bool:
    truncated = False
    for filename in sorted(filenames):
        if _classified_scan_exhausted(
            deep=deep,
            classified_count=len(classified_paths),
            max_files=max_files,
            deadline=deadline,
        ):
            truncated = True
            break
        candidate = current_path / filename
        if candidate.is_file() and not candidate.is_symlink():
            classified_paths.append(candidate.resolve())
    return truncated


def _classified_scan_exhausted(*, deep: bool, classified_count: int, max_files: int, deadline: float) -> bool:
    return bool(deep and (classified_count >= max_files or time.monotonic() > deadline))


def _should_descend_directory(current_path: Path, *, workspace_root: Path, deep: bool) -> bool:
    relative_parts = _relative_parts(current_path, workspace_root)
    return deep or (
        _study_artifact_source_bucket(relative_parts) is None
        and (
            len(relative_parts) <= 1
            or relative_parts[0] in {"studies", "papers"}
            or any(_is_prefix(relative_parts, candidate) for candidate in _STATISTICAL_RELATIVE_DIR_BUCKETS)
        )
    )


def _should_scan_classified_files(current_path: Path, *, workspace_root: Path, deep: bool) -> bool:
    relative_parts = _relative_parts(current_path, workspace_root)
    return deep or (
        _study_artifact_source_bucket(relative_parts) is None
        and (len(relative_parts) <= 1 or relative_parts[0] in {"studies", "papers"})
    )


def _statistical_source_bucket(directory: Path, *, workspace_root: Path) -> str | None:
    relative_parts = _relative_parts(directory, workspace_root)
    return (
        _STATISTICAL_DIR_BUCKETS.get(directory.name)
        or _STATISTICAL_RELATIVE_DIR_BUCKETS.get(relative_parts)
        or _study_artifact_source_bucket(relative_parts)
    )


def _study_artifact_source_bucket(relative_parts: tuple[str, ...]) -> str | None:
    if len(relative_parts) < 4 or relative_parts[0] not in {"studies", "papers"}:
        return None
    return _STATISTICAL_STUDY_ARTIFACT_DIR_BUCKETS.get(relative_parts[2:])


def _is_prefix(prefix: tuple[str, ...], parts: tuple[str, ...]) -> bool:
    return len(prefix) <= len(parts) and parts[: len(prefix)] == prefix


def _classify_workspace_artifacts(
    *,
    workspace_root: Path,
    paths: Iterable[Path],
    study_roots: Iterable[Path],
) -> list[dict[str, Any]]:
    roots = tuple(sorted({_as_path(root) for root in study_roots}, key=lambda path: len(path.parts), reverse=True))
    artifacts: list[dict[str, Any]] = []
    for path in paths:
        study_root = _study_root_for_path(path=path, study_roots=roots, workspace_root=workspace_root)
        artifact = classify_artifact(path=path, study_root=study_root)
        role = str(artifact.get("role") or "")
        lifecycle = str(artifact.get("lifecycle") or "")
        size_bytes = _file_size(path)
        artifacts.append(
            {
                **artifact,
                "workspace_relative_path": _rel(path, workspace_root),
                "study_root": str(study_root),
                "study_id": _study_id_for_root(study_root, workspace_root),
                "size_bytes": size_bytes,
                "scan_mode": _CLASSIFIED_SCAN_MODE,
                "source_bucket": _source_bucket_for_artifact(role=role, lifecycle=lifecycle, path=path),
            }
        )
    return sorted(artifacts, key=lambda item: str(item.get("workspace_relative_path") or ""))


def _statistical_directory_report(
    *,
    directory: Path,
    workspace_root: Path,
    source_bucket: str,
    scan_policy: Mapping[str, Any],
) -> dict[str, Any]:
    role, lifecycle = _STATISTICAL_ROLE_LIFECYCLE_BY_BUCKET.get(source_bucket, ("cache", "cache_transient"))
    snapshot = _storage_snapshot_for_directory(
        workspace_root=workspace_root,
        directory=directory,
        source_bucket=source_bucket,
    )
    if snapshot is not None and not bool(scan_policy.get("deep_scan_enabled")):
        return {
            "path": str(directory.resolve()),
            "workspace_relative_path": _rel(directory, workspace_root),
            "source_bucket": source_bucket,
            "role": role,
            "lifecycle": lifecycle,
            "scan_mode": _SNAPSHOT_SCAN_MODE,
            "source_snapshot": snapshot["source_snapshot"],
            "size_bytes": snapshot["bytes"],
            "file_count": snapshot["file_count"],
            "directory_count": snapshot["directory_count"],
            "cleanup_candidate_action": "audit-only",
            "cleanup_blockers": [
                "snapshot_reference_no_physical_cleanup_contract",
            ],
        }
    stats = _tree_stats(
        directory,
        deep=bool(scan_policy.get("deep_scan_enabled")),
        max_files=int(scan_policy.get("max_files") or _DEFAULT_MAX_FILES),
        max_seconds=float(scan_policy.get("max_seconds") or _DEFAULT_MAX_SECONDS),
    )
    scan_mode = _DEEP_STATISTICAL_SCAN_MODE if bool(scan_policy.get("deep_scan_enabled")) else _NOISE_SCAN_MODE
    return {
        "path": str(directory.resolve()),
        "workspace_relative_path": _rel(directory, workspace_root),
        "source_bucket": source_bucket,
        "role": role,
        "lifecycle": lifecycle,
        "scan_mode": scan_mode,
        "size_bytes": stats["bytes"],
        "file_count": stats["file_count"],
        "directory_count": stats["directory_count"],
        "bounded": bool(scan_policy.get("deep_scan_enabled")),
        "truncated": bool(stats["truncated"]),
        "cleanup_candidate_action": "audit-only",
        "cleanup_blockers": [
            "statistical_only_no_physical_cleanup_contract",
        ],
    }


def _tree_stats(
    root: Path,
    *,
    deep: bool = False,
    max_files: int = _DEFAULT_MAX_FILES,
    max_seconds: float = _DEFAULT_MAX_SECONDS,
) -> dict[str, int | bool]:
    total_bytes = 0
    file_count = 0
    directory_count = 0
    truncated = False
    deadline = time.monotonic() + max(0.0, max_seconds)
    for current_root, dirnames, filenames in os.walk(root):
        directory_count += 1
        dirnames[:] = [name for name in dirnames if name not in _HARD_SKIPPED_DIR_NAMES]
        if not deep:
            dirnames[:] = []
        for filename in filenames:
            if deep and (file_count >= max_files or time.monotonic() > deadline):
                truncated = True
                break
            candidate = Path(current_root) / filename
            if candidate.is_symlink():
                continue
            try:
                stat = candidate.stat()
            except OSError:
                continue
            file_count += 1
            total_bytes += int(stat.st_size)
        if truncated:
            break
    return {
        "bytes": total_bytes,
        "file_count": file_count,
        "directory_count": directory_count,
        "truncated": truncated,
    }


def _storage_snapshot_for_directory(
    *,
    workspace_root: Path,
    directory: Path,
    source_bucket: str,
) -> dict[str, Any] | None:
    for snapshot_path in _storage_snapshot_paths(workspace_root):
        payload = _read_json(snapshot_path)
        snapshot = _snapshot_bucket_stats(payload, source_bucket)
        if snapshot is None:
            continue
        return {
            **snapshot,
            "source_snapshot": _rel(snapshot_path, workspace_root),
        }
    return None


def _storage_snapshot_paths(workspace_root: Path) -> tuple[Path, ...]:
    return (
        workspace_root / "storage_audit" / "latest.json",
        workspace_runtime_artifact_path(workspace_root, "runtime_storage", "latest.json"),
        workspace_runtime_artifact_path(workspace_root, "storage_audit_latest.json"),
    )


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _snapshot_bucket_stats(payload: Mapping[str, Any], source_bucket: str) -> dict[str, int] | None:
    for candidate in _snapshot_bucket_candidates(payload, source_bucket):
        snapshot = _coerce_snapshot_bucket_stats(candidate)
        if snapshot is not None:
            return snapshot
    return None


def _snapshot_bucket_candidates(payload: Mapping[str, Any], source_bucket: str) -> list[Mapping[str, Any]]:
    candidates: list[Mapping[str, Any]] = []
    direct = payload.get(source_bucket)
    if isinstance(direct, Mapping):
        candidates.append(direct)
    totals = payload.get("source_totals")
    if isinstance(totals, Mapping) and isinstance(totals.get(source_bucket), Mapping):
        candidates.append(totals[source_bucket])
    summary = payload.get("summary")
    if isinstance(summary, Mapping) and source_bucket == "runtime":
        runtime = summary.get("runtime")
        if isinstance(runtime, Mapping):
            candidates.append(runtime)
    return candidates


def _coerce_snapshot_bucket_stats(candidate: Mapping[str, Any]) -> dict[str, int] | None:
    bytes_count = _first_int(candidate, ("bytes", "size_bytes", "total_bytes"))
    file_count = _first_int(candidate, ("file_count", "files", "total_files_count"))
    if bytes_count is None or file_count is None:
        return None
    return {
        "bytes": bytes_count,
        "file_count": file_count,
        "directory_count": _first_int(candidate, ("directory_count", "directories", "dir_count")) or 0,
    }


def _first_int(payload: Mapping[str, Any], keys: Iterable[str]) -> int | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _workspace_summary(
    *,
    artifacts: Iterable[Mapping[str, Any]],
    statistical_directories: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    artifact_list = [dict(item) for item in artifacts]
    statistical_list = [dict(item) for item in statistical_directories]
    classified_bytes = sum(int(item.get("size_bytes") or 0) for item in artifact_list)
    statistical_bytes = sum(int(item.get("size_bytes") or 0) for item in statistical_list)
    return {
        "total_bytes": classified_bytes + statistical_bytes,
        "classified_bytes": classified_bytes,
        "statistical_bytes": statistical_bytes,
        "classified_file_count": len(artifact_list),
        "statistical_file_count": sum(int(item.get("file_count") or 0) for item in statistical_list),
        "role_counts": _role_counts(artifact_list, statistical_list),
        "lifecycle_counts": _lifecycle_counts(artifact_list, statistical_list),
        "authority_blocker_counts": _blocker_counts(artifact_list, "authority_blockers"),
        "cleanup_blocker_counts": _blocker_counts(artifact_list + statistical_list, "cleanup_blockers"),
    }


def _aggregate_summary(workspaces: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    totals = {
        "total_bytes": 0,
        "classified_bytes": 0,
        "statistical_bytes": 0,
        "classified_file_count": 0,
        "statistical_file_count": 0,
        "role_counts": {},
        "lifecycle_counts": {},
        "authority_blocker_counts": {},
        "cleanup_blocker_counts": {},
    }
    for workspace in workspaces:
        summary = dict(workspace.get("summary") or {})
        for key in ("total_bytes", "classified_bytes", "statistical_bytes", "classified_file_count", "statistical_file_count"):
            totals[key] += int(summary.get(key) or 0)
        for key in ("role_counts", "lifecycle_counts", "authority_blocker_counts", "cleanup_blocker_counts"):
            _merge_counts(totals[key], dict(summary.get(key) or {}))
    return totals


def _workspace_source_totals(
    *,
    artifacts: Iterable[Mapping[str, Any]],
    statistical_directories: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    totals = _empty_source_totals()
    for item in artifacts:
        bucket = str(item.get("source_bucket") or "other")
        _add_source_total(
            totals,
            bucket=bucket,
            bytes_count=int(item.get("size_bytes") or 0),
            file_count=1,
            classified_count=1,
            statistical_count=0,
            scan_mode=_CLASSIFIED_SCAN_MODE,
        )
    for item in statistical_directories:
        bucket = str(item.get("source_bucket") or "other")
        _add_source_total(
            totals,
            bucket=bucket,
            bytes_count=int(item.get("size_bytes") or 0),
            file_count=int(item.get("file_count") or 0),
            classified_count=0,
            statistical_count=1,
            scan_mode=str(item.get("scan_mode") or _NOISE_SCAN_MODE),
        )
    return totals


def _aggregate_source_totals(workspaces: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    totals = _empty_source_totals()
    for workspace in workspaces:
        for bucket, source_total in dict(workspace.get("source_totals") or {}).items():
            if not isinstance(source_total, Mapping):
                continue
            _add_source_total(
                totals,
                bucket=bucket,
                bytes_count=int(source_total.get("bytes") or 0),
                file_count=int(source_total.get("file_count") or 0),
                classified_count=int(source_total.get("classified_file_count") or 0),
                statistical_count=int(source_total.get("statistical_directory_count") or 0),
                scan_mode=str(source_total.get("scan_mode") or ""),
            )
    return totals


def _aggregate_retention_plan(workspaces: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return aggregate_artifact_retention_operations_plans(
        dict(workspace.get("retention_plan") or {}) for workspace in workspaces
    )


def _empty_source_totals() -> dict[str, Any]:
    return {
        bucket: {
            "bytes": 0,
            "file_count": 0,
            "classified_file_count": 0,
            "statistical_directory_count": 0,
            "scan_mode": "none",
        }
        for bucket in _SOURCE_BUCKETS
    }


def _add_source_total(
    totals: dict[str, Any],
    *,
    bucket: str,
    bytes_count: int,
    file_count: int,
    classified_count: int,
    statistical_count: int,
    scan_mode: str,
) -> None:
    if bucket not in totals:
        bucket = "other"
    total = totals[bucket]
    total["bytes"] += bytes_count
    total["file_count"] += file_count
    total["classified_file_count"] += classified_count
    total["statistical_directory_count"] += statistical_count
    total["scan_mode"] = _merge_scan_modes(str(total.get("scan_mode") or ""), scan_mode)


def _merge_scan_modes(left: str, right: str) -> str:
    modes = {mode for mode in (left, right) if mode and mode != "none"}
    if not modes:
        return "none"
    if len(modes) == 1:
        return next(iter(modes))
    return "mixed"


def _role_counts(
    artifacts: Iterable[Mapping[str, Any]],
    statistical_directories: Iterable[Mapping[str, Any]],
) -> dict[str, int]:
    counts = {role: 0 for role in ARTIFACT_ROLES}
    for item in list(artifacts) + list(statistical_directories):
        role = str(item.get("role") or "")
        if role in counts:
            counts[role] += int(item.get("file_count") or 1)
    return counts


def _lifecycle_counts(
    artifacts: Iterable[Mapping[str, Any]],
    statistical_directories: Iterable[Mapping[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in list(artifacts) + list(statistical_directories):
        lifecycle = str(item.get("lifecycle") or "")
        if not lifecycle:
            continue
        counts[lifecycle] = counts.get(lifecycle, 0) + int(item.get("file_count") or 1)
    return counts


def _blocker_counts(items: Iterable[Mapping[str, Any]], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for blocker in item.get(field_name) or []:
            key = str(blocker)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _merge_counts(target: dict[str, int], source: Mapping[str, Any]) -> None:
    for key, value in source.items():
        target[str(key)] = target.get(str(key), 0) + int(value or 0)


def _discover_study_roots(*, workspace_root: Path, paths: Iterable[Path]) -> tuple[Path, ...]:
    roots: set[Path] = set()
    for container_name in ("studies", "papers"):
        container = workspace_root / container_name
        if container.exists():
            roots.update(child.resolve() for child in container.iterdir() if child.is_dir())
    for path in paths:
        relative_parts = _relative_parts(path, workspace_root)
        for container_name in ("studies", "papers"):
            if container_name not in relative_parts:
                continue
            index = relative_parts.index(container_name)
            if index + 1 < len(relative_parts):
                roots.add((workspace_root / Path(*relative_parts[: index + 2])).resolve())
    if not roots:
        roots.add(workspace_root)
    return tuple(sorted(roots))


def _study_root_for_path(*, path: Path, study_roots: Iterable[Path], workspace_root: Path) -> Path:
    for root in study_roots:
        if _is_relative_to(path, root):
            return root
    return workspace_root


def _source_bucket_for_artifact(*, role: str, lifecycle: str, path: Path) -> str:
    if role == "runtime_ephemeral":
        return "runtime"
    if role == "data_release":
        return "dataset"
    if role in {"derived_projection", "human_handoff_mirror"}:
        return "delivery_projection"
    if role == "audit_log":
        return "audit_log"
    if role == "canonical_source":
        return "canonical_source"
    if role == "cold_archive":
        return "cold_archive"
    if "cache" in path.parts:
        return "cache"
    if lifecycle == "rebuildable_projection":
        return "delivery_projection"
    return "other"


def _file_size(path: Path) -> int:
    try:
        return int(path.stat().st_size)
    except OSError:
        return 0


def _study_id_for_root(study_root: Path, workspace_root: Path) -> str:
    if study_root == workspace_root:
        return workspace_root.name
    return study_root.name


def _as_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _relative_parts(path: Path, root: Path) -> tuple[str, ...]:
    try:
        return path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return path.resolve().parts


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


__all__ = ["SCHEMA_VERSION", "SURFACE_KIND", "render_lifecycle_operations_report_markdown", "run_lifecycle_operations_report"]

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
import shutil
import tarfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import load_profile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout
from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    file_sha256,
    restore_proof,
    safe_artifact_id,
    write_json,
)


SURFACE_KIND = "legacy_ds_retirement"
ARCHIVE_RETENTION_SURFACE_KIND = "legacy_ds_archive_body_retention"
SCHEMA_VERSION = 1


def run_legacy_ds_retirement(
    *,
    profile_path: Path,
    apply: bool,
    archive_retention: bool = False,
    archive_retention_apply: bool = False,
    archive_retention_min_mb: int = 16,
    archive_retention_cold_store_root: Path | None = None,
) -> dict[str, Any]:
    if archive_retention_apply and not archive_retention:
        raise ValueError("archive_retention_apply requires archive_retention")
    if archive_retention_apply and not apply:
        raise ValueError("archive_retention_apply requires apply mode")
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    workspace_root = profile.workspace_root.expanduser().resolve()
    recorded_at = _utc_now()
    archive_stamp = _artifact_stamp(recorded_at)
    ds_roots = _discover_ds_roots(workspace_root)
    retired: list[dict[str, Any]] = []
    planned: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for ds_root in ds_roots:
        plan = _retirement_plan(
            workspace_root=workspace_root,
            ds_root=ds_root,
            recorded_at=recorded_at,
            archive_stamp=archive_stamp,
        )
        planned.append(plan)
        if plan.get("blockers"):
            blockers.append({"ds_root": str(ds_root), "blockers": plan["blockers"]})
            continue
        if apply:
            retired.append(_apply_retirement(plan=plan))
    report = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "mode": "apply" if apply else "dry_run",
        "status": "blocked" if blockers else "retired" if apply and planned else "planned" if planned else "nothing_to_retire",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(workspace_root),
        "ds_root_count": len(ds_roots),
        "planned_count": len(planned),
        "retired_count": len(retired),
        "all_ds_removed": _remaining_ds_count(workspace_root) == 0 if apply and not blockers else False,
        "planned": planned,
        "retired": retired,
        "blockers": blockers,
        "authority_boundary": {
            "paper_body_mutated": False,
            "publication_eval_mutated": False,
            "controller_decisions_mutated": False,
            "current_package_mutated": False,
            "legacy_ds_long_term_read_layer": False,
            "restore_proof_required": True,
        },
    }
    if archive_retention:
        report["archive_retention"] = retain_legacy_ds_archive_bodies(
            workspace_root=workspace_root,
            recorded_at=recorded_at,
            apply=archive_retention_apply,
            min_archive_mb=archive_retention_min_mb,
            cold_store_root=archive_retention_cold_store_root,
        )
    if apply and planned and not blockers:
        _write_report(workspace_root=workspace_root, recorded_at=recorded_at, report=report)
    return report


def retain_legacy_ds_archive_bodies(
    *,
    workspace_root: Path,
    recorded_at: str | None = None,
    apply: bool = False,
    min_archive_mb: int = 16,
    cold_store_root: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    recorded_at = recorded_at or _utc_now()
    threshold_bytes = max(0, int(min_archive_mb)) * 1024 * 1024
    cold_root = _cold_store_root(workspace_root=resolved_workspace_root, cold_store_root=cold_store_root)
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    moved_count = 0
    deduped_count = 0
    actual_release_bytes = 0
    for archive_path in _legacy_archive_paths(resolved_workspace_root):
        inspection = _inspect_legacy_archive(
            workspace_root=resolved_workspace_root,
            archive_path=archive_path,
            threshold_bytes=threshold_bytes,
        )
        if inspection.get("status") == "blocked":
            blockers.append(inspection)
            continue
        if inspection.get("status") != "candidate":
            continue
        if apply:
            applied = _apply_legacy_archive_retention(
                workspace_root=resolved_workspace_root,
                archive_path=archive_path,
                inspection=inspection,
                cold_root=cold_root,
                recorded_at=recorded_at,
            )
            inspection.update(applied)
            actual_release_bytes += int(applied.get("online_release_bytes") or 0)
            if applied.get("status") == "moved_to_cold_object":
                moved_count += 1
            elif applied.get("status") == "deduped_to_existing_cold_object":
                deduped_count += 1
            elif str(applied.get("status") or "").startswith("blocked"):
                blockers.append(inspection)
        candidates.append(inspection)
    status = (
        "applied"
        if apply and (moved_count or deduped_count)
        else "blocked"
        if apply and blockers
        else "planned"
        if candidates
        else "nothing_to_retain"
        if not blockers
        else "blocked"
    )
    receipt = {
        "surface_kind": ARCHIVE_RETENTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "workspace_root": str(resolved_workspace_root),
        "apply": bool(apply),
        "min_archive_bytes": threshold_bytes,
        "cold_store_root": str(cold_root),
        "candidate_count": len(candidates),
        "moved_count": moved_count,
        "deduped_count": deduped_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "restore_proof_required": True,
        "mutation_policy": {
            "moves_archive_body": bool(apply),
            "keeps_original_archive_path_as_symlink": bool(apply),
            "deletes_source_manifest_or_restore_proof": False,
            "deletes_retirement_receipt": False,
            "deletes_domain_truth": False,
            "reintroduces_legacy_ds_read_layer": False,
        },
        "candidate_samples": _sample_entries(candidates),
        "blocker_samples": _sample_entries(blockers),
    }
    _write_archive_retention_receipt(workspace_root=resolved_workspace_root, recorded_at=recorded_at, receipt=receipt)
    return receipt


def _discover_ds_roots(workspace_root: Path) -> list[Path]:
    if not workspace_root.exists():
        return []
    candidates = sorted(path for path in workspace_root.rglob(".ds") if path.is_dir() and not _is_under_retirement_archive(path))
    return [path for path in candidates if not _is_under_another_ds(path)]


def _retirement_plan(*, workspace_root: Path, ds_root: Path, recorded_at: str, archive_stamp: str) -> dict[str, Any]:
    owner_root = ds_root.parent
    owner_kind = _owner_kind(workspace_root=workspace_root, owner_root=owner_root)
    artifact_root = _artifact_root(workspace_root=workspace_root, owner_root=owner_root, archive_stamp=archive_stamp)
    source_manifest_path = artifact_root / "source_manifest.json"
    archive_path = artifact_root / "legacy_ds.tar.gz"
    restore_proof_path = artifact_root / "restore_proof.json"
    receipt_path = artifact_root / "retirement_receipt.json"
    runtime_state_plan = _runtime_state_plan(owner_root=owner_root, ds_root=ds_root)
    blockers: list[dict[str, Any]] = []
    if not _path_is_inside(ds_root, workspace_root):
        blockers.append({"reason": "ds_root_outside_workspace"})
    if _path_is_inside(artifact_root, ds_root):
        blockers.append({"reason": "artifact_root_inside_ds_root"})
    return {
        "surface_kind": "legacy_ds_retirement_plan",
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "workspace_root": str(workspace_root),
        "owner_root": str(owner_root),
        "owner_kind": owner_kind,
        "ds_root": str(ds_root),
        "source_manifest_path": str(source_manifest_path),
        "archive_path": str(archive_path),
        "restore_proof_path": str(restore_proof_path),
        "receipt_path": str(receipt_path),
        "runtime_state_plan": runtime_state_plan,
        "blockers": blockers,
    }


def _apply_retirement(*, plan: Mapping[str, Any]) -> dict[str, Any]:
    ds_root = Path(str(plan["ds_root"]))
    archive_path = Path(str(plan["archive_path"]))
    source_manifest_path = Path(str(plan["source_manifest_path"]))
    restore_proof_path = Path(str(plan["restore_proof_path"]))
    receipt_path = Path(str(plan["receipt_path"]))
    owner_root = Path(str(plan["owner_root"]))
    recorded_at = str(plan["recorded_at"])
    source_manifest = _source_manifest(ds_root=ds_root, owner_root=owner_root, recorded_at=recorded_at)
    write_json(source_manifest_path, source_manifest)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(ds_root, arcname=".ds", recursive=True)
    archive_sha256 = file_sha256(archive_path)
    proof = restore_proof(
        archive_path=archive_path,
        manifest=source_manifest,
        archive_sha256=archive_sha256,
        verified_at=_utc_now(),
    )
    write_json(restore_proof_path, proof)
    if proof.get("status") != "verified":
        return {
            "surface_kind": "legacy_ds_retirement_receipt",
            "status": "blocked_restore_proof_failed",
            "ds_root": str(ds_root),
            "restore_proof_path": str(restore_proof_path),
            "legacy_ds_removed": False,
        }
    runtime_state_receipt = _materialize_runtime_state(plan)
    shutil.rmtree(ds_root)
    receipt = {
        "surface_kind": "legacy_ds_retirement_receipt",
        "schema_version": SCHEMA_VERSION,
        "status": "retired",
        "recorded_at": recorded_at,
        "owner_root": str(owner_root),
        "owner_kind": plan.get("owner_kind"),
        "ds_root": str(ds_root),
        "legacy_ds_removed": not ds_root.exists(),
        "archive_path": str(archive_path),
        "archive_sha256": archive_sha256,
        "source_manifest_path": str(source_manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "runtime_state_receipt": runtime_state_receipt,
        "restore_command": f"tar -xzf {archive_path} -C {owner_root}",
        "authority_boundary": {
            "body_included_in_receipt": False,
            "paper_body_mutated": False,
            "publication_eval_mutated": False,
            "controller_decisions_mutated": False,
            "current_package_mutated": False,
        },
    }
    write_json(receipt_path, receipt)
    result = dict(receipt)
    result["receipt_path"] = str(receipt_path)
    return result


def _source_manifest(*, ds_root: Path, owner_root: Path, recorded_at: str) -> dict[str, Any]:
    files = [_manifest_entry(ds_root=ds_root, path=path) for path in sorted(ds_root.rglob("*")) if path.is_file() or path.is_symlink()]
    return {
        "surface_kind": "legacy_ds_retirement_source_manifest",
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "owner_root": str(owner_root),
        "ds_root": str(ds_root),
        "source_files": files,
        "source_file_count": len(files),
        "body_included": False,
    }


def _manifest_entry(*, ds_root: Path, path: Path) -> dict[str, Any]:
    relpath = path.relative_to(ds_root.parent).as_posix()
    if path.is_symlink():
        return {
            "path": relpath,
            "entry_type": "symlink",
            "size_bytes": path.lstat().st_size,
            "link_target": str(path.readlink()),
        }
    return {
        "path": relpath,
        "entry_type": "file",
        "size_bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }


def _materialize_runtime_state(plan: Mapping[str, Any]) -> dict[str, Any]:
    runtime_state_plan = plan.get("runtime_state_plan")
    if not isinstance(runtime_state_plan, Mapping) or not runtime_state_plan.get("legacy_runtime_state_exists"):
        return {"status": "skipped_no_runtime_state"}
    owner_root = Path(str(plan["owner_root"]))
    ds_root = Path(str(plan["ds_root"]))
    legacy_runtime_state = ds_root / "runtime_state.json"
    if not legacy_runtime_state.is_file():
        return {"status": "skipped_no_runtime_state"}
    canonical_path = quest_state.canonical_runtime_state_path(owner_root)
    if canonical_path.exists() and canonical_path.read_bytes() != legacy_runtime_state.read_bytes():
        return {
            "status": "canonical_runtime_state_retained",
            "canonical_path": str(canonical_path),
            "legacy_runtime_state_sha256": file_sha256(legacy_runtime_state),
            "canonical_runtime_state_sha256": file_sha256(canonical_path),
        }
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_runtime_state, canonical_path)
    return {
        "status": "materialized",
        "canonical_path": str(canonical_path),
        "legacy_runtime_state_sha256": file_sha256(legacy_runtime_state),
    }


def _runtime_state_plan(*, owner_root: Path, ds_root: Path) -> dict[str, Any]:
    legacy_runtime_state = ds_root / "runtime_state.json"
    canonical_path = quest_state.canonical_runtime_state_path(owner_root)
    return {
        "legacy_runtime_state_exists": legacy_runtime_state.is_file(),
        "legacy_runtime_state_path": str(legacy_runtime_state),
        "canonical_runtime_state_path": str(canonical_path),
        "canonical_runtime_state_exists": canonical_path.exists(),
    }


def _artifact_root(*, workspace_root: Path, owner_root: Path, archive_stamp: str) -> Path:
    rel_owner = _safe_relative_ref(workspace_root=workspace_root, path=owner_root)
    safe_owner = "__".join(safe_artifact_id(part) for part in rel_owner.parts)
    if _is_quest_root(workspace_root=workspace_root, owner_root=owner_root):
        return owner_root / "artifacts" / "runtime" / "restore_index" / "legacy_ds_retirement" / archive_stamp
    return workspace_root / "runtime" / "artifacts" / "legacy_ds_retirement" / "owners" / archive_stamp / safe_owner


def _write_report(*, workspace_root: Path, recorded_at: str, report: Mapping[str, Any]) -> None:
    root = build_workspace_runtime_layout(workspace_root=workspace_root).runtime_artifacts_root / "legacy_ds_retirement"
    write_json(root / f"{_artifact_stamp(recorded_at)}.json", report)
    write_json(root / "latest.json", report)


def _remaining_ds_count(workspace_root: Path) -> int:
    return len(_discover_ds_roots(workspace_root))


def _legacy_archive_paths(workspace_root: Path) -> list[Path]:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    archives: list[Path] = []
    workspace_retirement_root = layout.runtime_artifacts_root / "legacy_ds_retirement"
    if workspace_retirement_root.exists():
        archives.extend(
            path for path in workspace_retirement_root.rglob("legacy_ds.tar.gz") if path.is_file() and not path.is_symlink()
        )
    if layout.quests_root.exists():
        archives.extend(
            path
            for path in layout.quests_root.glob(
                "*/artifacts/runtime/restore_index/legacy_ds_retirement/*/legacy_ds.tar.gz"
            )
            if path.is_file() and not path.is_symlink()
        )
    return sorted(set(archives))


def _inspect_legacy_archive(*, workspace_root: Path, archive_path: Path, threshold_bytes: int) -> dict[str, Any]:
    size_bytes = archive_path.stat().st_size
    if size_bytes < threshold_bytes:
        return {"status": "below_threshold", "archive_path": str(archive_path), "bytes": size_bytes}
    manifest_path = archive_path.with_name("source_manifest.json")
    restore_proof_path = archive_path.with_name("restore_proof.json")
    receipt_path = archive_path.with_name("retirement_receipt.json")
    if not manifest_path.is_file() or not restore_proof_path.is_file() or not receipt_path.is_file():
        return {
            "status": "blocked",
            "reason": "missing_manifest_restore_proof_or_receipt",
            "archive_path": str(archive_path),
            "source_manifest_path": str(manifest_path),
            "restore_proof_path": str(restore_proof_path),
            "retirement_receipt_path": str(receipt_path),
        }
    restore_proof_payload = _read_json_mapping(restore_proof_path)
    if restore_proof_payload.get("status") != "verified":
        return {
            "status": "blocked",
            "reason": "restore_proof_not_verified",
            "archive_path": str(archive_path),
            "restore_proof_path": str(restore_proof_path),
        }
    observed_sha = file_sha256(archive_path)
    expected_sha = str(restore_proof_payload.get("archive_sha256") or "").strip()
    if expected_sha and observed_sha != expected_sha:
        return {
            "status": "blocked",
            "reason": "archive_sha256_mismatch",
            "archive_path": str(archive_path),
            "expected_sha256": expected_sha,
            "observed_sha256": observed_sha,
        }
    receipt = _read_json_mapping(receipt_path)
    receipt_sha = str(receipt.get("archive_sha256") or "").strip()
    if receipt_sha and receipt_sha != observed_sha:
        return {
            "status": "blocked",
            "reason": "retirement_receipt_sha256_mismatch",
            "archive_path": str(archive_path),
            "expected_sha256": receipt_sha,
            "observed_sha256": observed_sha,
            "retirement_receipt_path": str(receipt_path),
        }
    owner_root = Path(str(receipt.get("owner_root") or archive_path.parent))
    return {
        "status": "candidate",
        "archive_path": str(archive_path),
        "workspace_relative_archive_path": _workspace_relative(workspace_root=workspace_root, path=archive_path),
        "owner_root": str(owner_root),
        "owner_kind": receipt.get("owner_kind"),
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "retirement_receipt_path": str(receipt_path),
        "bytes": size_bytes,
        "sha256": observed_sha,
        "restore_command": str(receipt.get("restore_command") or f"tar -xzf {archive_path} -C {owner_root}"),
    }


def _apply_legacy_archive_retention(
    *,
    workspace_root: Path,
    archive_path: Path,
    inspection: Mapping[str, Any],
    cold_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    sha256 = str(inspection.get("sha256") or "")
    if not sha256:
        return {"status": "blocked_missing_sha256", "online_release_bytes": 0}
    object_path = cold_root / "objects" / sha256[:2] / f"{sha256}.tar.gz"
    object_path.parent.mkdir(parents=True, exist_ok=True)
    size_before = archive_path.stat().st_size
    if object_path.exists():
        if file_sha256(object_path) != sha256:
            return {
                "status": "blocked_cold_object_sha256_mismatch",
                "cold_object_path": str(object_path),
                "online_release_bytes": 0,
            }
        archive_path.unlink()
        _write_relative_symlink(target=object_path, link_path=archive_path)
        status = "deduped_to_existing_cold_object"
    else:
        shutil.move(str(archive_path), str(object_path))
        _write_relative_symlink(target=object_path, link_path=archive_path)
        status = "moved_to_cold_object"
    ref_path = archive_path.with_name(archive_path.name + ".cold_ref.json")
    cold_ref = {
        "surface_kind": "legacy_ds_cold_archive_body_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "online_path_retained_as_symlink",
        "recorded_at": recorded_at,
        "workspace_root": str(workspace_root),
        "archive_path": str(archive_path),
        "workspace_relative_archive_path": _workspace_relative(workspace_root=workspace_root, path=archive_path),
        "cold_object_path": str(object_path),
        "sha256": sha256,
        "bytes": size_before,
        "source_manifest_path": inspection.get("source_manifest_path"),
        "restore_proof_path": inspection.get("restore_proof_path"),
        "retirement_receipt_path": inspection.get("retirement_receipt_path"),
        "restore_command": str(inspection.get("restore_command") or ""),
        "body_included": False,
        "reintroduces_legacy_ds_read_layer": False,
    }
    write_json(ref_path, cold_ref)
    symlink_bytes = archive_path.lstat().st_size
    return {
        "status": status,
        "cold_object_path": str(object_path),
        "cold_ref_path": str(ref_path),
        "archive_body_online": False,
        "source_archive_path_is_symlink": archive_path.is_symlink(),
        "online_release_bytes": max(0, size_before - symlink_bytes - ref_path.stat().st_size),
    }


def _cold_store_root(*, workspace_root: Path, cold_store_root: Path | None) -> Path:
    safe_workspace = safe_artifact_id(workspace_root.name)
    if cold_store_root is not None:
        return Path(cold_store_root).expanduser().resolve() / safe_workspace / "legacy_ds_retirement"
    return workspace_root.parent / "_cold_objects" / "legacy_ds_retirement" / safe_workspace


def _write_archive_retention_receipt(*, workspace_root: Path, recorded_at: str, receipt: dict[str, Any]) -> None:
    root = build_workspace_runtime_layout(workspace_root=workspace_root).runtime_artifacts_root / "legacy_ds_retirement"
    receipt_path = root / f"{_artifact_stamp(recorded_at)}.archive_body_retention.json"
    latest_path = root / "latest_archive_body_retention.json"
    write_json(receipt_path, receipt)
    write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)


def _write_relative_symlink(*, target: Path, link_path: Path) -> None:
    relative_target = os.path.relpath(target, start=link_path.parent)
    link_path.symlink_to(relative_target)


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _workspace_relative(*, workspace_root: Path, path: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return str(path)


def _sample_entries(entries: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return [dict(entry) for entry in entries[:limit]]


def _owner_kind(*, workspace_root: Path, owner_root: Path) -> str:
    if _is_quest_root(workspace_root=workspace_root, owner_root=owner_root):
        return "runtime_quest_root"
    if "runtime" in owner_root.parts and "archives" in owner_root.parts:
        return "runtime_archive_legacy_root"
    if "recovery" in owner_root.parts:
        return "runtime_recovery_legacy_root"
    if "_archive" in owner_root.parts:
        return "study_archive_legacy_root"
    return "workspace_legacy_root"


def _is_quest_root(*, workspace_root: Path, owner_root: Path) -> bool:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    return owner_root.parent == layout.quests_root and (owner_root / "quest.yaml").exists()


def _safe_relative_ref(*, workspace_root: Path, path: Path) -> Path:
    try:
        return path.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        return Path(safe_artifact_id(path.name))


def _path_is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_under_retirement_archive(path: Path) -> bool:
    return "legacy_ds_retirement" in path.parts


def _is_under_another_ds(path: Path) -> bool:
    return ".ds" in path.parent.parts


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _artifact_stamp(value: str) -> str:
    return datetime.fromisoformat(value).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


__all__ = ["run_legacy_ds_retirement", "retain_legacy_ds_archive_bodies"]

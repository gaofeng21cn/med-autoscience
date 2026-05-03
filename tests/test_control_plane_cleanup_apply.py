from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _dir_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(child.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _cleanup_apply_fixture(
    root: Path,
    *,
    action: str = "delete-safe-cache",
    runtime_status: str = "stopped",
    artifact_role: str = "safe_cache",
    include_restore_contract: bool = True,
    allowlist: list[str] | None = None,
) -> tuple[Path, Path]:
    workspace_root = root / "workspace"
    cache_root = workspace_root / "scratch" / "cache"
    cache_root.mkdir(parents=True)
    (cache_root / "cache.tmp").write_text("delete-safe fixture\n", encoding="utf-8")
    restore_index = workspace_root / "restore_index.json"
    _write_json(restore_index, {"entries": [{"path": "scratch/cache"}]})

    cleanup_action: dict[str, object] = {
        "action": action,
        "target_path": "scratch/cache",
        "artifact_role": artifact_role,
    }
    if include_restore_contract:
        cleanup_action["restore_contract"] = {
            "restore_index_path": "restore_index.json",
            "sha256": _dir_sha256(cache_root),
            "rehydrate_verification": {"status": "verified"},
        }

    _write_json(
        workspace_root / "control_plane_cleanup_apply.json",
        {
            "surface": "control_plane_cleanup_apply_contract",
            "runtime": {"status": runtime_status, "active_run_id": "run-live" if runtime_status == "running" else None},
            "controller_decision": {"decision": "approve_cleanup_apply", "apply_intent": True},
            "action_allowlist": allowlist if allowlist is not None else ["delete-safe-cache"],
            "actions": [cleanup_action],
        },
    )
    return workspace_root, cache_root


def test_cleanup_apply_default_generates_plan_without_mutating(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)

    report = module.run_cleanup_apply(workspace_roots=[workspace_root])

    assert report["surface"] == "control_plane_cleanup_apply"
    assert report["apply"] is False
    assert report["status"] == "planned"
    assert cache_root.exists()
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0}
    assert report["apply_plan"][0]["action"] == "delete-safe-cache"
    assert report["apply_plan"][0]["eligible_for_apply"] is True


def test_cleanup_apply_true_deletes_safe_cache_after_all_gates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)

    report = module.run_cleanup_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "applied"
    assert not cache_root.exists()
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 1, "mutating": 1}
    assert report["applied_actions"][0]["action"] == "delete-safe-cache"


def test_cleanup_apply_live_runtime_is_audit_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path, runtime_status="running")

    report = module.run_cleanup_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert report["apply_plan"][0]["candidate_action"] == "audit-only"
    assert "live_runtime_active" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_data_release_without_restore_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(
        tmp_path,
        artifact_role="data_release",
        include_restore_contract=False,
    )

    report = module.run_cleanup_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert "missing_restore_contract" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_non_allowlisted_actions(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(
        tmp_path,
        action="delete",
        allowlist=["delete"],
    )

    report = module.run_cleanup_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert "action_not_allowlisted" in report["apply_plan"][0]["blockers"]

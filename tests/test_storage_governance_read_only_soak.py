from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from . import control_plane_fixtures as fixtures


def _regular_files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _dir_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(child.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _add_storage_growth_buckets(workspace_root: Path) -> None:
    cache_root = workspace_root / ".cache" / "safe-cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    (cache_root / "cache.tmp").write_text("cache fixture\n", encoding="utf-8")
    runtime_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "quest.log").write_text("runtime fixture\n", encoding="utf-8")
    release_root = workspace_root / "datasets" / "release"
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "release.csv").write_text("id,value\n1,1\n", encoding="utf-8")
    _write_json(
        workspace_root / "storage_audit" / "latest.json",
        {
            "surface": "storage_audit",
            "source_totals": {
                "cache": {"bytes": 13, "file_count": 1, "directory_count": 1},
                "runtime": {"bytes": 16, "file_count": 1, "directory_count": 1},
                "dataset": {"bytes": 13, "file_count": 1, "directory_count": 1},
            },
        },
    )


def _add_safe_cache_cleanup_contract(workspace_root: Path) -> Path:
    cache_root = workspace_root / ".cache" / "safe-cache"
    _write_json(
        workspace_root / "restore_index.json",
        {"entries": [{"path": ".cache/safe-cache"}]},
    )
    _write_json(
        workspace_root / "control_plane_cleanup_apply.json",
        {
            "surface": "control_plane_cleanup_apply_contract",
            "runtime": {"status": "stopped", "active_run_id": None},
            "controller_decision": {
                "decision": "approve_cleanup_apply",
                "apply_intent": True,
            },
            "action_allowlist": ["delete-safe-cache"],
            "actions": [
                {
                    "action": "delete-safe-cache",
                    "target_path": ".cache/safe-cache",
                    "artifact_role": "safe_cache",
                    "target_allowlist": {
                        "source": "test_soak_contract",
                        "target_path": ".cache/safe-cache",
                    },
                    "restore_contract": {
                        "restore_index_path": "restore_index.json",
                        "sha256": _dir_sha256(cache_root),
                        "rehydrate_verification": {"status": "verified"},
                    },
                }
            ],
        },
    )
    return cache_root


def test_dm_cvd_and_nf_pitnet_storage_governance_soak_is_read_only(tmp_path: Path) -> None:
    lifecycle = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    migration = importlib.import_module("med_autoscience.controllers.control_plane_migration_audit")
    cleanup = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspaces = [
        fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path / "dm"),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path / "nf"),
    ]
    for workspace_root in workspaces:
        _add_storage_growth_buckets(workspace_root)
    cache_root = _add_safe_cache_cleanup_contract(workspaces[0])
    before = _regular_files(tmp_path)

    governance_report = lifecycle.run_lifecycle_operations_report(workspace_roots=workspaces)
    backfill_plan = migration.run_migration_audit(workspace_roots=workspaces, dry_run=True)
    cleanup_plan = cleanup.run_cleanup_apply(workspace_roots=workspaces, apply=False)

    assert _regular_files(tmp_path) == before
    assert cache_root.exists()
    assert governance_report["mutation_policy"] == {
        "read_only": True,
        "writes_workspace": False,
        "cleanup_apply_supported": False,
        "physical_cleanup_performed": False,
    }
    assert backfill_plan["mutation_policy"] == {
        "dry_run_read_only": True,
        "cleanup_apply_supported": False,
    }
    assert cleanup_plan["apply"] is False
    assert cleanup_plan["action_counts"]["mutating"] == 0
    assert {workspace["workspace_style"] for workspace in backfill_plan["workspaces"]} == {
        "dm_cvd",
        "nf_pitnet",
    }
    assert all(
        study["authority_classification"] == "controller_authorized"
        for study in backfill_plan["studies"]
    )
    assert backfill_plan["historical_backfill_plan_count"] == 1
    legacy_study = next(
        study for study in backfill_plan["studies"] if study["historical_backfill_plan"] is not None
    )
    assert legacy_study["historical_backfill_plan"]["plan_type"] == "delivery_manifest_historical_backfill"
    assert legacy_study["historical_backfill_plan"]["mutation_policy"] == {
        "read_only": True,
        "writes_workspace": False,
        "manual_patch_allowed": False,
        "allowed_mutating_actions": [],
    }
    source_totals = governance_report["source_totals"]
    assert source_totals["cache"]["bytes"] >= 13
    assert source_totals["runtime"]["bytes"] >= 16
    assert source_totals["dataset"]["bytes"] >= 13
    retention_plan = governance_report["retention_plan"]
    assert retention_plan["mutation_policy"]["physical_cleanup_performed"] is False
    assert "delete-safe-cache" in retention_plan["mutation_policy"]["allowed_physical_actions"]
    assert cleanup_plan["apply_plan"][0]["action"] == "delete-safe-cache"
    assert cleanup_plan["apply_plan"][0]["eligible_for_apply"] is True

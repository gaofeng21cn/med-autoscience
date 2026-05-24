from __future__ import annotations

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


def test_dm_cvd_and_nf_pitnet_storage_governance_soak_is_read_only(tmp_path: Path) -> None:
    lifecycle = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    migration = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    summary = importlib.import_module("med_autoscience.controllers.continuous_soak_summary")
    workspaces = [
        fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path / "dm"),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path / "nf"),
    ]
    for workspace_root in workspaces:
        _add_storage_growth_buckets(workspace_root)
    before = _regular_files(tmp_path)

    governance_report = lifecycle.run_lifecycle_operations_report(workspace_roots=workspaces)
    backfill_plan = migration.run_migration_audit(workspace_roots=workspaces, dry_run=True)
    soak_summary = summary.build_continuous_soak_summary(workspace_roots=workspaces)

    assert _regular_files(tmp_path) == before
    assert governance_report["mutation_policy"] == {
        "read_only": True,
        "writes_workspace": False,
        "physical_cleanup_owned_by": "one-person-lab",
        "physical_cleanup_performed": False,
    }
    assert backfill_plan["mutation_policy"] == {
        "dry_run_read_only": True,
        "cleanup_apply_supported": False,
    }
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
    assert retention_plan["mutation_policy"]["writes_workspace"] is False
    assert "delete-safe-cache" in retention_plan["mutation_policy"]["allowed_physical_actions"]
    assert governance_report["storage_governance_policy"]["mutation_policy"] == {
        "read_only": True,
        "writes_workspace": False,
        "physical_cleanup_performed": False,
        "cleanup_apply_supported": False,
    }
    assert soak_summary["surface"] == "continuous_soak_summary"
    assert soak_summary["mutating_actions"] == 0
    assert soak_summary["unclassified_authority_surface"] == 0
    assert soak_summary["writes_workspace"] is False
    assert 1 <= len(soak_summary["top_growth_buckets"]) <= 5
    assert [item["bytes"] for item in soak_summary["top_growth_buckets"]] == sorted(
        [item["bytes"] for item in soak_summary["top_growth_buckets"]],
        reverse=True,
    )
    assert all(item["bytes"] > 0 for item in soak_summary["top_growth_buckets"])
    assert soak_summary["backfill_blockers"] == [
        {
            "workspace_style": "dm_cvd",
            "study_id": "007-legacy-delivery-manifest-backfill",
            "plan_type": "delivery_manifest_historical_backfill",
            "missing_surfaces": [
                "delivery_manifest_lifecycle_hook",
                "source_signature",
                "publication_refs",
            ],
            "writes_workspace": False,
            "next_action": "rerun_publication_gate_after_canonical_regeneration",
        }
    ]
    assert soak_summary["next_safe_action"] == {
        "action": "regenerate_projection_before_cleanup_review",
        "read_only": True,
        "reason": "canonical_regeneration_required",
    }
    assert soak_summary["read_only_contract"] == {
        "dry_run": True,
        "physical_cleanup_owned_by": "one-person-lab",
        "writes_workspace": False,
    }


def test_lifecycle_safe_cache_candidate_is_read_only_and_artifact_receipt_gated(
    tmp_path: Path,
) -> None:
    retention = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    storage_governance = importlib.import_module(
        "med_autoscience.controllers.storage_governance_policy_kernel"
    )
    cache_file = tmp_path / ".cache" / "safe-cache" / "cache.tmp"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("cache fixture\n", encoding="utf-8")
    before = _regular_files(tmp_path)

    plan = retention.build_artifact_retention_operations_plan(
        workspace_root=tmp_path,
        artifacts=[
            {
                "path": str(cache_file),
                "workspace_relative_path": ".cache/safe-cache/cache.tmp",
                "role": "cache",
                "lifecycle": "cache_transient",
                "cleanup_candidate_action": "delete-safe-cache",
                "cleanup_blockers": [],
            }
        ],
    )
    compact_plan = retention.compact_artifact_retention_operations_plan(plan)
    governance = storage_governance.build_storage_governance_policy_projection(
        lifecycle_report={
            "summary": {"total_bytes": len("cache fixture\n")},
            "source_totals": {"cache": {"bytes": len("cache fixture\n"), "file_count": 1}},
            "workspaces": [
                {
                    "workspace_root": str(tmp_path),
                    "summary": {"total_bytes": len("cache fixture\n")},
                    "source_totals": {"cache": {"bytes": len("cache fixture\n"), "file_count": 1}},
                    "retention_plan": compact_plan,
                    "studies": [],
                    "artifact_sample": [],
                }
            ],
        }
    )

    assert _regular_files(tmp_path) == before
    assert cache_file.exists()
    assert plan["mutation_policy"]["read_only"] is True
    assert plan["mutation_policy"]["writes_workspace"] is False
    assert plan["mutation_policy"]["physical_cleanup_performed"] is False
    assert plan["summary"]["applyable_action_counts"] == {"delete_safe_cache": 1}
    operation = plan["operations"][0]
    assert operation["retention_action"] == "delete_safe_cache"
    assert operation["physical_delete_allowed"] is True
    packet = operation["body_free_evidence_packet"]
    assert packet["role"] == "artifact_mutation_receipt_ref"
    assert packet["owner"] == "MedAutoScience"
    assert packet["no_forbidden_write_proof"]["artifact_body_write_performed"] is False
    assert governance["mutation_policy"] == {
        "read_only": True,
        "writes_workspace": False,
        "physical_cleanup_performed": False,
        "cleanup_apply_supported": False,
    }
    assert governance["alert_status"]["status"] == "safe_cache_candidate_pending_approval"
    assert governance["next_safe_action"] == {
        "action": "review_safe_cache_delete_candidate",
        "read_only": True,
        "reason": "safe_cache_candidate_available",
    }
    assert governance["recommended_operations"][0]["operation_type"] == "delete_safe_cache_candidate"
    assert governance["recommended_operations"][0]["physical_apply_performed"] is False

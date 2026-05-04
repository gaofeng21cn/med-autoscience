from __future__ import annotations

import importlib


def _report(
    *,
    total_bytes: int = 0,
    previous_total_bytes: int | None = None,
    runtime_bytes: int = 0,
    cache_bytes: int = 0,
    operations: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    report: dict[str, object] = {
        "summary": {"total_bytes": total_bytes},
        "source_totals": {
            "runtime": {"bytes": runtime_bytes, "file_count": 1, "scan_mode": "snapshot_reference"},
            "cache": {"bytes": cache_bytes, "file_count": 1, "scan_mode": "classified"},
        },
        "retention_plan": {
            "summary": {
                "operation_count": len(operations or []),
                "action_counts": {},
                "applyable_action_counts": {},
            },
            "mutation_policy": {
                "read_only": True,
                "physical_cleanup_performed": False,
            },
        },
        "workspaces": [
            {
                "workspace_root": "/tmp/ws",
                "summary": {"total_bytes": total_bytes},
                "source_totals": {
                    "runtime": {"bytes": runtime_bytes, "file_count": 1, "scan_mode": "snapshot_reference"},
                    "cache": {"bytes": cache_bytes, "file_count": 1, "scan_mode": "classified"},
                },
                "retention_plan": {
                    "operation_sample": operations or [],
                    "operation_sample_truncated": False,
                    "summary": {"operation_count": len(operations or [])},
                },
                "studies": [
                    {
                        "study_id": "001-risk",
                        "workspace_relative_study_root": "studies/001-risk",
                    }
                ],
            }
        ],
    }
    if previous_total_bytes is not None:
        report["previous_summary"] = {"total_bytes": previous_total_bytes}
    return report


def test_storage_governance_kernel_projects_budget_status_and_trend_delta() -> None:
    module = importlib.import_module("med_autoscience.controllers.storage_governance_policy_kernel")

    projection = module.build_storage_governance_policy_projection(
        lifecycle_report=_report(total_bytes=1_200, previous_total_bytes=900, runtime_bytes=900),
        threshold_schema={"workspace": {"warning_bytes": 1_000, "critical_bytes": 2_000}},
    )

    assert projection["surface_kind"] == "storage_governance_policy_projection"
    assert projection["mutation_policy"]["read_only"] is True
    assert projection["threshold_schema"]["workspace"]["warning_bytes"] == 1_000
    assert projection["budget_status"]["status"] == "warning"
    assert projection["trend_delta"] == {
        "current_bytes": 1_200,
        "previous_bytes": 900,
        "delta_bytes": 300,
        "delta_ratio": 0.333333,
        "growth_bucket": "growth",
    }
    workspace = projection["workspaces"][0]
    assert workspace["budget_status"]["status"] == "warning"
    assert workspace["top_growth_buckets"][0]["source_bucket"] == "runtime"


def test_storage_governance_kernel_keeps_read_only_when_recommending_safe_cache() -> None:
    module = importlib.import_module("med_autoscience.controllers.storage_governance_policy_kernel")
    operations = [
        {
            "workspace_relative_path": ".pytest_cache/v/cache/nodeids",
            "retention_action": "delete_safe_cache",
            "physical_delete_allowed": True,
            "role": "cache",
            "lifecycle": "cache_transient",
            "blockers": [],
        }
    ]

    projection = module.build_storage_governance_policy_projection(
        lifecycle_report=_report(total_bytes=500, cache_bytes=400, operations=operations),
        threshold_schema={"workspace": {"warning_bytes": 1_000, "critical_bytes": 2_000}},
    )

    assert projection["budget_status"]["status"] == "within_budget"
    assert projection["recommended_operations"][0]["operation_type"] == "delete_safe_cache_candidate"
    assert projection["recommended_operations"][0]["read_only"] is True
    assert projection["recommended_operations"][0]["physical_apply_performed"] is False
    assert projection["next_safe_action"] == {
        "action": "review_safe_cache_delete_candidate",
        "read_only": True,
        "reason": "safe_cache_candidate_available",
    }


def test_storage_governance_kernel_prioritizes_blocked_reason_and_restore_contract_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.storage_governance_policy_kernel")
    operations = [
        {
            "workspace_relative_path": "ops/runtime/quest/.ds/cold_archive/payload.tar.gz",
            "retention_action": "restore_contract_required",
            "physical_delete_allowed": False,
            "physical_archive_compress_allowed": False,
            "restore_contract_gate": {"required": True, "status": "required_before_cleanup"},
            "blockers": ["restore_contract_missing"],
        },
        {
            "workspace_relative_path": "studies/001-risk/manuscript/current_package.zip",
            "retention_action": "regenerate_projection_then_remove_stale",
            "physical_delete_allowed": False,
            "blockers": ["canonical_regeneration_required_before_projection_removal"],
        },
    ]

    projection = module.build_storage_governance_policy_projection(
        lifecycle_report=_report(total_bytes=2_500, previous_total_bytes=1_000, runtime_bytes=2_000, operations=operations),
        threshold_schema={"workspace": {"warning_bytes": 1_000, "critical_bytes": 2_000}},
    )

    assert projection["budget_status"]["status"] == "critical"
    assert projection["blocked_reasons"][0] == {
        "reason": "canonical_regeneration_required_before_projection_removal",
        "count": 1,
    }
    assert projection["restore_contract_gaps"][0]["workspace_relative_path"] == (
        "ops/runtime/quest/.ds/cold_archive/payload.tar.gz"
    )
    assert projection["recommended_operations"][0]["operation_type"] == "restore_contract_gap"
    assert projection["next_safe_action"] == {
        "action": "define_restore_contract_before_cleanup",
        "read_only": True,
        "reason": "restore_contract_gap",
    }


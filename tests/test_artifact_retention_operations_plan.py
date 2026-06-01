from __future__ import annotations

import importlib
from pathlib import Path


def _artifact(
    path: Path,
    *,
    role: str,
    lifecycle: str,
    cleanup_candidate_action: str,
    workspace_relative_path: str | None = None,
    cleanup_blockers: list[str] | None = None,
) -> dict[str, object]:
    return {
        "path": str(path),
        "workspace_relative_path": workspace_relative_path or str(path),
        "role": role,
        "lifecycle": lifecycle,
        "cleanup_candidate_action": cleanup_candidate_action,
        "cleanup_blockers": cleanup_blockers or [],
    }


def test_retention_plan_keeps_authority_release_audit_and_handoff_online(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("studies/001/paper/source/manuscript.md"),
            role="canonical_source",
            lifecycle="active_authority",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("datasets/release/dataset_manifest.yaml"),
            role="data_release",
            lifecycle="retained_release",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/artifacts/runtime/latest.json"),
            role="audit_log",
            lifecycle="audit_retained",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/manuscript/README.md"),
            role="human_handoff_mirror",
            lifecycle="human_handoff",
            cleanup_candidate_action="keep-online",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)

    assert plan["surface_kind"] == "artifact_retention_operations_plan"
    assert plan["mutation_policy"]["physical_cleanup_performed"] is False
    assert plan["mutation_policy"]["allowed_physical_actions"] == ["delete-safe-cache"]
    assert plan["retention_policy_catalog"]["default_keep_online_roles"] == [
        "audit_log",
        "canonical_source",
        "data_release",
        "human_handoff_mirror",
    ]
    assert {item["retention_action"] for item in plan["operations"]} == {"keep_online"}
    assert all(item["physical_delete_allowed"] is False for item in plan["operations"])
    assert plan["summary"]["action_counts"]["keep_online"] == 4


def test_retention_plan_projects_generated_surfaces_without_physical_delete(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("studies/001/manuscript/current_package/manuscript.docx"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
        _artifact(
            Path("studies/001/paper/submission_minimal/paper.pdf"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
        _artifact(
            Path("studies/001/manuscript/current_package.zip"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)

    assert {item["retention_action"] for item in plan["operations"]} == {
        "regenerate_projection_then_remove_stale",
    }
    for item in plan["operations"]:
        assert item["projection_status"] == "stale_or_rebuildable_projection"
        assert item["removal_marker"] == "regenerate-before-remove"
        assert item["canonical_regeneration_gate"]["required"] is True
        assert item["canonical_regeneration_gate"]["status"] == "required_before_physical_removal"
        assert "canonical_regeneration_required_before_projection_removal" in item["blockers"]
        assert item["physical_delete_allowed"] is False
    assert plan["retention_policy_catalog"]["derived_projection_removal_marker"] == "regenerate-before-remove"
    handoff = plan["physical_thinning_handoff"]
    assert handoff["surface_kind"] == "artifact_lifecycle_physical_thinning_handoff"
    assert handoff["body_free"] is True
    assert handoff["domain_owner"] == "MedAutoScience"
    assert handoff["apply_owner"] == "one-person-lab"
    assert handoff["candidate_count"] == 3
    assert handoff["candidate_counts_by_action"] == {"regenerate_projection_then_remove_stale": 3}
    assert handoff["candidate_ref_count"] == 3
    assert len(handoff["candidate_refs"]) == 3
    assert len(handoff["candidate_sample"]) == 3
    assert handoff["candidate_refs_truncated"] is False
    assert handoff["candidate_sample_truncated"] is False
    assert handoff["selected_payload_path"] == "typed_blocker_path"
    assert handoff["receipt_refs"] == []
    assert handoff["typed_blocker_ref_count"] == 3
    assert handoff["next_owner_action"] == {
        "owner": "one-person-lab",
        "action": "generic_lifecycle_apply",
        "requires_restore_or_regeneration_receipt_before_cleanup": True,
        "accepts_handoff_ref": handoff["handoff_ref"],
        "selected_payload_path": "typed_blocker_path",
    }
    assert handoff["authority_boundary"]["mas_executes_physical_cleanup"] is False
    assert handoff["authority_boundary"]["can_authorize_artifact_mutation"] is False


def test_retention_plan_blocks_runtime_archive_compress_and_keeps_live_runtime_audit_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("ops/runtime/quests/001/.ds/runs/run-live/stdout.jsonl"),
            role="runtime_ephemeral",
            lifecycle="runtime_transient",
            cleanup_candidate_action="audit-only",
            cleanup_blockers=["live_runtime_active"],
        ),
        _artifact(
            Path("ops/runtime/quests/002/.ds/runs/run-stopped/stderr.jsonl"),
            role="runtime_ephemeral",
            lifecycle="runtime_transient",
            cleanup_candidate_action="archive-compress",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)
    live = plan["operations"][0]
    terminal = plan["operations"][1]

    assert live["retention_action"] == "keep_online"
    assert live["runtime_retention_mode"] == "audit_only"
    assert live["blockers"] == ["live_runtime_active"]
    assert live["physical_delete_allowed"] is False
    assert terminal["retention_action"] == "archive_compress_candidate_blocked"
    assert terminal["physical_archive_compress_allowed"] is False
    assert terminal["restore_contract_gate"]["required"] is True
    assert terminal["restore_contract_gate"]["status"] == "apply_implementation_required"
    assert "physical_archive_compress_not_open" in terminal["blockers"]
    assert "restore_contract_apply_implementation_required" in terminal["blockers"]


def test_retention_plan_only_marks_safe_cache_as_applyable(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    cache_path = tmp_path / ".pytest_cache" / "v" / "cache" / "nodeids"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text("nodeids\n", encoding="utf-8")
    artifacts = [
        _artifact(
            cache_path,
            role="cache",
            lifecycle="cache_transient",
            cleanup_candidate_action="delete-safe-cache",
            workspace_relative_path=".pytest_cache/v/cache/nodeids",
        ),
        _artifact(
            Path("ops/runtime/quests/001/.ds/cold_archive/payload.tar.gz"),
            role="cold_archive",
            lifecycle="archived_restore_candidate",
            cleanup_candidate_action="restore-gated",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)

    assert plan["summary"]["applyable_action_counts"] == {"delete_safe_cache": 1}
    assert plan["retention_policy_catalog"]["physical_apply_allowlist"] == ["delete-safe-cache"]
    assert plan["operations"][0]["retention_action"] == "delete_safe_cache"
    assert plan["operations"][0]["physical_delete_allowed"] is True
    assert plan["operations"][0]["cleanup_candidate_action"] == "delete-safe-cache"
    assert plan["operations"][0]["workspace_relative_path"] == ".pytest_cache/v/cache/nodeids"
    assert plan["operations"][0]["target_sha256"]
    assert plan["operations"][1]["retention_action"] == "restore_contract_required"
    assert plan["operations"][1]["physical_delete_allowed"] is False
    assert plan["operations"][1]["restore_contract_gate"]["status"] == "required_before_cleanup"


def test_retention_plan_preserves_artifact_lifecycle_receipt_ref_families(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    cache_path = tmp_path / ".pytest_cache" / "v" / "cache" / "nodeids"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text("nodeids\n", encoding="utf-8")
    artifacts = [
        _artifact(
            Path("studies/001/paper/source/manuscript.md"),
            role="canonical_source",
            lifecycle="active_authority",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/manuscript/current_package.zip"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
        _artifact(
            cache_path,
            role="cache",
            lifecycle="cache_transient",
            cleanup_candidate_action="delete-safe-cache",
            workspace_relative_path=".pytest_cache/v/cache/nodeids",
        ),
        _artifact(
            Path("ops/runtime/quests/001/.ds/cold_archive/payload.tar.gz"),
            role="cold_archive",
            lifecycle="archived_restore_candidate",
            cleanup_candidate_action="restore-gated",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(
        workspace_root=tmp_path,
        artifacts=artifacts,
    )
    compact = module.compact_artifact_retention_operations_plan(plan)
    aggregate = module.aggregate_artifact_retention_operations_plans([compact])

    for result in (plan, compact, aggregate):
        assert result["artifact_lifecycle_receipt_refs"]
        assert result["artifact_authority_receipt_refs"]
        assert result["cleanup_receipt_refs"]
        assert result["restore_proof_refs"]
        assert result["retention_receipt_refs"]
        assert set(result["artifact_authority_receipt_refs"]).issubset(
            set(result["artifact_lifecycle_receipt_refs"])
        )
        assert set(result["cleanup_receipt_refs"]).issubset(
            set(result["artifact_lifecycle_receipt_refs"])
        )
        assert set(result["restore_proof_refs"]).issubset(
            set(result["artifact_lifecycle_receipt_refs"])
        )
        assert set(result["retention_receipt_refs"]).issubset(
            set(result["artifact_lifecycle_receipt_refs"])
        )
        handoff = result["physical_thinning_handoff"]
        assert handoff["handoff_ref"].startswith(
            "mas-artifact-lifecycle-handoff:medautoscience:physical-thinning:"
        )
        assert handoff["candidate_refs"]
        assert handoff["candidate_ref_count"] == 3
        assert handoff["candidate_sample"]
        assert handoff["next_owner_action"]["owner"] == "one-person-lab"
        assert handoff["next_owner_action"]["action"] == "generic_lifecycle_apply"
        assert handoff["authority_boundary"]["mas_executes_physical_cleanup"] is False
    assert plan["mutation_policy"]["physical_cleanup_performed"] is False


def test_retention_plan_bounds_artifact_receipt_ref_families_and_preserves_counts(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts: list[dict[str, object]] = []
    for index in range(60):
        artifacts.extend(
            [
                _artifact(
                    Path(f"studies/001/paper/source/manuscript-{index}.md"),
                    role="canonical_source",
                    lifecycle="active_authority",
                    cleanup_candidate_action="keep-online",
                ),
                _artifact(
                    Path(f".pytest_cache/v/cache/nodeids-{index}"),
                    role="cache",
                    lifecycle="cache_transient",
                    cleanup_candidate_action="delete-safe-cache",
                    workspace_relative_path=f".pytest_cache/v/cache/nodeids-{index}",
                ),
                _artifact(
                    Path(f"ops/runtime/quests/{index}/.ds/cold_archive/payload.tar.gz"),
                    role="cold_archive",
                    lifecycle="archived_restore_candidate",
                    cleanup_candidate_action="restore-gated",
                ),
            ]
        )

    plan = module.build_artifact_retention_operations_plan(
        workspace_root=tmp_path,
        artifacts=artifacts,
    )
    compact = module.compact_artifact_retention_operations_plan(plan)
    aggregate = module.aggregate_artifact_retention_operations_plans([compact])

    for result in (plan, compact, aggregate):
        assert len(result["artifact_lifecycle_receipt_refs"]) == module.RECEIPT_REF_SAMPLE_LIMIT
        assert result["artifact_lifecycle_receipt_ref_count"] == 180
        assert result["artifact_lifecycle_receipt_refs_truncated"] is True
        assert len(result["artifact_authority_receipt_refs"]) == module.RECEIPT_REF_SAMPLE_LIMIT
        assert result["artifact_authority_receipt_ref_count"] == 180
        assert result["artifact_authority_receipt_refs_truncated"] is True
        assert len(result["cleanup_receipt_refs"]) == module.RECEIPT_REF_SAMPLE_LIMIT
        assert result["cleanup_receipt_ref_count"] == 60
        assert result["cleanup_receipt_refs_truncated"] is True
        assert len(result["restore_proof_refs"]) == module.RECEIPT_REF_SAMPLE_LIMIT
        assert result["restore_proof_ref_count"] == 60
        assert result["restore_proof_refs_truncated"] is True
        assert len(result["retention_receipt_refs"]) == module.RECEIPT_REF_SAMPLE_LIMIT
        assert result["retention_receipt_ref_count"] == 60
        assert result["retention_receipt_refs_truncated"] is True
        handoff = result["physical_thinning_handoff"]
        assert len(handoff["candidate_refs"]) == module.PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT
        assert handoff["candidate_ref_count"] == 120
        assert handoff["candidate_refs_truncated"] is True
        assert len(handoff["candidate_sample"]) == module.PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT
        assert handoff["candidate_sample_truncated"] is True
    assert plan["summary"]["operation_count"] == 180


def test_terminal_stop_loss_retention_plan_requires_explicit_non_reopenable_macro_state(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("studies/001/paper/source/manuscript_source.md"),
            role="canonical_source",
            lifecycle="active_authority",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/artifacts/interventions/events.jsonl"),
            role="audit_log",
            lifecycle="audit_retained",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("ops/runtime/quests/001/.ds/runs/run-old/stdout.jsonl"),
            role="runtime_ephemeral",
            lifecycle="runtime_transient",
            cleanup_candidate_action="archive-compress",
        ),
    ]
    reopenable_macro_state = {
        "writer_state": "parked",
        "user_next": "none",
        "reason": "stop_loss",
        "details": {"reopen_allowed": True},
    }

    plan = module.build_terminal_study_file_lifecycle_plan(
        workspace_root=tmp_path,
        study_root=tmp_path / "studies" / "001",
        study_macro_state=reopenable_macro_state,
        artifacts=artifacts,
    )

    assert plan["eligible"] is False
    assert plan["eligibility"]["blockers"] == ["macro_state_not_terminal_non_reopenable_stop_loss"]
    assert plan["retention_plan"]["summary"]["action_counts"]["archive_compress_candidate_blocked"] == 1
    assert plan["archive_manifest_contract"]["required"] is True
    assert plan["mutation_policy"]["physical_cleanup_performed"] is False


def test_terminal_stop_loss_retention_plan_preserves_truth_and_marks_runtime_for_manifested_compaction(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("studies/001/paper/source/manuscript_source.md"),
            role="canonical_source",
            lifecycle="active_authority",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/artifacts/interventions/events.jsonl"),
            role="audit_log",
            lifecycle="audit_retained",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/manuscript/current_package/paper.pdf"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
        _artifact(
            Path("ops/runtime/quests/001/.ds/runs/run-old/stdout.jsonl"),
            role="runtime_ephemeral",
            lifecycle="runtime_transient",
            cleanup_candidate_action="archive-compress",
        ),
    ]
    terminal_macro_state = {
        "writer_state": "parked",
        "user_next": "none",
        "reason": "stop_loss",
        "details": {
            "reopen_allowed": False,
            "final_line_decision": {"decision": "abandon", "reopen_allowed": False},
        },
        "source_fingerprint": "study-macro-state::terminal-stop-loss",
    }

    plan = module.build_terminal_study_file_lifecycle_plan(
        workspace_root=tmp_path,
        study_root=tmp_path / "studies" / "001",
        study_macro_state=terminal_macro_state,
        artifacts=artifacts,
    )

    assert plan["surface_kind"] == "terminal_study_file_lifecycle_plan"
    assert plan["mode"] == "dry_run"
    assert plan["eligible"] is True
    assert plan["eligibility"]["required_macro_state"] == {
        "writer_state": "parked",
        "user_next": "none",
        "reason": "stop_loss",
        "details.reopen_allowed": False,
    }
    assert plan["archive_manifest_contract"] == {
        "required": True,
        "format": "manifest_with_sha256_and_restore_index",
        "restore_proof_required": True,
        "summary_required": True,
    }
    assert plan["preserve_roles"] == [
        "audit_log",
        "canonical_source",
        "data_release",
        "human_handoff_mirror",
    ]
    assert plan["candidate_summary"]["runtime_archive_compact_candidates"] == 1
    assert plan["candidate_summary"]["derived_projection_refresh_candidates"] == 1
    runtime_operation = next(
        item
        for item in plan["retention_plan"]["operations"]
        if item["role"] == "runtime_ephemeral"
    )
    assert runtime_operation["retention_action"] == "terminal_archive_compact_after_manifest"
    assert runtime_operation["physical_archive_compress_allowed"] is False
    assert runtime_operation["restore_contract_gate"] == {
        "required": True,
        "status": "manifest_and_restore_proof_required_before_apply",
    }
    assert "terminal_stop_loss_manifest_required" in runtime_operation["blockers"]

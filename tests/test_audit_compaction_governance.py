from __future__ import annotations

import importlib
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta


def test_audit_compaction_governance_builds_maintainability_read_model(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction_governance")
    boundary = importlib.import_module("med_autoscience.controllers.boundary_fitness")
    repo_root = tmp_path
    domain_health_diagnostic = repo_root / "src/med_autoscience/controllers/domain_health_diagnostic.py"
    gate_clearing = repo_root / "src/med_autoscience/controllers/gate_clearing_batch.py"
    study_progress = repo_root / "src/med_autoscience/controllers/study_progress.py"
    domain_health_diagnostic.parent.mkdir(parents=True)
    domain_health_diagnostic.write_text("\n".join("line" for _ in range(1025)), encoding="utf-8")
    gate_clearing.write_text("\n".join("line" for _ in range(1015)), encoding="utf-8")
    study_progress.write_text("line\n", encoding="utf-8")

    fitness_report = boundary.audit_boundary_fitness(
        repo_root,
        tracked_files=[
            "src/med_autoscience/controllers/gate_clearing_batch.py",
            "src/med_autoscience/controllers/domain_health_diagnostic.py",
            "src/med_autoscience/controllers/study_progress.py",
        ],
        baseline={
            "src/med_autoscience/controllers/gate_clearing_batch.py": 1010,
            "src/med_autoscience/controllers/domain_health_diagnostic.py": 1010,
        },
    )

    report = module.build_audit_compaction_governance_report(
        repo_root,
        worktrees=[
            {"path": "/repo", "branch": "main", "commit": "a"},
            {
                "path": "/repo/.worktrees/mas-l5-compaction-structure",
                "branch": "codex/mas-l5-compaction-structure",
                "commit": "b",
            },
            {"path": "/repo/.worktrees/mas-l2", "branch": "codex/mas-pi-action-projection", "commit": "c"},
            {"path": "/repo/.worktrees/detached", "detached": True, "commit": "d"},
        ],
        boundary_report=fitness_report,
    )

    assert report["surface"] == "mas_l5_audit_compaction_governance"
    assert report["lane_id"] == "L5_natural_boundary_and_audit_compaction"
    assert report["authority_mode"] == "maintainability_only"
    assert report["projection_only"] is True
    assert report["maintainability_only"] is True
    assert report["truth_writes"] == []
    assert report["truth_surfaces_out_of_scope"] == [
        "study_truth",
        "runtime_truth",
        "publication_truth",
        "delivery_truth",
    ]
    ownership = report["worktree_ownership_audit"]
    assert [item["branch"] for item in ownership["main"]] == ["main"]
    assert [item["branch"] for item in ownership["current_l5_worktree"]] == [
        "codex/mas-l5-compaction-structure"
    ]
    assert [item["branch"] for item in ownership["external_active_worktree"]] == [
        "codex/mas-pi-action-projection"
    ]
    assert ownership["unknown_owner"][0]["detached"] is True
    assert ownership["cleanup_candidates"] == []
    assert all(
        item["cleanup_allowed"] is False
        for bucket in ownership.values()
        if isinstance(bucket, list)
        for item in bucket
    )

    target_list = report["structure_target_list"]
    assert target_list["surface"] == "mas_l5_structure_top_target_list"
    assert target_list["source"] == "Sentrux structure lane + line budget + boundary fitness"
    assert [item["path"] for item in target_list["top_targets"]] == [
        "src/med_autoscience/controllers/domain_health_diagnostic.py",
        "src/med_autoscience/controllers/gate_clearing_batch.py",
    ]
    assert {item["action_kind"] for item in target_list["top_targets"]} == {"natural_boundary_split"}
    assert {item["truth_impact"] for item in target_list["top_targets"]} == {"maintainability_only"}

    pre_contract = report["audit_compaction_pre_contract"]
    assert pre_contract["implementation_status"] == "blocked_until_contract_passes"
    assert pre_contract["contract_passed"] is False
    assert pre_contract["required_proof_refs"] == [
        "restore_index_ref",
        "provenance_ref",
        "lifecycle_export_ref",
    ]
    assert [gate["gate_id"] for gate in pre_contract["gates"]] == ["restore", "index", "provenance"]
    assert report["compaction_implementation_allowed"] is False

    validation = module.validate_audit_compaction_governance_report(report)

    assert validation["ok"] is True
    assert validation["issues"] == []


def test_audit_compaction_governance_allows_passed_contract_with_restore_index_provenance_and_compatibility_refs() -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction_governance")
    boundary = importlib.import_module("med_autoscience.controllers.boundary_fitness")

    report = module.build_audit_compaction_governance_report(
        "/tmp",
        worktrees=[{"path": "/repo", "branch": "main", "commit": "a"}],
        boundary_report=boundary.BoundaryFitnessReport(findings=()),
        audit_compaction_contract={
            "gates": [
                {"gate_id": "restore", "status": "passed"},
                {"gate_id": "index", "status": "passed"},
                {"gate_id": "provenance", "status": "passed"},
            ],
            "restore_index_ref": "artifact://audit-compaction/restore-index.json",
            "provenance_ref": {"ref": "artifact://audit-compaction/provenance.json"},
            "lifecycle_export_ref": {"digest": "sha256:1234"},
        },
    )

    pre_contract = report["audit_compaction_pre_contract"]
    assert pre_contract["implementation_status"] == "contract_passed"
    assert pre_contract["contract_passed"] is True
    assert report["compaction_implementation_allowed"] is True

    validation = module.validate_audit_compaction_governance_report(report)

    assert validation["ok"] is True
    assert validation["issues"] == []


def test_audit_compaction_governance_reports_missing_proof_refs_when_gates_claim_passed() -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction_governance")
    boundary = importlib.import_module("med_autoscience.controllers.boundary_fitness")

    report = module.build_audit_compaction_governance_report(
        "/tmp",
        worktrees=[{"path": "/repo", "branch": "main", "commit": "a"}],
        boundary_report=boundary.BoundaryFitnessReport(findings=()),
        audit_compaction_contract={
            "gates": [
                {"gate_id": "restore", "status": "passed"},
                {"gate_id": "index", "status": "passed"},
                {"gate_id": "provenance", "status": "passed"},
            ],
            "restore_index_ref": "artifact://audit-compaction/restore-index.json",
        },
    )
    assert report["audit_compaction_pre_contract"]["contract_passed"] is False
    assert report["compaction_implementation_allowed"] is False

    validation = module.validate_audit_compaction_governance_report(report)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "missing_provenance_ref",
        "missing_lifecycle_export_ref",
    }


def test_audit_compaction_governance_validation_fails_closed_on_authority_cleanup_and_gate_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction_governance")

    report = module.build_audit_compaction_governance_report(
        "/tmp",
        worktrees=[{"path": "/repo", "branch": "main", "commit": "a"}],
        boundary_report=importlib.import_module(
            "med_autoscience.controllers.boundary_fitness"
        ).BoundaryFitnessReport(findings=()),
    )
    report["authority_mode"] = "runtime_authority"
    report["truth_writes"] = ["progress_projection"]
    report["truth_surfaces_out_of_scope"] = ["study_truth"]
    report["worktree_ownership_audit"]["cleanup_candidates"] = [
        {"path": "/repo/.worktrees/old", "cleanup_allowed": True}
    ]
    report["structure_target_list"]["top_targets"] = [
        {"path": "src/med_autoscience/controllers/domain_health_diagnostic.py", "action_kind": "mechanical_split"}
    ]
    report["audit_compaction_pre_contract"]["gates"] = [{"gate_id": "restore", "status": "contract_required"}]
    report["compaction_implementation_allowed"] = True

    validation = module.validate_audit_compaction_governance_report(report)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "l5_claims_non_maintainability_authority",
        "l5_declares_truth_writes",
        "missing_truth_surface_exclusion",
        "cleanup_allowed_without_absorb_authority",
        "structure_target_not_natural_boundary",
        "missing_compaction_pre_contract_gate",
        "compaction_allowed_before_contract_passes",
    }

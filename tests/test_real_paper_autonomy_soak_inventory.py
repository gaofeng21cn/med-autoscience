from __future__ import annotations

import json
import subprocess
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_guarded_apply_proof,
    build_real_paper_autonomy_soak_inventory,
    build_real_paper_autonomy_provider_hosted_paper_proof,
    build_real_paper_autonomy_soak_closeout_projection,
    build_real_paper_autonomy_soak_projection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_profile(workspace: Path, profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        "\n".join(
            [
                'name = "fixture"',
                f'workspace_root = "{workspace}"',
                f'runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace / "studies"}"',
                f'portfolio_root = "{workspace / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_real_paper_autonomy_soak_inventory_is_dry_run_and_reports_legacy_evidence(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "Fixture"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "fixture.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    (workspace / "ops" / "med-deepscientist" / "runtime" / "quests").mkdir(parents=True)
    (workspace / "ops" / "medautoscience" / "bin").mkdir(parents=True)
    launcher = workspace / "ops" / "medautoscience" / "bin" / "watch-runtime"
    launcher.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    status_path = _write_json(
        workspace / "studies" / "001-paper" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": "001-paper",
            "health_status": "inactive",
            "runtime_reason": "quest_parked_on_unchanged_finalize_state",
            "active_run_id": "",
        },
    )
    before_mtimes = {path: path.stat().st_mtime_ns for path in (profile_path, launcher, status_path)}

    payload = build_real_paper_autonomy_soak_inventory(yang_root=yang_root)

    assert payload["surface"] == "real_paper_autonomy_soak_inventory"
    assert payload["mode"] == "dry_run_inventory"
    assert payload["read_only_contract"]["writes_real_workspace"] is False
    assert payload["summary"]["writes_performed"] is False
    assert payload["profile_count"] == 1
    report = payload["profiles"][0]
    assert report["profile_readable"] is True
    assert report["migration_readiness"] == "dry_run_ready_legacy_evidence_present"
    assert report["status_progress_readability"] == {
        "study_count": 1,
        "readable_study_count": 1,
        "all_discovered_studies_readable": True,
    }
    assert report["studies"][0]["status"] == "parked"
    assert report["studies"][0]["reason"] == "quest_parked_on_unchanged_finalize_state"
    assert any(item["kind"] == "profile_path" for item in report["legacy_mds_evidence"])
    assert any(item["key"] == "ops/medautoscience/bin/watch-runtime" for item in report["legacy_mds_evidence"])
    assert not (workspace / "artifacts" / "runtime" / "real_paper_autonomy_soak_inventory.json").exists()
    assert {path: path.stat().st_mtime_ns for path in before_mtimes} == before_mtimes


def test_real_paper_autonomy_soak_inventory_reports_active_as_audit_only(tmp_path: Path) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "Active"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "active.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    _write_json(
        workspace / "studies" / "002-active" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": "002-active",
            "health_status": "running",
            "active_run_id": "run-123",
            "runtime_reason": "worker_running",
        },
    )

    payload = build_real_paper_autonomy_soak_inventory(yang_root=yang_root)

    report = payload["profiles"][0]
    assert report["migration_readiness"] == "audit_only_active_study_present"
    assert report["studies"][0]["status"] == "active"
    assert report["studies"][0]["active_run_id"] == "run-123"


def test_real_paper_autonomy_soak_inventory_script_outputs_json_without_writes(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "Script"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "script.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    _write_json(
        workspace / "studies" / "003-complete" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {"study_id": "003-complete", "quest_status": "completed", "runtime_reason": "done"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "--yang-root",
            str(yang_root),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["profile_count"] == 1
    assert payload["profiles"][0]["studies"][0]["status"] == "completed"
    assert not (workspace / "artifacts").exists()


def test_real_paper_autonomy_soak_projection_reports_dispatch_and_evidence_without_writes(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    study_root = workspace / "studies" / "DM002"
    sidecar_task = {
        "domain_id": "medautoscience",
        "task_kind": "paper_autonomy/repair-recheck",
        "dedupe_key": "reviewer_refinement_loop:dm002",
        "payload": {"study_id": "DM002"},
    }
    dispatch_receipt = {
        "surface_kind": "mas_family_sidecar_dispatch_receipt",
        "accepted": True,
        "dispatch": {"action_type": "paper_repair_executor_dispatch"},
    }
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": "DM002", "active_run_id": "run-1"})
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json",
        {"execution_status": "executed", "work_unit_type": "text_repair"},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {"progress_delta_candidate": True, "canonical_artifact_delta": {"meaningful_artifact_delta": True}},
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts" / "receipt.json",
        dispatch_receipt,
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "opl_family_sidecar" / "exported_task.json",
        sidecar_task,
    )
    before = {path: path.stat().st_mtime_ns for path in study_root.rglob("*.json")}

    payload = build_real_paper_autonomy_soak_projection(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002", "DM003", "Obesity"),
    )

    assert payload["surface"] == "real_paper_autonomy_soak_projection"
    assert payload["read_only_contract"]["writes_real_workspace"] is False
    assert payload["summary"]["target_studies"] == ["DM002", "DM003", "Obesity"]
    assert payload["summary"]["accepted_state_counts"]["artifact_delta"] == 1
    coverage = {item["target_study"]: item for item in payload["summary"]["target_coverage"]}
    assert coverage["DM002"]["status"] == "has_projection_evidence"
    assert coverage["DM002"]["matched_study_ids"] == ["DM002"]
    assert coverage["DM003"]["status"] == "typed_blocker"
    assert coverage["DM003"]["typed_blockers"][0]["blocker_id"] == "target_study_not_discovered:003"
    assert coverage["Obesity"]["status"] == "typed_blocker"
    assert payload["summary"]["typed_blocker_count"] == 2
    study = payload["profiles"][0]["studies"][0]
    assert study["study_id"] == "DM002"
    assert study["final_projection"] == "artifact_delta"
    assert study["sidecar_task"]["task_kind"] == "paper_autonomy/repair-recheck"
    assert study["dispatch_receipt"]["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    assert study["repair_execution_evidence"]["progress_delta_candidate"] is True
    assert study["ai_reviewer_evidence"]["owner"] == "ai_reviewer"
    assert {path: path.stat().st_mtime_ns for path in before} == before


def test_real_paper_autonomy_soak_projection_accepts_common_study_aliases(tmp_path: Path) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    for study_id in (
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "obesity_multicenter_phenotype_atlas",
    ):
        _write_json(
            workspace / "studies" / study_id / "artifacts" / "runtime" / "runtime_status_summary.json",
            {"study_id": study_id, "health_status": "running"},
        )

    payload = build_real_paper_autonomy_soak_projection(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002", "DM003", "Obesity"),
    )

    studies = {study["study_id"] for study in payload["profiles"][0]["studies"]}
    assert studies == {
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "obesity_multicenter_phenotype_atlas",
    }


def test_real_paper_autonomy_soak_closeout_projection_is_opl_ingestable_refs_only(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    dm003 = workspace / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    obesity = workspace / "studies" / "obesity_multicenter_phenotype_atlas"
    for study_root, eval_id in (
        (dm002, "eval-dm002"),
        (dm003, "eval-dm003"),
        (obesity, "eval-obesity"),
    ):
        _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": eval_id},
        )
        _write_json(
            study_root / "artifacts" / "controller_decisions" / "latest.json",
            {"next_owner": "write", "route_decision": "route_back_same_line"},
        )
    _write_json(
        dm003 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {"canonical_artifact_delta": {"meaningful_artifact_delta": True}},
    )
    _write_json(
        obesity / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {"progress_delta_candidate": True},
    )
    _write_json(
        obesity / "artifacts" / "stage_knowledge" / "paper_soak_memory_apply_proof" / "latest.json",
        {
            "status": "ready",
            "stage_entry": {
                "publication_route_memory_refs": [
                    {"memory_id": "publication_route_memory_seed__negative_result_stoploss"}
                ]
            },
            "mas_router_receipt_refs": [{"ref": "receipt:memory-router"}],
            "workspace_writeback_receipt_refs": [{"ref": "receipt:writeback"}],
            "opl_aion_readonly_receipt_refs": [{"ref": "receipt:aion", "body_included": False}],
        },
    )
    before = {path: path.stat().st_mtime_ns for path in workspace.rglob("*.json")}

    payload = build_real_paper_autonomy_soak_closeout_projection(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002", "DM003", "Obesity"),
    )

    assert payload["surface"] == "real_paper_autonomy_soak_closeout_projection"
    assert payload["summary"]["resolved_closeout_count"] == 3
    assert payload["summary"]["typed_blocker_count"] == 0
    assert payload["authority_boundary"]["opl_can_write_mas_truth"] is False
    assert "source_projection" not in payload
    assert "eval-dm002" not in json.dumps(payload, ensure_ascii=False)
    packets = {packet["route_impact"]["study_id"]: packet for packet in payload["closeout_packets"]}
    assert packets["002-dm-china-us-mortality-attribution"]["surface_kind"] == "domain_stage_closeout_packet"
    assert packets["002-dm-china-us-mortality-attribution"]["domain_ready_verdict"] == "ai_reviewer_re_eval"
    assert packets["003-dpcc-primary-care-phenotype-treatment-gap"]["domain_ready_verdict"] == "artifact_delta"
    assert packets["obesity_multicenter_phenotype_atlas"]["consumed_memory_refs"] == [
        "publication_route_memory_seed__negative_result_stoploss"
    ]
    assert packets["obesity_multicenter_phenotype_atlas"]["writeback_receipt_refs"] == [
        "receipt:memory-router",
        "receipt:writeback",
        "receipt:aion",
    ]
    assert all("publication_eval/latest.json" in packet["rejected_writes"][0]["forbidden_surfaces"] for packet in packets.values())
    assert {path: path.stat().st_mtime_ns for path in before} == before


def test_real_paper_autonomy_provider_hosted_paper_proof_is_readonly_and_guarded(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    dm003 = workspace / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    obesity = workspace / "studies" / "obesity_multicenter_phenotype_atlas"
    for study_root in (dm002, dm003, obesity):
        _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": f"eval-{study_root.name}"},
        )
    _write_json(
        dm003 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {"canonical_artifact_delta": {"meaningful_artifact_delta": True}},
    )
    _write_json(
        obesity / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {"progress_delta_candidate": True},
    )
    _write_json(
        dm002 / "artifacts" / "stage_knowledge" / "paper_soak_memory_apply_proof" / "latest.json",
        {
            "status": "ready",
            "stage_entry": {
                "publication_route_memory_refs": [
                    {"memory_id": "publication_route_memory_seed__negative_result_stoploss"}
                ]
            },
            "mas_router_receipt_refs": [{"ref": "receipt:memory-router"}],
            "workspace_writeback_receipt_refs": [{"ref": "receipt:writeback"}],
            "opl_aion_readonly_receipt_refs": [{"ref": "receipt:aion", "body_included": False}],
        },
    )
    before = {path: path.stat().st_mtime_ns for path in workspace.rglob("*.json")}

    payload = build_real_paper_autonomy_provider_hosted_paper_proof(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002", "DM003", "Obesity"),
    )

    assert payload["surface"] == "real_paper_autonomy_provider_hosted_paper_proof"
    assert payload["provider_hosted_status"] == "readonly_closeout_packet_ready_guarded_apply_pending"
    assert payload["provider_attempt_projection"]["attempt_owner"] == "one-person-lab"
    assert payload["provider_attempt_projection"]["guarded_apply_performed"] is False
    assert payload["summary"]["typed_closeout_packet_count"] == 3
    assert payload["summary"]["writes_performed"] is False
    assert payload["summary"]["guarded_apply_performed"] is False
    packets = {packet["route_impact"]["study_id"]: packet for packet in payload["typed_closeout_packets"]}
    assert packets["002-dm-china-us-mortality-attribution"]["domain_ready_verdict"] == "ai_reviewer_re_eval"
    assert packets["003-dpcc-primary-care-phenotype-treatment-gap"]["domain_ready_verdict"] == "artifact_delta"
    assert packets["obesity_multicenter_phenotype_atlas"]["domain_ready_verdict"] == "artifact_delta"
    assert payload["publication_route_memory"]["consumed_refs"] == [
        "publication_route_memory_seed__negative_result_stoploss"
    ]
    assert payload["publication_route_memory"]["writeback_receipt_refs"] == [
        "receipt:memory-router",
        "receipt:writeback",
        "receipt:aion",
    ]
    assert payload["publication_route_memory"]["body_included"] is False
    assert payload["publication_route_memory"]["opl_can_accept_or_reject_writeback"] is False
    guard = payload["forbidden_write_guard"]
    assert guard["aggregate_result"] == "fail_closed_no_forbidden_writes"
    assert guard["packet_guard_count"] == 3
    assert guard["blocked_probe"]["result"] == "blocked"
    assert "publication_eval" in guard["blocked_probe"]["forbidden_requested_writes"]
    assert guard["can_write_domain_truth"] is False
    assert guard["can_write_current_package"] is False
    assert {path: path.stat().st_mtime_ns for path in before} == before


def test_real_paper_autonomy_guarded_apply_proof_blocks_without_mas_owner_apply_receipt(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    dm003 = workspace / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    obesity = workspace / "studies" / "obesity_multicenter_phenotype_atlas"
    for study_root in (dm002, dm003, obesity):
        _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": f"eval-{study_root.name}"},
        )
    _write_json(
        dm002 / "artifacts" / "stage_knowledge" / "paper_soak_memory_apply_proof" / "latest.json",
        {
            "status": "ready",
            "stage_entry": {
                "publication_route_memory_refs": [
                    {"memory_id": "publication_route_memory_seed__negative_result_stoploss"}
                ]
            },
            "mas_router_receipt_refs": [{"ref": "receipt:memory-router"}],
            "workspace_writeback_receipt_refs": [{"ref": "receipt:writeback"}],
            "opl_aion_readonly_receipt_refs": [{"ref": "receipt:aion", "body_included": False}],
        },
    )
    before = {path: path.stat().st_mtime_ns for path in workspace.rglob("*.json")}

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002", "DM003", "Obesity"),
    )

    assert payload["surface"] == "real_paper_autonomy_guarded_apply_proof"
    assert payload["mode"] == "mas_owned_guarded_apply_proof"
    assert payload["guarded_apply_status"] == "blocked_no_mas_owner_apply_receipt"
    assert payload["provider_attempt_projection"]["attempt_owner"] == "one-person-lab"
    assert payload["provider_attempt_projection"]["guarded_apply_performed"] is False
    assert payload["provider_attempt_projection"]["can_advance_paper_progress_without_mas_owner_receipt"] is False
    assert payload["summary"]["writes_performed"] is False
    assert payload["summary"]["real_workspace_mutation_allowed"] is False
    assert payload["summary"]["guarded_apply_performed"] is False
    assert payload["summary"]["typed_blocker_count"] == 3
    assert payload["summary"]["mas_owner_apply_receipt_count"] == 0
    assert payload["summary"]["artifact_delta_or_gate_progress_count"] == 0
    assert payload["publication_route_memory_final_proof"]["target_study"] == "DM002"
    assert payload["publication_route_memory_final_proof"]["status"] == "final_ref_chain_proven"
    assert payload["publication_route_memory_final_proof"]["body_included"] is False
    assert payload["publication_route_memory_final_proof"]["consumed_refs"] == [
        "publication_route_memory_seed__negative_result_stoploss"
    ]
    assert payload["publication_route_memory_final_proof"]["writeback_receipt_refs"] == [
        "receipt:memory-router",
        "receipt:writeback",
        "receipt:aion",
    ]
    assert payload["publication_route_memory_final_proof"]["opl_can_read_memory_body"] is False
    assert payload["publication_route_memory_final_proof"]["opl_can_accept_or_reject_writeback"] is False
    blocker = payload["guarded_apply_receipts"][0]
    assert blocker["surface_kind"] == "mas_guarded_apply_receipt"
    assert blocker["apply_result"] == "typed_blocker"
    assert blocker["typed_blocker"]["blocker_id"].startswith("mas_owner_apply_receipt_missing:")
    assert blocker["typed_blocker"]["write_permitted"] is False
    assert blocker["workspace_mutation"]["writes_performed"] is False
    assert blocker["workspace_mutation"]["allowed_by_mas_owner_gate"] is False
    assert blocker["workspace_mutation"]["forbidden_surfaces"] == [
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "current_package",
        "publication_quality_verdict",
        "memory_body",
    ]
    guard = payload["forbidden_write_guard"]
    assert guard["aggregate_result"] == "fail_closed_no_forbidden_writes"
    assert guard["blocked_probe"]["result"] == "blocked"
    assert {path: path.stat().st_mtime_ns for path in before} == before


def test_real_paper_autonomy_guarded_apply_proof_accepts_existing_mas_owner_progress_receipt(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
    _write_json(
        dm002 / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )
    _write_json(
        dm002 / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json",
        {
            "surface": "paper_repair_owner_receipt",
            "accepted": True,
            "execution_status": "executed",
            "canonical_artifact_delta_refs": [{"path": str(dm002 / "paper" / "manuscript.md")}],
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "progress_delta_candidate": True,
        },
    )

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )

    assert payload["guarded_apply_status"] == "mas_owner_apply_receipt_observed"
    assert payload["summary"]["guarded_apply_performed"] is True
    assert payload["summary"]["real_workspace_mutation_allowed"] is True
    assert payload["summary"]["typed_blocker_count"] == 0
    assert payload["summary"]["mas_owner_apply_receipt_count"] == 1
    assert payload["summary"]["artifact_delta_or_gate_progress_count"] == 1
    receipt = payload["guarded_apply_receipts"][0]
    assert receipt["apply_result"] == "artifact_delta"
    assert receipt["workspace_mutation"]["allowed_by_mas_owner_gate"] is True
    assert receipt["workspace_mutation"]["writes_performed"] is True
    assert receipt["workspace_mutation"]["mutation_owner"] == "med-autoscience"
    assert receipt["workspace_mutation"]["provider_attempt_wrote_workspace"] is False
    assert receipt["mas_owner_apply_receipt_refs"]


def test_real_paper_autonomy_guarded_apply_proof_accepts_mas_owner_route_receipts(
    tmp_path: Path,
) -> None:
    cases = [
        (
            "route_decision",
            "route_decision",
            "artifacts/controller_decisions/latest.json",
            {"route_decision": "route_back_same_line", "next_owner": "write"},
        ),
        (
            "human_gate",
            "human_gate",
            "artifacts/controller_decisions/latest.json",
            {"route_decision": "route_back_same_line", "requires_human_confirmation": True},
        ),
        (
            "stop_loss",
            "stop_loss",
            "artifacts/controller_decisions/latest.json",
            {"route_decision": "stop_loss", "route_target": "stop"},
        ),
        (
            "stable_blocker",
            "stable_blocker",
            "artifacts/controller_decisions/latest.json",
            {"runtime_decision": "blocked", "blocked_reason": "owner surface blocked"},
        ),
        (
            "ai_reviewer_re_eval",
            "ai_reviewer_re_eval",
            "artifacts/publication_eval/latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
        ),
    ]
    for case_id, expected_result, expected_ref_suffix, owner_surface in cases:
        yang_root = tmp_path / case_id / "Yang"
        workspace = yang_root / "DM"
        profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
        _write_profile(workspace, profile_path)
        (workspace / "portfolio").mkdir(parents=True)
        dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
        _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
        if expected_ref_suffix == "artifacts/controller_decisions/latest.json":
            _write_json(dm002 / expected_ref_suffix, owner_surface)
        else:
            _write_json(dm002 / expected_ref_suffix, owner_surface)

        payload = build_real_paper_autonomy_guarded_apply_proof(
            yang_root=yang_root,
            profile_paths=[profile_path],
            target_studies=("DM002",),
        )

        assert payload["guarded_apply_status"] == "mas_owner_apply_receipt_observed"
        assert payload["summary"]["guarded_apply_performed"] is True
        assert payload["summary"]["typed_blocker_count"] == 0
        assert payload["summary"]["mas_owner_apply_receipt_count"] == 1
        receipt = payload["guarded_apply_receipts"][0]
        assert receipt["apply_result"] == expected_result
        assert receipt["workspace_mutation"]["allowed_by_mas_owner_gate"] is True
        assert receipt["workspace_mutation"]["provider_attempt_wrote_workspace"] is False
        assert receipt["mas_owner_apply_receipt_refs"] == [str(dm002 / expected_ref_suffix)]
        assert all(item["body_included"] is False for item in receipt["source_refs"])
        assert expected_ref_suffix in json.dumps(receipt["source_refs"], ensure_ascii=False)


def test_real_paper_autonomy_guarded_apply_proof_blocks_evidence_without_owner_receipt(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
    _write_json(
        dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "progress_delta_candidate": True,
        },
    )

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )

    assert payload["guarded_apply_status"] == "blocked_no_mas_owner_apply_receipt"
    assert payload["summary"]["guarded_apply_performed"] is False
    assert payload["summary"]["mas_owner_apply_receipt_count"] == 0
    receipt = payload["guarded_apply_receipts"][0]
    assert receipt["apply_result"] == "typed_blocker"
    assert receipt["mas_owner_apply_receipt_refs"] == []
    assert receipt["workspace_mutation"]["writes_performed"] is False


def test_real_paper_autonomy_soak_script_outputs_closeout_mode(tmp_path: Path) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    study_root = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "--yang-root",
            str(yang_root),
            "--profile",
            str(profile_path),
            "--mode",
            "closeout",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["surface"] == "real_paper_autonomy_soak_closeout_projection"
    assert payload["closeout_packets"][0]["domain_ready_verdict"] == "ai_reviewer_re_eval"
    assert payload["summary"]["writes_performed"] is False
    coverage = {item["target_study"]: item for item in payload["summary"]["target_coverage"]}
    assert coverage["DM002"]["status"] == "has_projection_evidence"
    assert coverage["DM003"]["status"] == "typed_blocker"
    assert coverage["Obesity"]["status"] == "typed_blocker"
    packets = {packet["route_impact"]["study_id"]: packet for packet in payload["closeout_packets"]}
    assert packets["DM003"]["domain_ready_verdict"] == "typed_blocker"
    assert packets["Obesity"]["domain_ready_verdict"] == "typed_blocker"
    assert payload["summary"]["typed_blocker_count"] == 2


def test_real_paper_autonomy_soak_script_outputs_provider_proof_mode(tmp_path: Path) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    study_root = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "--yang-root",
            str(yang_root),
            "--profile",
            str(profile_path),
            "--mode",
            "provider-proof",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["surface"] == "real_paper_autonomy_provider_hosted_paper_proof"
    assert payload["summary"]["writes_performed"] is False
    assert payload["summary"]["typed_closeout_packet_count"] == 3
    assert payload["summary"]["typed_blocker_count"] == 2
    assert payload["forbidden_write_guard"]["aggregate_result"] == "fail_closed_no_forbidden_writes"


def test_real_paper_autonomy_soak_script_outputs_guarded_apply_proof_mode(tmp_path: Path) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    study_root = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "--yang-root",
            str(yang_root),
            "--profile",
            str(profile_path),
            "--mode",
            "guarded-apply-proof",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["surface"] == "real_paper_autonomy_guarded_apply_proof"
    assert payload["guarded_apply_status"] == "blocked_no_mas_owner_apply_receipt"
    assert payload["summary"]["writes_performed"] is False
    assert payload["guarded_apply_receipts"][0]["apply_result"] == "typed_blocker"


def test_real_paper_autonomy_soak_projection_cli_reports_target_coverage(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    _write_json(
        workspace / "studies" / "002-dm-china-us-mortality-attribution" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {"study_id": "002-dm-china-us-mortality-attribution", "health_status": "running"},
    )
    _write_json(
        workspace / "studies" / "002-dm-china-us-mortality-attribution" / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "med_autoscience.cli",
            "real-paper-autonomy-soak-projection",
            "--yang-root",
            str(yang_root),
            "--target-study",
            "DM002",
            "--target-study",
            "DM003",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    coverage = {item["target_study"]: item for item in payload["summary"]["target_coverage"]}
    assert coverage["DM002"]["status"] == "has_projection_evidence"
    assert coverage["DM003"]["status"] == "typed_blocker"
    assert coverage["DM003"]["typed_blockers"][0]["write_permitted"] is False


def test_real_paper_autonomy_guarded_apply_proof_cli_reports_typed_blocker_without_writes(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    _write_json(
        workspace / "studies" / "002-dm-china-us-mortality-attribution" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {"study_id": "002-dm-china-us-mortality-attribution", "health_status": "running"},
    )
    _write_json(
        workspace / "studies" / "002-dm-china-us-mortality-attribution" / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "med_autoscience.cli",
            "real-paper-autonomy-guarded-apply-proof",
            "--yang-root",
            str(yang_root),
            "--profile",
            str(profile_path),
            "--target-study",
            "DM002",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["surface"] == "real_paper_autonomy_guarded_apply_proof"
    assert payload["summary"]["writes_performed"] is False
    assert payload["guarded_apply_receipts"][0]["apply_result"] == "typed_blocker"
    assert payload["guarded_apply_receipts"][0]["typed_blocker"]["required_owner_surface"] == (
        "MAS owner gate / guarded apply contract"
    )

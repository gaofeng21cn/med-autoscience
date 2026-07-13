from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_opl_generated_interfaces_compile_mas_standard_pack() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [str(opl_bin), "agents", "interfaces", "--repo-dir", str(REPO_ROOT), "--json"],
        cwd=opl_root,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    bundle = payload["generated_agent_interfaces"]

    assert bundle["source_kind"] == "standard_agent_repo_contracts"
    assert bundle["status"] == "ready"
    assert bundle["owner"] == "one-person-lab"
    assert bundle["domain_repo_can_own_generated_surface"] is False
    assert bundle["blocker_reasons"] == []
    assert bundle["cli"]["status"] == "ready"
    assert bundle["mcp"]["status"] == "ready"
    assert bundle["skill"]["status"] == "ready"
    assert bundle["product_entry"]["status"] == "ready"
    assert bundle["openai_tool"]["status"] == "ready"
    assert bundle["ai_sdk"]["status"] == "ready"
    cli_descriptors = bundle["cli"]["descriptors"]
    assert {descriptor["action_id"] for descriptor in cli_descriptors} == {
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    }
    for descriptor in cli_descriptors:
        assert descriptor["execution_binding"] == {
            "kind": "stage_binding",
            "stage_manifest_ref": "agent/stages/manifest.json",
        }
        assert descriptor["surface_kind"] == "opl_hosted_stage_action"
        assert descriptor["command"].startswith(
            f"opl agents run --domain mas --action {descriptor['action_id']} --workspace "
        )
        assert set(descriptor["required_fields"]).isdisjoint(
            descriptor["optional_fields"]
        )
        assert "callable_ref" not in descriptor
        assert "request" not in descriptor

    handler_descriptors = bundle["domain_handler"]["descriptors"]
    assert len(handler_descriptors) == 1
    assert handler_descriptors[0]["action_id"] == "paper_mission_authority_evaluate"
    assert handler_descriptors[0]["execution_binding"] == {
        "kind": "handler_ref",
        "handler_ref": "handler:mas.paper-mission-authority-evaluate",
    }
    stage_manifest = json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )
    assert {item["stage_id"] for item in bundle["stage_routes"]} == {
        stage["stage_id"] for stage in stage_manifest["stages"]
    }
    generated_plane = bundle["product_entry"]["family_stage_control_plane"]
    for stage in generated_plane["stages"]:
        runtime_event_refs = stage["stage_contract"].get("runtime_event_refs", [])
        if stage["trust_boundary"]["effect_boundary"]:
            assert runtime_event_refs == [
                f"runtime_event:{stage['stage_id']}.owner_receipt_recorded"
            ]
        else:
            assert runtime_event_refs == []


def test_opl_conformance_is_blocked_only_by_legacy_source_closure() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [str(opl_bin), "agents", "conformance", "--agent", f"mas={REPO_ROOT}", "--json"],
        cwd=opl_root,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)["standard_domain_agent_conformance"]
    assert report["status"] == "blocked"
    repo_report = report["reports"][0]
    assert repo_report["blockers"]
    assert all(blocker.startswith("source_closure:") for blocker in repo_report["blockers"])
    source_behavior = repo_report["source_behavior_checks"]
    assert source_behavior["status"] == "passed"
    assert source_behavior["matches"] == []
    source_closure = repo_report["source_closure_checks"]
    assert source_closure["scan_complete"] is True
    assert source_closure["status"] == "blocked"
    assert source_closure["unresolved_edges"]
    assert source_closure["audit_mismatches"]
    assert source_closure["unreachable_sensitive_residue"]
    assert all(
        effect["reachable"] is False
        for effect in source_closure["unreachable_sensitive_residue"]
    )

    expected_adapters = {
        "src/med_autoscience/controllers/mds_capability_parity/behavior_equivalence.py": (
            "mds_behavior_equivalence_provenance",
            "refs_only_domain_adapter",
        ),
    }
    allowed = {entry["path"]: entry["audit_coverage"] for entry in source_behavior["allowed_matches"]}
    for path, (module_id, migration_class) in expected_adapters.items():
        assert path in allowed
        assert any(
            item["module_id"] == module_id
            and item["migration_class"] == migration_class
            and item["active_callers"]
            for item in allowed[path]
        )


def test_opl_default_callers_record_mas_retirement_receipt_without_report_authority() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [
            str(opl_bin),
            "agents",
            "default-callers",
            "--agent",
            f"mas={REPO_ROOT}",
            "--json",
        ],
        cwd=opl_root,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    readiness = json.loads(result.stdout)["agent_default_caller_readiness"]
    assert readiness["status"] == "blocked"
    assert readiness["summary"]["generated_default_caller_surface_count"] == 8
    assert readiness["summary"]["blocked_surface_count"] == 0
    assert readiness["summary"]["surface_retirement_gate_count"] == 8
    assert readiness["summary"]["closed_surface_retirement_gate_count"] == 8
    assert readiness["summary"]["missing_domain_owner_receipt_or_typed_blocker_count"] == 0
    assert readiness["summary"]["deletion_evidence_worklist_count"] == 0
    assert readiness["summary"]["source_closure_verified_repo_count"] == 0
    assert readiness["summary"]["source_closure_blocked_repo_count"] == 1
    assert readiness["summary"]["source_closure_unresolved_edge_count"] > 0
    assert readiness["summary"]["source_closure_audit_mismatch_count"] > 0
    assert readiness["summary"]["default_caller_delete_ready"] is False
    assert readiness["summary"]["physical_delete_authorized"] is False
    assert readiness["summary"]["owner_decision_closeout_status"] == (
        "owner_decision_ref_observed_no_further_opl_delete_work"
    )
    assert readiness["migration_gate_policy"]["physical_delete_authorized_by_this_report"] is False
    assert readiness["migration_gate_policy"][
        "source_closure_pass_is_required_for_default_caller_replacement"
    ] is True
    assert readiness["migration_gate_policy"][
        "generated_default_caller_readiness_can_authorize_physical_delete"
    ] is False
    assert readiness["authority_boundary"]["report_can_authorize_domain_repo_physical_delete"] is False

    report = readiness["reports"][0]
    assert report["status"] == "blocked"
    assert report["source_closure"]["status"] == "blocked"
    assert report["deletion_gate"]["physical_delete_authorized"] is False
    assert report["deletion_gate"]["default_caller_delete_ready"] is False
    assert report["deletion_evidence_worklists"] == []


def test_opl_standard_scaffold_validates_mas_pack() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [str(opl_bin), "agents", "scaffold", "--validate", str(REPO_ROOT), "--json"],
        cwd=opl_root,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    validation = payload["standard_domain_agent_scaffold"]["validation"]

    assert validation["status"] == "passed"
    assert validation["blockers"] == []
    assert validation["missing_contract_files"] == []
    assert validation["missing_forbidden_role_guards"] == []

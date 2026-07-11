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
    first_cli = bundle["cli"]["descriptors"][0]
    assert first_cli["binding_kind"] == "python_callable"
    assert first_cli["callable_ref"] == (
        "med_autoscience.domain_entry:MedAutoScienceDomainEntry.dispatch"
    )
    assert first_cli["request"] == {"command": first_cli["action_id"]}
    assert set(first_cli["required_fields"]).isdisjoint(first_cli["optional_fields"])
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


def test_opl_default_callers_project_mas_delete_evidence_as_pending_without_authority() -> None:
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
    assert readiness["status"] == "ready_domain_evidence_required"
    assert readiness["summary"]["generated_default_caller_surface_count"] == 8
    assert readiness["summary"]["missing_domain_owner_receipt_or_typed_blocker_count"] == 6
    assert readiness["summary"]["deletion_evidence_worklist_count"] == 6
    assert readiness["summary"]["default_caller_delete_ready"] is False
    assert readiness["summary"]["physical_delete_authorized"] is False
    assert readiness["summary"]["owner_decision_closeout_status"] == (
        "waiting_for_structural_prerequisites"
    )
    assert readiness["migration_gate_policy"]["physical_delete_authorized_by_this_report"] is False
    assert readiness["migration_gate_policy"][
        "generated_default_caller_readiness_can_authorize_physical_delete"
    ] is False
    assert readiness["authority_boundary"]["report_can_authorize_domain_repo_physical_delete"] is False

    report = readiness["reports"][0]
    assert report["deletion_gate"]["physical_delete_authorized"] is False
    assert report["deletion_gate"]["default_caller_delete_ready"] is False
    assert len(report["deletion_evidence_worklists"]) == 6
    assert all(
        item["status"] == "domain_evidence_required"
        for item in report["deletion_evidence_worklists"]
    )
    assert len(report["surface_gates"]) == 8
    assert all(
        item["status"] == "ready_for_default_caller_cutover"
        for item in report["surface_gates"]
    )
    assert len(report["surface_retirement_gates"]) == 8
    assert sum(
        item["status"] == "domain_evidence_required"
        for item in report["surface_retirement_gates"]
    ) == 6


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

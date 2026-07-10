from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LIGHT_EXTERNAL_PATTERN_INTAKE_STAGE_IDS = {
    "direction_and_route_selection",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
}


def test_light_external_pattern_intake_projects_into_stage_surfaces_as_refs_only() -> None:
    generated = json.loads(
        (REPO_ROOT / "contracts/stage_control_plane.json").read_text(encoding="utf-8")
    )
    stages_by_id = {
        stage["stage_id"]: stage for stage in generated["stages"]
    }

    assert LIGHT_EXTERNAL_PATTERN_INTAKE_STAGE_IDS <= set(stages_by_id)
    for stage_id, stage in stages_by_id.items():
        stage_has_light_intake = "external_pattern_intake_pack" in stage["quality_pack_refs"]
        assert stage_has_light_intake is (stage_id in LIGHT_EXTERNAL_PATTERN_INTAKE_STAGE_IDS)
        assert stage["quality_pack_projection"]["pack_refs"] == stage["quality_pack_refs"]
        assert stage["codex_cli_launch_packet"]["quality_pack_refs"] == stage["quality_pack_refs"]

        projection = stage["quality_pack_projection"]
        assert projection["role"] == "quality_input_and_reviewer_rubric"
        assert projection["opl_projection_boundary"] == "descriptor_ref_freshness_locator_only"
        assert projection["publication_readiness_authority"] is False
        assert projection["quality_verdict_authority"] is False
        assert projection["runtime_permission_authority"] is False

        skill_projection = stage["stage_skill_surface_projection"]
        assert "external_pattern_intake_pack" in skill_projection["quality_pack_refs"]
        skill_boundary = skill_projection["authority_boundary"]
        assert skill_boundary["can_write_mas_truth"] is False
        assert skill_boundary["can_authorize_publication_readiness"] is False
        assert skill_boundary["can_authorize_quality_verdict"] is False


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
    generated = json.loads(
        (REPO_ROOT / "contracts/stage_control_plane.json").read_text(encoding="utf-8")
    )
    assert {item["stage_id"] for item in bundle["stage_routes"]} == {
        stage["stage_id"] for stage in generated["stages"]
    }


def test_opl_default_callers_project_mas_delete_authorization_without_becoming_authority() -> None:
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
    assert readiness["summary"]["missing_domain_owner_receipt_or_typed_blocker_count"] == 0
    assert readiness["summary"]["missing_no_forbidden_write_proof_count"] == 0
    assert readiness["summary"]["missing_tombstone_or_provenance_ref_count"] == 0
    assert readiness["summary"]["physical_delete_authorized"] is True
    assert readiness["summary"]["owner_decision_result_shape"] == (
        "physical_delete_authorization_ref"
    )
    assert readiness["migration_gate_policy"]["physical_delete_authorized_by_this_report"] is True
    assert readiness["migration_gate_policy"][
        "generated_default_caller_readiness_can_authorize_physical_delete"
    ] is False
    assert readiness["authority_boundary"]["report_can_authorize_domain_repo_physical_delete"] is False

    report = readiness["reports"][0]
    assert report["deletion_gate"]["physical_delete_authorized"] is True
    assert report["deletion_gate"]["owner_decision_result_shape"] == (
        "physical_delete_authorization_ref"
    )
    assert report["deletion_evidence_worklists"] == []
    assert "surface_gates" not in report
    assert "surface_retirement_gates" not in report
    assert report["closed_surface_detail_policy"] == (
        "closed_retirement_gate_details_omitted_from_default_payload"
    )


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

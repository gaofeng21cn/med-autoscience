from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_CATEGORIES = {
    "currentness",
    "stale_dispatch",
    "provider_terminal_sync",
    "owner_precedence",
    "paper_delta_missing",
    "quality_authority_stale",
}

FORBIDDEN_RUNTIME_FILES = {
    "src/med_autoscience/controllers/runtime_control/owner_route.py",
    "src/med_autoscience/controllers/domain_action_request_materializer.py",
    "src/med_autoscience/controllers/domain_owner_action_dispatch.py",
}


def test_unique_control_plane_canary_registry_covers_dm002_dm003_categories() -> None:
    module = importlib.import_module("med_autoscience.controllers.unique_control_plane_canary_registry")

    registry = module.build_unique_control_plane_canary_registry()
    canaries = registry["canaries"]

    assert registry["surface_kind"] == "opl_unique_control_plane_canary_registry"
    assert registry["registry_id"] == "opl-unique-control-plane-canary-registry-dm002-dm003-v1"
    assert registry["migration_semantics"] == {
        "program": "mas_duplicate_runtime_retirement",
        "canonical_control_plane_owner": "OPL",
        "domain_owner": "MedAutoScience",
        "duplicate_mas_runtime_claimed": False,
    }
    assert registry["target_studies"] == ["DM002", "DM003"]
    assert {canary["category"] for canary in canaries} == EXPECTED_CATEGORIES

    for canary in canaries:
        assert canary["canary_id"].startswith("opl-unique-control-plane-canary:")
        assert set(canary["target_studies"]) <= {"DM002", "DM003"}
        assert canary["semantic_role"] == "mas_duplicate_runtime_retirement_regression"
        assert canary["mas_fixture_refs"]
        assert canary["opl_transport_fixture_refs"]
        assert canary["owner_route_regression_refs"]
        assert canary["no_forbidden_write_proof_refs"]
        assert canary["work_order_refs"]
        assert any(ref.startswith(("tests/", "contracts/")) for ref in canary["mas_fixture_refs"])
        assert all(ref.startswith(("opl:", "contracts/")) for ref in canary["opl_transport_fixture_refs"])
        assert all(ref.startswith(("tests/", "regression-suite:")) for ref in canary["owner_route_regression_refs"])
        assert all(ref.startswith(("tests/", "no-forbidden-write:")) for ref in canary["no_forbidden_write_proof_refs"])
        assert all(ref.startswith("work-order:opl/unique-control-plane-canary/") for ref in canary["work_order_refs"])


def test_agent_lab_outputs_executable_work_orders_with_mas_authority_limits() -> None:
    module = importlib.import_module("med_autoscience.controllers.unique_control_plane_canary_registry")

    for canary in module.build_unique_control_plane_canary_registry()["canaries"]:
        loop = canary["agent_lab_regression_loop"]
        work_order = loop["developer_patch_work_order"]

        assert loop["output_mode"] == "executable_regression_work_order"
        assert loop["executable"] is True
        assert loop["suite_ref"].startswith("agent-lab-suite:opl/unique-control-plane-canary/")
        assert loop["work_order_ref"] in canary["work_order_refs"]
        assert "recommendation" not in json.dumps(loop, sort_keys=True)

        assert work_order["work_order_id"].startswith("oma_developer_patch_work_order_opl_ucp_canary_")
        assert work_order["owner_agent"] == "opl-meta-agent"
        assert work_order["role"] == "developer_direct_repo_patch"
        assert work_order["can_modify_mas_repo"] is True
        assert work_order["can_write_study_truth"] is False
        assert work_order["can_authorize_quality_verdict"] is False
        assert work_order["executable"] is True
        assert work_order["canary_id"] == canary["canary_id"]
        assert work_order["category"] == canary["category"]
        assert set(canary["owner_route_regression_refs"]) <= set(work_order["target_test_refs"])
        assert set(canary["mas_fixture_refs"]) <= set(work_order["mas_fixture_refs"])
        assert set(canary["opl_transport_fixture_refs"]) <= set(work_order["opl_transport_fixture_refs"])
        assert set(canary["no_forbidden_write_proof_refs"]) <= set(work_order["no_forbidden_write_proof_refs"])
        assert not (FORBIDDEN_RUNTIME_FILES & set(work_order["allowed_patch_refs"]))
        assert FORBIDDEN_RUNTIME_FILES <= set(work_order["forbidden_patch_refs"])
        assert any(ref.startswith("scripts/run-pytest-clean.sh ") for ref in work_order["verification_command_refs"])
        assert any(ref.startswith("opl agent-lab run ") for ref in work_order["verification_command_refs"])


def test_repo_tracked_contract_matches_runtime_registry_and_ref_coverage_proof() -> None:
    module = importlib.import_module("med_autoscience.controllers.unique_control_plane_canary_registry")

    contract = json.loads(
        (REPO_ROOT / "contracts" / "unique_control_plane_canary_registry.json").read_text(encoding="utf-8")
    )

    assert contract == module.build_unique_control_plane_canary_registry()
    proof = contract["coverage_proof"]
    assert proof["covers_mas_fixture_refs"] is True
    assert proof["covers_opl_transport_fixture_refs"] is True
    assert proof["covers_owner_route_regression_refs"] is True
    assert proof["covers_no_forbidden_write_proof_refs"] is True
    assert set(proof["required_ref_groups"]) == {
        "mas_fixture_refs",
        "opl_transport_fixture_refs",
        "owner_route_regression_refs",
        "no_forbidden_write_proof_refs",
    }
    assert "contracts/unique_control_plane_canary_registry.json" in proof["contract_refs"]

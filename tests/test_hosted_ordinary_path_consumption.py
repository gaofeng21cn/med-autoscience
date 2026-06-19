from __future__ import annotations

import importlib
import json
from pathlib import Path


def _delta() -> dict[str, str]:
    return {
        "action_type": "run_quality_repair_batch",
        "action_id": "dispatch-001",
        "owner": "MedAutoScience",
        "work_unit_id": "repair-story",
        "work_unit_fingerprint": "sha256:repair-story",
        "source_ref": "projection/current_owner_delta.json",
    }


def test_hosted_ordinary_path_consumption_evidence_uses_agent_hot_path_surfaces() -> None:
    module = importlib.import_module("med_autoscience.hosted_ordinary_path_consumption")

    evidence = module.build_hosted_ordinary_path_consumption_evidence(
        current_owner_delta=_delta()
    )

    assert evidence["surface_kind"] == "mas_hosted_ordinary_path_consumption_evidence"
    assert evidence["status"] == "ready_for_hosted_consumption"
    assert evidence["ordinary_planning_root"] == "current_owner_delta"
    assert evidence["hosted_runtime_owner"] == "one-person-lab"
    assert evidence["domain_owner"] == "MedAutoScience"
    assert evidence["ordinary_path_consumes"] == {
        "agent_execution_index": True,
        "operational_tool_card": True,
        "capability_invocation_plan": True,
        "tool_result_envelope_recovery": True,
        "scientific_capability_resolution": True,
        "owner_consumption_evidence_packet": False,
    }
    assert evidence["agent_execution_index_ref"] == (
        "contracts/agent_tool_arsenal.json#/agent_execution_index"
    )
    assert evidence["primary_operational_card"]["card_kind"] == "owner_callable"
    assert evidence["primary_operational_card"]["tool_id"] == (
        "owner_callable:run_quality_repair_batch"
    )
    assert "verify_required_input_refs" in evidence["capability_invocation_plan"][
        "invocation_steps"
    ]
    assert evidence["capability_invocation_plan"][
        "requires_owner_receipt_or_typed_blocker"
    ] is True
    assert evidence["capability_invocation_plan"]["executor_receipt_ref_required"] is False
    assert evidence["capability_invocation_plan"][
        "support_or_diagnostic_tools_auto_selected"
    ] is False
    assert evidence["capability_invocation_plan"]["missing_capability_default"] == (
        "fail_open_unless_hard_gate"
    )
    assert evidence["result_envelope_schema_ref"] == (
        "contracts/agent_tool_arsenal.json#/result_envelope_schema"
    )
    assert evidence["lightweight_executor_receipt_contract_ref"] == (
        "src/med_autoscience/lightweight_executor_receipts.py::"
        "build_lightweight_executor_receipt_contract"
    )
    assert evidence["scientific_capability_resolution"]["status"] == "resolved"
    assert evidence["scientific_capability_resolution"]["fail_open"] is True
    assert evidence["scientific_capability_resolution"][
        "mainline_waits_for_capability"
    ] is False
    assert evidence["scientific_capability_resolution"][
        "missing_capability_blocks_owner_action"
    ] is False
    selected_ids = {
        item["capability_id"]
        for item in evidence["scientific_capability_resolution"]["selected_capabilities"]
    }
    assert "external_learning_authoring_advisory" in selected_ids
    assert "light_external_skill_content_advisory" not in selected_ids
    assert "evo_scientist_progress_sidecar" not in selected_ids
    explicit_evidence = module.build_hosted_ordinary_path_consumption_evidence(
        current_owner_delta={
            **_delta(),
            "capability_families": ["light_external_skill_content_advisory"],
        }
    )
    explicit_selected = {
        item["capability_id"]: item
        for item in explicit_evidence["scientific_capability_resolution"][
            "selected_capabilities"
        ]
    }
    assert explicit_selected["light_external_skill_content_advisory"][
        "wildcard_action_trigger_policy"
    ] == {
        "auto_select": False,
        "requires_explicit_capability_request": True,
        "reason": "support_or_diagnostic_wildcards_must_not_become_mas_private_selectors",
    }
    assert evidence["owner_consumption_evidence"] is None


def test_hosted_ordinary_path_consumption_evidence_records_owner_consumed_refs_without_authority(
    tmp_path: Path,
) -> None:
    capability_registry = importlib.import_module(
        "med_autoscience.scientific_capability_registry"
    )
    module = importlib.import_module("med_autoscience.hosted_ordinary_path_consumption")
    study_root = tmp_path / "studies" / "001-risk"
    invocation = capability_registry.invoke_scientific_capability(
        capability_id="external_learning_authoring_advisory",
        study_root=study_root,
        current_owner_delta=_delta(),
        apply=True,
    )

    evidence = module.build_hosted_ordinary_path_consumption_evidence(
        current_owner_delta=_delta(),
        invocation_result=invocation,
        owner_response_refs={
            "typed_blocker_ref": (
                "artifacts/stage_outputs/08-publication_package_handoff/"
                "receipts/typed_blocker.json"
            ),
            "route_back_evidence_ref": "artifacts/routes/route-back.json",
        },
    )

    assert evidence["ordinary_path_consumes"]["owner_consumption_evidence_packet"] is True
    consumption = evidence["owner_consumption_evidence"]
    assert consumption["surface_kind"] == (
        "mas_scientific_capability_owner_consumption_evidence"
    )
    assert consumption["owner_consumption_status"] == "owner_response_refs_observed"
    assert consumption["typed_blocker_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )
    assert consumption["route_back_evidence_ref"] == "artifacts/routes/route-back.json"
    assert consumption["counts_as_progress"] is False
    assert consumption["can_authorize_owner_action"] is False
    assert consumption["mainline_waits_for_owner_consumption"] is False
    assert consumption["missing_owner_response_refs_blocks"] is False
    assert consumption["fail_open"] is True
    assert evidence["authority_boundary"] == {
        "evidence_packet_is_authority_outcome": False,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_authorize_publication_quality": False,
        "can_authorize_artifact_authority": False,
        "can_block_current_owner_action": False,
    }
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_hosted_ordinary_path_consumption_contract_stays_friction_free() -> None:
    module = importlib.import_module("med_autoscience.hosted_ordinary_path_consumption")

    contract = module.build_hosted_ordinary_path_consumption_contract()

    assert contract["surface_kind"] == "mas_hosted_ordinary_path_consumption_contract"
    assert contract["planning_root"] == "current_owner_delta"
    assert contract["required_consumed_surfaces"] == [
        "agent_execution_index",
        "operational_tool_card",
        "capability_invocation_plan",
        "tool_result_envelope_recovery",
        "scientific_capability_resolution",
        "owner_consumption_evidence_packet",
    ]
    assert contract["friction_policy"] == {
        "human_operator_manual_tool_selection_required": False,
        "raw_contract_direct_read_required": False,
        "new_default_preflight": False,
        "sidecar_blocks_owner_action": False,
        "missing_capability_blocks_owner_action": False,
        "missing_owner_response_refs_blocks": False,
        "docker_or_dind_required": False,
    }
    assert contract["authority_boundary"] == {
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_publication_quality": False,
        "opl_can_write_owner_receipt": False,
        "opl_can_write_typed_blocker": False,
        "evidence_packet_can_claim_paper_progress": False,
    }
    assert json.dumps(contract["sample_evidence"], sort_keys=True)

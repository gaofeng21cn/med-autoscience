from __future__ import annotations

import importlib
import json
from pathlib import Path


def _structured_payload(result: dict[str, object]) -> dict[str, object]:
    structured = result["structuredContent"]
    assert isinstance(structured, dict)
    assert structured["surface_kind"] == "mas_tool_result_envelope"
    payload = structured["structured_payload"]
    assert isinstance(payload, dict)
    return payload


def test_scientific_capability_registry_resolves_current_delta_bound_candidates() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    registry = module.build_scientific_capability_registry()
    resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "repair-story",
            "work_unit_fingerprint": "sha256:repair",
        }
    )

    assert registry["surface_kind"] == "mas_scientific_capability_registry"
    assert registry["default_policy"]["fail_open"] is True
    assert registry["default_policy"]["always_on_scan"] is False
    assert registry["authority_boundary"]["can_write_domain_truth"] is False
    assert registry["authority_boundary"]["can_write_owner_receipt"] is False
    capability_ids = {item["capability_id"] for item in registry["capabilities"]}
    assert {
        "external_learning_authoring_advisory",
        "evo_scientist_progress_sidecar",
        "light_external_skill_content_advisory",
        "co_scientist_current_owner_affordance",
        "display_pack_visual_capability",
    } <= capability_ids

    selected = {item["capability_id"]: item for item in resolution["selected_capabilities"]}
    assert resolution["surface_kind"] == "mas_scientific_capability_resolution"
    assert resolution["status"] == "resolved"
    assert resolution["mainline_waits_for_capability"] is False
    assert resolution["missing_capability_blocks_owner_action"] is False
    assert selected["external_learning_authoring_advisory"]["invocation_kind"] == (
        "external_learning_sidecar"
    )
    assert selected["co_scientist_current_owner_affordance"]["invocation_kind"] == (
        "descriptor_only_current_owner_input_refs"
    )
    assert all(item["refs_only"] is True for item in selected.values())
    assert all(item["can_block_current_owner_action"] is False for item in selected.values())


def test_scientific_capability_registry_invokes_external_learning_sidecar_refs_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"

    result = module.invoke_scientific_capability(
        capability_id="external_learning_authoring_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "action_id": "dispatch-001",
            "owner_route": {
                "owner": "quality_repair_batch",
                "work_unit_id": "repair-story",
                "work_unit_fingerprint": "sha256:repair",
            },
        },
        apply=True,
    )

    result_path = study_root / "artifacts/advisory/external_learning_sidecar/latest.json"
    assert result["surface_kind"] == "mas_scientific_capability_invocation"
    assert result["status"] == "invoked"
    assert result["refs_only"] is True
    assert result["mainline_waits_for_capability"] is False
    assert result["authority_boundary"]["can_write_publication_eval"] is False
    assert result_path.is_file()
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["surface_kind"] == "mas_external_learning_sidecar_result"
    assert payload["refs_only"] is True
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_builds_nonblocking_consumption_evidence_without_owner_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    invocation = module.invoke_scientific_capability(
        capability_id="external_learning_authoring_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "action_id": "dispatch-001",
            "work_unit_id": "repair-story",
            "work_unit_fingerprint": "sha256:repair",
            "source_ref": "artifacts/controller_decisions/latest.json",
        },
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "action_id": "dispatch-001",
            "work_unit_id": "repair-story",
            "work_unit_fingerprint": "sha256:repair",
            "source_ref": "artifacts/controller_decisions/latest.json",
        },
    )

    assert evidence["surface_kind"] == "mas_scientific_capability_owner_consumption_evidence"
    assert evidence["schema_version"] == 1
    assert evidence["refs_only"] is True
    assert evidence["capability_id"] == "external_learning_authoring_advisory"
    assert evidence["output_refs"] == ["artifacts/advisory/external_learning_sidecar/latest.json"]
    assert evidence["current_owner_delta_identity"] == {
        "action_type": "run_quality_repair_batch",
        "action_id": "dispatch-001",
        "owner": "",
        "work_unit_id": "repair-story",
        "work_unit_fingerprint": "sha256:repair",
        "source_ref": "artifacts/controller_decisions/latest.json",
    }
    assert evidence["owner_consumption_status"] == "no_owner_response_refs"
    assert evidence["owner_receipt_ref"] is None
    assert evidence["typed_blocker_ref"] is None
    assert evidence["reviewer_receipt_ref"] is None
    assert evidence["route_back_evidence_ref"] is None
    assert evidence["counts_as_progress"] is False
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["mainline_waits_for_owner_consumption"] is False
    assert evidence["fail_open"] is True
    assert evidence["missing_owner_response_refs_blocks"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert evidence["no_forbidden_write_proof"]["checked_relative_refs"] == [
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
        "paper",
        "package",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
    ]
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_consumption_evidence_with_owner_refs_stays_non_authorizing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    invocation = module.invoke_scientific_capability(
        capability_id="external_learning_review_and_progress_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "unit_harmonized_external_validation_rerun",
            "action_id": "dispatch-002",
            "owner": "MedAutoScience",
            "work_unit_id": "external-validation",
            "work_unit_fingerprint": "sha256:external-validation",
            "source_ref": "projection/current_owner_delta.json",
        },
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta={
            "action_type": "unit_harmonized_external_validation_rerun",
            "action_id": "dispatch-002",
            "owner": "MedAutoScience",
            "work_unit_id": "external-validation",
            "work_unit_fingerprint": "sha256:external-validation",
            "source_ref": "projection/current_owner_delta.json",
        },
        owner_response_refs={
            "owner_receipt_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
            "reviewer_receipt_ref": "artifacts/reviewer/receipt.json",
            "route_back_evidence_ref": "artifacts/routes/route-back.json",
        },
    )

    assert evidence["owner_consumption_status"] == "owner_response_refs_observed"
    assert evidence["owner_receipt_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json"
    )
    assert evidence["typed_blocker_ref"] is None
    assert evidence["reviewer_receipt_ref"] == "artifacts/reviewer/receipt.json"
    assert evidence["route_back_evidence_ref"] == "artifacts/routes/route-back.json"
    assert evidence["counts_as_progress"] is False
    assert evidence["consumption_evidence_only"] is True
    assert evidence["authority_boundary"]["can_write_owner_receipt"] is False
    assert evidence["authority_boundary"]["can_write_typed_blocker"] is False
    assert evidence["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_invokes_light_and_evo_without_authority_writes(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    light = module.invoke_scientific_capability(
        capability_id="light_external_skill_content_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "study_id": "001-risk",
            "work_unit_id": "repair-story",
            "source_refs": ["study.yaml"],
        },
        payload={
            "fresh_evidence_gate": {"claim_supported": True},
            "argument_review_hint": {"claim_boundary_state": "bounded"},
        },
        apply=True,
    )
    evo = module.invoke_scientific_capability(
        capability_id="evo_scientist_progress_sidecar",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "study_id": "001-risk",
            "source_ref": "artifacts/controller_decisions/latest.json",
            "work_unit_id": "repair-story",
        },
        payload={"executor_turn_summary_ref": "artifacts/executor/turn.json"},
        apply=True,
    )

    assert light["result"]["surface_kind"] == "light_external_advisory_materializer"
    assert light["result"]["light_runtime_dependency"] is False
    assert (
        study_root
        / "artifacts/stage_outputs/current_owner_action/advisory/light_external_pattern_refs.json"
    ).is_file()
    assert evo["result"]["surface_kind"] == "mas_evo_scientist_sidecar_observation"
    assert evo["result"]["counts_as_owner_answer"] is False
    assert (study_root / "artifacts/runtime/evo_scientist_sidecar/latest.json").is_file()
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_mcp_modes_and_tool_arsenal_card(
    tmp_path: Path,
) -> None:
    mcp = importlib.import_module("med_autoscience.mcp_server")
    arsenal_module = importlib.import_module("med_autoscience.agent_tool_arsenal")
    tools = {tool["name"]: tool for tool in mcp.build_tool_manifest()}

    assert "scientific_capability_registry" in tools
    assert tools["scientific_capability_registry"]["inputSchema"]["properties"]["mode"]["enum"] == [
        "index",
        "resolve",
        "invoke",
    ]

    resolve_result = mcp.call_tool(
        "scientific_capability_registry",
        {
            "mode": "resolve",
            "current_owner_delta": {
                "action_type": "unit_harmonized_external_validation_rerun",
                "work_unit_id": "external-validation",
            },
        },
    )
    assert resolve_result["isError"] is False
    resolve_envelope = resolve_result["structuredContent"]
    assert resolve_envelope["surface_kind"] == "mas_tool_result_envelope"
    assert resolve_envelope["tool_id"] == "scientific_capability_registry"
    assert resolve_envelope["tool_mode"] == "resolve"
    assert resolve_envelope["status"] == "succeeded"
    assert resolve_envelope["authority_boundary"]["tool_result_envelope_is_authority_outcome"] is False
    assert resolve_envelope["authority_boundary"]["can_write_domain_truth"] is False
    assert resolve_envelope["authority_boundary"]["can_authorize_publication_quality"] is False
    assert "publication_quality" in resolve_envelope["audit_trail"]["forbidden_authority"]
    resolve_payload = resolve_envelope["structured_payload"]
    assert resolve_payload["surface_kind"] == "mas_scientific_capability_resolution"
    selected = {
        item["capability_id"]
        for item in resolve_payload["selected_capabilities"]
    }
    assert "external_learning_review_and_progress_advisory" in selected

    invoke_result = mcp.call_tool(
        "scientific_capability_registry",
        {
            "mode": "invoke",
            "capability_id": "external_learning_review_and_progress_advisory",
            "study_root": str(tmp_path / "studies" / "001-risk"),
            "current_owner_delta": {
                "action_type": "unit_harmonized_external_validation_rerun",
                "action_id": "dispatch-001",
                "owner_route": {
                    "owner": "source_truth",
                    "work_unit_id": "external-validation",
                    "work_unit_fingerprint": "sha256:external-validation",
                },
            },
        },
    )
    assert invoke_result["isError"] is False
    invoke_envelope = invoke_result["structuredContent"]
    assert invoke_envelope["surface_kind"] == "mas_tool_result_envelope"
    assert invoke_envelope["tool_id"] == "scientific_capability_registry"
    assert invoke_envelope["tool_mode"] == "invoke"
    assert invoke_envelope["audit_trail"]["authority_flags"]["readOnlyHint"] is False
    assert invoke_envelope["audit_trail"]["authority_flags"]["destructiveHint"] is False
    assert (
        "artifacts/advisory/external_learning_sidecar/latest.json"
        in invoke_envelope["audit_trail"]["allowed_write_refs"]
    )
    assert invoke_envelope["authority_boundary"]["can_write_domain_truth"] is False
    assert invoke_envelope["authority_boundary"]["can_authorize_submission_readiness"] is False
    assert invoke_envelope["structured_payload"]["surface_kind"] == (
        "mas_scientific_capability_invocation"
    )

    arsenal = arsenal_module.build_agent_tool_arsenal_index()
    assert arsenal["scientific_capability_registry"]["surface_kind"] == (
        "mas_scientific_capability_registry"
    )
    plan = arsenal_module.build_capability_invocation_plan(
        current_owner_delta={
            "action_type": "scientific_capability_registry",
            "source_ref": "artifacts/controller_decisions/latest.json",
        },
        arsenal=arsenal,
    )
    assert plan["selected_card_kind"] == "action_catalog"
    assert plan["selected_tool_id"] == "scientific_capability_registry"
    assert plan["authority_boundary"]["can_write_domain_truth"] is False


def test_scientific_capability_registry_cli_modes_emit_json(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"

    exit_code = cli.main(["scientific-capability-registry", "--mode", "index"])
    assert exit_code == 0
    index_payload = json.loads(capsys.readouterr().out)
    assert index_payload["surface_kind"] == "mas_scientific_capability_registry"
    assert index_payload["default_policy"]["fail_open"] is True

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "resolve",
            "--current-owner-delta-json",
            json.dumps({"action_type": "run_quality_repair_batch"}),
        ]
    )
    assert exit_code == 0
    resolve_payload = json.loads(capsys.readouterr().out)
    assert resolve_payload["surface_kind"] == "mas_scientific_capability_resolution"
    assert resolve_payload["status"] == "resolved"

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "invoke",
            "--capability-id",
            "external_learning_authoring_advisory",
            "--study-root",
            str(study_root),
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "run_quality_repair_batch",
                    "owner_route": {
                        "owner": "quality_repair_batch",
                        "work_unit_id": "repair-story",
                        "work_unit_fingerprint": "sha256:repair",
                    },
                }
            ),
            "--apply",
        ]
    )
    assert exit_code == 0
    invoke_payload = json.loads(capsys.readouterr().out)
    assert invoke_payload["surface_kind"] == "mas_scientific_capability_invocation"
    assert invoke_payload["refs_only"] is True
    assert (study_root / "artifacts/advisory/external_learning_sidecar/latest.json").is_file()

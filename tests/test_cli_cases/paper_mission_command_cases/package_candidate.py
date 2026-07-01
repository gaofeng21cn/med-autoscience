from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


DM_CANARY_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[2] / "fixtures" / "paper_mission_dm_canary"
)


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))


def test_paper_mission_package_candidate_materializes_route_back_executor_handoff(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    _write_paper_source_fixture(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624T0115Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::route-back"
    route_back_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
    )
    route_back_transaction["stage_terminal_decision"][
        "route_back_evidence_ref"
    ] = "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Repair DM002 claim/evidence gaps after terminal owner gate.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::route-back-repair",
                "artifact_ref": "mission://dm002/route-back-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": route_back_transaction[
                "stage_terminal_decision"
            ],
            "opl_route_command": route_back_transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": route_back_transaction,
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-route-back",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260624T0116Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "package-candidate",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(output_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    output_manifest = payload["output_manifest"]
    assert len(output_manifest["written_files"]) == 21
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False
    assert output_manifest["written_files"]
    handoff = json.loads(
        Path(output_manifest["mission_executor_handoff_ref"]).read_text(
            encoding="utf-8"
        )
    )
    paper_facing_delta = json.loads(
        Path(output_manifest["paper_facing_candidate_delta_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_consumption_request = json.loads(
        Path(output_manifest["owner_consumption_request_ref"]).read_text(
            encoding="utf-8"
        )
    )
    assert set(output_manifest["ai_owner_decision_sidecar_refs"]) == {
        "claim_strength_adjustment",
        "scope_reduction",
        "evidence_substitution",
        "research_pivot",
        "carry_forward_risk_receipt",
    }
    assert owner_consumption_request["ai_owner_decision_sidecar_refs"] == (
        output_manifest["ai_owner_decision_sidecar_refs"]
    )
    owner_blocker_packet = json.loads(
        Path(output_manifest["owner_blocker_packet_ref"]).read_text(encoding="utf-8")
    )
    submission_milestone_checklist = json.loads(
        Path(output_manifest["submission_milestone_checklist_ref"]).read_text(
            encoding="utf-8"
        )
    )
    candidate_manifest = json.loads(
        Path(output_manifest["candidate_manifest_ref"]).read_text(encoding="utf-8")
    )
    package_manifest = json.loads(
        Path(output_manifest["package_manifest_ref"]).read_text(encoding="utf-8")
    )
    assert payload["mission_executor_handoff"] == handoff
    assert payload["owner_consumption_request"] == owner_consumption_request
    assert payload["owner_blocker_packet"] == owner_blocker_packet
    assert package_manifest["mission_executor_materialized"] is True
    assert package_manifest["candidate_content_kind"] == (
        "concrete_non_authority_paper_delta"
    )
    assert any(
        ref.endswith("/paper/draft.md")
        for ref in package_manifest["source_document_refs"]
    )
    assert handoff["surface_kind"] == "paper_mission_executor_handoff"
    assert handoff["status"] == "ready_for_mission_executor"
    assert handoff["next_owner"] == "mission_executor"
    assert handoff["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert handoff["repair_scope"] == "claim-evidence-repair"
    assert handoff["target_stage_id"] == "paper-stage::gate-clearing"
    assert handoff["current_terminal_decision"]["decision_kind"] == "route_back"
    assert handoff["current_terminal_decision"]["route_command"] == "route_back"
    assert [
        item["kind"] for item in handoff["expected_paper_facing_outputs"]
    ] == [
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    ]
    assert handoff["authority_boundary"]["writes_authority"] is False
    assert handoff["authority_boundary"]["writes_runtime"] is False
    assert handoff["authority_boundary"]["writes_yang_authority"] is False
    assert handoff["authority_boundary"]["writes_paper_body"] is False
    assert handoff["authority_boundary"]["can_claim_paper_progress"] is False
    assert "owner receipt" in handoff["forbidden_authority_writes"]
    assert payload["paper_facing_candidate_delta"] == paper_facing_delta
    assert paper_facing_delta["surface_kind"] == (
        "paper_mission_paper_facing_candidate_delta"
    )
    assert paper_facing_delta["milestone_kind"] == "submission_milestone_candidate"
    assert paper_facing_delta["status"] == "submission_milestone_candidate_ready"
    assert paper_facing_delta["counts_as_paper_progress"] is True
    assert paper_facing_delta["candidate_is_authority"] is False
    assert paper_facing_delta["mission_executor_materialized"] is True
    assert paper_facing_delta["candidate_content_kind"] == (
        "concrete_non_authority_paper_delta"
    )
    assert any(
        ref.endswith("/paper/claim_evidence_map.json")
        for ref in paper_facing_delta["source_document_refs"]
    )
    assert paper_facing_delta["paper_source_snapshot"]["source_snapshot_complete"] is False
    assert paper_facing_delta["can_claim_submission_ready"] is False
    assert paper_facing_delta["can_claim_publication_ready"] is False
    assert paper_facing_delta["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert [item["kind"] for item in paper_facing_delta["paper_facing_outputs"]] == [
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    ]
    assert all(
        item["status"] == "candidate_required"
        for item in paper_facing_delta["paper_facing_outputs"]
    )
    assert paper_facing_delta["authority_boundary"]["writes_paper_body"] is False
    assert paper_facing_delta["authority_boundary"]["can_claim_paper_progress"] is False
    assert owner_consumption_request["status"] == "ready_for_mas_authority_consume"
    assert owner_consumption_request["request_kind"] == (
        "route_back_candidate_delta_consumption"
    )
    assert owner_consumption_request["next_owner"] == "mission_executor"
    assert "mission_executor:" in owner_consumption_request["owner_question"]
    assert "route_back_without_blocker" in owner_consumption_request["owner_question"]
    assert owner_consumption_request["next_legal_action"] == (
        "consume_candidate_or_return_owner_answer_shape"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_consumption_request["next_legal_command"]["argv_template"]
    )
    assert owner_consumption_request["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "paper_facing_delta_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_consumption_request["evidence_refs"]["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert owner_consumption_request["carry_forward_risk_receipt"] == (
        owner_blocker_packet["carry_forward_risk_receipt"]
    )
    carry_forward_risk = owner_consumption_request["carry_forward_risk_receipt"]
    assert carry_forward_risk["risk_kind"] == "synonymous_route_back_redrive"
    assert carry_forward_risk["forbidden_next_action"] == (
        "synonymous_route_back_redrive"
    )
    assert carry_forward_risk["required_owner_fallback_action"] == (
        "consume_candidate_or_return_owner_answer_shape"
    )
    assert carry_forward_risk["source_route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert owner_consumption_request["candidate_refs"]["mission_executor_handoff"] == (
        output_manifest["mission_executor_handoff_ref"]
    )
    assert owner_consumption_request["candidate_refs"][
        "paper_facing_candidate_delta"
    ] == output_manifest["paper_facing_candidate_delta_ref"]
    assert owner_consumption_request["candidate_refs"]["owner_blocker_packet"] == (
        output_manifest["owner_blocker_packet_ref"]
    )
    assert owner_consumption_request["authority_boundary"]["writes_authority"] is False
    assert owner_consumption_request["authority_boundary"]["writes_runtime"] is False
    assert owner_consumption_request["authority_boundary"]["writes_paper_body"] is False
    assert owner_consumption_request["authority_boundary"][
        "can_claim_paper_progress"
    ] is False
    assert owner_blocker_packet["status"] == "context_only"
    assert owner_blocker_packet["blocker_kind"] == "route_back_without_blocker"
    assert "mission_executor:" in owner_blocker_packet["owner_question"]
    assert owner_blocker_packet["next_legal_action"] == (
        "consume_candidate_or_return_owner_answer_shape"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_blocker_packet["next_legal_command"]["argv_template"]
    )
    assert owner_blocker_packet["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "paper_facing_delta_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_blocker_packet["evidence_refs"]["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert owner_blocker_packet["terminal_owner_gate_materialized"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_owner_receipt"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_typed_blocker"] is False
    assert (
        submission_milestone_checklist["milestone_kind"]
        == "submission_milestone_candidate"
    )
    assert submission_milestone_checklist["counts_as_paper_progress"] is True
    assert submission_milestone_checklist["candidate_is_authority"] is False
    assert {
        item["ref_kind"]
        for item in submission_milestone_checklist[
            "required_authority_materialization_refs"
        ]
    } >= {"domain_owner_receipt_ref", "publication_eval_record_ref"}
    assert {
        item["ref_kind"]
        for item in submission_milestone_checklist["required_quality_gate_refs"]
    } >= {"independent_reviewer_invocation_ref", "reviewer_quality_receipt_ref"}
    assert {
        item["item_id"]: item["status"]
        for item in submission_milestone_checklist["mas_automatable_items"]
    }["manuscript_patch_plan"] == "candidate_included"
    assert set(output_manifest["paper_facing_artifact_refs"]) == {
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    }
    assert paper_facing_delta["paper_facing_artifact_refs"] == output_manifest[
        "paper_facing_artifact_refs"
    ]
    manuscript_patch_plan = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["manuscript_patch_plan"]).read_text(
            encoding="utf-8"
        )
    )
    claim_evidence_delta = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["claim_evidence_ledger_delta"]).read_text(
            encoding="utf-8"
        )
    )
    figure_table_delta = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["figure_table_caption_delta"]).read_text(
            encoding="utf-8"
        )
    )
    reviewer_response = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["reviewer_gate_response_draft"]).read_text(
            encoding="utf-8"
        )
    )
    owner_decision_artifact = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["owner_decision_packet"]).read_text(
            encoding="utf-8"
        )
    )
    assert manuscript_patch_plan["surface_kind"] == (
        "paper_mission_manuscript_patch_plan"
    )
    assert manuscript_patch_plan["candidate_content"]["patch_targets"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
    ]
    assert manuscript_patch_plan["mission_executor_materialized"] is True
    assert manuscript_patch_plan["candidate_content_kind"] == (
        "concrete_non_authority_paper_delta"
    )
    assert manuscript_patch_plan["candidate_content"]["source_headings"][0][
        "headings"
    ][0]["text"] == "DM paper draft"
    assert manuscript_patch_plan["candidate_content"]["candidate_patch_operations"][0][
        "target_heading"
    ]["text"] == "Results"
    assert manuscript_patch_plan["authority_boundary"]["writes_paper_body"] is False
    assert manuscript_patch_plan["milestone_kind"] == "submission_milestone_candidate"
    assert manuscript_patch_plan["counts_as_paper_progress"] is True
    assert manuscript_patch_plan["candidate_is_authority"] is False
    assert manuscript_patch_plan["authority_materialized"] is False
    assert manuscript_patch_plan["can_claim_submission_ready"] is False
    assert claim_evidence_delta["surface_kind"] == (
        "paper_mission_claim_evidence_ledger_delta"
    )
    assert claim_evidence_delta["candidate_content"]["delta_targets"] == [
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
    ]
    assert claim_evidence_delta["candidate_content"]["claim_evidence_rows"][0][
        "candidate_row"
    ]["claim_id"] == "claim-primary"
    assert claim_evidence_delta["candidate_content"]["source_claim_count"] == 1
    assert claim_evidence_delta["candidate_content"]["source_evidence_count"] == 1
    assert claim_evidence_delta["authority_boundary"]["writes_authority"] is False
    assert claim_evidence_delta["counts_as_paper_progress"] is True
    assert figure_table_delta["candidate_content"]["table_candidates"][0][
        "candidate_ref"
    ]["table_id"] == "T1"
    assert figure_table_delta["candidate_content"]["figure_candidates"][0][
        "candidate_ref"
    ]["figure_id"] == "F1"
    assert reviewer_response["candidate_content"]["response_draft_items"][0][
        "review_item"
    ]["id"] == "gate-1"
    assert owner_decision_artifact["candidate_content"]["owner_ballot"][
        "recommended_owner"
    ] == "MAS authority consume path"
    assert (
        output_manifest["paper_facing_candidate_delta_ref"]
        in candidate_manifest["candidate_artifact_refs"]
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_package_candidate_repackages_accepted_consumption_ledger_with_external_delta(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    _write_paper_source_fixture(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::paper_mission_import::one-shot"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    source_package = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=transaction,
    )
    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(source_package),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_consumption_ledger"
                / "accepted-sci-review"
            ),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert consume_exit_code == 0
    capsys.readouterr()
    external_delta = tmp_path / "external_sci_registry_review_v4_delta.json"
    external_delta.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_external_reviewer_revision_delta",
                "candidate_is_authority": False,
                "writes_authority": False,
                "writes_runtime": False,
                "writes_paper_body": False,
                "reviewer_revision_checklist": [
                    {"id": "SCI4-007-internal-report-prose", "severity": "major"}
                ],
            }
        ),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "external-sci-review-v4"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "package-candidate",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(output_root),
            "--paper-facing-delta-ref",
            str(external_delta),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_candidate_package_write_readback"
    assert payload["consume_candidate_status"] == "accepted_candidate"
    assert payload["stage_terminal_decision"]["status"] == (
        "accepted_submission_milestone_candidate"
    )
    output_manifest = payload["output_manifest"]
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False
    assert output_manifest["adopted_external_paper_delta_ref"] == str(
        external_delta.resolve()
    )
    package_manifest = json.loads(
        Path(output_manifest["package_manifest_ref"]).read_text(encoding="utf-8")
    )
    assert package_manifest["adopted_external_paper_delta_ref"] == str(
        external_delta.resolve()
    )
    assert package_manifest["candidate_is_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_package_candidate_preserves_display_pack_figure_digests(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    _write_paper_source_fixture(tmp_path, study_id=study_id)
    paper_root = tmp_path / "workspace" / "studies" / study_id / "paper"
    (paper_root / "figures" / "figure_catalog.json").write_text(
        json.dumps(
            {
                "figures": [
                    {
                        "figure_id": "F1",
                        "title": "Cohort and source-layer accounting",
                        "status": "candidate",
                        "template_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
                        "renderer_family": "r_ggplot2",
                        "render_receipt_ref": "paper/figure_render_receipt.json",
                        "visual_audit_receipt_ref": "paper/figure_visual_audit_receipt.json",
                        "publication_manifest_ref": "paper/build/display_pack_publication_manifest.json",
                        "display_artifact_manifest_ref": "paper/build/display_artifact_manifest.F1.json",
                        "rendered_artifact_refs": [
                            "paper/figures/generated/F1.png",
                            "paper/figures/generated/F1.pdf",
                            "paper/figures/generated/F1.layout.json",
                        ],
                        "rendered_artifact_digests": {
                            "paper/figures/generated/F1.png": "png-sha",
                            "paper/figures/generated/F1.pdf": "pdf-sha",
                            "paper/figures/generated/F1.layout.json": "layout-sha",
                        },
                        "visual_audit": {
                            "status": "clear",
                            "artifact_path": "paper/figures/generated/F1.png",
                            "artifact_sha256": "png-sha",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260701T0000Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Refresh paper-facing candidate package.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::obesity::figure-refresh",
                "artifact_ref": "mission://obesity/figure-refresh",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": transaction,
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260701T0001Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "package-candidate",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(output_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    figure_table_delta = json.loads(
        Path(
            payload["output_manifest"]["paper_facing_artifact_refs"][
                "figure_table_caption_delta"
            ]
        ).read_text(encoding="utf-8")
    )

    assert exit_code == 0
    figure_candidate = figure_table_delta["candidate_content"]["figure_candidates"][0]
    assert figure_candidate["candidate_ref"]["figure_id"] == "F1"
    assert figure_candidate["display_artifact_refs"] == [
        "paper/figures/generated/F1.png",
        "paper/figures/generated/F1.pdf",
        "paper/figures/generated/F1.layout.json",
    ]
    assert figure_candidate["display_artifact_digests"] == {
        "paper/figures/generated/F1.png": "png-sha",
        "paper/figures/generated/F1.pdf": "pdf-sha",
        "paper/figures/generated/F1.layout.json": "layout-sha",
    }
    assert figure_candidate["render_receipt_ref"] == "paper/figure_render_receipt.json"
    assert figure_candidate["visual_audit_receipt_ref"] == (
        "paper/figure_visual_audit_receipt.json"
    )
    assert figure_candidate["visual_audit"]["status"] == "clear"
    assert figure_candidate["authority_materialized"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_package_candidate_materializes_typed_blocker_owner_packet(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    migration_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624T0200Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--one-shot-migration",
            "--study-progress-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dm003_progress.json"),
            "--runtime-readback-payload",
            str(DM_CANARY_FIXTURE_ROOT / "runtime_readback.json"),
            "--output-root",
            str(migration_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    package_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260624T0201Z"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "package-candidate",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(package_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["consume_candidate_status"] == "typed_blocker"
    output_manifest = payload["output_manifest"]
    assert len(output_manifest["written_files"]) == 21
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False
    owner_consumption_request = json.loads(
        Path(output_manifest["owner_consumption_request_ref"]).read_text(
            encoding="utf-8"
        )
    )
    assert set(output_manifest["ai_owner_decision_sidecar_refs"]) == {
        "claim_strength_adjustment",
        "scope_reduction",
        "evidence_substitution",
        "research_pivot",
        "carry_forward_risk_receipt",
    }
    assert owner_consumption_request["ai_owner_decision_sidecar_refs"] == (
        output_manifest["ai_owner_decision_sidecar_refs"]
    )
    owner_blocker_packet = json.loads(
        Path(output_manifest["owner_blocker_packet_ref"]).read_text(encoding="utf-8")
    )
    submission_milestone_checklist = json.loads(
        Path(output_manifest["submission_milestone_checklist_ref"]).read_text(
            encoding="utf-8"
        )
    )
    paper_facing_delta = json.loads(
        Path(output_manifest["paper_facing_candidate_delta_ref"]).read_text(
            encoding="utf-8"
        )
    )
    assert payload["owner_consumption_request"] == owner_consumption_request
    assert payload["owner_blocker_packet"] == owner_blocker_packet
    assert payload["paper_facing_candidate_delta"] == paper_facing_delta
    assert paper_facing_delta["milestone_kind"] == "submission_milestone_candidate"
    assert (
        paper_facing_delta["status"]
        == "submission_milestone_candidate_ready_with_owner_blocker_context"
    )
    assert paper_facing_delta["counts_as_paper_progress"] is True
    assert paper_facing_delta["candidate_is_authority"] is False
    assert paper_facing_delta["can_claim_submission_ready"] is False
    assert paper_facing_delta["can_claim_publication_ready"] is False
    assert (
        submission_milestone_checklist["milestone_kind"]
        == "submission_milestone_candidate"
    )
    assert (
        submission_milestone_checklist["status"]
        == "candidate_ready_with_owner_blocker_context"
    )
    assert submission_milestone_checklist["counts_as_paper_progress"] is True
    assert submission_milestone_checklist["authority_materialized"] is False
    assert {
        item["ref_kind"]
        for item in submission_milestone_checklist[
            "required_authority_materialization_refs"
        ]
    } >= {"typed_blocker_ref", "human_gate_ref"}
    assert {
        item["ref_kind"]
        for item in submission_milestone_checklist["required_quality_gate_refs"]
    } >= {"independent_reviewer_context_ref", "reviewer_quality_receipt_ref"}
    assert set(output_manifest["paper_facing_artifact_refs"]) == {
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    }
    assert owner_consumption_request["status"] == "owner_blocker_packet_required"
    assert owner_consumption_request["request_kind"] == "owner_blocker_resolution"
    assert owner_consumption_request["next_owner"] == "one-person-lab"
    assert "one-person-lab:" in owner_consumption_request["owner_question"]
    assert owner_consumption_request["next_legal_action"] == (
        "provide_opl_terminal_readback_or_governed_owner_answer"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_consumption_request["next_legal_command"]["argv_template"]
    )
    assert owner_consumption_request["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "paper_facing_delta_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    consume_path = owner_consumption_request["consume_path"]
    assert consume_path["authority_materialized_by_this_request"] is False
    assert "human_gate_ref" in consume_path["required_authority_materialization_refs"]
    assert "reviewer_quality_receipt_ref" in consume_path[
        "required_quality_gate_refs"
    ]
    assert owner_consumption_request["candidate_refs"]["owner_blocker_packet"] == (
        output_manifest["owner_blocker_packet_ref"]
    )
    assert owner_consumption_request["authority_boundary"]["writes_authority"] is False
    assert owner_consumption_request["authority_boundary"]["writes_runtime"] is False
    assert owner_consumption_request["authority_boundary"]["writes_paper_body"] is False
    assert owner_consumption_request["authority_boundary"][
        "can_claim_paper_progress"
    ] is False
    assert owner_blocker_packet["surface_kind"] == "paper_mission_owner_blocker_packet"
    assert owner_blocker_packet["status"] == "owner_blocker_candidate_ready"
    assert owner_blocker_packet["blocker_kind"] == "missing_opl_runtime_readback"
    assert "one-person-lab:" in owner_blocker_packet["owner_question"]
    assert owner_blocker_packet["next_legal_action"] == (
        "provide_opl_terminal_readback_or_governed_owner_answer"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_blocker_packet["next_legal_command"]["argv_template"]
    )
    assert owner_blocker_packet["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "paper_facing_delta_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_blocker_packet["current_terminal_decision"]["decision_kind"] == (
        "typed_blocker"
    )
    assert owner_blocker_packet["current_terminal_decision"]["route_command"] == (
        "stop_with_typed_blocker"
    )
    assert owner_blocker_packet["terminal_owner_gate_materialized"] is False
    assert owner_blocker_packet["typed_blocker_authority_materialized"] is False
    assert owner_blocker_packet["human_gate_materialized"] is False
    assert {
        item["ref_kind"]
        for item in owner_blocker_packet["required_authority_materialization_refs"]
    } >= {"typed_blocker_ref", "human_gate_ref", "publication_eval_record_ref"}
    assert owner_blocker_packet["authority_boundary"]["can_write_owner_receipt"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_typed_blocker"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_human_gate"] is False
    assert owner_blocker_packet["authority_boundary"]["can_claim_paper_progress"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)

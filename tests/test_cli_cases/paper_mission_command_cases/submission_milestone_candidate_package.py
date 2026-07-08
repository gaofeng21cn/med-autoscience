from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import (
    DM_CANARY_FIXTURE_ROOT,
    FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
    _assert_forbidden_authority_untouched,
    _paper_mission_forbidden_write_guard,
    _paper_mission_transaction_payload,
    _write_candidate_manifest,
    _write_matching_domain_gate_closeout,
    _write_paper_source_fixture,
    _write_profile_with_study,
    _write_submission_milestone_package,
)

def test_paper_mission_package_candidate_writes_non_authority_owner_decision_package(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260623T2032Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::one-shot-migration",
        "study_id": study_id,
        "objective": "Consume DM002 publication blockers and repair claim/evidence gaps.",
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::claim-evidence-repair",
                "artifact_ref": "mission://dm002/claim-evidence-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    mission_payload["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission_id=mission_payload["mission_id"],
        study_id=study_id,
        decision_kind="advance",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002",
                "mission_id": mission_payload["mission_id"],
                "study_id": study_id,
                "next_owner": "analysis-campaign",
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
        / "20260623T2100Z"
    )
    external_paper_delta_ref = tmp_path / "non_synonymous_paper_delta_packet.json"
    external_paper_delta_ref.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_non_authority_owner_decision_packet",
                "authority_flags": {
                    "writes_authority": False,
                    "writes_runtime": False,
                    "writes_yang_authority": False,
                    "writes_paper_body": False,
                },
            }
        ),
        encoding="utf-8",
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
            str(external_paper_delta_ref),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_candidate_package_write_readback"
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    assert payload["mutation_policy"]["writes_yang_authority"] is False
    assert (
        "Yang output outside ops/medautoscience/paper_mission_candidate_package"
        in payload["mutation_policy"]["forbidden_authority_writes"]
    )
    assert (
        "Yang output outside ops/medautoscience/paper_mission_one_shot_migration"
        not in payload["mutation_policy"]["forbidden_authority_writes"]
    )
    assert payload["output_manifest"]["writes_authority"] is False
    assert payload["output_manifest"]["writes_runtime"] is False
    assert payload["output_manifest"]["writes_yang_authority"] is False
    assert payload["output_manifest"]["package_manifest_ref"].endswith(
        "/package_manifest.json"
    )
    assert payload["output_manifest"]["mission_executor_handoff_ref"].endswith(
        "/mission_executor_handoff.json"
    )
    assert payload["output_manifest"]["paper_facing_candidate_delta_ref"].endswith(
        "/paper_facing_candidate_delta.json"
    )
    assert payload["output_manifest"]["owner_consumption_request_ref"].endswith(
        "/owner_consumption_request.json"
    )
    assert payload["output_manifest"]["owner_blocker_packet_ref"].endswith(
        "/owner_blocker_packet.json"
    )
    written_files = [Path(path) for path in payload["output_manifest"]["written_files"]]
    assert len(written_files) == 21
    assert all(path.is_file() for path in written_files)
    assert all(output_root in path.parents for path in written_files)
    package_manifest = json.loads(
        Path(payload["output_manifest"]["package_manifest_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_summary = json.loads(
        Path(payload["output_manifest"]["foreground_owner_decision_summary_ref"]).read_text(
            encoding="utf-8"
        )
    )
    mission_executor_handoff = json.loads(
        Path(payload["output_manifest"]["mission_executor_handoff_ref"]).read_text(
            encoding="utf-8"
        )
    )
    paper_facing_delta = json.loads(
        Path(payload["output_manifest"]["paper_facing_candidate_delta_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_consumption_request = json.loads(
        Path(payload["output_manifest"]["owner_consumption_request_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_blocker_packet = json.loads(
        Path(payload["output_manifest"]["owner_blocker_packet_ref"]).read_text(
            encoding="utf-8"
        )
    )
    submission_milestone_checklist = json.loads(
        Path(payload["output_manifest"]["submission_milestone_checklist_ref"]).read_text(
            encoding="utf-8"
        )
    )
    candidate_manifest = json.loads(
        Path(payload["output_manifest"]["candidate_manifest_ref"]).read_text(
            encoding="utf-8"
        )
    )
    adopted_external_ref = str(external_paper_delta_ref.resolve())
    assert package_manifest["mode"] == "non_authority_candidate_package"
    assert package_manifest["milestone_kind"] == "submission_milestone_candidate"
    assert package_manifest["counts_as_paper_progress"] is True
    assert package_manifest["can_claim_submission_ready"] is False
    assert package_manifest["can_claim_publication_ready"] is False
    assert package_manifest["candidate_is_authority"] is False
    assert package_manifest["authority_materialized_by_this_package"] is False
    assert (
        package_manifest["artifact_refs"]["mission_executor_handoff"]
        == payload["output_manifest"]["mission_executor_handoff_ref"]
    )
    assert (
        package_manifest["artifact_refs"]["paper_facing_candidate_delta"]
        == payload["output_manifest"]["paper_facing_candidate_delta_ref"]
    )
    assert (
        package_manifest["artifact_refs"]["owner_consumption_request"]
        == payload["output_manifest"]["owner_consumption_request_ref"]
    )
    assert (
        package_manifest["artifact_refs"]["owner_blocker_packet"]
        == payload["output_manifest"]["owner_blocker_packet_ref"]
    )
    assert package_manifest["adopted_external_paper_delta_ref"] == adopted_external_ref
    assert payload["output_manifest"]["adopted_external_paper_delta_ref"] == (
        adopted_external_ref
    )
    assert (
        package_manifest["artifact_refs"]["submission_milestone_checklist"]
        == payload["output_manifest"]["submission_milestone_checklist_ref"]
    )
    assert (
        "Yang output outside ops/medautoscience/paper_mission_candidate_package"
        in package_manifest["forbidden_authority_writes"]
    )
    assert (
        "Yang output outside ops/medautoscience/paper_mission_one_shot_migration"
        not in package_manifest["forbidden_authority_writes"]
    )
    assert owner_summary["candidate_is_authority"] is False
    assert owner_summary["governed_runtime_truth"] is False
    assert owner_summary["authority_materialized_by_this_packet"] is False
    assert (
        "Yang output outside ops/medautoscience/paper_mission_candidate_package"
        in owner_summary["forbidden_authority_writes"]
    )
    assert "remaining_owner_gap" in owner_summary
    assert mission_executor_handoff["surface_kind"] == "paper_mission_executor_handoff"
    assert mission_executor_handoff["status"] == "not_routed_to_mission_executor"
    assert mission_executor_handoff["next_owner"] == "analysis-campaign"
    assert mission_executor_handoff["authority_boundary"]["writes_authority"] is False
    assert mission_executor_handoff["authority_boundary"]["writes_runtime"] is False
    assert mission_executor_handoff["authority_boundary"]["writes_yang_authority"] is False
    assert (
        mission_executor_handoff["authority_boundary"]["can_claim_paper_progress"]
        is False
    )
    assert paper_facing_delta["surface_kind"] == (
        "paper_mission_paper_facing_candidate_delta"
    )
    assert paper_facing_delta["milestone_kind"] == "submission_milestone_candidate"
    assert paper_facing_delta["status"] == "submission_milestone_candidate_ready"
    assert paper_facing_delta["counts_as_paper_progress"] is True
    assert paper_facing_delta["candidate_is_authority"] is False
    assert paper_facing_delta["can_claim_submission_ready"] is False
    assert paper_facing_delta["can_claim_publication_ready"] is False
    assert paper_facing_delta["authority_boundary"]["writes_authority"] is False
    assert paper_facing_delta["adopted_external_paper_delta_ref"] == adopted_external_ref
    assert paper_facing_delta["source_paper_facing_delta_ref"] == adopted_external_ref
    assert paper_facing_delta[
        "adopted_external_paper_delta_authority_boundary"
    ] == {
        "candidate_is_authority": False,
        "authority_materialized": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
    }
    assert owner_consumption_request["surface_kind"] == (
        "paper_mission_owner_consumption_request"
    )
    assert owner_consumption_request["status"] == "owner_review_required"
    assert owner_consumption_request["request_kind"] == "owner_decision_consumption"
    assert owner_consumption_request["candidate_refs"][
        "paper_facing_candidate_delta"
    ] == payload["output_manifest"]["paper_facing_candidate_delta_ref"]
    assert owner_consumption_request["candidate_refs"][
        "adopted_external_paper_delta"
    ] == adopted_external_ref
    assert owner_consumption_request["candidate_refs"]["owner_blocker_packet"] == (
        payload["output_manifest"]["owner_blocker_packet_ref"]
    )
    assert owner_consumption_request["accepted_owner_answer_shapes"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "paper_facing_delta_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    consume_path = owner_consumption_request["consume_path"]
    assert consume_path["authority_materialized_by_this_request"] is False
    assert "publication_eval_record_ref" in consume_path[
        "required_authority_materialization_refs"
    ]
    assert "reviewer_quality_receipt_ref" in consume_path[
        "required_quality_gate_refs"
    ]
    assert owner_consumption_request["authority_boundary"]["writes_authority"] is False
    assert owner_consumption_request["authority_boundary"]["writes_runtime"] is False
    assert owner_consumption_request["authority_boundary"][
        "can_claim_paper_progress"
    ] is False
    assert owner_consumption_request["counts_as_paper_progress"] is False
    assert submission_milestone_checklist["adopted_external_paper_delta_ref"] == (
        adopted_external_ref
    )
    assert submission_milestone_checklist[
        "adopted_external_paper_delta_authority_boundary"
    ] == {
        "candidate_is_authority": False,
        "authority_materialized": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
    }
    assert owner_blocker_packet["surface_kind"] == "paper_mission_owner_blocker_packet"
    assert owner_blocker_packet["status"] == "context_only"
    assert owner_blocker_packet["candidate_is_authority"] is False
    assert owner_blocker_packet["authority_materialized"] is False
    assert {
        item["ref_kind"] for item in owner_blocker_packet["required_quality_gate_refs"]
    } >= {
        "independent_reviewer_invocation_ref",
        "reviewer_quality_receipt_ref",
    }
    assert owner_blocker_packet["authority_boundary"]["can_write_typed_blocker"] is False
    assert set(payload["output_manifest"]["ai_owner_decision_sidecar_refs"]) == {
        "claim_strength_adjustment",
        "scope_reduction",
        "evidence_substitution",
        "research_pivot",
        "carry_forward_risk_receipt",
    }
    assert package_manifest["ai_owner_decision_sidecar_refs"] == payload[
        "output_manifest"
    ]["ai_owner_decision_sidecar_refs"]
    assert owner_consumption_request["ai_owner_decision_sidecar_refs"] == payload[
        "output_manifest"
    ]["ai_owner_decision_sidecar_refs"]
    assert owner_consumption_request["consume_path"]["ai_owner_decision_sidecar_refs"] == (
        payload["output_manifest"]["ai_owner_decision_sidecar_refs"]
    )
    ai_owner_sidecars = {
        kind: json.loads(Path(path).read_text(encoding="utf-8"))
        for kind, path in payload["output_manifest"][
            "ai_owner_decision_sidecar_refs"
        ].items()
    }
    assert all(
        sidecar["candidate_is_authority"] is False
        and sidecar["authority_materialized"] is False
        and sidecar["authority_boundary"]["writes_authority"] is False
        and sidecar["authority_boundary"]["writes_runtime"] is False
        for sidecar in ai_owner_sidecars.values()
    )
    assert ai_owner_sidecars["claim_strength_adjustment"]["decision_kind"] == (
        "claim_strength_adjustment"
    )
    assert ai_owner_sidecars["scope_reduction"]["decision_kind"] == "scope_reduction"
    assert ai_owner_sidecars["evidence_substitution"]["decision_kind"] == (
        "evidence_substitution"
    )
    assert ai_owner_sidecars["research_pivot"]["decision_kind"] == "research_pivot"
    assert ai_owner_sidecars["carry_forward_risk_receipt"]["decision_kind"] == (
        "carry_forward_risk_receipt"
    )
    assert set(payload["output_manifest"]["paper_facing_artifact_refs"]) == {
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    }
    assert set(paper_facing_delta["paper_facing_artifact_refs"]) == set(
        payload["output_manifest"]["paper_facing_artifact_refs"]
    )
    assert all(
        Path(path).exists()
        for path in payload["output_manifest"]["paper_facing_artifact_refs"].values()
    )
    for artifact_ref in payload["output_manifest"]["paper_facing_artifact_refs"].values():
        artifact = json.loads(Path(artifact_ref).read_text(encoding="utf-8"))
        assert artifact["adopted_external_paper_delta_ref"] == adopted_external_ref
        assert artifact["source_paper_facing_delta_ref"] == adopted_external_ref
        assert artifact["candidate_content"][
            "adopted_external_paper_delta_ref"
        ] == adopted_external_ref
        assert artifact["candidate_content"]["source_paper_facing_delta_ref"] == (
            adopted_external_ref
        )
        assert artifact["adopted_external_paper_delta_authority_boundary"] == {
            "candidate_is_authority": False,
            "authority_materialized": False,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
        }
    assert (
        payload["output_manifest"]["paper_facing_candidate_delta_ref"]
        in candidate_manifest["candidate_artifact_refs"]
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)

from __future__ import annotations

import json
import shutil
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_guarded_apply_proof,
)


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
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def _assert_body_free_canary_packet(packet: dict[str, object], *, owner: str) -> None:
    assert set(packet) == {
        "ref",
        "role",
        "freshness",
        "owner",
        "receipt_id",
        "no_forbidden_write_proof",
    }
    assert packet["owner"] == owner
    assert packet["ref"]
    assert packet["receipt_id"]
    proof = packet["no_forbidden_write_proof"]
    assert isinstance(proof, dict)
    assert proof["write_permitted"] is False
    assert proof["forbidden_writes_performed"] is False
    assert "artifact_body" not in packet
    assert "memory_body" not in packet
    assert "current_package" not in packet


def test_dm002_effective_eval_sprint_canary_requires_progress_delta_before_quality_gate(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    fixture = FIXTURE_ROOT / "dm002_20260529T095414Z_effective_eval_sprint_canary"
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    shutil.copytree(fixture, dm002)

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=tmp_path / "Yang",
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )["paper_line_provider_canary_closeout"]

    result = payload["paper_line_owner_chain_results"][0]
    refs = payload["live_paper_line_evidence_refs"]
    stage = {
        stage["stage_id"]: stage
        for stage in payload["stage_expected_receipt_payload_summary"]["stages"]
    }["finalize_and_publication_handoff"]
    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    record = evidence_payload["record_payload"]
    fixture_progress = json.loads(
        (dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    fixture_gate_replay = json.loads(
        (dm002 / "artifacts" / "controller" / "gate_replay_requests" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    fixture_decision = json.loads(
        (dm002 / "artifacts" / "controller_decisions" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    fixture_expectations = json.loads(
        (
            dm002
            / "expectations"
            / "post_reviewer_write_sprint_evidence_expectations.json"
        ).read_text(encoding="utf-8")
    )

    progress_ref = str(dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json")
    owner_receipt_ref = str(dm002 / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json")
    gate_replay_ref = str(dm002 / "artifacts" / "controller" / "gate_replay_requests" / "latest.json")
    human_gate_ref = str(dm002 / "artifacts" / "controller_decisions" / "latest.json")

    assert result["paper_line_id"] == "002-dm-china-us-mortality-attribution"
    assert result["result_kind"] == "owner_receipt"
    assert result["owner_receipt_refs"] == [
        owner_receipt_ref,
        progress_ref,
        gate_replay_ref,
        human_gate_ref,
    ]
    assert result["progress_delta_refs"] == [progress_ref]
    assert result["artifact_movement_refs"] == [owner_receipt_ref]
    assert result["human_gate_or_resume_refs"] == [human_gate_ref]
    assert result["ai_reviewer_gate_receipt_refs"] == []
    assert result["readiness_claims"] == {
        "claims_paper_closure": False,
        "claims_publication_ready": False,
        "claims_artifact_mutation_authorized": False,
        "claims_current_package_updated": False,
    }
    assert refs["progress_delta_refs"] == [progress_ref]
    assert refs["artifact_movement_refs"] == [owner_receipt_ref]
    assert refs["human_gate_or_resume_refs"] == [human_gate_ref]
    assert payload["no_forbidden_write_proof"]["provider_or_opl_wrote_current_package"] is False
    assert payload["no_forbidden_write_proof"]["provider_or_opl_wrote_artifact_body"] is False
    assert fixture_progress["effective_eval_id"] == "20260529T095414Z"
    assert fixture_progress["candidate_package_freshness"]["status"] == "freshness_proof_observed"
    assert fixture_progress["display_freshness"]["status"] == "freshness_proof_observed"
    assert fixture_progress["gate_order"] == {
        "principle": "sprint_delta_before_quality_gate",
        "gate_replay_requested_after_delta": True,
        "platform_repair_can_count_as_paper_progress": False,
    }
    assert fixture_gate_replay["requested_after_progress_delta"] is True
    assert fixture_decision["requires_human_confirmation"] is True
    assert fixture_decision["single_next_owner"] is True
    assert fixture_expectations["surface"] == (
        "dm002_post_reviewer_write_sprint_evidence_expectations"
    )
    assert fixture_expectations["canary_id"] == "dm002-20260529T095414Z-effective-eval-sprint"
    assert fixture_expectations["scope"] == "contract_expectation_only"
    assert fixture_expectations["forbidden_claims"] == {
        "claims_domain_ready": False,
        "claims_publication_ready": False,
        "claims_current_package_updated": False,
        "claims_artifact_mutation_authorized": False,
    }
    assert fixture_expectations["accepted_terminal_shapes"] == [
        "owner_receipt_with_required_ref_families",
        "stable_typed_blocker_with_required_routeback",
    ]
    assert fixture_expectations["positive_path"]["required_ref_families"] == [
        "research_evidence_pack_refs",
        "negative_or_failed_path_ledger_refs",
        "decision_trace_refs",
        "artifact_lineage_or_reproducibility_refs",
    ]
    assert fixture_expectations["stable_typed_blocker_path"]["required_ref_families"] == [
        "typed_blocker_refs",
        "routeback_owner_refs",
        "missing_ref_family_refs",
        "no_forbidden_write_proof_refs",
    ]
    assert (
        "studies/002-dm-china-us-mortality-attribution/artifacts/controller/"
        "repair_execution_evidence/latest.json#/candidate_package_freshness"
    ) in fixture_expectations["positive_path"]["current_fixture_seed_refs"][
        "artifact_lineage_or_reproducibility_refs"
    ]
    assert (
        "studies/002-dm-china-us-mortality-attribution/artifacts/controller/"
        "gate_replay_requests/latest.json"
    ) in fixture_expectations["positive_path"]["current_fixture_seed_refs"][
        "decision_trace_refs"
    ]
    assert (
        fixture_expectations["authority_boundary"][
            "opl_lifecycle_substrate_can_transport_refs"
        ]
        is True
    )
    assert (
        fixture_expectations["authority_boundary"][
            "opl_lifecycle_substrate_can_decide_medical_authority"
        ]
        is False
    )
    assert (
        fixture_expectations["authority_boundary"][
            "mas_medical_authority_required_for_publication_quality"
        ]
        is True
    )
    assert (
        fixture_expectations["authority_boundary"][
            "mas_medical_authority_required_for_artifact_mutation"
        ]
        is True
    )

    assert record["stage_expected_receipt_refs"] == [
        owner_receipt_ref,
        progress_ref,
        gate_replay_ref,
        human_gate_ref,
        "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard",
    ]
    assert record["stage_monitor_freshness_refs"] == [
        progress_ref,
        owner_receipt_ref,
        human_gate_ref,
        gate_replay_ref,
        "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard",
    ]
    assert gate_replay_ref in record["evidence_refs"]
    assert stage["success_refs_path_payload"]["domain_receipt_refs"] == record[
        "stage_expected_receipt_refs"
    ]
    assert stage["success_refs_path_payload"]["monitor_freshness_refs"] == record[
        "stage_monitor_freshness_refs"
    ]
    assert stage["typed_blocker_path_payload"]["typed_blocker_refs"] == [
        (
            "mas-stage-typed-blocker:"
            "medautoscience:finalize_and_publication_handoff:"
            "real-paper-line-owner-receipt-or-monitor-freshness-pending"
        )
    ]
    assert stage["recommended_current_payload_path"] == "typed_blocker_path"
    assert stage["success_refs_visible_is_completion"] is False
    assert stage["domain_readiness_claimed"] is False
    assert stage["publication_readiness_claimed"] is False

    packet_roles = {packet["role"] for packet in payload["body_free_evidence_packets"]}
    assert {
        "owner_receipt_ref",
        "progress_delta_ref",
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
        "no_forbidden_write_proof_ref",
    } <= packet_roles


def test_owner_receipt_canary_closeout_materializes_body_free_packets(tmp_path: Path) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
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
        yang_root=tmp_path / "Yang",
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )["paper_line_provider_canary_closeout"]

    packet_roles = {packet["role"] for packet in payload["body_free_evidence_packets"]}
    assert {
        "owner_receipt_ref",
        "progress_delta_ref",
        "artifact_movement_ref",
        "no_forbidden_write_proof_ref",
    } <= packet_roles
    per_line_result = payload["paper_line_owner_chain_results"][0]
    assert per_line_result["surface_kind"] == "mas_paper_line_owner_chain_result"
    assert per_line_result["paper_line_id"] == "002-dm-china-us-mortality-attribution"
    assert per_line_result["owner"] == "MedAutoScience"
    assert per_line_result["result_kind"] == "owner_receipt"
    assert per_line_result["required_return_shape_satisfied"] is True
    assert {
        str(dm002 / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"),
        str(dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"),
    } <= set(per_line_result["owner_receipt_refs"])
    assert per_line_result["stable_typed_blocker_refs"] == []
    assert per_line_result["progress_delta_refs"] == [
        str(dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json")
    ]
    assert per_line_result["ai_reviewer_gate_receipt_refs"] == []
    assert per_line_result["artifact_movement_refs"] == [
        str(dm002 / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json")
    ]
    assert per_line_result["human_gate_or_resume_refs"] == []
    assert per_line_result["no_forbidden_write_proof_ref"] == (
        "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard"
    )
    assert per_line_result["body_included"] is False
    assert per_line_result["readiness_claims"] == {
        "claims_paper_closure": False,
        "claims_publication_ready": False,
        "claims_artifact_mutation_authorized": False,
        "claims_current_package_updated": False,
    }
    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
    assert evidence_payload["task_kind"] == "paper_autonomy/guarded-apply"
    assert evidence_payload["study_id"] == "002-dm-china-us-mortality-attribution"
    assert evidence_payload["mode"] == "refs_only_domain_owned_success_payload"
    assert {
        str(dm002 / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"),
        str(dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"),
    } <= set(evidence_payload["record_payload"]["domain_owner_receipt_refs"])
    assert evidence_payload["record_payload"]["typed_blocker_refs"] == []
    assert evidence_payload["record_payload"]["domain_receipt_refs"] == evidence_payload[
        "record_payload"
    ]["domain_owner_receipt_refs"]
    assert evidence_payload["domain_ready_claimed"] is False
    assert evidence_payload["publication_ready_claimed"] is False
    assert evidence_payload["artifact_mutation_authorized"] is False
    stage_handoff = evidence_payload["stage_evidence_handoff"]
    expected_stage_refs = [
        str(dm002 / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"),
        str(dm002 / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"),
        "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard",
    ]
    assert evidence_payload["record_payload"]["stage_expected_receipt_refs"] == expected_stage_refs
    assert stage_handoff["expected_receipt_refs"] == expected_stage_refs
    assert set(evidence_payload["record_payload"]["stage_monitor_freshness_refs"]) == set(
        expected_stage_refs
    )
    assert set(stage_handoff["monitor_freshness_refs"]) == set(expected_stage_refs)
    assert stage_handoff["status"] == "refs_only_stage_evidence_refs_observed"
    assert stage_handoff["authority_boundary"]["stage_expected_receipt_refs_close_domain_ready"] is False
    stage_packet_roles = {packet["role"] for packet in evidence_payload["body_free_evidence_packets"]}
    assert "stage_expected_receipt_ref" in stage_packet_roles
    assert "stage_monitor_freshness_ref" in stage_packet_roles
    for packet in payload["body_free_evidence_packets"]:
        _assert_body_free_canary_packet(packet, owner="MedAutoScience")


def test_stable_blocker_canary_closeout_materializes_body_free_packets(tmp_path: Path) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
    _write_json(
        dm002 / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=tmp_path / "Yang",
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )["paper_line_provider_canary_closeout"]

    assert {
        packet["role"] for packet in payload["body_free_evidence_packets"]
    } == {"stable_typed_blocker_ref", "no_forbidden_write_proof_ref"}
    per_line_result = payload["paper_line_owner_chain_results"][0]
    assert per_line_result["paper_line_id"] == "002-dm-china-us-mortality-attribution"
    assert per_line_result["result_kind"] == "stable_typed_blocker"
    assert per_line_result["required_return_shape_satisfied"] is True
    assert per_line_result["owner_receipt_refs"] == []
    assert per_line_result["stable_typed_blocker_refs"][0].startswith(
        "mas_owner_apply_receipt_missing:"
    )
    assert per_line_result["body_included"] is False
    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
    assert evidence_payload["mode"] == "refs_only_domain_owned_typed_blocker_payload"
    assert evidence_payload["record_payload"]["domain_owner_receipt_refs"] == []
    assert evidence_payload["record_payload"]["typed_blocker_refs"]
    expected_stage_refs = [
        evidence_payload["record_payload"]["typed_blocker_refs"][0],
        "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard",
    ]
    assert evidence_payload["record_payload"]["stage_expected_receipt_refs"] == expected_stage_refs
    assert set(evidence_payload["record_payload"]["stage_monitor_freshness_refs"]) == set(
        expected_stage_refs
    )
    assert evidence_payload["stage_evidence_handoff"]["status"] == (
        "refs_only_stage_evidence_refs_observed"
    )
    for packet in payload["body_free_evidence_packets"]:
        _assert_body_free_canary_packet(packet, owner="MedAutoScience")


def test_canary_closeout_exposes_per_paper_line_owner_payloads(tmp_path: Path) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    dm003 = workspace / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
    _write_json(dm003 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm003.name})
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
    _write_json(
        dm003 / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm003"},
    )

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=tmp_path / "Yang",
        profile_paths=[profile_path],
        target_studies=("DM002", "DM003"),
    )["paper_line_provider_canary_closeout"]

    assert payload["paper_line_owner_payload_summary"] == {
        "paper_line_count": 2,
        "success_payload_count": 1,
        "typed_blocker_payload_count": 1,
        "domain_ready_claim_count": 0,
        "production_ready_claim_count": 0,
        "artifact_mutation_authorized_count": 0,
    }
    payloads = {
        item["study_id"]: item
        for item in payload["paper_line_domain_dispatch_evidence_record_payloads"]
    }
    assert set(payloads) == {
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    }
    assert payloads["002-dm-china-us-mortality-attribution"]["mode"] == (
        "refs_only_domain_owned_success_payload"
    )
    assert payloads["002-dm-china-us-mortality-attribution"]["record_payload"][
        "domain_owner_receipt_refs"
    ]
    assert payloads["002-dm-china-us-mortality-attribution"]["record_payload"][
        "typed_blocker_refs"
    ] == []
    assert payloads["003-dpcc-primary-care-phenotype-treatment-gap"]["mode"] == (
        "refs_only_domain_owned_typed_blocker_payload"
    )
    assert payloads["003-dpcc-primary-care-phenotype-treatment-gap"]["record_payload"]["typed_blocker_refs"][
        0
    ].startswith("mas_owner_apply_receipt_missing:")
    for evidence_payload in payloads.values():
        assert evidence_payload["domain_ready_claimed"] is False
        assert evidence_payload["publication_ready_claimed"] is False
        assert evidence_payload["artifact_mutation_authorized"] is False
        assert evidence_payload["current_package_mutation_authorized"] is False

    stage_summary = payload["stage_expected_receipt_payload_summary"]
    assert stage_summary["surface_kind"] == "mas_stage_expected_receipt_payload_summary"
    assert stage_summary["owner"] == "med-autoscience"
    assert stage_summary["consumer"] == "one_person_lab"
    assert stage_summary["status"] == (
        "per_stage_expected_receipt_payload_refs_ready_with_live_evidence_typed_blockers"
    )
    assert stage_summary["payload_body_allowed"] is False
    assert stage_summary["empty_payload_template_is_success_evidence"] is False
    assert stage_summary["required_operator_payload_refs"] == [
        "domain_receipt_refs",
        "monitor_freshness_refs",
        "runtime_event_refs",
        "typed_blocker_refs",
    ]
    assert stage_summary["required_return_shapes"] == [
        "domain_receipt_ref",
        "monitor_freshness_ref",
        "runtime_event_ref",
        "typed_blocker_ref",
    ]
    assert stage_summary["stage_count"] == 6
    stages = {stage["stage_id"]: stage for stage in stage_summary["stages"]}
    assert set(stages) == {
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    }
    for stage_id, sequence in {
        "direction_and_route_selection": 1,
        "baseline_and_evidence_setup": 2,
        "bounded_analysis_campaign": 3,
        "manuscript_authoring": 4,
        "review_and_quality_gate": 5,
    }.items():
        stage = stages[stage_id]
        assert stage["sequence"] == sequence
        assert stage["success_refs_path_payload"] == {
            "domain_receipt_refs": [],
            "monitor_freshness_refs": [],
            "runtime_event_refs": [],
            "typed_blocker_refs": [],
        }
        assert stage["typed_blocker_path_payload"] == {
            "domain_receipt_refs": [],
            "monitor_freshness_refs": [],
            "runtime_event_refs": [],
            "typed_blocker_refs": [
                (
                    "mas-stage-typed-blocker:"
                    f"medautoscience:{stage_id}:"
                    "real-paper-line-owner-receipt-or-monitor-freshness-pending"
                )
            ],
        }
        assert stage["recommended_current_payload_path"] == "typed_blocker_path"
        assert stage["success_refs_visible_is_completion"] is False
        assert stage["typed_blocker_visible_is_domain_ready"] is False
        assert stage["domain_readiness_claimed"] is False
        assert stage["production_readiness_claimed"] is False
        assert stage["publication_readiness_claimed"] is False

    stage = stages["finalize_and_publication_handoff"]
    assert stage["sequence"] == 6
    assert stage["current_payload_template"] == {
        "domain_receipt_refs": [],
        "monitor_freshness_refs": [],
        "runtime_event_refs": [],
        "typed_blocker_refs": [],
    }
    assert stage["success_refs_path_payload"]["domain_receipt_refs"] == payloads[
        "002-dm-china-us-mortality-attribution"
    ]["record_payload"]["stage_expected_receipt_refs"]
    assert stage["success_refs_path_payload"]["monitor_freshness_refs"] == payloads[
        "002-dm-china-us-mortality-attribution"
    ]["record_payload"]["stage_monitor_freshness_refs"]
    assert stage["typed_blocker_path_payload"]["typed_blocker_refs"] == payloads[
        "003-dpcc-primary-care-phenotype-treatment-gap"
    ]["record_payload"]["typed_blocker_refs"]
    assert stage["recommended_current_payload_path"] == "typed_blocker_path"
    assert stage["success_refs_visible_is_completion"] is False
    assert stage["domain_readiness_claimed"] is False
    assert stage["production_readiness_claimed"] is False

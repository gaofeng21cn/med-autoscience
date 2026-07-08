from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from med_autoscience.paper_mission_stage_closure_ledger import (
    write_paper_mission_stage_closure_decision,
)
from tests.study_runtime_test_helpers import write_synced_submission_delivery
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


def test_paper_mission_inspect_projects_ledger_typed_blocker_owner_gate(
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
        / "20260630Tledger-typed-blocker"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone::typed-blocker"
    one_shot_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Consumed milestone with typed blocker stage closure.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {
                    "status": "accepted",
                    "outcome": "accepted_submission_milestone_candidate",
                },
                "claim_permissions": {
                    "can_claim_artifact_delta": False,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": one_shot_transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "one-person-lab",
                        "work_unit_id": "submission_milestone_candidate",
                    },
                    "consume_candidate_status": "typed_blocker",
                },
            }
        ),
        encoding="utf-8",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=one_shot_transaction,
    )
    consume_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "sat-current"
    )
    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(consume_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert consume_exit_code == 0
    consume_payload = json.loads(capsys.readouterr().out)
    current_transaction = consume_payload["paper_mission_transaction_readback"][
        "paper_mission_transaction"
    ]
    stage_closure_ref = "typed-blocker:dm002:submission-authority-human-gate"
    write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "sat-current"
        ),
        study_id=study_id,
        decision={
            "decision_ref": stage_closure_ref,
            "study_id": study_id,
            "stage_id": "submission_milestone_candidate",
            "work_unit_id": "submission_blocker_human_gate",
            "outcome": {
                "kind": "typed_blocker",
                "blocker_id": "submission_authority_human_gate_required",
                "typed_blocker_evidence_ref": stage_closure_ref,
                "authority_materialized": False,
            },
        },
        source_readback={
            **consume_payload,
            "paper_mission_transaction": current_transaction,
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready", "owner_receipt_written"),
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["stage_closure_outcome"] == "typed_blocker"
    gate = payload["terminal_owner_gate"]
    assert gate["owner"] == "mas_authority_kernel"
    assert gate["gate_kind"] == "typed_blocker"
    assert gate["typed_blocker_ref"] == stage_closure_ref
    assert gate["legal_next_action"] == "route_to_owner_or_human_gate"
    assert gate["can_claim_paper_progress"] is False
    assert gate["can_claim_runtime_ready"] is False
    assert payload["next_owner_or_human_decision"] == {
        "kind": "owner_or_route",
        "next_owner": "mas_authority_kernel",
        "human_decision_required": False,
        "summary": "submission_authority_human_gate_required",
        "typed_blocker_ref": stage_closure_ref,
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }
    authority_readback = payload["terminal_owner_gate_authority_readback"]
    assert authority_readback["status"] == "owner_answer_required"
    assert authority_readback["next_owner"] == "mas_authority_kernel"
    assert authority_readback["authority_boundary"]["can_write_typed_blocker"] is False
    assert payload["paper_mission_transaction_readback"]["terminal_owner_gate"] == gate
    assert payload["next_action"]["owner"] == "mas_authority_kernel"
    assert payload["next_action"]["authority_boundary"][
        "can_claim_publication_ready"
    ] is False
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_inspect_prefers_latest_governed_consumption_ledger_transaction(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    write_synced_submission_delivery(
        study_root=study_root,
        quest_root=workspace_root / "managed-runtime" / "quests" / "quest-003",
        include_submission_checklist=False,
    )
    current_package_manifest = (
        study_root
        / "manuscript"
        / "current_package"
        / "audit"
        / "submission_manifest.json"
    )
    current_package_manifest.parent.mkdir(parents=True, exist_ok=True)
    current_package_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_signature": "source::dm003-current",
                "package_kind": "submission_ready_package",
                "can_submit": True,
                "quality_gate_status": "clear",
                "known_blockers": [],
                "generated_from_current_source": True,
            }
        ),
        encoding="utf-8",
    )
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = (
        f"paper-mission::{study_id}::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    one_shot_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Older one-shot typed blocker mission.",
                "mission_state": "stable_blocker",
                "artifact_delta_ledger": [
                    {
                        "delta_id": "delta::dm003::one-shot",
                        "artifact_ref": "mission://dm003/prose-repair-owner-decision",
                        "delta_kind": "formal_paper_mission_owner_decision_packet",
                        "status": "candidate",
                    }
                ],
                "source_refs": [
                    {
                        "ref_id": "legacy_truth_import_pack",
                        "ref_kind": "legacy_truth_import_pack",
                        "uri": "mission://dm003/import-pack",
                    }
                ],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "typed_blocker"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": one_shot_transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "one-person-lab",
                        "work_unit_id": "analysis_claim_evidence_repair",
                    },
                    "consume_candidate_status": "typed_blocker",
                },
            }
        ),
        encoding="utf-8",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=one_shot_transaction,
    )
    consume_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "sat-current"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(consume_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    stale_receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / "stale-opl-attempt"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stale_receipt_ref.parent.mkdir(parents=True)
    stale_receipt_ref.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_receipt_owner_consumption",
                "schema_version": 1,
                "status": "owner_consumption_applied",
                "study_id": study_id,
                "apply_mode": "typed_blocker",
                "authority_materialized": True,
                "stage_closure_decision": {
                    "surface_kind": "mas_stage_closure_decision",
                    "schema_version": 1,
                    "study_id": study_id,
                    "authority_materialized": True,
                    "counts_as_typed_blocker": True,
                    "outcome": {
                        "kind": "typed_blocker",
                        "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                        "next_action": "resolve_typed_blocker_or_route_redesign",
                        "known_blockers": [
                            "paper_mission_stage_route_domain_gate_pending"
                        ],
                        "authority_materialized": True,
                    },
                    "authority_boundary": {
                        "surface_role": "paper_mission_receipt_owner_consumption",
                        "writes_receipt_owner_consumption": True,
                        "writes_owner_receipt": False,
                        "writes_typed_blocker": False,
                        "writes_human_gate": False,
                        "writes_current_package": False,
                        "writes_submission_ready_package": False,
                        "writes_runtime_queue_or_provider_attempt": False,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    consume_record_ref = consume_root / study_id / "consume_record.json"
    os.utime(stale_receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(consume_record_ref, (3_000_000_000, 3_000_000_000))
    capsys.readouterr()

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["consume_result"]["status"] == "accepted"
    assert payload["paper_mission_run"]["consume_result"]["outcome"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["transaction_state"] == "accepted_submission_milestone_candidate"
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["durable_mission_stop_guard"][
        "accepted_submission_milestone_candidate_is_durable_stop"
    ] is False
    assert payload["durable_mission_stop_guard"]["durable_stop_allowed"] is False
    assert payload["stage_closure"]["outcome_kind"] == "next_stage_transition"
    assert payload["stage_closure"]["next_transition"] != "complete_mission"
    assert "receipt_owner_consumption_readback" not in payload
    assert payload["next_action"]["action_family"] != "mission.complete"
    assert payload["current_package"]["status"] == "missing"
    assert payload["current_package"]["package_kind"] == "submission_ready_package"
    assert payload["current_package"]["can_submit"] is True
    assert payload["current_package"]["known_blockers"] == []
    assert payload["current_package"]["generated_from_current_source"] is True
    assert payload["current_package"]["root"] == str(
        study_root / "manuscript" / "current_package"
    )
    assert payload["current_package"]["zip_path"] == str(
        study_root / "manuscript" / "current_package.zip"
    )
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["next_owner_or_human_decision"]["next_owner"] == (
        "mission_executor"
    )
    assert payload["next_owner_or_human_decision"]["route_command"] == (
        "resume_stage"
    )
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["paper_mission_transaction"]["stage_id"] == (
        "submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["paper_mission_transaction"] == (
        payload["paper_mission_transaction"]
    )
    assert payload["paper_mission_consumption_ledger_readback"]["source_ref"].endswith(
        f"/paper_mission_consumption_ledger/sat-current/{study_id}/consume_record.json"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)

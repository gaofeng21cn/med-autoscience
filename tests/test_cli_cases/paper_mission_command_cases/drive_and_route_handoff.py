from __future__ import annotations

import importlib
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from med_autoscience.cli_parts import paper_mission_commands as commands
from med_autoscience.cli_parts.paper_mission_command_parts.drive_readback import (
    build_paper_mission_drive_readback,
    _drive_owner_action_stop_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    materialized_mission_readback as materialized_readback,
)
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))


def test_domain_handler_export_default_route_handoff_carries_top_level_identity(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "001-paper"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    mission_id = f"paper-mission::{study_id}::gate-clearing::manual"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="advance",
    )
    candidate_path = _write_candidate_manifest(
        tmp_path,
        study_id=study_id,
        paper_mission_transaction=transaction,
    )
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "domain-handler-export-identity"
        / study_id
    )
    mission_root.mkdir(parents=True)
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Consume paper mission candidate and hand it to OPL.",
                "mission_state": "candidate_ready_for_consumption",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "accepted"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": transaction,
            }
        ),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-001", "study_id": study_id}),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "domain-handler-export-identity"
    )

    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--output-root",
            str(output_root),
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

    export_exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    export_payload = json.loads(capsys.readouterr().out)

    assert export_exit_code == 0
    task = next(
        item
        for item in export_payload["paper_mission_default_tasks"]
        if item["study_id"] == study_id
    )
    handoff = task["opl_route_handoff"]
    record = task["opl_route_handoff_record"]
    payload_handoff = task["payload"]["opl_route_handoff"]
    carrier = handoff["opl_runtime_carrier"]
    next_action = task["next_action"]

    for exported_handoff in (handoff, record, payload_handoff):
        assert exported_handoff["route_identity_key"] == carrier["route_identity_key"]
        assert exported_handoff["attempt_idempotency_key"] == (
            carrier["attempt_idempotency_key"]
        )
        assert exported_handoff["request_idempotency_key"] == (
            carrier["request_idempotency_key"]
        )
    assert task["route_identity_key"] == carrier["route_identity_key"]
    assert task["attempt_idempotency_key"] == carrier["attempt_idempotency_key"]
    assert task["request_idempotency_key"] == carrier["request_idempotency_key"]
    assert task["payload"]["route_identity_key"] == carrier["route_identity_key"]
    assert task["payload"]["attempt_idempotency_key"] == carrier[
        "attempt_idempotency_key"
    ]
    assert task["payload"]["request_idempotency_key"] == carrier[
        "request_idempotency_key"
    ]
    assert task["payload"]["next_action"] == next_action
    assert next_action["surface_kind"] == "mas_next_action_envelope"
    assert next_action["action_family"] == "runtime.opl_route"
    assert next_action["action_kind"] == "submit_to_opl_runtime"
    assert next_action["owner"] == "one-person-lab"
    assert next_action["idempotency_key"] == carrier["request_idempotency_key"]
    assert {"role": "paper_mission_transaction", "ref": handoff["paper_mission_transaction_ref"]} in next_action[
        "diagnostic_refs"
    ]
    assert {"role": "stage_terminal_decision", "ref": handoff["stage_terminal_decision_ref"]} in next_action[
        "diagnostic_refs"
    ]
    assert {"role": "opl_route_command", "ref": handoff["opl_route_command_ref"]} in next_action["diagnostic_refs"]
    assert next_action["authority_boundary"]["can_write_runtime_queue"] is False
    assert next_action["authority_boundary"]["can_write_provider_attempt"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)



def test_paper_mission_drive_packages_consumes_and_returns_opl_route_handoff(
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
        / "20260624Tdrive"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::drive"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM002 route-back candidate to OPL handoff.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::route-back",
                "artifact_ref": "mission://dm002/route-back",
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
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-drive",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrive",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--no-submit-opl-runtime",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_drive_readback"
    assert payload["action_intent"] == "paper_mission/drive"
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["consume_readback"]["next_action"][
        "action_family"
    ] == "runtime.opl_route"
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["drive_result"]["status"] == "mas_owned_executor_delta_ready"
    assert payload["drive_result"]["stage_terminal_decision"] == "continue_same_stage"
    assert payload["drive_result"]["route_command"] == "resume_stage"
    assert payload["drive_result"]["next_owner"] == "mission_executor"
    assert payload["drive_result"]["can_submit_to_opl_runtime"] is True
    assert payload["stage_closure_outcome"] == "next_stage_transition"
    assert payload["output_manifest"]["stage_closure"]["writes_authority"] is False
    assert payload["drive_result"]["opl_runtime_submission_status"] == "not_requested"
    assert payload["opl_runtime_submission"]["status"] == "not_requested"
    assert payload["opl_runtime_submission"]["writes_runtime"] is False
    assert payload["drive_result"]["provider_attempt_running_observed"] is False
    assert payload["drive_result"]["terminal_closeout_observed"] is False
    assert payload["drive_result"]["can_claim_paper_progress"] is False
    assert payload["drive_result"]["can_claim_runtime_ready"] is False
    assert payload["drive_result"]["authority_materialized"] is False
    package_manifest = payload["candidate_package_readback"]["output_manifest"]
    consume_manifest = payload["consume_readback"]["consume_output_manifest"]
    assert package_manifest["mode"] == "non_authority_candidate_package"
    assert consume_manifest["mode"] == "governed_consume_record"
    assert consume_manifest["route_handoff_status"] == "ready_for_opl_route_command"
    assert consume_manifest["next_owner"] == "mission_executor"
    assert payload["opl_route_handoff"]["next_owner"] == "mission_executor"
    assert payload["opl_route_handoff"]["can_submit_to_opl_runtime"] is True
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    assert payload["mutation_policy"]["writes_yang_authority"] is False
    assert payload["output_manifest"]["writes_authority"] is False
    assert payload["output_manifest"]["writes_runtime"] is False
    assert payload["output_manifest"]["writes_yang_authority"] is False
    assert Path(package_manifest["package_manifest_ref"]).exists()
    assert Path(consume_manifest["opl_route_handoff_ref"]).exists()
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_reuses_existing_reviewer_revision_handoff_without_one_shot_migration(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::paper_mission_import::one-shot"
    package_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "external-sci-review-v3"
        / study_id
    )
    package_root.mkdir(parents=True)
    action_matrix = (
        package_root
        / "paper_facing_candidate_artifacts"
        / "reviewer_action_matrix.json"
    )
    action_matrix.parent.mkdir(parents=True)
    action_matrix.write_text(
        json.dumps({"concerns": [{"id": "SCI3-001", "severity": "blocker"}]}),
        encoding="utf-8",
    )
    owner_request = package_root / "owner_consumption_request.json"
    owner_request.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_owner_consumption_request",
                "requested_action": (
                    "consume_external_sci_registry_review_v3_as_reviewer_revision"
                ),
                "recommended_next_route": (
                    "ai_reviewer_recheck_then_analysis-campaign_write_and_human_gate"
                ),
            }
        ),
        encoding="utf-8",
    )
    package_path = package_root / "package_manifest.json"
    package_path.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_foreground_candidate_package_manifest",
                "schema_version": 1,
                "mode": "non_authority_candidate_package",
                "milestone_kind": "reviewer_revision_candidate",
                "candidate_content_kind": "external_high_quality_sci_review_intake",
                "candidate_revision_round": (
                    "external_sci_registry_review_v3_submission_readiness"
                ),
                "study_id": study_id,
                "mission_id": mission_id,
                "candidate_is_authority": False,
                "artifact_refs": {
                    "reviewer_action_matrix": str(action_matrix),
                    "owner_consumption_request": str(owner_request),
                },
                "recommended_next_route": (
                    "ai_reviewer_recheck_then_analysis-campaign_write_and_human_gate"
                ),
            }
        ),
        encoding="utf-8",
    )
    consume_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "external-sci-review-v3-fixed-route"
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
    capsys.readouterr()

    drive_exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "no-one-shot-materialized",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--no-submit-opl-runtime",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert drive_exit_code == 0
    assert payload["drive_mode"] == "existing_consumption_handoff"
    assert payload["candidate_package_readback"]["status"] == (
        "skipped_existing_consumption_handoff"
    )
    assert payload["transaction_state"] == "reviewer_revision_candidate_ready"
    assert payload["consume_readback"]["consume_output_manifest"][
        "route_handoff_status"
    ] == "ready_for_opl_route_command"
    assert payload["opl_route_handoff"]["next_owner"] == "ai_reviewer"
    assert payload["stage_terminal_decision"]["next_work_unit"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["opl_runtime_submission"]["status"] == "not_requested"
    assert payload["output_manifest"]["writes_authority"] is False
    assert payload["output_manifest"]["writes_runtime"] is False
    assert payload["output_manifest"]["writes_yang_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_packages_when_submission_minimal_owner_action_ready(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "typed-blocker-readback.json"
    readback_file.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "next_action": {
                    "action_family": "paper.package.submission_minimal",
                    "action_kind": "package_materialization",
                    "action_type": (
                        "classify_quality_blockers_or_materialize_degraded_handoff_gate"
                    ),
                    "owner": "mas_authority_kernel",
                    "work_unit_id": (
                        "submission_blocker_degraded_handoff_or_quality_repair"
                    ),
                    "work_unit_fingerprint": "obesity-quality-repair",
                },
                "stage_closure_decision": {
                    "outcome": {
                        "kind": "typed_blocker",
                        "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                        "typed_blocker_evidence_ref": str(tmp_path / "typed.json"),
                    }
                },
                "current_package": {
                    "status": "current",
                    "package_kind": "current_package",
                    "can_submit": False,
                    "quality_gate_status": "blocked",
                    "known_blockers": ["submission_metadata_pending"],
                    "root": str(tmp_path / "current_package"),
                    "zip_path": str(tmp_path / "current_package.zip"),
                    "zip_exists": True,
                    "generated_from_current_source": True,
                },
            }
        ),
        encoding="utf-8",
    )
    resolution_output_root = (
        tmp_path
        / "workspace"
        / "ops"
        / "medautoscience"
        / "paper_mission_typed_blocker_resolution"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "typed-blocker-resolution",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--output-root",
            str(resolution_output_root),
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    drive_output_root = tmp_path / "workspace" / "ops" / "medautoscience" / "drive"
    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--output-root",
            str(drive_output_root),
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
    assert payload["drive_mode"] == "package_consume_and_optionally_submit"
    assert payload["candidate_package_readback"]["output_manifest"][
        "package_manifest_ref"
    ]
    assert payload["inspect_readback"]["next_action"]["action_type"] == (
        "classify_quality_blockers_or_materialize_degraded_handoff_gate"
    )
    assert payload["mutation_policy"]["writes_yang_ops_candidate_package"] is False
    assert payload["mutation_policy"]["writes_yang_ops_consumption_ledger"] is False
    assert (drive_output_root / "candidate_package").exists()
    assert (drive_output_root / "consumption_ledger").exists()
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_stops_when_route_back_checkpoint_owner_action_ready(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    profile = SimpleNamespace(
        name="Obesity",
        studies_root=tmp_path / "workspace" / "studies",
    )
    (Path(profile.studies_root) / study_id).mkdir(parents=True)
    output_root = tmp_path / "workspace" / "ops" / "medautoscience" / "drive"

    payload = _drive_owner_action_stop_readback(
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
        output_root=output_root,
        source="test",
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
        inspect_readback={
            "mission_id": "paper-mission::obesity::one-shot",
            "objective": "Consume route-back checkpoint.",
            "paper_mission_current_transaction_source": (
                "paper_mission_consumption_ledger"
            ),
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.stage_closure.owner_consumption",
                "action_kind": "owner_consumption",
                "action_type": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "owner": "MedAutoScience",
                "work_unit_id": "write",
            },
            "stage_closure_decision": {
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                }
            },
            "terminal_owner_gate_authority_readback": {
                "status": "owner_answer_required",
                "authority_boundary": {"can_claim_paper_progress": False},
            },
            "terminal_owner_gate_owner_answer_readback": {
                "owner_answer_shape": "route_back_evidence_ref",
                "consume_result": {"outcome": "route_back_evidence_ref"},
            },
        },
    )

    assert payload is not None
    assert payload["drive_mode"] == "owner_action_ready_no_redrive"
    assert payload["drive_result"]["reason"] == (
        "stage_closure_route_back_checkpoint_requires_owner_consumption"
    )
    assert payload["drive_result"]["forbidden_next_action"] == (
        "synonymous_route_back_redrive"
    )
    assert payload["next_action"]["action_family"] == (
        "paper.stage_closure.owner_consumption"
    )
    assert payload["mutation_policy"]["writes_yang_ops_candidate_package"] is False
    assert payload["mutation_policy"]["writes_yang_ops_consumption_ledger"] is False
    assert not output_root.exists()


def test_paper_mission_drive_does_not_stop_runtime_route_on_stale_owner_gate(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile = SimpleNamespace(
        name="DM-CVD",
        studies_root=tmp_path / "workspace" / "studies",
    )
    (Path(profile.studies_root) / study_id).mkdir(parents=True)
    output_root = tmp_path / "workspace" / "ops" / "medautoscience" / "drive"

    payload = _drive_owner_action_stop_readback(
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
        output_root=output_root,
        source="test",
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::one-shot",
            "objective": "Submit accepted mission route to OPL.",
            "paper_mission_current_transaction_source": (
                "paper_mission_consumption_ledger"
            ),
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "runtime.opl_route",
                "action_kind": "submit_to_opl_runtime",
                "owner": "one-person-lab",
                "work_unit_id": "submission_milestone_candidate",
                "authority_boundary": {
                    "can_submit_to_opl_runtime": True,
                    "can_claim_paper_progress": False,
                },
            },
            "terminal_owner_gate": {
                "gate_kind": "typed_blocker",
                "blocked_reason": (
                    "mission_executor_owner_answer_or_same_transaction_opl_readback_required"
                ),
                "typed_blocker_ref": "old-closeout#domain_blocker",
                "can_claim_paper_progress": False,
            },
        },
    )

    assert payload is None
    assert not output_root.exists()


def test_paper_mission_drive_does_not_stop_domain_next_action_on_current_consumption(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile = SimpleNamespace(
        name="DM-CVD",
        studies_root=tmp_path / "workspace" / "studies",
    )
    (Path(profile.studies_root) / study_id).mkdir(parents=True)
    output_root = tmp_path / "workspace" / "ops" / "medautoscience" / "drive"

    payload = _drive_owner_action_stop_readback(
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
        output_root=output_root,
        source="test",
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::one-shot",
            "objective": "Return current revision to AI reviewer.",
            "paper_mission_current_transaction_source": (
                "paper_mission_consumption_ledger"
            ),
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            },
            "current_opl_runtime_carrier_readback": {
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "next_legal_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "receipt_evidence_ref": "opl://stage-attempts/sat_old",
                    "route_checkpoint_evidence_ref": "old-checkpoint.json",
                    "can_claim_paper_progress": False,
                }
            },
        },
    )

    assert payload is None
    assert not output_root.exists()


def test_consumption_ledger_inspect_prefers_domain_transition_after_route_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review"
        ),
    }
    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: {
            "status": "owner_consumption_applied",
            "stage_closure_decision": {
                "decision_ref": f"{transaction['transaction_id']}#stage_closure_decision",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "next_owner": "MedAutoScience",
                    "can_submit": False,
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "next_legal_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-review",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-review/stage_attempt_closeout_packet.json"
                ),
                "can_claim_paper_progress": False,
            },
        },
    )
    monkeypatch.setattr(
        commands.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
            },
            "next_action": next_action,
        },
    )

    payload = commands._consumption_ledger_inspect_readback(
        profile=profile,
        profile_ref=tmp_path / "dm.local.toml",
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        consumption_readback={
            "surface_kind": "paper_mission_consumption_readback",
            "mission_id": mission_id,
            "study_id": study_id,
            "selected_outcome": "accepted_submission_milestone_candidate",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": transaction,
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert payload["next_action"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert payload["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )


def test_paper_mission_drive_submits_domain_transition_next_action_without_candidate_package(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    output_root = workspace_root / "ops" / "medautoscience" / "drive"
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl-direct.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def payloads():",
                "    return [r['payload'] for r in records if 'payload' in r]",
                "def current_payload():",
                "    ps = payloads()",
                "    return ps[-1] if ps else {}",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_write_repair',",
                "        'work_unit_id': payload.get('work_unit_id'),",
                "        'work_unit_fingerprint': payload.get('work_unit_fingerprint'),",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "            'work_unit_id': payload.get('work_unit_id'),",
                "            'work_unit_fingerprint': payload.get('work_unit_fingerprint'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_write_repair','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = current_payload()",
                "    task = {'task_id':'frt_write_repair','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task], 'queue': {'total': 1}, 'stage_attempts':[running_attempt(payload)]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = current_payload()",
                "    task = {'task_id':'frt_write_repair','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[running_attempt(payload)]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)
    builder_calls: list[str] = []

    def fake_readback_builder(**kwargs):
        command = kwargs["paper_mission_command"]
        builder_calls.append(command)
        assert command == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Route medical methods and registry reporting repair.",
            "study_id": study_id,
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-write-repair",
                "study_id": study_id,
                "stage_id": "write",
                "outcome_ref": (
                    "domain-transition::route_back_same_line::"
                    "medical_methods_and_registry_reporting_repair"
                ),
                "action_family": "paper.write.prose_repair",
                "action_kind": "paper_write",
                "action_type": "request_opl_stage_attempt",
                "owner": "write",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "medical_methods_and_registry_reporting_repair",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "medical_methods_and_registry_reporting_repair"
                ),
            },
            "canonical_next_action_source": "domain_transition.next_action",
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=output_root,
        run_id=None,
        submit_opl_runtime=True,
        opl_bin=fake_opl,
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert builder_calls == ["inspect"]
    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None
    assert not (output_root / "candidate_package").exists()
    assert not (output_root / "consumption_ledger").exists()
    assert payload["opl_route_handoff"]["route_target"] == "write"
    assert payload["opl_route_handoff"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert payload["opl_runtime_carrier"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert payload["opl_runtime_carrier_readback"]["running_attempt"]["stage_id"] == (
        "write"
    )
    assert payload["opl_runtime_carrier_readback"]["running_attempt"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert payload["drive_result"]["status"] == "opl_stage_route_running"
    captured = json.loads(capture_path.read_text(encoding="utf-8"))
    enqueue_payload = next(item["payload"] for item in captured if "payload" in item)
    assert enqueue_payload["route_target"] == "write"
    assert enqueue_payload["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert enqueue_payload["stage_run_request"]["route_target"] == "write"
    assert enqueue_payload["authority_boundary"]["writes_paper_body"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_submits_domain_transition_owner_workflow_after_route_back_checkpoint(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    output_root = workspace_root / "ops" / "medautoscience" / "drive"

    def fake_readback_builder(**kwargs):
        assert kwargs["paper_mission_command"] == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Re-run AI reviewer after manuscript revision.",
            "study_id": study_id,
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "outcome_ref": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "ai_reviewer_medical_prose_quality_review"
                ),
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "ai_reviewer_medical_prose_quality_review"
                ),
            },
            "paper_mission_current_transaction_source": (
                "paper_mission_consumption_ledger"
            ),
            "stage_closure_decision": {
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                }
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=output_root,
        run_id=None,
        submit_opl_runtime=False,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert payload["opl_route_handoff"]["route_target"] == "review"
    assert payload["opl_route_handoff"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None
    assert payload["mutation_policy"]["writes_runtime"] is False


def test_paper_mission_drive_prefers_domain_next_action_over_current_opl_consumption(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )

    def fake_readback_builder(**kwargs):
        assert kwargs["paper_mission_command"] == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Re-run AI reviewer after manuscript revision.",
            "study_id": study_id,
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai-reviewer",
            },
            "current_opl_runtime_carrier_readback": {
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "next_legal_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "route_back_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-review/route_back_evidence_packet.json"
                    ),
                    "can_claim_paper_progress": False,
                }
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=workspace_root / "ops" / "medautoscience" / "drive",
        run_id=None,
        submit_opl_runtime=True,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_family"] == "paper.review.ai_reviewer"
    assert payload["opl_route_handoff"]["route_target"] == "review"
    assert payload["opl_route_handoff"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["mutation_policy"]["writes_runtime"] is False


@pytest.mark.parametrize(
    "stale_next_legal_action",
    [
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
        "record_typed_blocker",
    ],
)
def test_paper_mission_drive_ignores_stale_current_opl_consumption_after_owner_consumed_route_checkpoint(
    tmp_path: Path,
    stale_next_legal_action: str,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-review/route_back_evidence_packet.json"
    )
    receipt_ref = "opl://stage-attempts/sat-review"

    def fake_readback_builder(**kwargs):
        assert kwargs["paper_mission_command"] == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Re-run AI reviewer after manuscript revision.",
            "study_id": study_id,
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai-reviewer",
            },
            "current_opl_runtime_carrier_readback": {
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "next_legal_action": stale_next_legal_action,
                    "receipt_evidence_ref": receipt_ref,
                    "route_back_evidence_ref": route_back_ref,
                    "typed_runtime_blocker_ref": (
                        "opl://stage-attempts/sat-review/runtime-blockers/"
                        "closeout-not-materialized"
                    ),
                    "forbidden_next_action": "synonymous_route_back_redrive",
                    "can_claim_paper_progress": False,
                }
            },
            "receipt_owner_consumption_readback": {
                "status": "owner_consumption_applied",
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "owner_consumed_route_checkpoint",
                    "next_legal_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "receipt_evidence_ref": receipt_ref,
                    "route_back_evidence_ref": route_back_ref,
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-review/stage_attempt_closeout_packet.json"
                    ),
                    "typed_runtime_blocker_ref": (
                        "opl://stage-attempts/sat-review/runtime-blockers/"
                        "closeout-not-materialized"
                    ),
                    "forbidden_next_action": "synonymous_route_back_redrive",
                    "can_claim_paper_progress": False,
                },
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=workspace_root / "ops" / "medautoscience" / "drive",
        run_id=None,
        submit_opl_runtime=False,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["drive_result"]["reason"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None
    assert payload["mutation_policy"]["writes_runtime"] is False


def test_paper_mission_inspect_projects_domain_transition_running_attempt(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-write-repair",
        "study_id": study_id,
        "stage_id": "write",
        "outcome_ref": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
        "action_family": "paper.write.prose_repair",
        "action_kind": "paper_write",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "medical_methods_and_registry_reporting_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
    }
    fake_opl = tmp_path / "fake-opl-running-list.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                "args = sys.argv[1:]",
                "if args[:3] != ['family-runtime', 'queue', 'list']:",
                "    raise SystemExit('unexpected args: ' + ' '.join(args))",
                f"study_id = {study_id!r}",
                "transaction_ref = 'paper-mission-transaction::' + study_id + '::write::paper-mission::' + study_id + '::paper_mission_import::one-shot-migration'",
                "route_ref = transaction_ref + '#opl_route_command'",
                "payload = {",
                "    'study_id': study_id,",
                "    'paper_mission_transaction_ref': transaction_ref,",
                "    'opl_route_command_ref': route_ref,",
                "    'command_kind': 'resume_stage',",
                "    'route_target': 'write',",
                "    'work_unit_id': 'medical_methods_and_registry_reporting_repair',",
                "    'work_unit_fingerprint': 'domain-transition::route_back_same_line::medical_methods_and_registry_reporting_repair',",
                "}",
                "linked = {",
                "    'stage_attempt_id': 'sat-write-repair',",
                "    'status': 'live',",
                "    'stage_id': 'write',",
                "    'provider_kind': 'temporal',",
                "    'workflow_id': 'wf-write-repair',",
                "    'provider_run': {'provider_status': 'running', 'last_heartbeat_at': '2026-07-02T03:49:04.038Z'},",
                "    'workspace_locator': payload,",
                "}",
                "task = {",
                "    'task_id': 'frt-write-repair',",
                "    'domain_id': 'medautoscience',",
                "    'task_kind': 'paper_mission/stage-route',",
                "    'status': 'running',",
                "    'payload': payload,",
                "    'linked_stage_attempt_liveness': linked,",
                "}",
                "print(json.dumps({'version': 'g2', 'family_runtime_queue': {'tasks': [task]}}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    readback = materialized_readback._domain_transition_direct_next_action_runtime_readback(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::paper_mission_import::one-shot-migration",
        },
        next_action=next_action,
        canonical_next_action_source="domain_transition.next_action",
        enable_opl_live_probe=True,
        opl_bin=fake_opl,
    )

    assert readback["transaction_state"] == "domain_transition_direct_stage_attempt"
    assert readback["opl_runtime_readback_status"] == (
        "opl_runtime_attempt_running_observed"
    )
    running = readback["opl_runtime_carrier_readback"]["running_attempt"]
    assert running["stage_attempt_id"] == "sat-write-repair"
    assert running["stage_id"] == "write"
    assert running["work_unit_id"] == "medical_methods_and_registry_reporting_repair"
    assert readback["authority_boundary"]["writes_paper_body"] is False


def test_paper_mission_inspect_projects_ai_reviewer_direct_stage_attempt(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
    }

    readback = materialized_readback._domain_transition_direct_next_action_runtime_readback(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::paper_mission_import::one-shot-migration",
        },
        next_action=next_action,
        canonical_next_action_source="domain_transition.next_action",
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert readback["transaction_state"] == "domain_transition_direct_stage_attempt"
    assert readback["opl_runtime_carrier"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert readback["opl_runtime_carrier"]["work_unit_fingerprint"].endswith(
        "::source::fresh"
    )
    assert readback["opl_runtime_readback_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )


def test_paper_mission_drive_can_submit_opl_stage_route_via_public_enqueue(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Tdrive"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone::drive"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM003 consumed candidate into OPL stage-route.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [],
        "source_refs": [],
        "consume_result": {"status": "accepted"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "submission_milestone_candidate",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "submission_milestone_candidate",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "accepted_candidate",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm003-drive",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
            }
        ),
        encoding="utf-8",
    )
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "records = []",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_test_drive',",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_terminal',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_terminal',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_test_drive','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = records[0]['payload'] if records else {}",
                "    task = {'task_id':'frt_test_drive','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = records[0]['payload'] if records else {}",
                "    task = {'task_id':'frt_test_drive','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[running_attempt(payload)]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrive",
            "--opl-bin",
            str(fake_opl),
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
    assert capture_path.exists()
    handoff = payload["opl_route_handoff"]
    assert handoff["route_identity_key"]
    assert handoff["attempt_idempotency_key"]
    assert handoff["candidate_ref"]
    submission = payload["opl_runtime_submission"]
    assert submission["status"] in {"submitted", "running", "terminal_readback_observed"}
    assert submission["writes_runtime"] is True
    assert submission["can_claim_provider_running"] is False
    assert submission["can_claim_paper_progress"] is False
    assert payload["mutation_policy"]["writes_runtime"] is True
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["drive_result"]["status"] in {
        "opl_stage_route_running",
        "submitted",
        "terminal_readback_observed",
    }
    assert payload["stage_closure_outcome"] == "next_stage_transition"
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_followthroughs_terminal_route_back_into_fresh_stage_route(
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
        / "20260624Tdrivefollowthrough"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::drive-followthrough"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    transaction["stage_terminal_decision"]["target_stage_id"] = (
        "paper_mission_stage_route_domain_gate_pending"
    )
    transaction["stage_terminal_decision"]["repair_scope"] = (
        "MAS authority kernel observed a domain gate terminal closeout; mission "
        "executor must revise the paper mission candidate or submit a concrete "
        "owner answer shape before OPL can advance."
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM002 route-back through MAS followthrough.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::route-back",
                "artifact_ref": "mission://dm002/route-back",
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
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-followthrough",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl-followthrough.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def payloads():",
                "    return [r['payload'] for r in records if 'payload' in r]",
                "def current_payload():",
                "    ps = payloads()",
                "    return ps[-1] if ps else {}",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_terminal_followthrough',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_running_followthrough',",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_followthrough','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    attempt = terminal_attempt(payload) if len(ps) == 1 else running_attempt(payload)",
                "    task = {'task_id':'frt_followthrough','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task], 'queue': {'total': 1}, 'stage_attempts':[attempt]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    attempt = terminal_attempt(payload) if len(ps) == 1 else running_attempt(payload)",
                "    task = {'task_id':'frt_followthrough','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[attempt]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrivefollowthrough",
            "--opl-bin",
            str(fake_opl),
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
    assert capture_path.exists()
    assert payload["followthrough"]["attempted"] is False
    assert payload["followthrough"]["round_count"] == 0
    assert payload["followthrough"]["stop_reason"] == "mas_owned_executor_delta_ready"
    assert payload["drive_result"]["status"] != "stage_closure_decision_missing"
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    followthrough_transaction = payload["consume_readback"][
        "paper_mission_transaction_readback"
    ][
        "paper_mission_transaction"
    ]
    assert followthrough_transaction["mission_id"] == mission_id
    assert (
        followthrough_transaction["transaction_id"]
        != payload["mission_id"]
    )
    assert payload["consume_readback"]["contract_validation"]["status"] == "validated"
    assert payload["output_manifest"]["followthrough_round_count"] == 0
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)

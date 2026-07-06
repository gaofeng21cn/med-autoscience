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
    _drive_should_submit_direct_next_action,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    opl_runtime_submission,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    materialized_mission_readback as materialized_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    direct_next_action_handoff as direct_handoff,
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


def test_direct_write_handoff_carries_latest_task_intake_scope_into_runtime_request(
    tmp_path: Path,
) -> None:
    direct_handoff = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.direct_next_action_handoff"
    )
    runtime_submission = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.opl_runtime_submission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    task_intake_path = (
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json"
    )
    task_intake_path.parent.mkdir(parents=True, exist_ok=True)
    task_intake_path.write_text(
        json.dumps(
            {
                "task_id": f"study-task::{study_id}::20260705T102124Z",
                "study_id": study_id,
                "task_intake_kind": "reviewer_revision",
                "task_intent": (
                    "Reframe DM002 around retained cross-population risk stratification, "
                    "promote what remains usable, and require recalibration only for "
                    "absolute-risk communication."
                ),
                "constraints": [
                    "Prefer MAS-native revision surfaces.",
                    "Refresh canonical paper source first, then package.",
                ],
            }
        ),
        encoding="utf-8",
    )
    profile = SimpleNamespace(
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    handoff = direct_handoff.build_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
        },
        next_action={
            "surface_kind": "mas_next_action_envelope",
            "schema_version": 1,
            "action_family": "paper.write.prose_repair",
            "action_kind": "repair",
            "action_type": "request_opl_stage_attempt",
            "owner": "write",
            "stage_id": "write",
            "work_unit_id": "dm002_after_story_repair_medical_prose_hardening",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "dm002_after_story_repair_medical_prose_hardening"
            ),
            "outcome_ref": (
                "domain-transition::route_back_same_line::"
                "dm002_after_story_repair_medical_prose_hardening"
            ),
        },
    )

    runtime_request = runtime_submission._opl_stage_route_runtime_request_from_handoff(
        handoff
    )

    assert handoff["task_intake_kind"] == "reviewer_revision"
    assert handoff["task_intake_ref"]["task_id"] == (
        f"study-task::{study_id}::20260705T102124Z"
    )
    assert handoff["task_intake_ref"]["artifact_path"] == str(task_intake_path)
    assert handoff["task_intake_summary"]["task_intent"].startswith(
        "Reframe DM002 around retained cross-population risk stratification"
    )
    assert runtime_request is not None
    assert runtime_request["payload"]["task_intake_kind"] == "reviewer_revision"
    assert runtime_request["payload"]["task_intake_ref"]["artifact_path"] == str(
        task_intake_path
    )
    assert runtime_request["payload"]["task_intake_summary"]["task_intent"].startswith(
        "Reframe DM002 around retained cross-population risk stratification"
    )


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


def test_paper_mission_drive_auto_consumes_route_back_checkpoint_before_direct_write_handoff(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    calls: list[str] = []

    def fake_readback_builder(**kwargs):
        calls.append(kwargs["source"])
        if len(calls) == 1:
            return {
                "surface_kind": "paper_mission_materialized_readback",
                "mission_id": f"paper-mission::{study_id}::reviewer-revision",
                "objective": "Resume DM002 write revision after reviewer feedback.",
                "study_id": study_id,
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
                    "stage_id": "write",
                    "work_unit_id": "dm002_after_story_repair_medical_prose_hardening",
                },
                "stage_closure_decision": {
                    "stage_id": "write",
                    "work_unit_id": "dm002_after_story_repair_medical_prose_hardening",
                    "opl_closeout": {
                        "status": "opl_runtime_terminal_readback_observed",
                        "stage_attempt_id": "sat-dm002-write",
                        "work_unit_id": (
                            "dm002_after_story_repair_medical_prose_hardening"
                        ),
                    },
                    "outcome": {
                        "kind": "next_stage_transition",
                        "transition_kind": "route_back_candidate_checkpoint",
                        "next_action": (
                            "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                        ),
                        "next_owner": "MedAutoScience",
                    },
                },
                "current_package": {
                    "package_kind": "current_package",
                    "can_submit": False,
                },
                "current_opl_runtime_carrier_readback": {
                    "opl_transition_receipt": {
                        "surface_kind": "opl_transition_receipt",
                        "receipt_status": "terminal_closeout_observed",
                        "role": "transport_receipt_only",
                        "stage_attempt_id": "sat-dm002-write",
                        "stage_attempt_ref": "opl://stage-attempts/sat-dm002-write",
                        "can_claim_paper_progress": False,
                    },
                    "receipt_evidence": {
                        "stage_attempt_ref": "opl://stage-attempts/sat-dm002-write",
                        "receipt_ref": "opl://stage-attempts/sat-dm002-write",
                        "runtime_closeout_ref": (
                            "opl://stage-attempts/sat-dm002-write/runtime-closeout"
                        ),
                        "route_checkpoint_evidence_ref": (
                            "ops/medautoscience/paper_mission_stage_attempts/"
                            "sat-dm002-write/stage_attempt_closeout_packet.json"
                        ),
                    },
                    "mas_receipt_consumption": {
                        "surface_kind": "mas_receipt_consumption_projection",
                        "status": "requires_mas_owner_consumption",
                        "next_legal_action": (
                            "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                        ),
                        "receipt_ref": "opl://stage-attempts/sat-dm002-write",
                        "runtime_closeout_ref": (
                            "opl://stage-attempts/sat-dm002-write/runtime-closeout"
                        ),
                        "can_claim_paper_progress": False,
                    },
                },
            }
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Resume DM002 write revision after reviewer feedback.",
            "study_id": study_id,
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-dm002-write",
                "study_id": study_id,
                "stage_id": "write",
                "action_family": "paper.write.prose_repair",
                "action_kind": "repair",
                "action_type": "request_opl_stage_attempt",
                "owner": "write",
                "work_unit_id": "dm002_after_story_repair_medical_prose_hardening",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_after_story_repair_medical_prose_hardening"
                ),
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "dm.local.toml",
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

    receipt_packet = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
        / "receipt_owner_consumption.json"
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_type"] == "request_opl_stage_attempt"
    assert payload["opl_route_handoff"]["route_target"] == "write"
    assert payload["opl_route_handoff"]["work_unit_id"] == (
        "dm002_after_story_repair_medical_prose_hardening"
    )
    assert receipt_packet.exists()
    assert len(calls) == 2
    assert calls[0].endswith(":drive:canonical-next-action-inspect")
    assert calls[1].endswith(":drive:post-route-checkpoint:drive:canonical-next-action-inspect")


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

from tests.test_cli_cases.paper_mission_command_cases.drive_and_route_handoff_cases.consumption_ledger_readback import *  # noqa: F401,F403,E501
from tests.test_cli_cases.paper_mission_command_cases.drive_and_route_handoff_cases.domain_transition_routes import *  # noqa: F401,F403,E501
from tests.test_cli_cases.paper_mission_command_cases.drive_and_route_handoff_cases.direct_next_action_and_opl_stage import *  # noqa: F401,F403,E501

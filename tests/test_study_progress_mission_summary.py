from __future__ import annotations

import importlib
import json
import os

import pytest

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND
from tests.test_cli_cases.paper_mission_command_helpers import (
    _paper_mission_transaction_payload,
    _paper_mission_forbidden_write_guard,
    _write_submission_milestone_package,
)
from tests.test_cli_cases.shared import write_profile


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))


from tests.test_study_progress_mission_summary_cases.materialized_readback import annotations, test_artifact_first_mission_summary_prefers_materialized_paper_mission_run, test_materialized_mission_summary_does_not_let_opl_closeout_override_stage_outcome, test_materialized_mission_summary_prefers_latest_governed_consumption_ledger, test_consumption_ledger_summary_uses_terminalized_stage_closure_readback, test_materialized_mission_summary_consumes_receipt_owner_consumption_ledger, test_typed_blocker_resolution_successor_supersedes_stale_wakeup_top_level, test_materialized_mission_summary_keeps_governed_consumption_current_when_terminal_residue_exists, test_submission_authority_owner_gate_removes_superseded_next_action, test_submission_authority_owner_gate_keeps_new_next_action_for_different_identity
from tests.test_study_progress_mission_summary_cases.next_action_stage_closure import (
    test_top_level_next_legal_action_prefers_canonical_runtime_readback_request,
    test_single_next_action_projection_prefers_domain_transition_reviewer_action,
    test_typed_blocker_successor_does_not_override_domain_transition_reviewer_action,
    test_new_reviewer_revision_intake_retire_stale_typed_blocker_resolution,
    test_top_level_next_legal_action_prefers_receipt_consumption_over_stage_replay,
    test_artifact_first_mission_summary_prefers_stage_closure_ledger_over_stale_progress_projection,
    test_paper_mission_run_nested_stage_closure_readback_keeps_terminalizer_fields,
)


def test_receipt_owner_consumption_route_checkpoint_maps_to_route_back_status() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.mission_summary"
    )

    status = module._effective_consume_candidate_status_for_receipt_owner_consumption(
        fallback="accepted",
        receipt_owner_consumption_readback={
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            }
        },
    )

    assert status == "route_back"


def test_fallback_mission_summary_consumes_governed_ledger_without_materialized_run(
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    old_resolution = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_typed_blocker_resolution"
        / study_id
        / "typed_blocker_resolution.json"
    )
    old_resolution.parent.mkdir(parents=True)
    old_resolution.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_typed_blocker_resolution",
                "schema_version": 1,
                "status": "human_gate_resolution_packet_materialized",
                "study_id": study_id,
                "typed_blocker": {
                    "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                    "typed_blocker_evidence_ref": "/tmp/old-typed-blocker.json",
                },
                "next_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "schema_version": 1,
                    "status": "ready",
                    "study_id": study_id,
                    "next_owner": "mas_authority_kernel",
                    "owner": "mas_authority_kernel",
                    "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
                    "allowed_actions": [
                        "classify_quality_blockers_or_materialize_degraded_handoff_gate"
                    ],
                    "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
                    "work_unit_fingerprint": "oldtypedblockerroute",
                    "acceptance_refs": ["/tmp/old-typed-blocker.json"],
                },
            }
        ),
        encoding="utf-8",
    )
    old_time = old_resolution.stat().st_mtime - 10
    os.utime(old_resolution, (old_time, old_time))
    mission_id = f"paper-mission::{study_id}::fallback-ledger-current"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    package_path = _write_submission_milestone_package(
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
            str(package_path),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_consumption_ledger"
                / "sat-current"
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

    progress_exit_code = cli.main(
        [
            "study",
            "progress",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert progress_exit_code == 0
    assert payload["mission_state"] == "consumed"
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == (
        "continue_same_stage"
    )
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["next_owner_or_human_decision"]["next_owner"] == "mission_executor"
    assert payload["current_objective"]["next_owner"] == "mission_executor"
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["consume_result"]["status"] == "accepted"
    assert _count_surface_kind(payload, SURFACE_KIND) == 1
    assert payload["canonical_next_action_source"] == (
        "artifact_first_mission_summary.next_action"
    )
    assert payload["next_action"]["surface_kind"] == SURFACE_KIND
    assert payload["next_action"]["action_family"] == "runtime.opl_route"
    assert payload["next_action"]["authority_source"] == "mas_next_action_compiler"
    assert payload["next_action"]["legacy_fields_are_diagnostic"] is True
    assert payload["next_action"]["legacy_field_diagnostic_roles"][
        "work_unit_id"
    ] == "diagnostic_currentness_id"
    assert payload["next_action"]["authority_boundary"][
        "exact_work_unit_id_authority"
    ] is False
    assert "next_action" not in payload["artifact_first_mission_summary"]
    assert payload["artifact_first_mission_summary"]["next_action_ref"] == (
        payload["next_action"]["action_id"]
    )
    assert payload["canonical_next_action_source"] != (
        "paper_mission_typed_blocker_resolution"
    )
    assert payload.get("typed_blocker_resolution_readback") is None
    assert "accepted_submission_milestone_candidate" in payload["paper_mission_run"][
        "stage_closure_readback"
    ]["known_blockers"]
    assert payload["artifact_first_mission_summary"]["read_model_source"] == {
        "source_kind": "paper_mission_consumption_ledger",
        "consumption_ledger_ref": str(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_consumption_ledger"
            / "sat-current"
            / study_id
            / "consume_record.json"
        ),
        "consumption_ledger_role": "current_paper_mission_transaction",
        "legacy_projection_accepted": False,
    }
    assert_legacy_completion_surfaces_absent(payload)


def assert_legacy_completion_surfaces_absent(payload: dict[str, object]) -> None:
    for key in (
        "current_work_unit",
        "current_executable_owner_action",
        "paper_recovery_state",
        "progress_first_monitoring_summary",
        "provider_admission_candidates",
        "provider_admission_pending_count",
        "provider_admission_terminal_closeout_consumed",
        "transition_request_candidates",
        "transition_request_pending_count",
        "owner_action_admission",
        "current_execution_envelope",
        "current_execution_evidence",
    ):
        assert key not in payload
    assert payload["legacy_next_action_authority_retired"] == {
        "status": "retired",
        "authority": "NextActionEnvelope",
        "reason": "legacy_next_action_authority_retired_use_next_action_envelope",
        "retired_surfaces": [
            "current_work_unit",
            "current_executable_owner_action",
            "provider_admission",
            "current_execution_envelope",
        ],
        "default_selector_policy": "fail_closed",
        "diagnostic_only": True,
    }


def _count_surface_kind(value: object, surface_kind: str) -> int:
    if isinstance(value, dict):
        count = 1 if value.get("surface_kind") == surface_kind else 0
        return count + sum(_count_surface_kind(item, surface_kind) for item in value.values())
    if isinstance(value, list):
        return sum(_count_surface_kind(item, surface_kind) for item in value)
    return 0

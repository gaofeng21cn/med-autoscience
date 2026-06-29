from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.paper_mission import (
    DM002_STUDY_ID,
    DM003_STUDY_ID,
    build_dm_paper_mission_one_shot_migration_pack,
    paper_mission_candidate_artifact_delta,
    paper_mission_owner_decision_packet,
    paper_mission_by_study,
)
from med_autoscience.paper_mission_run import PaperMissionRun


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "paper_mission_dm_canary"


def _load_json(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _migration_pack() -> dict:
    return build_dm_paper_mission_one_shot_migration_pack(
        dm002_progress=_load_json("dm002_progress.json"),
        dm003_progress=_load_json("dm003_progress.json"),
        runtime_readback_payload=_load_json("runtime_readback.json"),
        profile_ref=(
            "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
            "ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml"
        ),
    )


def test_dm002_one_shot_migration_imports_legacy_truth_and_formal_mission() -> None:
    mission = paper_mission_by_study(_migration_pack(), DM002_STUDY_ID)
    run = PaperMissionRun.from_payload(mission)
    readback = mission["one_shot_migration_readback"]
    legacy = readback["legacy_truth_import_pack"]

    assert run.mission_state == "consumed"
    assert readback["current_mission"]["objective_kind"] == (
        "gate_clearing_claim_evidence_repair"
    )
    assert readback["current_mission"]["legacy_blocker_is_default_execution_state"] is False
    assert readback["next_owner"] == "analysis-campaign"
    assert readback["required_output"]["kind"] == (
        "owner_decision_packet_or_consumable_artifact_delta"
    )
    assert readback["consume_candidate_status"] == "accepted"
    assert any("publication_eval/latest.json" in ref for ref in legacy["publication_eval_refs"])
    assert any(
        "controller_decisions/latest.json" in ref
        for ref in legacy["controller_decision_refs"]
    )
    assert legacy["evidence_and_review_ledger_refs"]
    assert legacy["opl_current_control_refs"]
    assert legacy["legacy_constraints"]["old_blocker"]["why_not_progressing"] == (
        "owner_action_ready"
    )
    assert legacy["legacy_constraints"]["old_blocker_is_default_execution_state"] is False
    assert legacy["decision_constraints"]["legacy_blocker_may_select_default_execution_state"] is False
    assert legacy["non_degradation_evidence"]["legacy_blocker_not_default_execution_state"] is True


def test_dm003_one_shot_migration_preserves_typed_blocker_as_constraint_only() -> None:
    mission = paper_mission_by_study(_migration_pack(), DM003_STUDY_ID)
    run = PaperMissionRun.from_payload(mission)
    readback = mission["one_shot_migration_readback"]
    legacy = readback["legacy_truth_import_pack"]
    old_blocker = legacy["legacy_constraints"]["old_blocker"]

    assert run.mission_state == "stable_blocker"
    assert readback["current_mission"]["objective_kind"] == (
        "medical_prose_write_repair_publication_gate_replay"
    )
    assert readback["current_mission"]["legacy_blocker_is_default_execution_state"] is False
    assert readback["next_owner"] == "one-person-lab"
    assert readback["consume_candidate_status"] == "typed_blocker"
    assert old_blocker["typed_blocker"]["blocker_id"] == (
        "opl_execution_authorization_required"
    )
    assert "opl_execution_authorization_required" in old_blocker["current_blockers"]
    assert any(
        "sat_9afe683ca699e4186f556fec.closeout.json" in ref
        for ref in legacy["legacy_owner_state_refs"]
    )
    assert any(
        "sat_9afe683ca699e4186f556fec.closeout.json" in ref
        for ref in legacy["evidence_and_review_ledger_refs"]
    )
    assert legacy["non_degradation_evidence"]["old_blocker_preserved_in_constraints"] is True
    assert legacy["non_degradation_evidence"]["legacy_blocker_not_default_execution_state"] is True


def test_one_shot_migration_readback_remains_refs_only_and_no_authority_materialized() -> None:
    pack = _migration_pack()

    assert pack["mode"] == "legacy_truth_import_to_formal_paper_mission_run"
    assert pack["authority_boundary"]["can_write_yang_workspace"] is False
    assert pack["paper_progress_accounting"]["old_blockers_count_as_default_execution_state"] is False

    for mission in pack["missions"]:
        readback = mission["one_shot_migration_readback"]
        consume = readback["consume_candidate_readback"]
        legacy = readback["legacy_truth_import_pack"]

        assert mission["forbidden_write_guard"]["candidate_writes_authority"] is False
        assert mission["claim_permissions"]["can_claim_current_package"] is False
        assert mission["claim_permissions"]["can_claim_publication_ready"] is False
        assert mission["claim_permissions"]["can_claim_owner_receipt_written"] is False
        assert consume["candidate_is_authority"] is False
        assert consume["consume_result"]["status"] in {
            "accepted",
            "typed_blocker",
            "human_gate",
            "route_back",
        }
        assert consume["consume_result"]["authority_materialized"] is False
        assert consume["write_plan"]["written_files"] == []
        assert consume["write_plan"]["can_write_current_package"] is False
        assert consume["authority_boundary"]["can_write_current_package"] is False
        assert legacy["current_artifact_refs"]
        assert legacy["all_source_refs"]
        assert "platform_diagnostics" not in readback
        assert "current_work_unit" not in readback
        assert "current_executable_owner_action" not in readback
        assert "provider_admission_current_control" not in readback
        assert "paper_recovery_state" not in readback


def test_one_shot_migration_generates_candidate_delta_and_owner_decision_packet() -> None:
    for study_id in (DM002_STUDY_ID, DM003_STUDY_ID):
        mission = paper_mission_by_study(_migration_pack(), study_id)
        delta = paper_mission_candidate_artifact_delta(mission)
        packet = paper_mission_owner_decision_packet(mission)

        assert delta["surface_kind"] == "paper_mission_candidate_artifact_delta"
        assert delta["study_id"] == study_id
        assert delta["counts_as_paper_progress"] is True
        assert delta["candidate_is_authority"] is False
        assert delta["source_ref_families"]["current_artifact_refs"]
        assert delta["source_ref_families"]["publication_eval_refs"]
        assert delta["source_ref_families"]["controller_decision_refs"]
        assert delta["source_ref_families"]["evidence_and_review_ledger_refs"]
        assert delta["source_ref_families"]["opl_current_control_refs"]
        assert delta["forbidden_write_acknowledgement"]["writes_authority"] is False
        assert delta["forbidden_write_acknowledgement"]["writes_runtime"] is False
        assert delta["forbidden_write_acknowledgement"]["writes_yang_authority"] is False
        assert delta["forbidden_write_acknowledgement"]["writes_paper_body"] is False

        assert packet["surface_kind"] == "paper_mission_owner_decision_packet"
        assert packet["study_id"] == study_id
        assert packet["packet_status"] == "candidate_ready_for_mas_consume"
        assert packet["candidate_is_authority"] is False
        assert packet["artifact_delta_ref"] == delta["artifact_ref"]
        assert packet["consume_path"]["authority_materialized_by_this_packet"] is False
        assert packet["legacy_constraints"]["old_blocker_is_default_execution_state"] is False
        assert packet["decision_constraints"][
            "legacy_blocker_may_select_default_execution_state"
        ] is False

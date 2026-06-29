from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.paper_mission import (
    DM002_STUDY_ID,
    DM003_STUDY_ID,
    build_dm_paper_mission_canary_import_pack,
    consume_paper_mission_canary_candidate,
    paper_mission_by_study,
)
from med_autoscience.paper_mission_run import PaperMissionRun


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "paper_mission_dm_canary"
REQUIRED_PAPER_AUDIT_PACK_FAMILIES = {
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
}


def _load_json(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _import_pack() -> dict:
    return build_dm_paper_mission_canary_import_pack(
        dm002_progress=_load_json("dm002_progress.json"),
        dm003_progress=_load_json("dm003_progress.json"),
        runtime_readback_payload=_load_json("runtime_readback.json"),
        profile_ref=(
            "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
            "ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml"
        ),
    )


def test_dm002_canary_import_builds_gate_clearing_objective() -> None:
    mission = paper_mission_by_study(_import_pack(), DM002_STUDY_ID)
    run = PaperMissionRun.from_payload(mission)
    readback = mission["canary_import_readback"]

    assert mission["schema_version"] == "paper-mission-run.v1"
    assert run.study_id == DM002_STUDY_ID
    assert run.mission_state == "planned"
    assert mission["consume_result"]["status"] == "not_consumed"
    assert mission["forbidden_write_guard"]["candidate_writes_authority"] is False
    assert "/Users/gaofeng/workspace/Yang/**" in mission["forbidden_write_guard"]["blocked_paths"]
    assert readback["mission_objective"]["objective_kind"] == (
        "gate_clearing_claim_evidence_repair"
    )
    assert readback["current_blocker"]["status"] == "owner_action_ready"
    assert readback["current_blocker"]["owner"] == "analysis-campaign"
    assert readback["current_blocker"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert readback["owner_decision_packet_requirement"]["required"] is True
    assert readback["owner_decision_packet_requirement"]["accepted_terminal_results"] == [
        "owner_receipt",
        "typed_blocker",
    ]
    assert any("publication_eval/latest.json" in ref["uri"] for ref in mission["source_refs"])
    assert any("controller_decisions/latest.json" in ref["uri"] for ref in mission["source_refs"])
    assert set(mission["paper_audit_pack"]) == REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    assert all(
        family["status"] == "candidate_ref_chain" and family["refs"]
        for family in mission["paper_audit_pack"].values()
    )
    assert readback["authority_boundary"]["can_write_yang_workspace"] is False


def test_dm003_canary_import_builds_prose_repair_typed_blocker_readback() -> None:
    mission = paper_mission_by_study(_import_pack(), DM003_STUDY_ID)
    PaperMissionRun.from_payload(mission)
    readback = mission["canary_import_readback"]

    assert mission["schema_version"] == "paper-mission-run.v1"
    assert mission["consume_result"]["status"] == "not_consumed"
    assert mission["claim_permissions"]["can_claim_publication_ready"] is False
    assert set(mission["paper_audit_pack"]) == REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    assert all(
        {"ref_id", "ref_kind", "uri"} <= set(ref)
        for family in mission["paper_audit_pack"].values()
        for ref in family["refs"]
    )
    assert readback["mission_objective"]["objective_kind"] == (
        "medical_prose_write_repair_publication_gate_replay"
    )
    assert readback["mission_objective"]["basis"]["next_work_units"] == [
        "medical_prose_write_repair"
    ]
    assert readback["current_blocker"]["status"] == "typed_blocker"
    assert readback["current_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert readback["current_blocker"]["owner"] == "one-person-lab"
    assert "OPL DomainProgressTransitionRuntime" in readback["current_blocker"]["required_input"]
    assert readback["owner_decision_packet_requirement"]["existing_owner_answer_ref"] == (
        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
        "sat_9afe683ca699e4186f556fec.closeout.json"
    )
    assert any(
        "sat_9afe683ca699e4186f556fec.closeout.json" in ref["uri"]
        for ref in mission["source_refs"]
    )


def test_runtime_readback_is_not_default_paper_progress_or_owner_truth() -> None:
    pack = _import_pack()

    assert pack["mode"] == "no_write_import_inspect"
    assert pack["paper_progress_accounting"]["import_pack_counts_as_paper_progress"] is False
    assert pack["paper_progress_accounting"]["runtime_readback_counts_as_paper_progress"] is False
    assert pack["source_surfaces"]["runtime_readback"]["available"] is True
    assert pack["source_surfaces"]["runtime_readback"]["dry_run_written"] is False

    for mission in pack["missions"]:
        PaperMissionRun.from_payload(mission)
        readback = mission["canary_import_readback"]
        assert readback["paper_progress"]["progress_delta_kind"] == "no_write_inspect_only"
        assert readback["paper_progress"]["mission_import_counts_as_paper_progress"] is False
        assert readback["paper_progress"]["platform_diagnostics_count_as_paper_progress"] is False
        assert "platform_diagnostics" not in readback
        assert "current_work_unit" not in readback
        assert "current_executable_owner_action" not in readback
        assert "provider_admission_current_control" not in readback
        assert "paper_recovery_state" not in readback


def test_dm002_canary_candidate_is_consumable_without_authority_writes() -> None:
    mission = paper_mission_by_study(_import_pack(), DM002_STUDY_ID)

    readback = consume_paper_mission_canary_candidate(mission)
    candidate = readback["candidate_manifest"]
    authority = readback["authority_consume_readback"]

    assert readback["surface_kind"] == "paper_mission_canary_candidate_consume_readback"
    assert candidate["study_id"] == DM002_STUDY_ID
    assert candidate["requested_outcome"] == "accepted_candidate"
    assert candidate["candidate_artifact_refs"] == [
        "mission://002-dm-china-us-mortality-attribution/canary/"
        "dm002_gate_clearing_claim_evidence_repair"
    ]
    assert candidate["quality_auditor_requirement"]["independent_auditor_required"] is True
    assert candidate["artifact_authority_boundary"]["candidate_is_authority"] is False
    assert authority["status"] == "accepted_candidate"
    assert authority["consume_result"]["status"] == "accepted"
    assert authority["accepted_candidate"]["authority_materialized"] is False
    assert authority["write_plan"]["written_files"] == []
    assert authority["authority_boundary"]["can_write_publication_eval"] is False
    assert authority["authority_boundary"]["can_write_controller_decisions"] is False
    assert authority["authority_boundary"]["can_write_owner_receipt"] is False
    assert authority["authority_boundary"]["can_write_current_package"] is False


def test_dm003_canary_candidate_consumes_as_typed_blocker_request_without_writing() -> None:
    mission = paper_mission_by_study(_import_pack(), DM003_STUDY_ID)

    readback = consume_paper_mission_canary_candidate(mission)
    candidate = readback["candidate_manifest"]
    authority = readback["authority_consume_readback"]

    assert candidate["study_id"] == DM003_STUDY_ID
    assert candidate["requested_outcome"] == "typed_blocker_required"
    assert candidate["typed_blocker_request"]["blocker_id"] == (
        "opl_execution_authorization_required"
    )
    assert candidate["typed_blocker_request"]["blocker_ref"] == (
        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
        "sat_9afe683ca699e4186f556fec.closeout.json"
    )
    assert authority["status"] == "typed_blocker_required"
    assert authority["consume_result"]["status"] == "typed_blocker"
    assert authority["typed_blocker_required"]["materialized"] is False
    assert authority["write_plan"]["written_files"] == []
    assert authority["write_plan"]["can_write_typed_blockers"] is False
    assert authority["authority_boundary"]["can_write_typed_blocker"] is False

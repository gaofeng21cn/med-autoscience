from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.paper_mission import (
    DM002_STUDY_ID,
    DM003_STUDY_ID,
    build_dm_paper_mission_canary_import_pack,
    paper_mission_by_study,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "paper_mission_dm_canary"


def _load_json(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _import_pack() -> dict:
    return build_dm_paper_mission_canary_import_pack(
        dm002_progress=_load_json("dm002_progress.json"),
        dm003_progress=_load_json("dm003_progress.json"),
        domain_health_diagnostic_payload=_load_json("dhd_dry_run.json"),
        profile_ref=(
            "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
            "ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml"
        ),
    )


def test_dm002_canary_import_builds_gate_clearing_objective() -> None:
    mission = paper_mission_by_study(_import_pack(), DM002_STUDY_ID)

    assert mission["mission_objective"]["objective_kind"] == (
        "gate_clearing_claim_evidence_repair"
    )
    assert mission["current_blocker"]["status"] == "owner_action_ready"
    assert mission["current_blocker"]["owner"] == "analysis-campaign"
    assert mission["current_blocker"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert mission["owner_decision_packet_requirement"]["required"] is True
    assert mission["owner_decision_packet_requirement"]["accepted_terminal_results"] == [
        "owner_receipt",
        "typed_blocker",
    ]
    assert any("publication_eval/latest.json" in ref for ref in mission["artifact_refs"])
    assert any("controller_decisions/latest.json" in ref for ref in mission["artifact_refs"])
    assert mission["authority_boundary"]["can_write_yang_workspace"] is False


def test_dm003_canary_import_builds_prose_repair_typed_blocker_readback() -> None:
    mission = paper_mission_by_study(_import_pack(), DM003_STUDY_ID)

    assert mission["mission_objective"]["objective_kind"] == (
        "medical_prose_write_repair"
    )
    assert mission["mission_objective"]["basis"]["next_work_units"] == [
        "medical_prose_write_repair"
    ]
    assert mission["current_blocker"]["status"] == "typed_blocker"
    assert mission["current_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert mission["current_blocker"]["owner"] == "one-person-lab"
    assert "OPL DomainProgressTransitionRuntime" in mission["current_blocker"]["required_input"]
    assert mission["owner_decision_packet_requirement"]["existing_owner_answer_ref"] == (
        "artifacts/supervision/consumer/default_executor_execution/"
        "sat_9afe683ca699e4186f556fec.closeout.json"
    )
    assert any("sat_9afe683ca699e4186f556fec.closeout.json" in ref for ref in mission["artifact_refs"])


def test_dhd_diagnostics_are_imported_as_platform_diagnostics_not_paper_progress() -> None:
    pack = _import_pack()

    assert pack["mode"] == "no_write_import_inspect"
    assert pack["paper_progress_accounting"]["import_pack_counts_as_paper_progress"] is False
    assert pack["paper_progress_accounting"]["dhd_diagnostics_count_as_paper_progress"] is False
    assert pack["source_surfaces"]["domain_health_diagnostic"]["available"] is True
    assert pack["source_surfaces"]["domain_health_diagnostic"]["dry_run_written"] is False

    for mission in pack["missions"]:
        assert mission["paper_progress"]["progress_delta_kind"] == "no_write_inspect_only"
        assert mission["paper_progress"]["mission_import_counts_as_paper_progress"] is False
        assert mission["paper_progress"]["platform_diagnostics_count_as_paper_progress"] is False
        assert mission["platform_diagnostics"]["counts_as_paper_progress"] is False
        assert mission["platform_diagnostics"]["dhd_written"] is False
        assert mission["platform_diagnostics"]["provider_admission_current_control"][
            "provider_admission_pending_count"
        ] == 0
        assert mission["platform_diagnostics"]["provider_admission_current_control"][
            "transition_request_pending_count"
        ] == 0

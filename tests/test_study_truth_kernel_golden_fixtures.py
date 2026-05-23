from __future__ import annotations

import importlib
from pathlib import Path


def _kernel():
    return importlib.import_module("med_autoscience.controllers.study_truth_kernel")


def test_as_biologics_live_writer_makes_package_currentness_provisional(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "as-biologics"
    module.append_truth_event(
        study_root=study_root,
        study_id="as-biologics",
        event_type="writer_lock_acquired",
        payload={"writer_epoch": "writer::run-live", "active_run_id": "run-live"},
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="as-biologics",
        event_type="package_authority_eval",
        payload={
            "submission_minimal_authority_status": "current",
            "current_package_status": "fresh",
            "source_signature": "paper-relative::stable",
        },
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="as-biologics")

    assert snapshot["package_state"]["authority_state"] == "provisionally_current_for_epoch"
    assert snapshot["active_run_id"] == "run-live"


def test_nf_pitnet_stop_loss_dominates_finalize_eval(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-invasive-architecture"
    module.append_truth_event(
        study_root=study_root,
        study_id="004-invasive-architecture",
        event_type="publication_gate_eval",
        payload={
            "current_required_action": "finalize",
            "assessment_provenance": {"owner": "ai_reviewer"},
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="004-invasive-architecture",
        event_type="stop_loss",
        payload={"summary": "publishability stop-loss recommended"},
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="004-invasive-architecture")

    assert snapshot["canonical_next_action"] == "stop_runtime"
    assert snapshot["dominant_authority_refs"][0]["event_type"] == "stop_loss"


def test_nf_pitnet_reviewer_reactivation_dominates_stopped_finalize_state(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    module.append_truth_event(
        study_root=study_root,
        study_id="003-endocrine-burden-followup",
        event_type="runtime_native_event",
        payload={"quest_status": "stopped", "reason": "quest_stopped_requires_explicit_rerun"},
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="003-endocrine-burden-followup",
        event_type="publication_gate_eval",
        payload={"current_required_action": "finalize"},
        recorded_at="2026-05-01T00:01:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="003-endocrine-burden-followup",
        event_type="task_intake",
        payload={
            "revision_intake": {"kind": "reviewer_revision"},
            "reactivation_policy": {"same_study_line": True},
            "current_required_action": "resume_same_study_line",
        },
        recorded_at="2026-05-01T00:02:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="003-endocrine-burden-followup")

    assert snapshot["canonical_next_action"] == "resume_same_study_line"
    assert snapshot["execution_state"]["state"] == "reactivation_requested"


def test_dm_cvd_live_supervisor_only_blocks_downstream_bundle_actions(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    module.append_truth_event(
        study_root=study_root,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        event_type="opl_runtime_owner_handoff",
        payload={
            "execution_owner_guard": {"supervisor_only": True, "active_run_id": "run-e52f5574"},
            "publication_supervisor_state": {
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_analysis_campaign",
            },
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(
        study_root=study_root,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
    )

    assert snapshot["canonical_next_action"] == "request_opl_handoff_hydration"
    assert "direct_paper_line_write" not in snapshot["allowed_controller_actions"]
    assert "direct_bundle_build" not in snapshot["allowed_controller_actions"]


def test_dm_cvd_explicit_resume_dominates_stopped_analysis_recommendation(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dpcc-followup"
    module.append_truth_event(
        study_root=study_root,
        study_id="004-dpcc-followup",
        event_type="runtime_native_event",
        payload={"quest_status": "stopped", "reason": "quest_stopped_requires_explicit_rerun"},
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="004-dpcc-followup",
        event_type="publication_gate_eval",
        payload={"current_required_action": "return_to_analysis_campaign"},
        recorded_at="2026-05-01T00:01:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="004-dpcc-followup",
        event_type="explicit_resume",
        payload={"current_required_action": "resume_runtime"},
        recorded_at="2026-05-01T00:02:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="004-dpcc-followup")

    assert snapshot["canonical_next_action"] == "resume_runtime"
    assert snapshot["dominant_authority_refs"][0]["event_type"] == "explicit_resume"

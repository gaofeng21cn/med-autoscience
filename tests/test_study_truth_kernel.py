from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _kernel():
    return importlib.import_module("med_autoscience.controllers.study_truth_kernel")


def test_append_only_truth_events_rebuild_single_snapshot(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-invasive"

    first = module.append_truth_event(
        study_root=study_root,
        study_id="004-invasive",
        event_type="publication_gate_eval",
        payload={
            "current_required_action": "complete_bundle_stage",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "route_target": "finalize",
            },
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    second = module.append_truth_event(
        study_root=study_root,
        study_id="004-invasive",
        event_type="stop_loss",
        payload={
            "summary": "publishability stop-loss recommended",
            "controller_action": "stop_runtime",
        },
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="004-invasive")

    assert first["event_id"] != second["event_id"]
    assert snapshot["canonical_next_action"] == "stop_runtime"
    assert snapshot["dominant_authority_refs"][0]["event_type"] == "stop_loss"
    assert snapshot["quality_state"]["state"] == "stop_loss_recommended"
    assert snapshot["publication_gate_state"]["current_required_action"] == "complete_bundle_stage"
    assert snapshot["projection_invalidations"][0]["invalidated_surface"] == "publication_gate_eval"
    assert snapshot["authority_epoch"] == second["event_id"]


def test_task_intake_reactivation_dominates_stopped_finalize_projection(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-endocrine"

    module.append_truth_event(
        study_root=study_root,
        study_id="003-endocrine",
        event_type="runtime_native_event",
        payload={
            "quest_status": "stopped",
            "reason": "quest_stopped_requires_explicit_rerun",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="003-endocrine",
        event_type="publication_gate_eval",
        payload={
            "current_required_action": "complete_bundle_stage",
            "same_line_route_truth": {"route_target": "finalize"},
        },
        recorded_at="2026-05-01T00:01:00+00:00",
    )
    task_intake = module.append_truth_event(
        study_root=study_root,
        study_id="003-endocrine",
        event_type="task_intake",
        payload={
            "revision_intake": {"kind": "reviewer_revision"},
            "reactivation_policy": {"same_study_line": True},
            "current_required_action": "resume_same_study_line",
            "summary": "new reviewer revision intake supersedes parked finalize state",
        },
        recorded_at="2026-05-01T00:02:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="003-endocrine")

    assert snapshot["canonical_next_action"] == "resume_same_study_line"
    assert snapshot["execution_state"]["state"] == "reactivation_requested"
    assert snapshot["dominant_authority_refs"][0]["event_id"] == task_intake["event_id"]
    assert any(item["invalidated_surface"] == "runtime_native_event" for item in snapshot["projection_invalidations"])


def test_supervisor_only_and_downstream_bundle_block_define_allowed_actions(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dpcc"

    module.append_truth_event(
        study_root=study_root,
        study_id="003-dpcc",
        event_type="opl_runtime_owner_handoff",
        payload={
            "execution_owner_guard": {
                "supervisor_only": True,
                "active_run_id": "run-d80c4a5e",
            },
            "publication_supervisor_state": {
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_analysis_campaign",
            },
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="003-dpcc",
        event_type="package_authority_eval",
        payload={
            "submission_minimal_authority_status": "current",
            "current_package_status": "fresh",
        },
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="003-dpcc")

    assert snapshot["execution_owner"]["owner"] == "one-person-lab"
    assert snapshot["execution_owner"]["runtime_control_owner"] == "one-person-lab"
    assert snapshot["execution_owner"]["mas_role"] == "domain_authority_refs_only"
    assert snapshot["canonical_next_action"] == "request_opl_handoff_hydration"
    assert "direct_paper_line_write" not in snapshot["allowed_controller_actions"]
    assert "direct_bundle_build" not in snapshot["allowed_controller_actions"]
    assert snapshot["blocking_reasons"] == [
        "opl_current_control_state.handoff_required",
        "publication_supervisor_state.bundle_tasks_downstream_only",
    ]


def test_writer_lock_marks_package_authority_provisional_until_released(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "as-biologics"

    module.append_truth_event(
        study_root=study_root,
        study_id="as-biologics",
        event_type="writer_lock_acquired",
        payload={"writer_epoch": "writer-1", "active_run_id": "run-live"},
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_truth_event(
        study_root=study_root,
        study_id="as-biologics",
        event_type="package_authority_eval",
        payload={
            "submission_minimal_authority_status": "current",
            "source_signature": "source::abc",
        },
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    locked = module.rebuild_truth_snapshot(study_root=study_root, study_id="as-biologics")
    assert locked["package_state"]["authority_state"] == "provisionally_current_for_epoch"
    assert locked["package_state"]["writer_epoch"] == "writer-1"

    module.append_truth_event(
        study_root=study_root,
        study_id="as-biologics",
        event_type="writer_lock_released",
        payload={"writer_epoch": "writer-1"},
        recorded_at="2026-05-01T00:02:00+00:00",
    )
    released = module.rebuild_truth_snapshot(study_root=study_root, study_id="as-biologics")

    assert released["package_state"]["authority_state"] == "current"
    assert released["package_state"]["writer_epoch"] is None


def test_mechanical_publication_eval_cannot_declare_finalize_ready(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-invasive"
    module.append_truth_event(
        study_root=study_root,
        study_id="004-invasive",
        event_type="publication_gate_eval",
        payload={
            "current_required_action": "finalize",
            "assessment_provenance": {"owner": "mechanical_projection"},
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "route_target": "finalize",
            },
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot = module.rebuild_truth_snapshot(study_root=study_root, study_id="004-invasive")

    assert snapshot["canonical_next_action"] == "review_required"
    assert "publication_eval.ai_reviewer_required" in snapshot["blocking_reasons"]


def test_materialized_snapshot_writes_stable_latest_surface(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-invasive"
    module.append_truth_event(
        study_root=study_root,
        study_id="004-invasive",
        event_type="explicit_resume",
        payload={"current_required_action": "resume_same_study_line"},
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    path = module.materialize_truth_snapshot(study_root=study_root, study_id="004-invasive")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path == study_root / "artifacts" / "truth" / "latest.json"
    assert payload["study_id"] == "004-invasive"
    assert payload["truth_epoch"] == payload["authority_epoch"]
    assert payload["canonical_next_action"] == "resume_same_study_line"


def test_status_payload_can_derive_shadow_truth_snapshot_without_writing_latest(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dpcc"
    status_payload = {
        "study_id": "003-dpcc",
        "study_root": str(study_root),
        "quest_id": "003-dpcc",
        "quest_status": "running",
        "decision": "blocked",
        "reason": "medical_publication_surface_blocked",
        "execution_owner_guard": {
            "supervisor_only": True,
            "active_run_id": "run-d80c4a5e",
        },
        "publication_supervisor_state": {
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_analysis_campaign",
        },
    }

    snapshot = module.derive_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dpcc",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    assert snapshot["canonical_next_action"] == "request_opl_handoff_hydration"
    assert snapshot["truth_epoch"] == snapshot["authority_epoch"]
    assert snapshot["event_count"] == 3
    assert snapshot["writer_epoch"] == "writer::run-d80c4a5e"
    assert not (study_root / "artifacts" / "truth" / "latest.json").exists()


def test_reconcile_materializes_status_events_once_per_source_signature(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dpcc"
    status_payload = {
        "study_id": "003-dpcc",
        "study_root": str(study_root),
        "quest_status": "running",
        "decision": "blocked",
        "reason": "medical_publication_surface_blocked",
        "execution_owner_guard": {
            "supervisor_only": True,
            "active_run_id": "run-e52f5574",
        },
        "publication_supervisor_state": {
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_analysis_campaign",
        },
        "submission_minimal_authority_status": "current",
        "submission_minimal_evaluated_source_signature": "source::abc",
        "submission_minimal_authority_source_signature": "source::abc",
        "current_package_status": "fresh",
        "current_package_source_signature": "source::abc",
    }

    first = module.reconcile_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dpcc",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    second = module.reconcile_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dpcc",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    events = module.read_truth_events(study_root=study_root)
    event_types = [event["event_type"] for event in events]
    assert first["appended_event_count"] == 4
    assert second["appended_event_count"] == 0
    assert event_types == [
        "runtime_native_event",
        "opl_runtime_owner_handoff",
        "writer_lock_acquired",
        "package_authority_eval",
    ]
    assert all(event.get("source_signature") for event in events)
    assert first["snapshot"]["canonical_next_action"] == "request_opl_handoff_hydration"
    assert first["snapshot"]["package_state"]["authority_state"] == "provisionally_current_for_epoch"
    assert first["snapshot"]["writer_epoch"] == "writer::run-e52f5574"
    assert Path(first["snapshot_path"]).exists()
    assert json.loads(Path(first["snapshot_path"]).read_text(encoding="utf-8"))["truth_epoch"] == first["truth_epoch"]


def test_supervisor_tick_source_signature_ignores_read_time_age(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dpcc"
    status_payload = {
        "study_id": "004-dpcc",
        "study_root": str(study_root),
        "quest_status": "stopped",
        "decision": "blocked",
        "reason": "quest_stopped_requires_explicit_rerun",
        "publication_supervisor_state": {
            "bundle_tasks_downstream_only": True,
            "current_required_action": "wait_for_explicit_resume",
        },
        "supervisor_tick_audit": {
            "status": "stale",
            "required": True,
            "latest_recorded_at": "2026-05-01T01:31:09+00:00",
            "seconds_since_latest_recorded_at": 601,
        },
    }

    first = module.reconcile_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="004-dpcc",
        status_payload=status_payload,
        recorded_at="2026-05-01T01:41:10+00:00",
    )
    status_payload["supervisor_tick_audit"]["seconds_since_latest_recorded_at"] = 899
    second = module.reconcile_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="004-dpcc",
        status_payload=status_payload,
        recorded_at="2026-05-01T01:46:08+00:00",
    )

    assert first["appended_event_count"] == 2
    assert second["appended_event_count"] == 0
    assert [event["event_type"] for event in module.read_truth_events(study_root=study_root)] == [
        "runtime_native_event",
        "opl_runtime_owner_handoff",
    ]


def test_shadow_status_derives_live_writer_lock_without_materializing(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "as-biologics"
    snapshot = module.derive_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="as-biologics",
        status_payload={
            "study_id": "as-biologics",
            "study_root": str(study_root),
            "quest_status": "running",
            "execution_owner_guard": {
                "supervisor_only": True,
                "active_run_id": "run-live",
            },
            "submission_minimal_authority_status": "current",
            "submission_minimal_evaluated_source_signature": "source::live",
            "submission_minimal_authority_source_signature": "source::live",
            "current_package_status": "fresh",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    assert snapshot["package_state"]["authority_state"] == "provisionally_current_for_epoch"
    assert snapshot["writer_epoch"] == "writer::run-live"
    assert not module.truth_snapshot_path(study_root=study_root).exists()


def test_legacy_reviewer_revision_task_intake_dominates_runtime_tick(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dpcc"
    task_intake_root = study_root / "artifacts" / "controller" / "task_intake"
    task_intake_root.mkdir(parents=True)
    (task_intake_root / "latest.json").write_text(
        json.dumps(
            {
                "emitted_at": "2026-04-25T04:01:37+00:00",
                "task_intent": (
                    "Reviewer revision: absorb the explicit user reviewer feedback and revise manuscript, "
                    "tables, figures, methods, statistics, and claim guardrails under MAS/MDS supervision."
                ),
            }
        ),
        encoding="utf-8",
    )

    status_payload = {
        "study_id": "003-dpcc",
        "study_root": str(study_root),
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "publication_supervisor_state": {
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
        },
    }
    result = module.reconcile_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dpcc",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    shadow = module.derive_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dpcc",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    assert [event["event_type"] for event in module.read_truth_events(study_root=study_root)] == [
        "runtime_native_event",
        "opl_runtime_owner_handoff",
        "task_intake",
    ]
    assert result["snapshot"]["canonical_next_action"] == "resume_same_study_line"
    assert result["snapshot"]["dominant_authority_refs"][0]["event_type"] == "task_intake"
    assert shadow["truth_epoch"] == result["truth_epoch"]
    assert shadow["event_count"] == result["snapshot"]["event_count"]


def test_shadow_snapshot_reads_latest_task_intake_as_reactivation_event(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-endocrine"
    task_intake_path = study_root / "artifacts" / "controller" / "task_intake" / "latest.json"
    task_intake_path.parent.mkdir(parents=True)
    task_intake_path.write_text(
        json.dumps(
            {
                "task_id": "task-003",
                "study_id": "003-endocrine",
                "emitted_at": "2026-05-01T00:02:00+00:00",
                "revision_intake": {"kind": "reviewer_revision", "status": "active"},
                "first_cycle_outputs": ["Updated canonical Table 1"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    snapshot = module.derive_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-endocrine",
        status_payload={
            "study_id": "003-endocrine",
            "study_root": str(study_root),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "publication_supervisor_state": {
                "current_required_action": "complete_bundle_stage",
            },
        },
        recorded_at="2026-05-01T00:03:00+00:00",
    )

    assert snapshot["canonical_next_action"] == "resume_same_study_line"
    assert snapshot["execution_state"]["state"] == "reactivation_requested"
    assert snapshot["dominant_authority_refs"][0]["event_type"] == "task_intake"


def test_methodology_rebuild_authorization_task_intake_dominates_waiting_human_gate(
    tmp_path: Path,
) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm"
    task_intake_path = study_root / "artifacts" / "controller" / "task_intake" / "latest.json"
    task_intake_path.parent.mkdir(parents=True)
    task_intake_path.write_text(
        json.dumps(
            {
                "task_id": "study-task::002-dm::20260519T074054Z",
                "study_id": "002-dm",
                "emitted_at": "2026-05-19T07:40:54+00:00",
                "task_intake_kind": "methodology_rebuild_authorization",
                "task_intent": (
                    "Human-gate decision: authorize a clean reproducible-model rebuild route "
                    "after the HDL unit harmonization blocker."
                ),
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.reconcile_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm",
        status_payload={
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_status": "waiting_for_user",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "publication_supervisor_state": {
                "current_required_action": "return_to_publishability_gate",
            },
        },
        recorded_at="2026-05-19T07:41:00+00:00",
    )

    snapshot = result["snapshot"]
    task_event = module.read_truth_events(study_root=study_root)[-1]
    assert snapshot["canonical_next_action"] == "authorize_clean_reproducible_model_rebuild"
    assert snapshot["execution_state"]["state"] == "reactivation_requested"
    assert snapshot["dominant_authority_refs"][0]["event_type"] == "task_intake"
    assert task_event["payload"]["task_intake_kind"] == "methodology_rebuild_authorization"
    assert task_event["payload"]["reactivation_policy"]["next_owner"] == "provenance_limited_harmonization_owner"


def test_progress_projection_carries_truth_epoch_from_status_payload(tmp_path: Path) -> None:
    progress = importlib.import_module("med_autoscience.controllers.study_progress")
    module = _kernel()
    profile = make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "004-invasive"
    study_root.mkdir(parents=True)
    truth_snapshot = module.derive_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id="004-invasive",
        status_payload={
            "study_id": "004-invasive",
            "study_root": str(study_root),
            "quest_id": "004-invasive",
            "quest_root": str(profile.runtime_root / "004-invasive"),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "publishability_stop_loss_recommended",
            "publication_supervisor_state": {
                "supervisor_phase": "stop_loss",
                "current_required_action": "stop_runtime",
            },
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    projection = progress.build_study_progress_projection(
        profile=profile,
        study_id="004-invasive",
        study_root=study_root,
        status_payload={
            "study_id": "004-invasive",
            "study_root": str(study_root),
            "quest_id": "004-invasive",
            "quest_root": str(profile.runtime_root / "004-invasive"),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "publishability_stop_loss_recommended",
            "publication_supervisor_state": {
                "supervisor_phase": "stop_loss",
                "current_required_action": "stop_runtime",
            },
            "study_truth_snapshot": truth_snapshot,
        },
    )

    assert projection["truth_epoch"] == truth_snapshot["truth_epoch"]
    assert projection["study_truth_snapshot"]["canonical_next_action"] == "stop_runtime"
    assert projection["refs"]["study_truth_snapshot_path"] == str(study_root / "artifacts" / "truth" / "latest.json")

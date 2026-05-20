from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tests.test_study_runtime_execution_control_intent_cases.helpers import (
    _base_status_payload,
    _write_runtime_state,
)


def _write_generic_controller_decision(
    study_root: Path,
    *,
    study_id: str,
    quest_id: str,
    decision_id: str,
    emitted_at: str,
    decision_type: str,
    route_target: str,
    route_key_question: str,
    publication_eval_id: str | None = None,
) -> None:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    resolved_publication_eval_id = publication_eval_id or f"publication-eval::{study_id}::latest"
    publication_eval_path.parent.mkdir(parents=True, exist_ok=True)
    publication_eval_path.write_text(
        json.dumps({"schema_version": 1, "eval_id": resolved_publication_eval_id}) + "\n",
        encoding="utf-8",
    )
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "study_id": study_id,
                "quest_id": quest_id,
                "emitted_at": emitted_at,
                "decision_type": decision_type,
                "charter_ref": {
                    "charter_id": f"charter::{study_id}::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": f"runtime-escalation::{study_id}::{quest_id}::controller-gap",
                    "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                },
                "publication_eval_ref": {
                    "eval_id": resolved_publication_eval_id,
                    "artifact_path": str(publication_eval_path),
                },
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": "ensure_study_runtime", "payload_ref": str(decision_path)}],
                "reason": "Route the current bounded paper work unit into managed runtime.",
                "route_target": route_target,
                "route_key_question": route_key_question,
                "route_rationale": "The current controller decision names a bounded paper work unit.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _status_for(study_root: Path, quest_root: Path, *, study_id: str, quest_id: str) -> Any:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    status_payload = _base_status_payload()
    status_payload["study_id"] = study_id
    status_payload["study_root"] = str(study_root)
    status_payload["quest_id"] = quest_id
    status_payload["quest_root"] = str(quest_root)
    status_payload["execution"]["quest_id"] = quest_id
    return module.StudyRuntimeStatus.from_payload(status_payload)


def _context(study_root: Path, quest_root: Path, runtime_root: Path) -> Any:
    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("completed generic work-unit evidence must be adopted instead of relayed")

    return SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=runtime_root,
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )


def test_execute_noop_runtime_decision_adopts_dm002_rebuttal_completion_receipt(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    decision_id = f"study-decision::{study_id}::{quest_id}::bounded_analysis::2026-05-13T22:28:34+00:00"
    route_key_question = (
        "paper/rebuttal/review_matrix.md and action_plan.md covering all feedback items with route "
        "text_revision/evidence_repackaging/supplementary_check/claim_downgrade/package_completion."
    )
    run_id = f"mas-run-{study_id}-20260514T030948701275Z"
    study_root = tmp_path / "workspace" / "studies" / study_id
    quest_root = tmp_path / "runtime" / "quests" / quest_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id=decision_id,
        emitted_at="2026-05-13T22:28:34+00:00",
        decision_type="bounded_analysis",
        route_target="analysis-campaign",
        route_key_question=route_key_question,
    )
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-dm002-rebuttal", "active_run_id": run_id},
        recorded_at="2026-05-13T22:29:00+00:00",
    )
    receipt_path = quest_root / "artifacts" / "runtime" / "work_unit_receipts" / f"{run_id}-rebuttal_route_coverage.completed.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "decision_id": decision_id,
                "status": "completed",
                "work_unit_id": route_key_question,
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    "../../../studies/002-dm-china-us-mortality-attribution/paper/rebuttal/review_matrix.md",
                    "../../../studies/002-dm-china-us-mortality-attribution/paper/rebuttal/action_plan.md",
                    "artifacts/intake/rebuttal_route_coverage_current_run_2026-05-14T031229Z.json",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": run_id, "pending_user_message_count": 0})

    status = _status_for(study_root, quest_root, study_id=study_id, quest_id=quest_id)
    outcome = module._execute_runtime_decision(
        status=status,
        context=_context(study_root, quest_root, tmp_path / "runtime"),
    )
    events = control_intent.read_events(study_root=study_root)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]
    next_route = status.to_dict()["controller_work_unit_next_route"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "artifact_written", "owner_handoff"]
    lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    assert lifecycle["terminal_consumed"] is True
    assert lifecycle["block_reason"] == "owner_handoff"
    assert adoption["report_ref"] == str(receipt_path)
    assert adoption["work_unit_id"] == route_key_question
    assert adoption["route_target"] == "analysis-campaign"
    assert adoption["status"] == "completed"
    assert adoption["result"]["completed"] is True
    assert adoption["result"]["meaningful_artifact_delta"] is True
    assert adoption["result"]["artifact_refs_count"] == 3
    assert next_route == {
        "recommended_next_route": "return_to_publication_gate_recheck",
        "owner": "publication_gate",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": True,
    }


def test_execute_noop_runtime_decision_terminalizes_existing_completed_work_unit_adoption(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    decision_id = f"study-decision::{study_id}::{quest_id}::route_back_same_line::2026-05-20T04:42:17+00:00"
    route_key_question = "manuscript_story_repair"
    run_id = f"mas-run-{study_id}-20260520T045311400847Z"
    study_root = tmp_path / "workspace" / "studies" / study_id
    quest_root = tmp_path / "runtime" / "quests" / quest_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id=decision_id,
        emitted_at="2026-05-20T04:42:17+00:00",
        decision_type="route_back_same_line",
        route_target="analysis-campaign",
        route_key_question=route_key_question,
    )
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    report_ref = (
        quest_root
        / "artifacts"
        / "runtime"
        / "turn_closeouts"
        / f"{run_id}.json"
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="artifact_written",
        payload={
            "active_run_id": None,
            "created_at": "2026-05-20T05:01:59+00:00",
            "next_owner": "publication_gate",
            "recommended_next_route": "return_to_publication_gate_recheck",
            "report_ref": str(report_ref),
            "result": {
                "artifact_refs_count": 7,
                "completed": True,
                "meaningful_artifact_delta": True,
                "publication_gate_recheck_required": True,
                "source_refs_count": 0,
            },
            "route_target": "analysis-campaign",
            "source": "runtime_watch",
            "status": "completed",
            "work_unit_id": "manuscript_story_repair",
        },
        recorded_at="2026-05-20T05:05:13+00:00",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": run_id, "pending_user_message_count": 0})

    status = _status_for(study_root, quest_root, study_id=study_id, quest_id=quest_id)
    outcome = module._execute_runtime_decision(
        status=status,
        context=_context(study_root, quest_root, tmp_path / "runtime"),
    )
    events = control_intent.read_events(study_root=study_root)
    lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["artifact_written", "owner_handoff"]
    assert lifecycle["terminal_consumed"] is True
    assert lifecycle["block_reason"] == "owner_handoff"
    assert status.to_dict()["controller_work_unit_evidence_adoption"]["already_recorded"] is True


def test_execute_noop_runtime_decision_adopts_dm003_revised_manuscript_write_artifact(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    decision_id = f"study-decision::{study_id}::{quest_id}::continue_same_line::2026-05-13T22:00:42+00:00"
    route_key_question = "MAS/MDS-supervised revised manuscript package"
    run_id = f"mas-run-{study_id}-20260514T030950134152Z"
    study_root = tmp_path / "workspace" / "studies" / study_id
    quest_root = tmp_path / "runtime" / "quests" / quest_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id=decision_id,
        emitted_at="2026-05-13T22:00:42+00:00",
        decision_type="continue_same_line",
        route_target="write",
        route_key_question=route_key_question,
    )
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-dm003-package", "active_run_id": run_id},
        recorded_at="2026-05-13T22:01:00+00:00",
    )
    artifact_path = quest_root / "artifacts" / "write" / "mas_mds_revised_manuscript_package_prose_reconciliation_20260514T030002Z.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "created_at": "2026-05-14T03:00:02Z",
                "status": "completed",
                "work_unit_id": route_key_question,
                "route_key_question": route_key_question,
                "route_target": "write",
                "meaningful_artifact_delta": True,
                "result": {"manuscript_package_written": True},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": run_id, "pending_user_message_count": 0})

    status = _status_for(study_root, quest_root, study_id=study_id, quest_id=quest_id)
    outcome = module._execute_runtime_decision(
        status=status,
        context=_context(study_root, quest_root, tmp_path / "runtime"),
    )
    events = control_intent.read_events(study_root=study_root)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "artifact_written", "owner_handoff"]
    assert adoption["report_ref"] == str(artifact_path)
    assert adoption["created_at"] == "2026-05-14T03:00:02+00:00"
    assert adoption["work_unit_id"] == route_key_question
    assert adoption["route_target"] == "write"
    assert adoption["result"]["completed"] is True
    assert adoption["result"]["manuscript_package_written"] is True


def test_execute_noop_runtime_decision_adopts_generic_artifact_from_runtime_relay_marker(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    decision_id = f"study-decision::{study_id}::{quest_id}::continue_same_line::2026-05-13T22:00:42+00:00"
    route_key_question = "MAS/MDS-supervised revised manuscript package"
    run_id = f"mas-run-{study_id}-20260514T041755443163Z"
    study_root = tmp_path / "workspace" / "studies" / study_id
    quest_root = tmp_path / "runtime" / "quests" / quest_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id=decision_id,
        emitted_at="2026-05-13T22:00:42+00:00",
        decision_type="continue_same_line",
        route_target="write",
        route_key_question=route_key_question,
    )
    artifact_path = quest_root / "artifacts" / "write" / "mas_mds_revised_manuscript_package_7day_episode_boundary_20260514T031330Z.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "created_at": "2026-05-14T03:13:30Z",
                "controller_decision_id": decision_id,
                "status": "completed",
                "work_unit_id": route_key_question,
                "route_key_question": route_key_question,
                "route_target": "write",
                "meaningful_artifact_delta": True,
                "result": {"boundary_revalidated": True},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": run_id,
            "pending_user_message_count": 0,
            "last_controller_decision_authorization": {
                "decision_id": decision_id,
                "route_target": "write",
                "route_key_question": route_key_question,
                "work_unit_id": route_key_question,
                "control_intent_key": "control-intent::dm003-package",
                "active_run_id": run_id,
                "delivery_mode": "managed_runtime_chat",
                "message_id": "msg-536fc8ef9bcc1772",
            },
        },
    )

    status = _status_for(study_root, quest_root, study_id=study_id, quest_id=quest_id)
    outcome = module._execute_runtime_decision(
        status=status,
        context=_context(study_root, quest_root, tmp_path / "runtime"),
    )
    events = importlib.import_module("med_autoscience.controllers.control_intent").read_events(study_root=study_root)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["artifact_written", "owner_handoff"]
    assert adoption["report_ref"] == str(artifact_path)
    assert adoption["created_at"] == "2026-05-14T03:13:30+00:00"
    assert adoption["work_unit_id"] == route_key_question
    assert adoption["route_target"] == "write"
    assert adoption["result"]["boundary_revalidated"] is True
    assert adoption["result"]["publication_gate_recheck_required"] is True


def test_controller_authorization_ignores_drifted_latest_publication_eval_work_unit_context(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    decision_id = f"study-decision::{study_id}::{quest_id}::continue_same_line::2026-05-13T22:00:42+00:00"
    route_key_question = "MAS/MDS-supervised revised manuscript package"
    original_eval_id = f"publication-eval::{study_id}::{quest_id}::2026-05-13T22:00:38+00:00"
    study_root = tmp_path / "workspace" / "studies" / study_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id=decision_id,
        emitted_at="2026-05-13T22:00:42+00:00",
        decision_type="continue_same_line",
        route_target="write",
        route_key_question=route_key_question,
        publication_eval_id=original_eval_id,
    )
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    latest_eval_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": f"publication-eval::{study_id}::{quest_id}::2026-05-14T06:02:10+00:00",
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "route_target": "finalize",
                        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                        "work_unit_fingerprint": "publication-blockers::384926545bfa6f3a",
                        "next_work_unit": {
                            "unit_id": "submission_authority_sync_closure",
                            "lane": "controller",
                            "summary": "Regenerate submission authority signatures, then replay the publication gate.",
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    assert authorization_context["publication_eval_id"] == original_eval_id
    assert authorization_context["route_target"] == "write"
    assert authorization_context["route_key_question"] == route_key_question
    assert authorization_context["work_unit_id"] == route_key_question
    assert authorization_context["next_work_unit"] == {}
    assert authorization_context["blocking_work_units"] == []


def test_execute_noop_runtime_decision_rejects_blocked_generic_work_unit_artifact(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    route_key_question = "MAS/MDS-supervised revised manuscript package"
    run_id = f"mas-run-{study_id}-20260514T030950134152Z"
    study_root = tmp_path / "workspace" / "studies" / study_id
    quest_root = tmp_path / "runtime" / "quests" / quest_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id="decision-blocked-generic-artifact",
        emitted_at="2026-05-13T22:00:42+00:00",
        decision_type="continue_same_line",
        route_target="write",
        route_key_question=route_key_question,
    )
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-dm003-package", "active_run_id": run_id},
        recorded_at="2026-05-13T22:01:00+00:00",
    )
    artifact_path = quest_root / "artifacts" / "write" / "blocked_revised_manuscript_package.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "created_at": "2026-05-14T03:00:02Z",
                "status": "completed",
                "work_unit_id": route_key_question,
                "route_target": "write",
                "meaningful_artifact_delta": True,
                "blocked": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": run_id, "pending_user_message_count": 0})
    status = _status_for(study_root, quest_root, study_id=study_id, quest_id=quest_id)

    outcome = module._execute_runtime_decision(
        status=status,
        context=_context(study_root, quest_root, tmp_path / "runtime"),
    )
    events = control_intent.read_events(study_root=study_root)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate"]
    assert "controller_work_unit_evidence_adoption" not in status.to_dict()


def test_execute_noop_runtime_decision_rejects_quality_relaxed_generic_work_unit_artifact(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    route_key_question = "MAS/MDS-supervised revised manuscript package"
    run_id = f"mas-run-{study_id}-20260514T030950134152Z"
    study_root = tmp_path / "workspace" / "studies" / study_id
    quest_root = tmp_path / "runtime" / "quests" / quest_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id="decision-quality-relaxed-generic-artifact",
        emitted_at="2026-05-13T22:00:42+00:00",
        decision_type="continue_same_line",
        route_target="write",
        route_key_question=route_key_question,
    )
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-dm003-package", "active_run_id": run_id},
        recorded_at="2026-05-13T22:01:00+00:00",
    )
    artifact_path = quest_root / "artifacts" / "write" / "quality_relaxed_revised_manuscript_package.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "created_at": "2026-05-14T03:00:02Z",
                "status": "completed",
                "work_unit_id": route_key_question,
                "route_target": "write",
                "meaningful_artifact_delta": True,
                "quality_gate_relaxed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": run_id, "pending_user_message_count": 0})
    status = _status_for(study_root, quest_root, study_id=study_id, quest_id=quest_id)

    outcome = module._execute_runtime_decision(
        status=status,
        context=_context(study_root, quest_root, tmp_path / "runtime"),
    )
    events = control_intent.read_events(study_root=study_root)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate"]
    assert "controller_work_unit_evidence_adoption" not in status.to_dict()


def test_execute_noop_runtime_decision_rejects_undated_generic_work_unit_artifact_without_decision_id(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    route_key_question = "MAS/MDS-supervised revised manuscript package"
    run_id = f"mas-run-{study_id}-20260514T030950134152Z"
    study_root = tmp_path / "workspace" / "studies" / study_id
    quest_root = tmp_path / "runtime" / "quests" / quest_id
    _write_generic_controller_decision(
        study_root,
        study_id=study_id,
        quest_id=quest_id,
        decision_id="decision-undated-generic-artifact",
        emitted_at="2026-05-13T22:00:42+00:00",
        decision_type="continue_same_line",
        route_target="write",
        route_key_question=route_key_question,
    )
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-dm003-package", "active_run_id": run_id},
        recorded_at="2026-05-13T22:01:00+00:00",
    )
    artifact_path = quest_root / "artifacts" / "write" / "undated_revised_manuscript_package.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "status": "completed",
                "work_unit_id": route_key_question,
                "route_target": "write",
                "meaningful_artifact_delta": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": run_id, "pending_user_message_count": 0})
    status = _status_for(study_root, quest_root, study_id=study_id, quest_id=quest_id)

    outcome = module._execute_runtime_decision(
        status=status,
        context=_context(study_root, quest_root, tmp_path / "runtime"),
    )
    events = control_intent.read_events(study_root=study_root)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate"]
    assert "controller_work_unit_evidence_adoption" not in status.to_dict()

from __future__ import annotations

from tests.paper_mission_owner_surface_cases.test_current_write_routeback_projection_cases.provider_admission_and_stale_projection_cases import *  # noqa: F403,F401
from pathlib import Path
import json

import pytest

from med_autoscience.controllers.paper_mission_owner_surface_parts import provider_admission_projection
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_owner_receipt_consumption_successor_overrides_stage_readiness_residue() -> None:
    stage_artifact_owner_actions = __import__(
        "med_autoscience.controllers.paper_mission_owner_surface_parts.stage_artifact_owner_actions",
        fromlist=["stage_artifact_owner_actions"],
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action = {
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "next_work_unit": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
        ),
        "domain_transition_decision_type": "ai_reviewer_re_eval",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
    }
    progress = {
        "current_work_unit": {
            "status": "owner_receipt_recorded",
            "state": {
                "state_kind": "owner_receipt_recorded",
                "next_safe_action_kind": "consume_owner_receipt",
                "owner_receipt_ref": (
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
            },
            "required_output_contract": {"owner_receipt_consumed": True},
        },
        "paper_recovery_state": {
            "phase": "owner_receipt_recorded",
            "next_safe_action": {
                "kind": "consume_owner_receipt",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
            },
        },
        "medical_paper_readiness": {"overall_status": "not_ready"},
        "stage_kernel_projection": {
            "current_owner_delta": {
                "source_kind": "typed_blocker",
                "action": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "reason": "medical_paper_readiness_missing",
                "required_input": "complete_medical_paper_readiness_surface",
                "source_ref": (
                    "artifacts/stage_outputs/08-publication_package_handoff/"
                    "receipts/typed_blocker.json"
                ),
                "latest_owner_answer_kind": "typed_blocker",
                "next_action": {
                    "action_id": "complete_medical_paper_readiness_surface",
                    "surface_key": "authoring_runtime_authorization",
                },
            },
        },
    }

    result = stage_artifact_owner_actions.action_queue_with_terminal_publication_handoff(
        actions=[dict(action)],
        progress=progress,
        study_id=study_id,
        quest_id=study_id,
        decorate_action=lambda **kwargs: {
            **dict(kwargs["action"]),
            "study_id": kwargs["study_id"],
            "quest_id": kwargs["quest_id"],
        },
        publication_eval_payload={
            "gaps": [{"gap_id": "medical_publication_surface_blocked"}],
        },
    )
    projection = stage_artifact_owner_actions.projection_fields(progress, actions=result)

    assert [item["action_type"] for item in result] == ["return_to_ai_reviewer_workflow"]
    assert result[0]["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert "current_executable_owner_action" not in projection


@pytest.mark.parametrize("ai_reviewer_lifecycle_stateful", [True, False])
def test_scan_routes_accepted_repair_reviewer_queue_overrides_stage_readiness_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    ai_reviewer_lifecycle_stateful: bool,
) -> None:
    scan = __import__("med_autoscience.controllers.paper_mission_owner_surface", fromlist=["paper_mission_owner_surface"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm002::readiness-blocked"
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    draft = study_root / "paper" / "draft.md"
    review_ledger = study_root / "paper" / "review" / "review_ledger.json"
    evidence_ledger = study_root / "paper" / "evidence_ledger.json"
    for path in (draft, review_ledger, evidence_ledger):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    ai_reviewer_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    gate_replay_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    ai_reviewer_lifecycle = (
        {"state": "requested"}
        if ai_reviewer_lifecycle_stateful
        else {
            "assessment_ref": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocked_reason": None,
            "source_ref": str(evidence_path),
        }
    )
    _write_json(
        ai_reviewer_request,
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": ai_reviewer_lifecycle,
            "target_surface": "artifacts/publication_eval/latest.json",
        },
    )
    _write_json(
        gate_replay_request,
        {"request_kind": "run_gate_replay_after_repair", "request_lifecycle": {"state": "requested"}},
    )
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "repair-source-current",
            "source_eval_id": eval_id,
            "repair_work_unit": {"unit_id": "readiness_blocker_publication_repair", "source_eval_id": eval_id},
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(review_ledger), "artifact_role": "review_ledger"},
                    {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                ],
            },
            "changed_artifact_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_refs": [str(gate_replay_request)],
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "readiness_blocker_publication_repair",
            "canonical_artifact_delta_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "repair_execution_evidence_ref": str(evidence_path),
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_request_ref": str(gate_replay_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
            "action_fingerprint": "stale-dispatch-fingerprint",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "overall_verdict": "blocked",
        "gaps": [
            {"gap_id": "medical_publication_surface_blocked"},
            {"gap_id": "reviewer_first_concerns_unresolved"},
            {"gap_id": "stale_submission_minimal_authority"},
        ],
    }
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "medical_paper_readiness_missing",
        "active_run_id": None,
        "publication_eval": publication_eval_payload,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm002-repair-accepted",
            "canonical_runtime_action": "continue_supervising_runtime",
            "worker_liveness_state": {"state": "ready", "worker_running": True},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-repair-accepted",
            "source_signature": "truth-source-dm002-repair-accepted",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "stage_kernel_projection": {
            "current_owner_delta": {
                "source_kind": "typed_blocker",
                "action": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "reason": "medical_paper_readiness_missing",
                "required_input": "complete_medical_paper_readiness_surface",
                "source_ref": str(
                    study_root
                    / "artifacts"
                    / "stage_outputs"
                    / "08-publication_package_handoff"
                    / "receipts"
                    / "typed_blocker.json"
                ),
                "latest_owner_answer_kind": "typed_blocker",
            },
        },
        "medical_paper_readiness": {"overall_status": "not_ready"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
        live_attempt_max_inspect_count=0,
        provider_readiness_timeout_seconds=0,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "repair_progress_ai_reviewer_recheck_required"
    assert action["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert action["repair_progress_followup"]["accepted_owner_receipt"] is True
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["owner_route"]["source_refs"]["work_unit_id"] == action["next_work_unit"]
    assert study["why_not_applied"] == "repair_progress_ai_reviewer_recheck_required"
    assert study["current_work_unit"]["status"] == "executable_owner_action"
    assert (
        study["current_work_unit"]["state"]["source"]
        == "repair_progress_projection.mas_owner_repair_execution_evidence"
    )
    assert study["current_executable_owner_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert study["current_executable_owner_action"]["next_owner"] == "ai_reviewer"
    assert study["current_executable_owner_action"]["work_unit_id"] == action["next_work_unit"]
    assert result["provider_admission_pending_count"] == 1
    assert study["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    admission = result["provider_admission_candidates"][0]
    assert admission["action_type"] == "return_to_ai_reviewer_workflow"
    assert admission["next_executable_owner"] == "ai_reviewer"
    assert admission["work_unit_id"] == action["next_work_unit"]
    assert admission["work_unit_fingerprint"] == "repair-source-current"
    assert admission["currentness_basis"]["work_unit_id"] == action["next_work_unit"]
    assert admission["currentness_basis"]["work_unit_fingerprint"] == "repair-source-current"


def test_action_queue_routes_accepted_repair_delta_to_gate_replay_when_current_ai_reviewer_record_exists(
    tmp_path: Path,
) -> None:
    action_projection = __import__(
        "med_autoscience.controllers.paper_mission_owner_surface_parts.action_projection",
        fromlist=["action_projection"],
    )
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = tmp_path / "studies" / study_id
    eval_id = "publication-eval::dm002::2026-06-08T14:13:14Z::repair-source"
    draft = study_root / "paper" / "draft.md"
    draft_text = "# Draft\n\nCurrent repaired manuscript.\n"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(draft_text, encoding="utf-8")
    for path in (
        study_root / "paper" / "review" / "review_ledger.json",
        study_root / "paper" / "evidence_ledger.json",
        study_root / "paper" / "claim_evidence_map.json",
    ):
        _write_json(path, {"schema_version": 1, "status": "current"})
    ai_reviewer_request = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    gate_replay_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    _write_json(
        ai_reviewer_request,
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested"},
            "target_surface": "artifacts/publication_eval/latest.json",
        },
    )
    _write_json(
        gate_replay_request,
        {"request_kind": "run_gate_replay_after_repair", "request_lifecycle": {"state": "requested"}},
    )
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "repair-source-current",
            "source_eval_id": eval_id,
            "repair_work_unit": {"unit_id": "readiness_blocker_publication_repair", "source_eval_id": eval_id},
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_refs": [str(gate_replay_request)],
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "readiness_blocker_publication_repair",
            "repair_execution_evidence_ref": str(evidence_path),
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_request_ref": str(gate_replay_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260609T011045Z_publication_eval_record.json",
        current_manuscript_routeback_record(
            study_root=study_root,
            manuscript_path=draft,
            manuscript_text=draft_text,
            study_id=study_id,
            quest_id=quest_id,
            eval_id="publication-eval::dm002::2026-06-09T01:10:45Z::current-ai-reviewer",
            emitted_at="2026-06-09T01:10:45Z",
        ),
    )
    actions = action_projection.action_queue(
        {},
        {},
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload={
            "eval_id": eval_id,
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "ai_reviewer_required": True,
            },
        },
        gate_specificity={},
        ai_reviewer_assessment={},
        request_allowed_write_surfaces=[],
        control_allowed_write_surfaces=[],
        forbidden_actions=[],
    )

    assert [item["action_type"] for item in actions] == ["run_gate_clearing_batch"]
    action = actions[0]
    assert action["reason"] == "repair_progress_gate_replay_required"
    assert action["next_work_unit"] == "publication_gate_replay"
    assert action["repair_progress_request_ref"] == str(gate_replay_request)
    assert action["owner"] == "gate_clearing_batch"


def test_action_queue_routes_projected_current_ai_reviewer_record_to_repair_gate_replay(
    tmp_path: Path,
) -> None:
    action_projection = __import__(
        "med_autoscience.controllers.paper_mission_owner_surface_parts.action_projection",
        fromlist=["action_projection"],
    )
    records = __import__(
        "med_autoscience.controllers.ai_reviewer_publication_eval_records",
        fromlist=["ai_reviewer_publication_eval_records"],
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = tmp_path / "studies" / study_id
    eval_id = "publication-eval::dm003::projected-current-record"
    draft = study_root / "paper" / "draft.md"
    draft_text = "# Draft\n\nProjected current AI reviewer record.\n"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(draft_text, encoding="utf-8")
    ai_reviewer_request = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    gate_replay_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    _write_json(
        ai_reviewer_request,
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested"},
        },
    )
    _write_json(gate_replay_request, {"request_kind": "run_gate_replay_after_repair"})
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "projected-current-record-source",
            "source_eval_id": eval_id,
            "repair_work_unit": {"unit_id": "readiness_blocker_publication_repair", "source_eval_id": eval_id},
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [{"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"}],
            },
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_refs": [str(gate_replay_request)],
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "readiness_blocker_publication_repair",
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_request_ref": str(gate_replay_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    projected_record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=draft,
        manuscript_text=draft_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-06-09T01:10:45Z",
    )
    projected_record[records.PROJECTION_SOURCE_KIND_FIELD] = (
        records.PROJECTION_SOURCE_KIND_AI_REVIEWER_RECORD
    )
    projected_record[records.PROJECTION_SOURCE_REF_FIELD] = str(
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260609T011045Z_publication_eval_record.json"
    )

    actions = action_projection.action_queue(
        {},
        {},
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=projected_record,
        gate_specificity={},
        ai_reviewer_assessment={},
        request_allowed_write_surfaces=[],
        control_allowed_write_surfaces=[],
        forbidden_actions=[],
    )

    assert [item["action_type"] for item in actions] == ["run_gate_clearing_batch"]
    assert actions[0]["reason"] == "repair_progress_gate_replay_required"


def test_action_queue_accepts_dm002_ai_reviewer_record_gate_consumption_work_unit(
    tmp_path: Path,
) -> None:
    action_projection = __import__(
        "med_autoscience.controllers.paper_mission_owner_surface_parts.action_projection",
        fromlist=["action_projection"],
    )
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = tmp_path / "studies" / study_id
    eval_id = "publication-eval::dm002::current-record-consumption"
    draft = study_root / "paper" / "draft.md"
    draft_text = "# Draft\n\nCurrent DM002 manuscript.\n"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(draft_text, encoding="utf-8")
    record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=draft,
        manuscript_text=draft_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-06-09T01:10:45Z",
    )
    record["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "ai_reviewer_record_gate_consumption",
        "lane": "review",
        "summary": "Consume current record-only AI-reviewer response and replay publication gate.",
    }

    actions = action_projection.action_queue(
        {},
        {},
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=record,
        gate_specificity={},
        ai_reviewer_assessment={"present": True},
        request_allowed_write_surfaces=[],
        control_allowed_write_surfaces=[],
        forbidden_actions=[],
    )

    assert [item["action_type"] for item in actions] == ["run_gate_clearing_batch"]
    assert actions[0]["next_work_unit"] == "ai_reviewer_record_gate_consumption"
    assert actions[0]["owner"] == "gate_clearing_batch"


def test_scan_routes_current_archive_ai_reviewer_record_over_stale_record_request_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = __import__("med_autoscience.controllers.paper_mission_owner_surface", fromlist=["paper_mission_owner_surface"])
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    eval_id = "publication-eval::dm002::current-archive-record"
    draft = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "draft.md"
    )
    draft_text = "# Draft\n\nCurrent DM002 manuscript with archive reviewer record.\n"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(draft_text, encoding="utf-8")
    record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=draft,
        manuscript_text=draft_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-06-20T23:52:11+00:00",
    )
    record["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "ai_reviewer_record_gate_consumption",
        "lane": "review",
        "summary": "Consume current record-only AI-reviewer response and replay publication gate.",
    }
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260620T235211Z_publication_eval_record.json"
    )
    _write_json(record_path, record)
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    stale_latest = dict(record)
    stale_latest["eval_id"] = "publication-eval::dm002::stale-latest"
    stale_latest["emitted_at"] = "2026-06-20T12:00:49+00:00"
    _write_json(latest_path, stale_latest)
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json"
    )
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "request_id": "return_to_ai_reviewer_workflow::dm002",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "stale_record_ref": str(latest_path),
                "required_currentness_refs": [str(draft)],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {
                        "path": str(draft),
                        "required": True,
                        "present": True,
                        "valid": True,
                    }
                }
            },
            "source_workflow_ref": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs"
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(profile.runtime_root / quest_id),
        "refs": {"publication_eval_path": str(latest_path)},
        "study_truth_snapshot": {"truth_epoch": "truth-dm002-current-archive-record"},
        "runtime_health_snapshot": {"runtime_health_epoch": "runtime-dm002-current-archive-record"},
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(profile.runtime_root / quest_id),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(latest_path)},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, record | {"_projection_source_ref": str(record_path)}),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"]["missing"] is False
    assert study["ai_reviewer_assessment"]["request_state"] == "assessment_written"
    assert study["ai_reviewer_assessment"]["assessment_ref"] == str(record_path.resolve())
    assert [item["action_type"] for item in study["action_queue"]] == ["run_gate_clearing_batch"]
    assert study["action_queue"][0]["next_work_unit"] == "ai_reviewer_record_gate_consumption"
    assert study["action_queue"][0]["source_eval_id"] == eval_id

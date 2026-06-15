from __future__ import annotations

from pathlib import Path
import json

import pytest

from med_autoscience.controllers.owner_route_reconcile_parts import provider_admission_projection
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
        "med_autoscience.controllers.owner_route_reconcile_parts.stage_artifact_owner_actions",
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
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
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
        "med_autoscience.controllers.owner_route_reconcile_parts.action_projection",
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
        "med_autoscience.controllers.owner_route_reconcile_parts.action_projection",
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
        "med_autoscience.controllers.owner_route_reconcile_parts.action_projection",
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


def test_scan_routes_rejects_provider_admission_when_retained_queue_conflicts_with_current_work_unit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_fingerprint = "sha256:stale-ai-reviewer-recheck"
    _write_json(
        stale_dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "action_fingerprint": stale_fingerprint,
            "refs": {"dispatch_path": str(stale_dispatch_path)},
            "owner_route": {
                "next_owner": "ai_reviewer",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "work_unit_fingerprint": stale_fingerprint,
                "source_refs": {
                    "work_unit_id": "stale_ai_reviewer_recheck",
                    "work_unit_fingerprint": stale_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "stale_ai_reviewer_recheck",
                        "work_unit_fingerprint": stale_fingerprint,
                    },
                },
            },
        },
    )
    current_gate_fingerprint = "sha256:current-gate-clearing"
    studies = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "study_root": str(study_root),
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_fingerprint": current_gate_fingerprint,
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_gate_fingerprint,
                    },
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "action_fingerprint": current_gate_fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "canonical_current_work_unit",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    ]
    action_queue = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "queued",
            "owner": "ai_reviewer",
            "next_work_unit": "stale_ai_reviewer_recheck",
            "action_fingerprint": stale_fingerprint,
            "work_unit_fingerprint": stale_fingerprint,
            "refs": {"dispatch_path": str(stale_dispatch_path)},
        }
    ]

    candidates = provider_admission_projection.candidates_from_current_control(
        studies=studies,
        action_queue=action_queue,
        current_control_ref=str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
    )

    assert candidates == []


def test_scan_routes_projects_provider_admission_when_queue_matches_current_work_unit(
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    current_gate_fingerprint = "sha256:current-gate-clearing"
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "action_fingerprint": current_gate_fingerprint,
            "refs": {"dispatch_path": str(dispatch_path)},
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_fingerprint": current_gate_fingerprint,
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_gate_fingerprint,
                    },
                },
            },
        },
    )
    studies = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "study_root": str(study_root),
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_fingerprint": current_gate_fingerprint,
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_gate_fingerprint,
                    },
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "action_fingerprint": current_gate_fingerprint,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "canonical_current_work_unit",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    ]
    action_queue = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_gate_clearing_batch",
            "status": "queued",
            "owner": "gate_clearing_batch",
            "next_work_unit": "publication_gate_replay",
            "action_fingerprint": current_gate_fingerprint,
            "work_unit_fingerprint": current_gate_fingerprint,
            "refs": {"dispatch_path": str(dispatch_path)},
        }
    ]

    candidates = provider_admission_projection.candidates_from_current_control(
        studies=studies,
        action_queue=action_queue,
        current_control_ref=str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
    )

    assert len(candidates) == 1
    assert candidates[0]["action_type"] == "run_gate_clearing_batch"
    assert candidates[0]["work_unit_id"] == "publication_gate_replay"
    assert candidates[0]["action_fingerprint"] == current_gate_fingerprint


def test_scan_projects_current_write_routeback_despite_stale_progress_active_run(monkeypatch, tmp_path: Path) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    opl_attempts = __import__(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts",
        fromlist=["opl_provider_attempts"],
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm002-write-route",
            "canonical_runtime_action": "continue_supervising_runtime",
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
                "summary": "Controller-authorized paper repair and package rebuild from latest evidence.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-write-route",
            "source_signature": "truth-source-dm002-write-route",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "active_run_id": "mas-run-stale-progress-only",
        "supervision": {"active_run_id": "mas-run-stale-progress-only", "health_status": "stale"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )
    seen_preferred_actions: list[dict[str, object]] = []

    def fake_live_provider_attempt_for_study(**kwargs: object) -> None:
        seen_preferred_actions.extend(dict(action) for action in kwargs.get("preferred_actions") or [])
        return None

    monkeypatch.setattr(
        opl_attempts,
        "live_provider_attempt_for_study",
        fake_live_provider_attempt_for_study,
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    macro_source = study["owner_route"]["source_refs"]["study_macro_state"]
    assert macro_source["writer_state"] == "queued"
    assert macro_source["user_next"] == "repair"
    assert macro_source["reason"] == "quality"
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    assert [item["action_type"] for item in result["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["next_work_unit"] == "dm002_same_line_publication_paper_repair"
    assert study["active_run_id"] is None
    assert study["owner_route"]["active_run_id"] is None
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["blocked_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert study["next_owner"] == "write"
    assert [action["action_type"] for action in seen_preferred_actions] == ["run_quality_repair_batch"]
    assert seen_preferred_actions[0]["next_work_unit"] == "dm002_same_line_publication_paper_repair"


def test_fresh_ai_reviewer_write_routeback_supersedes_stale_reviewer_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
            "runtime_health_epoch": "runtime-health-dm003-ai-reviewer-write-route",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-ai-reviewer-write-route",
            "source_signature": "truth-source-dm003-ai-reviewer-write-route",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::medical-prose-routeback::sha256-current",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "blocked"},
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request-current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                    "route_back_required": True,
                    "route_target": "write",
                    "overall_style_verdict": "revise",
                }
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "reason": "Repair current AI reviewer manuscript-quality concerns.",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair Methods, n/N reporting, tables, and journal prose.",
                },
            }
        ],
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
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == "domain-transition::route_back_same_line::medical_prose_write_repair"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["source_refs"]["source_eval_id"] == publication_eval_payload["eval_id"]


def test_owner_receipt_consumption_routes_domain_transition_reviewer_successor_over_gate_replay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("# Draft\n\nCurrent repaired manuscript.\n", encoding="utf-8")
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
            "source_fingerprint": "publication-blockers::0915410f804b3697",
            "source_eval_id": "publication-eval::dm003::owner-receipt-consumption",
            "repair_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "source_eval_id": "publication-eval::dm003::owner-receipt-consumption",
            },
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
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
            "work_unit_id": "medical_prose_write_repair",
            "repair_execution_evidence_ref": str(evidence_path),
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_request_ref": str(gate_replay_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-owner-receipt-consumption",
            "source_signature": "truth-source-dm003-owner-receipt-consumption",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "queued",
        "paper_stage": "analysis-campaign",
        "active_run_id": None,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "study_id": study_id,
            "quest_id": quest_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "owner_receipt_ref": str(receipt_path),
        },
        "paper_recovery_state": {
            "phase": "owner_receipt_recorded",
            "next_safe_action": {
                "kind": "consume_owner_receipt",
                "owner_receipt_ref": str(receipt_path),
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
            },
        },
        "domain_transition": status_payload["domain_transition"],
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::owner-receipt-consumption",
        "study_id": study_id,
        "quest_id": quest_id,
        "overall_verdict": "blocked",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
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
    assert action["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert action["next_work_unit"] == "ai_reviewer_medical_prose_quality_review"
    assert action["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    )
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["current_work_unit"]["status"] == "executable_owner_action"
    assert study["current_work_unit"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert study["current_work_unit"]["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"

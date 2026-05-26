from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_paper_repair_execution_evidence import _write_json
from tests.test_quality_repair_batch import _write_blocked_publication_eval, _write_quality_summary


def test_quality_repair_batch_writer_handoff_inherits_current_owner_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    quality_module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-002"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        quest_id=quest_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(study_root)
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("Current DM002 manuscript story.\n", encoding="utf-8")
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::002"},
    )
    gate_result = {
        "ok": True,
        "status": "executed",
        "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        "selected_publication_work_unit": {
            "unit_id": "manuscript_story_repair",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        "gate_replay": {
            "status": "blocked",
            "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "unit_results": [
            {
                "unit_id": "manuscript_story_repair",
                "status": "updated",
                "result": {
                    "changed_artifact_refs": [
                        {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
                        {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                        {"path": str(review_ledger), "artifact_role": "review_ledger"},
                    ],
                },
            }
        ],
    }
    monkeypatch.setattr(quality_module.gate_clearing_batch, "run_gate_clearing_batch", lambda **_: gate_result)
    current_owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": "truth-event-000017-bac190eb1c889a78",
        "runtime_health_epoch": "runtime-health-event-006174-current",
        "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "route_epoch": "truth-event-000017-bac190eb1c889a78",
        "source_fingerprint": "truth-snapshot::0cb514d1a19001eabb406824",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": [],
        "idempotency_key": (
            "owner-route::002-dm-china-us-mortality-attribution::truth-event-000017-"
            "bac190eb1c889a78::write::manuscript_story_surface_delta_missing::c9cfdcd3b74e7427"
        ),
    }

    result = quality_module.run_quality_repair_batch(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context={
            "current_owner_route": current_owner_route,
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "requires_human_confirmation": False,
                "source_eval_id": "eval-002",
                "work_unit_fingerprint": "publication-blockers::5d99b7c4019bd601",
            },
        },
    )

    handoff = result["writer_worker_handoff"]
    assert result["status"] == "handoff_ready"
    assert handoff["owner_route"]["idempotency_key"] == current_owner_route["idempotency_key"]
    assert handoff["owner_route"]["work_unit_fingerprint"] == "dm002_same_line_publication_paper_repair_20260521"
    assert handoff["owner_route"]["route_epoch"] == "truth-event-000017-bac190eb1c889a78"
    assert handoff["prompt_contract"]["owner_route"]["idempotency_key"] == current_owner_route["idempotency_key"]
    assert handoff["idempotency_key"] == current_owner_route["idempotency_key"]
    assert handoff["repeat_suppression_key"] == "dm002_same_line_publication_paper_repair_20260521"

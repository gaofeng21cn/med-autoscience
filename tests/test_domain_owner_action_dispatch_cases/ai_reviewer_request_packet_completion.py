from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_materializes_complete_ai_reviewer_request_packet_before_required_ref_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nDM002 current manuscript has a complete current AI reviewer record.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1, "items": []})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1, "items": []})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"schema_version": 1})
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260529T095414Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id="publication-eval::dm002::2026-05-29T09:54:14Z::ai-reviewer-current",
        emitted_at="2026-05-29T09:54:14Z",
    )
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": False,
                        "valid": False,
                    },
                }
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    captured: dict[str, object] = {}

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs):
        captured.update(kwargs)
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"schema_version": 1, "eval_id": record_payload["eval_id"]},
        )
        return {
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )
    monkeypatch.setattr(
        module,
        "_refresh_controller_decision_after_ai_reviewer_eval",
        lambda **_: {"refresh_status": "skipped"},
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert "missing_refs" not in execution
    assert captured["manuscript_ref"] == str(manuscript_path.resolve())
    assert captured["evidence_ref"] == str(study_root / "paper" / "evidence_ledger.json")
    assert captured["review_ref"] == str(study_root / "paper" / "review" / "review_ledger.json")
    assert captured["charter_ref"] == str(study_root / "artifacts" / "controller" / "study_charter.json")
    assert captured["additional_refs"] == {
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }


def test_execute_dispatch_completes_ai_reviewer_packet_with_stage_native_blueprint_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nDM002 current manuscript has a complete current AI reviewer record.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1, "items": []})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1, "items": []})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    stage_native_blueprint = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_manuscript_blueprint.json"
    )
    _write_json(stage_native_blueprint, {"schema_version": 1})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"schema_version": 1})
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260529T095414Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id="publication-eval::dm002::2026-05-29T09:54:14Z::ai-reviewer-current",
        emitted_at="2026-05-29T09:54:14Z",
    )
    _write_json(record_path, record_payload)
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": True,
                        "valid": True,
                    },
                }
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    captured: dict[str, object] = {}

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs):
        captured.update(kwargs)
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"schema_version": 1, "eval_id": record_payload["eval_id"]},
        )
        return {
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )
    monkeypatch.setattr(
        module,
        "_refresh_controller_decision_after_ai_reviewer_eval",
        lambda **_: {"refresh_status": "skipped"},
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    persisted_request = json.loads(request_path.read_text(encoding="utf-8"))
    persisted_blueprint_ref = persisted_request["input_contract"]["required_refs"]["medical_manuscript_blueprint"]

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert captured["additional_refs"]["medical_manuscript_blueprint"] == str(stage_native_blueprint.resolve())
    assert persisted_blueprint_ref["path"] == str(stage_native_blueprint.resolve())
    assert persisted_blueprint_ref["present"] is True
    assert persisted_blueprint_ref["valid"] is True
    assert not (study_root / "paper" / "medical_manuscript_blueprint.json").exists()

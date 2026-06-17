from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_dm002_same_tick_ai_reviewer_record_production_uses_domain_transition_eval_id_for_owner_route_currentness(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent inputs require AI reviewer record production.\n", encoding="utf-8")
    eval_id = "publication-eval::dm002::current-inputs"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"

    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "required_currentness_refs": [str(manuscript_path.resolve())],
            },
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "runtime_health_snapshot": {},
                    "study_truth_snapshot": {
                        "truth_epoch": "truth-epoch-dm002-current-inputs",
                        "source_signature": "truth-source-dm002-current-inputs",
                    },
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "controller",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": work_unit_id,
                            "lane": "ai_reviewer",
                            "summary": "Produce an AI reviewer publication evaluation against current inputs.",
                        },
                        "publication_eval_ref": {"eval_id": eval_id},
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "eval_id": eval_id,
                            "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                        },
                    },
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["owner_callable_adapters"][0]
    route = dispatch["owner_route"]
    basis = route["currentness_contract"]["basis"]
    assert request["action_type"] == "return_to_ai_reviewer_workflow"
    assert request["request_owner"] == "ai_reviewer"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["blocked_reason"] is None
    assert dispatch["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert dispatch["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    assert dispatch["prompt_contract"]["owner_callable_command"].endswith("--build-production-trace")
    assert dispatch["prompt_contract"]["owner_callable_payload_ref"].endswith(
        "record_production_payloads/return_to_ai_reviewer_workflow_payload.json"
    )
    assert dispatch["source_action"]["record_only_surface"] is True
    assert dispatch["source_action"]["publication_eval_latest_write_allowed"] is False
    assert dispatch["owner_route_attempt_envelope"]["dispatchable"] is True
    assert route["currentness_contract"]["missing_required_fields"] == []
    assert basis["source_eval_id"] == eval_id
    assert route["source_refs"]["owner_route_currentness_basis"]["source_eval_id"] == eval_id
    assert result["ready_owner_callable_adapter_count"] == 1
    assert result["blocked_owner_callable_adapter_count"] == 0

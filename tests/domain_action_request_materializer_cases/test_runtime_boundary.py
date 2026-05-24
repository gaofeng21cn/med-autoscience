from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
    }


def test_default_executor_dispatch_materializes_runtime_completion_as_transport_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_request_pending",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": route["route_epoch"],
            "runtime_health_epoch": "runtime-health-current",
            "work_unit_fingerprint": "ai-reviewer-request::current",
            "failure_signature": "ai_reviewer_request_pending",
            "source_refs": {
                "work_unit_id": "ai-reviewer-record-production",
                "runtime_health_epoch": "runtime-health-current",
            },
        }
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_request_pending",
                    "owner_route": route,
                    "provider_completion": "succeeded",
                    "running_worker": True,
                    "queue_status": "succeeded",
                    "retry_budget_remaining": 0,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "owner_route": route,
                    },
                },
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    envelope = dispatch["owner_route_attempt_envelope"]
    assert result["default_executor_dispatches"][0]["dispatch_status"] == "ready"
    assert envelope["dispatchable"] is True
    assert envelope["authority_boundary"]["opl_owns"] == [
        "queue",
        "attempt",
        "retry",
        "dead_letter",
        "provider_liveness",
    ]
    assert envelope["authority_boundary"]["mas_owns"] == [
        "domain_truth",
        "ai_reviewer",
        "publication_gate",
        "artifact_authority",
        "owner_receipt",
        "typed_blocker",
    ]
    assert envelope["runtime_completion_guard"]["provider_completion_is_domain_completion"] is False
    assert envelope["runtime_completion_guard"]["provider_completion_is_stage_state"] is False
    assert envelope["runtime_completion_guard"]["running_worker_is_stage_state"] is False
    assert envelope["runtime_completion_guard"]["queue_succeeded_is_domain_completion"] is False
    assert envelope["runtime_completion_guard"]["retry_budget_is_domain_completion"] is False
    assert "domain_completion" not in dispatch
    assert "stage_state" not in dispatch
    assert dispatch["source_action_runtime_completion_fields_omitted"] == [
        "provider_completion",
        "queue_status",
        "retry_budget_remaining",
        "running_worker",
    ]
    assert "provider_completion" not in dispatch["source_action"]
    assert "queue_status" not in dispatch["source_action"]
    assert "retry_budget_remaining" not in dispatch["source_action"]
    assert "running_worker" not in dispatch["source_action"]

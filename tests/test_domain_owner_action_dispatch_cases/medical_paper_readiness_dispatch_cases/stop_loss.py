from __future__ import annotations

from .shared import *

def test_execute_dispatch_materializes_stop_loss_memo_for_readiness_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="stop_loss_memo")
    dispatch["operator_payload"] = {
        "current_route": "dm002-publication-handoff",
        "decision": "stop_loss",
        "evidence_state": "blocked",
        "stop_pressure": "high",
        "attempted_paths": ["publication_handoff_owner_gate", "medical_paper_readiness"],
        "failure_reasons": ["publication_handoff_owner_gate_missing_current_artifact"],
        "continuation_cost": {"runtime_hours": 9, "review_cycles": 2},
        "evidence_gain_ceiling": "low_without_route_control_decision",
        "alternative_routes": ["return_to_write"],
        "evidence_refs": [
            "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
        ],
        "exploration_depth_review": {
            "subgroup": {"sufficient": True, "finding": "No subgroup path unblocks the handoff artifact gap."},
            "alternative_endpoint": {
                "sufficient": True,
                "finding": "Alternative endpoint work is outside this handoff blocker.",
            },
            "data_quality": {"sufficient": True, "finding": "Data quality is not the current blocker."},
            "statistical_power": {"sufficient": True, "finding": "Power is not the current blocker."},
            "mechanism_plausibility": {
                "sufficient": True,
                "finding": "Mechanism plausibility does not unblock publication handoff.",
            },
        },
    }
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["operator_payload"] = dict(dispatch["operator_payload"])
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "stop_loss_memo"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["status"] == "present"
    stop_loss = json.loads(
        (study_root / "artifacts" / "medical_paper" / "stop_loss_memo.json").read_text(encoding="utf-8")
    )
    assert stop_loss["surface"] == "stop_loss_memo"
    assert stop_loss["decision"] == "stop_loss"
    assert stop_loss["quality_claim_authorized"] is False
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["stop_loss_memo"]["status"] == "present"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()

def test_execute_dispatch_ignores_stale_operator_payload_for_stop_loss_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_type": "medical_paper_readiness_owner_blocker",
            "quality_claim_authorized": False,
            "readiness_next_action": {
                "action_id": ACTION_TYPE,
                "surface_key": "stop_loss_memo",
                "summary": "补齐 Stop-loss Memo 后再继续自动论文链路。",
            },
        },
    )
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    stale_payload = {
        "surface": "bounded_analysis_candidate_board",
        "status": "present",
        "candidates": [
            {
                "target_claim": "stale candidate",
                "expected_evidence_gain": "stale",
                "cost_risk": "bounded",
                "statistical_risk": "bounded",
                "clinical_interpretability": "owner-review-required-before-quality-claim",
                "decision": "explore",
                "decision_reason": "stale payload from an older surface",
            }
        ],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    _write_json(
        study_root / request_ref,
        {
            "surface": "supervisor_request_handoff_packet",
            "action_type": ACTION_TYPE,
            "surface_key": "bounded_analysis_candidate_board",
            "operator_payload": stale_payload,
            "payload_authoring_target": {
                "surface": "medical_paper_readiness_operator_payload_authoring_target",
                "surface_key": "bounded_analysis_candidate_board",
                "operator_payload": stale_payload,
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
            },
        },
    )
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="stop_loss_memo")
    dispatch["operator_payload"] = stale_payload
    dispatch["operator_payload_ref"] = request_ref
    dispatch["medical_paper_readiness_payload_ref"] = request_ref
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["operator_payload"] = stale_payload
    prompt_contract["operator_payload_ref"] = request_ref
    prompt_contract["medical_paper_readiness_payload_ref"] = request_ref
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["operator_payload_authoring"]["source_basis"] == (
        "controller_decision_readiness_next_action_stop_loss"
    )
    stop_loss = json.loads(
        (study_root / "artifacts" / "medical_paper" / "stop_loss_memo.json").read_text(encoding="utf-8")
    )
    assert stop_loss["surface"] == "stop_loss_memo"
    assert stop_loss["current_route"] == "complete_medical_paper_readiness_surface"
    assert "candidates" not in stop_loss

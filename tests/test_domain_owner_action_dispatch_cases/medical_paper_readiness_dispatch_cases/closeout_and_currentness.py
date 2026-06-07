from __future__ import annotations

from .shared import *

def test_execute_dispatch_consumes_inline_readiness_dispatch_closeout_binding(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch = _readiness_dispatch(study_id=study_id)
    binding = _attach_readiness_closeout_binding(dispatch, study_id=study_id)
    dispatch["refs"] = {
        "dispatch_path": str(
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / f"{ACTION_TYPE}.json"
        )
    }
    _write_scan_latest(profile, study_id, dict(dispatch["owner_route"]))
    consumer_payload = {
        "surface": "domain_action_request_materializer",
        "schema_version": 1,
        "default_executor_dispatch_count": 1,
        "default_executor_dispatches": [dispatch],
    }

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
        consumer_payload=consumer_payload,
    )

    assert result["requested_studies"] == [study_id]
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_surface_input_required"
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "stable_typed_blocker"
    assert owner_delta["required_return_shape_satisfied"] is True
    assert owner_delta["stable_typed_blocker_refs"] == [
        str(study_root / "artifacts" / "controller_decisions" / "latest.json")
    ]
    assert owner_delta["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    assert owner_delta["closeout_binding"]["stage_manifest_ref"] == binding["stage_manifest_ref"]
    assert owner_delta["closeout_binding"]["current_pointer_ref"] == binding["current_pointer_ref"]
    assert owner_delta["closeout_binding"]["provider_attempt_ref"] == (
        f"opl://stage-attempts/{study_id}/{ACTION_TYPE}"
    )
    assert owner_delta["source_fingerprint"] == binding["source_fingerprint"]
    assert owner_delta["idempotency_key"] == f"owner-route::{study_id}::{ACTION_TYPE}::MedAutoScience"
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{ACTION_TYPE}.json"
    ).exists()

def test_execute_dispatch_prefers_readiness_identity_over_stale_surface_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    identity = {
        "action_type": ACTION_TYPE,
        "surface_key": "literature_provider_runtime",
        "source": "current_owner_action",
    }
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch["surface_key"] = "bounded_analysis_candidate_board"
    dispatch["readiness_surface_identity"] = identity
    dispatch["operator_payload"] = _complete_provider_payload()
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["surface_key"] = "bounded_analysis_candidate_board"
    prompt_contract["readiness_surface_identity"] = identity
    prompt_contract["operator_payload"] = _complete_provider_payload()
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
    assert execution["owner_result"]["completed_surface_key"] == "literature_provider_runtime"
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["surface"] == "literature_provider_runtime"
    assert provider_surface["status"] == "ready"
    assert not (study_root / "artifacts" / "medical_paper" / "bounded_analysis_candidate_board.json").exists()

def test_execute_dispatch_materializes_provider_payload_from_readiness_request_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    _write_json(
        study_root / request_ref,
        {
            "surface": "supervisor_request_handoff_packet",
            "action_type": ACTION_TYPE,
            "surface_key": "literature_provider_runtime",
            "operator_payload": _complete_provider_payload(),
            "payload_authoring_target": {
                "surface": "medical_paper_readiness_operator_payload_authoring_target",
                "surface_key": "literature_provider_runtime",
                "operator_payload": _complete_provider_payload(),
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch["operator_payload_ref"] = request_ref
    dispatch["medical_paper_readiness_payload_ref"] = request_ref
    dispatch["prompt_contract"]["operator_payload_ref"] = request_ref
    dispatch["prompt_contract"]["medical_paper_readiness_payload_ref"] = request_ref
    binding = _attach_readiness_closeout_binding(dispatch, study_id=study_id)
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
    assert execution["owner_result"]["completed_surface_key"] == "literature_provider_runtime"
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "quality_gate_receipt_with_stable_typed_blocker"
    assert owner_delta["required_return_shape_satisfied"] is True
    assert owner_delta["owner_receipt_refs"] == []
    assert owner_delta["quality_gate_receipt_refs"][0] == str(
        study_root / "artifacts" / "medical_paper" / "readiness.json"
    )
    assert owner_delta["quality_gate_receipt_refs"][1].startswith(
        "artifacts/medical_paper/actions/results/"
    )
    assert owner_delta["stable_typed_blocker_refs"] == [
        str(study_root / "artifacts" / "controller_decisions" / "latest.json")
    ]
    assert owner_delta["quality_gate_receipt"]["completed_surface_key"] == "literature_provider_runtime"
    assert owner_delta["quality_gate_receipt"]["action_result_ref"] == owner_delta["quality_gate_receipt_refs"][1]
    assert owner_delta["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"
    assert owner_delta["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    assert owner_delta["closeout_binding"]["stage_manifest_ref"] == binding["stage_manifest_ref"]
    assert owner_delta["closeout_binding"]["current_pointer_ref"] == binding["current_pointer_ref"]
    assert owner_delta["closeout_binding"]["provider_attempt_ref"] == (
        f"opl://stage-attempts/{study_id}/{ACTION_TYPE}"
    )
    assert owner_delta["closeout_binding"]["attempt_lease_status"] == "active"
    assert owner_delta["idempotency_key"] == f"owner-route::{study_id}::{ACTION_TYPE}::MedAutoScience"
    assert owner_delta["authority_boundary"]["writes_publication_eval"] is False
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["surface"] == "literature_provider_runtime"
    assert provider_surface["status"] == "ready"

def test_execute_dispatch_allows_owner_authorized_readiness_surface_when_stall_scan_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_complete_soak_stage_refs(study_root)
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="real_study_soak_matrix_evidence")
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": False,
        "safe_reconcile_candidate": False,
        "action_fingerprint": "paper_progress_stall::missing-scan-readiness-surface",
        "source_refs": {
            "owner_route_work_unit_fingerprint": dispatch["owner_route"]["work_unit_fingerprint"],
        },
    }
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    _write_readiness_dispatch(study_root, profile, dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": dispatch["owner_route"],
                }
            ],
        },
    )

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
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["paper_progress_stall_diagnostic"] == {
        "surface_kind": "paper_progress_stall_diagnostic",
        "status": "owner_authorized_readiness_surface_current_missing_bypass",
        "blocking": False,
        "blocked_reason": None,
        "handoff_allowed": True,
        "dispatch_action_fingerprint": "paper_progress_stall::missing-scan-readiness-surface",
        "current_action_fingerprint": None,
        "current_terminal": None,
        "current_stalled": None,
    }
    assert execution["owner_result"]["completed_surface_key"] == "real_study_soak_matrix_evidence"
    assert execution["owner_result"]["guarded_operator_action_result"]["status"] == "present"
    assert (study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json").is_file()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()

def test_execute_dispatch_does_not_use_stale_request_payload_for_current_readiness_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_target_journal_writing_layer(study_root)
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    stale_payload = {
        "current_route": ACTION_TYPE,
        "decision": "stop_loss",
        "evidence_state": "blocked",
        "stop_pressure": "high",
        "attempted_paths": ["stop_loss_memo"],
        "failure_reasons": ["older readiness surface"],
        "continuation_cost": {"runtime_scope": "older"},
        "evidence_gain_ceiling": "low",
        "alternative_routes": ["return_to_write"],
        "evidence_refs": [],
        "exploration_depth_review": {
            "route_options_exhausted": {"sufficient": True},
            "artifact_delta_absent": {"sufficient": True},
            "upstream_evidence_ceiling_reached": {"sufficient": True},
        },
        "payload_source": "older_request",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    _write_json(
        study_root / request_ref,
        {
            "surface": "supervisor_request_handoff_packet",
            "action_type": ACTION_TYPE,
            "surface_key": "stop_loss_memo",
            "readiness_surface_identity": {
                "action_type": ACTION_TYPE,
                "surface_key": "stop_loss_memo",
                "source": "current_owner_action",
            },
            "operator_payload": stale_payload,
            "payload_authoring_target": {
                "surface": "medical_paper_readiness_operator_payload_authoring_target",
                "surface_key": "stop_loss_memo",
                "operator_payload": stale_payload,
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    dispatch = _readiness_dispatch_for_surface(study_id=study_id, surface_key="target_journal_writing_layer")
    dispatch["operator_payload_ref"] = request_ref
    dispatch["medical_paper_readiness_payload_ref"] = request_ref
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
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
    assert execution["owner_result"]["completed_surface_key"] == "target_journal_writing_layer"
    assert execution["owner_result"]["guarded_operator_action_result"]["status"] == "present"
    assert not (study_root / "artifacts" / "medical_paper" / "stop_loss_memo.json").exists()
    assert (study_root / "paper" / "target_journal_writing_layer.json").exists()

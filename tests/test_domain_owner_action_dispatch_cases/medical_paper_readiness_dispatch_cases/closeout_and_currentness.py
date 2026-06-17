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
        "owner_callable_adapter_count": 1,
        "owner_callable_adapters": [dispatch],
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


def test_explicit_readiness_dispatch_is_suppressed_by_fresh_typed_blocker_envelope(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch = _readiness_dispatch_for_surface(
        study_id=study_id,
        surface_key="authoring_runtime_authorization",
    )
    _write_readiness_dispatch(study_root, profile, dispatch)

    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_not_ready",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_executable_owner_action": {},
        },
    )
    monkeypatch.setattr(
        module.action_execution,
        "execute_complete_medical_paper_readiness_surface",
        lambda **_: (_ for _ in ()).throw(AssertionError("stale readiness dispatch should not execute")),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executions"] == []
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 0


def test_default_dispatch_does_not_execute_readiness_missing_typed_blocker_without_explicit_current_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    source_ref = str(
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    dispatch = _readiness_dispatch_for_surface(
        study_id=study_id,
        surface_key="authoring_runtime_authorization",
    )
    basis = {
        "work_unit_id": ACTION_TYPE,
        "work_unit_fingerprint": (
            f"current-readiness-typed-blocker::{study_id}::current"
        ),
        "truth_epoch": "truth-event::current",
        "runtime_health_epoch": "runtime-health-event::current",
    }
    for route in (dispatch["owner_route"], dispatch["prompt_contract"]["owner_route"]):
        assert isinstance(route, dict)
        route["truth_epoch"] = basis["truth_epoch"]
        route["runtime_health_epoch"] = basis["runtime_health_epoch"]
        route["work_unit_fingerprint"] = basis["work_unit_fingerprint"]
        route["source_fingerprint"] = "current-readiness-source::current"
        route["source_refs"] = {
            "work_unit_id": ACTION_TYPE,
            "work_unit_fingerprint": basis["work_unit_fingerprint"],
            "blocked_reason": "medical_paper_readiness_missing",
            "source_ref": source_ref,
            "owner_route_currentness_basis": dict(basis),
        }
    dispatch["source_action"] = {
        "action_type": ACTION_TYPE,
        "owner": "MedAutoScience",
        "reason": "medical_paper_readiness_missing",
        "authority": "current_work_unit.typed_blocker",
        "next_work_unit": ACTION_TYPE,
        "work_unit_fingerprint": basis["work_unit_fingerprint"],
        "source_ref": source_ref,
        "source_surface": "current_work_unit",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{ACTION_TYPE}.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "MedAutoScience",
        "action_type": ACTION_TYPE,
        "work_unit_id": ACTION_TYPE,
        "currentness_basis": {
            "truth_epoch": basis["truth_epoch"],
            "runtime_health_epoch": basis["runtime_health_epoch"],
            "work_unit_id": "older-terminal-stage-work-unit",
        },
        "state": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_id": "medical_paper_readiness_missing",
                "blocker_type": "medical_paper_readiness_missing",
                "owner": "MedAutoScience",
                "work_unit_id": ACTION_TYPE,
                "source_ref": source_ref,
            },
        },
    }
    current_execution_envelope = {
        "state_kind": "typed_blocker",
        "owner": "MedAutoScience",
        "typed_blocker": {
            "blocker_id": "medical_paper_readiness_missing",
            "blocker_type": "medical_paper_readiness_missing",
            "owner": "MedAutoScience",
            "work_unit_id": ACTION_TYPE,
            "source_ref": source_ref,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": current_work_unit,
                    "current_execution_envelope": current_execution_envelope,
                    "action_queue": [],
                }
            ],
        },
    )
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": current_work_unit,
            "current_execution_envelope": current_execution_envelope,
            "current_executable_owner_action": {},
        },
    )
    monkeypatch.setattr(
        module.action_execution,
        "execute_complete_medical_paper_readiness_surface",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("blocker-only readiness dispatch must not execute")
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 0
    assert result["dry_run_count"] == 0
    assert result["executions"] == []
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 0


def _provider_payload_for_query(query: str) -> dict[str, object]:
    payload = _complete_provider_payload()
    payload["search_strategy"]["query"] = query
    for provider in payload["providers"]:
        provider["query"] = query
    return payload


def _bind_readiness_currentness_identity(
    dispatch: dict[str, object],
    *,
    study_id: str,
    source_fingerprint: str,
    work_unit_digest: str,
) -> None:
    source_ref = (
        f"/tmp/{study_id}/artifacts/stage_outputs/"
        "08-publication_package_handoff/receipts/typed_blocker.json"
    )
    work_unit_fingerprint = (
        f"stage-current-owner-delta::{ACTION_TYPE}::literature_provider_runtime::{source_ref}"
    )
    basis = {
        "work_unit_id": ACTION_TYPE,
        "work_unit_fingerprint": work_unit_fingerprint,
        "truth_epoch": f"truth-event::{study_id}",
        "runtime_health_epoch": f"runtime-health-event::{study_id}",
    }
    digest_basis = {
        "stable_truth_digest": source_fingerprint,
        "runtime_digest": f"runtime::{source_fingerprint}",
        "volatile_projection_digest": f"projection::{source_fingerprint}",
        "work_unit_digest": work_unit_digest,
    }
    readiness_identity = {
        "action_type": ACTION_TYPE,
        "surface_key": "literature_provider_runtime",
        "source": "stage_kernel_projection.current_owner_delta",
        "source_ref": source_ref,
    }
    dispatch["source_fingerprint"] = source_fingerprint
    dispatch["work_unit_fingerprint"] = work_unit_fingerprint
    dispatch["readiness_surface_identity"] = readiness_identity
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["source_fingerprint"] = source_fingerprint
    prompt_contract["work_unit_fingerprint"] = work_unit_fingerprint
    prompt_contract["readiness_surface_identity"] = dict(readiness_identity)
    for route in (dispatch["owner_route"], prompt_contract["owner_route"]):
        assert isinstance(route, dict)
        route["source_fingerprint"] = source_fingerprint
        route["work_unit_fingerprint"] = work_unit_fingerprint
        route["currentness_digest_basis"] = dict(digest_basis)
        route["currentness_contract"] = {
            "status": "currentness_basis_required",
            "basis": dict(basis),
            "required_fields": [
                "work_unit_fingerprint",
                "truth_epoch",
                "runtime_health_epoch_or_source_eval_id",
            ],
            "missing_required_fields": [],
            "fail_closed_when_missing": True,
        }


def test_readiness_operator_idempotency_tracks_currentness_identity_payload_drift(
    tmp_path: Path,
) -> None:
    action_module = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.action_execution.medical_paper_readiness"
    )
    operator_module = importlib.import_module("med_autoscience.controllers.medical_paper_operator_actions")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")

    first_dispatch = _readiness_dispatch_for_surface(
        study_id=study_id,
        surface_key="literature_provider_runtime",
    )
    first_dispatch["prompt_contract"]["idempotency_key"] = "owner-route::dm002::readiness"
    _bind_readiness_currentness_identity(
        first_dispatch,
        study_id=study_id,
        source_fingerprint="truth-snapshot::old",
        work_unit_digest="work-unit-digest::old",
    )
    first_payload = _provider_payload_for_query("diabetes mortality prediction")
    first_key = action_module._operator_idempotency_key(
        dispatch=first_dispatch,
        surface_key="literature_provider_runtime",
        action_id="run_provider_literature_scout",
    )
    first_result = operator_module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=first_payload,
        idempotency_key=first_key,
    )

    second_dispatch = _readiness_dispatch_for_surface(
        study_id=study_id,
        surface_key="literature_provider_runtime",
    )
    second_dispatch["prompt_contract"]["idempotency_key"] = "owner-route::dm002::readiness"
    _bind_readiness_currentness_identity(
        second_dispatch,
        study_id=study_id,
        source_fingerprint="truth-snapshot::current",
        work_unit_digest="work-unit-digest::current",
    )
    second_payload = _provider_payload_for_query("diabetes CVD mortality attribution")
    second_key = action_module._operator_idempotency_key(
        dispatch=second_dispatch,
        surface_key="literature_provider_runtime",
        action_id="run_provider_literature_scout",
    )
    second_result = operator_module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=second_payload,
        idempotency_key=second_key,
    )

    assert first_result["status"] == "ready"
    assert second_result["status"] == "ready"
    assert first_key != second_key
    assert first_result["input_digest"] != second_result["input_digest"]
    assert second_result["missing_reason"] != "input_digest_drift"
    assert "::currentness::" in second_result["idempotency_key"]
    assert second_result["idempotency_key"].endswith(
        "::surface::literature_provider_runtime::action::run_provider_literature_scout"
    )


def test_execute_dispatch_materializes_provider_payload_from_readiness_request_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _materialize_publication_handoff_stage(study_root, profile, study_id)
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
    binding["stage_run_id"] = (
        f"opl-stage-run::{study_id}::{ACTION_TYPE}::preserve-source-binding"
    )
    binding["stage_run_ref"] = binding["stage_run_id"]
    binding["stage_manifest_ref"] = (
        "opl://stage-manifests/domain_owner%2Fdefault-executor-dispatch"
    )
    binding["current_pointer_ref"] = (
        f"opl://stage-runs/{binding['stage_run_id']}/current"
    )
    dispatch["closeout_binding"] = binding
    dispatch["prompt_contract"]["closeout_binding"] = binding
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
    stage_closeout = execution["stage_native_closeout"]
    assert stage_closeout["status"] == "materialized"
    assert stage_closeout["terminal_outcome_kind"] == "typed_blocker"
    assert stage_closeout["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    assert stage_closeout["written_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    blocker_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    assert blocker_path.is_file()
    assert not (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "owner_receipt.json"
    ).exists()
    blocker = json.loads(blocker_path.read_text(encoding="utf-8"))
    assert blocker["authority_type"] == "typed_blocker"
    assert blocker["blocker_id"] == "medical_paper_readiness_missing"
    assert blocker["blocked_surface"] == "publication_handoff_owner_gate"
    assert blocker["next_safe_action"] == ACTION_TYPE
    assert blocker["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    assert blocker["closeout_binding"]["provider_attempt_ref"] == (
        f"opl://stage-attempts/{study_id}/{ACTION_TYPE}"
    )
    manifest = json.loads(
        (
            study_root
            / "artifacts"
            / "stage_outputs"
            / "08-publication_package_handoff"
            / "stage_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["terminal_status"] == "blocked"
    assert manifest["owner_receipt_refs"] == []
    assert manifest["typed_blocker_refs"] == ["receipts/typed_blocker.json"]
    current_pointer = json.loads((blocker_path.parents[1] / "current.json").read_text(encoding="utf-8"))
    assert current_pointer["current_stage"]["status"] == "blocked"
    assert current_pointer["current_stage"]["terminal_outcome_kind"] == "typed_blocker"
    assert current_pointer["current_stage"]["terminal_outcome_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert current_pointer["projection_writer"] == "mas_terminal_handoff_stage_current_projection_writer.v1"
    assert current_pointer["projection_role"] == (
        "mas_terminal_stage_current_projection_not_opl_stage_run_current_pointer"
    )
    assert current_pointer["stage_run_current_authority"] == "opl_stage_transition_authority_only"
    assert current_pointer["authority_boundary"]["can_write_stage_current_pointer"] is False
    assert current_pointer["authority_boundary"]["can_write_stage_run_terminal_state"] is False
    assert current_pointer["authority_boundary"]["can_publish_opl_current_owner_delta"] is False
    current_owner_delta = json.loads(
        (blocker_path.parents[1] / "projection" / "current_owner_delta.json").read_text(
            encoding="utf-8"
        )
    )
    assert current_owner_delta["latest_owner_answer_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert current_owner_delta["latest_owner_answer_kind"] == "typed_blocker"
    assert current_owner_delta["projection_writer"] == "mas_terminal_handoff_stage_current_projection_writer.v1"
    assert current_owner_delta["projection_role"] == (
        "mas_terminal_owner_answer_projection_not_opl_current_owner_delta_publish"
    )
    assert current_owner_delta["stage_run_current_authority"] == "opl_stage_transition_authority_only"
    assert current_owner_delta["authority_boundary"]["can_write_stage_current_pointer"] is False
    assert current_owner_delta["authority_boundary"]["can_write_stage_run_terminal_state"] is False
    assert current_owner_delta["authority_boundary"]["can_publish_opl_current_owner_delta"] is False
    assert current_owner_delta["action"] == ACTION_TYPE
    assert current_owner_delta["stage_run_id"] == binding["stage_run_id"]
    assert current_owner_delta["provider_attempt_ref"] == (
        f"opl://stage-attempts/{study_id}/{ACTION_TYPE}"
    )
    assert current_owner_delta["attempt_lease_ref"] == (
        f"opl://stage-attempts/{study_id}/{ACTION_TYPE}/leases/current"
    )
    assert current_owner_delta["execution_authorization_decision_ref"] == (
        f"opl://stage-attempts/{study_id}/{ACTION_TYPE}/execution-authorizations/current"
    )
    provider_surface = json.loads(
        (study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert provider_surface["surface"] == "literature_provider_runtime"
    assert provider_surface["status"] == "ready"

def test_execute_dispatch_rejects_incomplete_stage_closeout_binding(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _materialize_publication_handoff_stage(study_root, profile, study_id)
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    _write_json(
        study_root / request_ref,
        {
            "surface": "supervisor_request_handoff_packet",
            "action_type": ACTION_TYPE,
            "surface_key": "literature_provider_runtime",
            "operator_payload": _complete_provider_payload(),
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
    binding.pop("stage_manifest_ref", None)
    dispatch["closeout_binding"] = binding
    dispatch["prompt_contract"]["closeout_binding"] = binding
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    stage_closeout = execution["stage_native_closeout"]
    assert stage_closeout["status"] == "blocked"
    assert stage_closeout["blocked_reason"] == "trusted_opl_execution_authorization_required"
    assert not (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    ).exists()

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

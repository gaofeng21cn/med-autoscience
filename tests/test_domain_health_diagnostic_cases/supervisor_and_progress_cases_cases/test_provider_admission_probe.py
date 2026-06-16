from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _assert_identity_extends_handoff(candidate: dict, handoff_identity: dict) -> None:
    for key, value in handoff_identity.items():
        if isinstance(value, dict) and isinstance(candidate.get(key), dict):
            assert candidate[key] | value == candidate[key]
            continue
        assert candidate.get(key) == value
    route_identity_key = (
        f"provider-admission::{handoff_identity['study_id']}::"
        f"{handoff_identity['action_fingerprint']}"
    )
    assert candidate["route_identity_key"] == route_identity_key
    assert candidate["attempt_idempotency_key"] == route_identity_key
    assert candidate["idempotency_key"] == route_identity_key


def test_domain_health_diagnostic_same_tick_reports_handoff_pending_without_provider_attempt(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "001-risk"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: {
            "surface": "portable_owner_route_reconcile",
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {"default_executor_dispatch_count": 1},
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "execution_count": 1,
            "codex_dispatch_count": 1,
            "executions": [{"execution_status": "handoff_ready", "will_start_llm": True}],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=3)

    assert supervisor_tick["stop_reason"] == "provider_handoff_written_transition_request_pending"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["same_tick_terminal_projection"] == {
        "terminal_state": "provider_handoff_written_transition_request_pending",
        "owner_delta_produced": False,
        "provider_attempt_running": False,
        "stable_typed_blocker_observed": False,
        "provider_handoff_written": True,
    }
    assert diagnostic["requires_opl_transition_readback"] is True
    assert diagnostic["provider_admission_probe"] == {
        "observed": False,
        "running_provider_attempt_count": 0,
        "study_ids": [study_id],
    }
    assert diagnostic["next_forced_delta"]["target_surface"]["owner"] == "one-person-lab"


def test_domain_health_diagnostic_dry_run_surfaces_current_handoff_ready_provider_admission_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    _write_charter(study_root)
    quest_root = profile.runtime_root / "quests" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    typed_blocker_ref = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    work_unit_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        f"authoring_runtime_authorization::{typed_blocker_ref}"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                    "next_executable_owner": "MedAutoScience",
                    "required_output_surface": "complete_medical_paper_readiness_surface",
                    "dispatch_path": str(dispatch_path),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "action_fingerprint": work_unit_fingerprint,
                    "owner_route_current": True,
                    "owner_route_basis": "scan_latest",
                    "will_start_llm": True,
                    "owner_route": {
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "blocked_reason": "medical_paper_readiness_not_ready",
                            "quest_root": str(quest_root),
                            "owner_route_currentness_basis": {
                                "work_unit_id": "complete_medical_paper_readiness_surface",
                                "work_unit_fingerprint": work_unit_fingerprint,
                                "truth_epoch": "2026-06-07T19:56:40+00:00",
                                "runtime_health_epoch": "2026-06-07T19:56:40+00:00",
                            },
                        },
                    },
                }
            ],
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "quest_status": "running",
    }
    current_action = {
        "status": "ready",
        "source": "stage_kernel_projection.current_owner_delta",
        "next_owner": "MedAutoScience",
        "action_type": "complete_medical_paper_readiness_surface",
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "allowed_actions": ["complete_medical_paper_readiness_surface"],
        "surface_key": "authoring_runtime_authorization",
        "source_ref": str(typed_blocker_ref),
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-07T19:56:40+00:00",
            "current_executable_owner_action": current_action,
            "transition_request_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "transition_request_pending",
                    "source": "default_executor_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "action_fingerprint": work_unit_fingerprint,
                    "dispatch_path": str(dispatch_path),
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "next_executable_owner": "MedAutoScience",
                    "provider_attempt_or_lease_required": False,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                    "provider_completion_is_domain_completion": False,
                    "owner_route_current": True,
                }
            ],
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    assert result["managed_study_opl_provider_admission_candidates"] == []
    candidate = result["managed_study_opl_transition_request_candidates"][0]
    assert candidate["status"] == "transition_request_pending"
    assert candidate["source"] == "default_executor_execution"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "complete_medical_paper_readiness_surface"
    assert candidate["work_unit_id"] == "complete_medical_paper_readiness_surface"
    assert candidate["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidate["action_fingerprint"] == work_unit_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["owner_callable_surface"] == "opl_default_executor.stage_attempt"
    assert candidate["provider_attempt_or_lease_required"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    envelope = result["current_execution_envelopes"][study_id]
    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert result["provider_admission_current_control_state"]["provider_admission_pending_count"] == 0
    assert result["provider_admission_current_control_state"]["transition_request_pending_count"] == 1
    current_control_study = result["provider_admission_current_control_state"]["studies"][0]
    assert current_control_study["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert current_control_study["current_execution_envelope"]["next_work_unit"] == "complete_medical_paper_readiness_surface"
    current_control_action = current_control_study["action_queue"][0]
    assert current_control_action["status"] == "transition_request_pending"
    assert current_control_action["work_unit_fingerprint"] == work_unit_fingerprint
    assert current_control_action["handoff_packet"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert result["action_fingerprints"] == [work_unit_fingerprint]


def test_runtime_owner_handoff_carries_current_provider_admission_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    quest_root = profile.runtime_root / "quests" / study_id
    action_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs::return_to_ai_reviewer_workflow"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "ai_reviewer",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "dispatch_path": str(dispatch_path),
                    "action_fingerprint": action_fingerprint,
                    "owner_route": {
                        "next_owner": "ai_reviewer",
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                                "work_unit_fingerprint": action_fingerprint,
                                "truth_epoch": "2026-06-08T05:50:00+00:00",
                                "runtime_health_epoch": "2026-06-08T05:50:00+00:00",
                            },
                        },
                    },
                }
            ],
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="domain_transition_ai_reviewer_re_eval",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "ai_reviewer",
            "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "current_executable_owner_action": {
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-08T05:50:00+00:00",
            "current_execution_envelope": status_payload["current_execution_envelope"],
            "current_executable_owner_action": status_payload["current_executable_owner_action"],
            "transition_request_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "transition_request_pending",
                    "source": "default_executor_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "dispatch_path": str(dispatch_path),
                    "blocked_reason": "opl_execution_authorization_required",
                    "next_executable_owner": "ai_reviewer",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "provider_attempt_or_lease_required": False,
                    "provider_admission_requires_opl_runtime_result": True,
                    "opl_transition_runtime_required": True,
                    "provider_completion_is_domain_completion": False,
                    "owner_route_current": True,
                }
            ],
        },
    )
    current_control_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    dump_json(
        current_control_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-08T02:11:41+00:00",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "complete_medical_paper_readiness_surface",
                            "action_id": f"stale-readiness::{study_id}",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "status": "queued",
                        }
                    ],
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "action_id": f"stale-readiness::{study_id}",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "status": "queued",
                }
            ],
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    handoff = result["managed_study_opl_runtime_owner_handoffs"][0]
    latest_handoff = json.loads(
        (study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    identity = handoff["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "return_to_ai_reviewer_workflow"
    assert identity["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert identity["action_fingerprint"] == action_fingerprint
    assert identity["blocked_reason"] == "opl_execution_authorization_required"
    assert identity["status"] == "transition_request_pending"
    assert identity["provider_attempt_or_lease_required"] is False
    assert identity["provider_admission_requires_opl_runtime_result"] is True
    assert handoff["provider_admission_candidates"] == [identity]
    assert latest_handoff["provider_admission_identity"] == identity
    assert latest_handoff["provider_admission_candidates"] == [identity]
    current_control = json.loads(current_control_path.read_text(encoding="utf-8"))
    assert current_control["provider_admission_pending_count"] == 0
    assert current_control["provider_admission_candidates"] == []
    assert current_control["transition_request_pending_count"] == 1
    assert len(current_control["transition_request_candidates"]) == 1
    _assert_identity_extends_handoff(current_control["transition_request_candidates"][0], identity)
    assert current_control["current_control_refresh_source"] == (
        "domain_health_diagnostic.provider_admission_candidates"
    )
    assert [action["action_type"] for action in current_control["action_queue"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    study = current_control["studies"][0]
    assert study["study_id"] == study_id
    _assert_identity_extends_handoff(study["provider_admission_identity"], identity)
    assert [action["action_type"] for action in study["action_queue"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    assert study["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert (
        study["current_execution_envelope"]["next_work_unit"]
        == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
from .provider_admission_current_control_cases import *  # noqa: F403,F401,E402
from .provider_admission_current_control_report_envelope_cases import *  # noqa: F403,F401,E402
from .provider_admission_progress_currentness_cases import *  # noqa: F403,F401,E402
from .provider_admission_probe_identity_cases import *  # noqa: F403,F401,E402
from .provider_admission_same_tick_cases import *  # noqa: F403,F401,E402

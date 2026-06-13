from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_keeps_same_tick_provider_admission_closed_without_stage_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    execution_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})

    stale_owner_route_payload = {
        "surface": "opl_current_control_state_handoff",
        "schema_version": 1,
        "generated_at": "2026-06-09T03:41:44+00:00",
        "workspace_root": str(profile.workspace_root),
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "studies": [
            {
                "study_id": study_id,
                "quest_id": study_id,
                "action_queue": [
                    {
                        "study_id": study_id,
                        "action_type": "run_gate_clearing_batch",
                        "status": "queued",
                        "authority": "observability_only",
                    }
                ],
            }
        ],
        "action_queue": [
            {
                "study_id": study_id,
                "action_type": "run_gate_clearing_batch",
                "status": "queued",
                "authority": "observability_only",
            }
        ],
    }

    def fake_impl(**kwargs) -> dict[str, object]:
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-09T03:40:56+00:00",
            "runtime_root": str(profile.runtime_root),
            "managed_study_opl_provider_admission_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "provider_admission_pending",
                    "source": "default_executor_execution",
                    "execution_ref": str(execution_path),
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::"
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "action_fingerprint": (
                        "domain-transition::route_back_same_line::"
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "dispatch_path": str(dispatch_path),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "blocked_reason": "opl_execution_authorization_required",
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                    "owner_route_current": True,
                    "currentness_basis": {
                        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                        ),
                        "truth_epoch": "2026-06-09T03:40:56+00:00",
                        "runtime_health_epoch": "2026-06-09T03:40:56+00:00",
                    },
                }
            ],
            "provider_admission_pending_count": 1,
        }

    currentness_basis = {
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
        ),
        "truth_epoch": "2026-06-09T03:40:56+00:00",
        "runtime_health_epoch": "2026-06-09T03:40:56+00:00",
    }
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-09T03:40:56+00:00",
            "current_work_unit": {
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                ),
                "action_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                ),
                "currentness_basis": currentness_basis,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "domain_transition.route_back_same_line",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                ),
                "action_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                ),
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        },
    )
    monkeypatch.setattr(module, "_run_domain_health_diagnostic_for_runtime_impl", fake_impl)
    monkeypatch.setattr(
        module,
        "_run_developer_supervisor_same_tick",
        lambda **kwargs: (
            dump_json(module.supervision_surfaces.latest_path(profile), stale_owner_route_payload)
            or {
                "surface": "developer_supervisor_same_tick",
                "schema_version": 1,
                "stop_reason": "provider_handoff_written_admission_pending",
                "study_ids": [study_id],
                "iterations": [],
                "materialize": {
                    "surface": "domain_action_request_materializer",
                    "default_executor_dispatch_count": 1,
                    "ready_default_executor_dispatch_count": 1,
                    "default_executor_dispatches": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_gate_clearing_batch",
                            "dispatch_status": "ready",
                            "dispatch_authority": "consumer_default_executor_dispatch",
                            "dispatch_path": str(dispatch_path),
                            "next_executable_owner": "gate_clearing_batch",
                            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "work_unit_fingerprint": (
                                "domain-transition::route_back_same_line::"
                                "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                            ),
                        }
                    ],
                },
            }
        ),
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    current_control_state = result["provider_admission_current_control_state"]
    assert current_control_state["provider_admission_pending_count"] == 0
    assert current_control_state["provider_admission_candidates"] == []
    assert current_control_state["action_queue"] == []
    assert current_control_state["stage_route_arbiter"]["decision_counts"] == {
        "weak_provider_admission_identity": 1,
    }
    decision = current_control_state["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "weak_provider_admission_identity"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["missing_identity_fields"] == ["stage_packet_ref_or_refs"]
    latest_payload = json.loads(
        module.supervision_surfaces.latest_path(profile).read_text(encoding="utf-8")
    )
    assert latest_payload["provider_admission_pending_count"] == 0
    assert latest_payload["provider_admission_candidates"] == []
    assert latest_payload["action_queue"] == []

def test_provider_admission_candidate_survives_readiness_typed_blocker_for_publication_eval_repair(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    fingerprint = "publication-blockers::0915410f804b3697"
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )
    dispatch_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(
        dispatch_path,
        {
            "surface": "consumer_default_executor_dispatch",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        },
    )
    current_control = {
        "surface": "opl_current_control_state_handoff",
        "studies": [
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "MedAutoScience",
                    "typed_blocker": {
                        "blocker_type": "medical_paper_readiness_missing",
                        "source_ref": typed_blocker_ref,
                    },
                },
            }
        ],
    }

    assert (
        provider_admission.current_control_provider_admission_candidates(
            current_control,
            study_root=study_root,
            status_payload={"study_id": study_id},
        )
        == []
    )

    current_control["studies"][0]["current_executable_owner_action"] = {
        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
        "status": "ready",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "allowed_actions": ["run_quality_repair_batch"],
        "target_surface": {
            "ref_kind": "publication_eval_recommended_action",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "route_target": "write",
            "stage_typed_blocker_ref": typed_blocker_ref,
            "publication_eval_id": "publication-eval::003::blocked::current",
            "gap_ids": ["gap-002"],
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
            },
        },
    }

    result = provider_admission.current_control_provider_admission_candidates(
        current_control,
        study_root=study_root,
        status_payload={"study_id": study_id},
        current_control_ref="/workspace/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["study_id"] == study_id
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == "medical_prose_write_repair"
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["action_fingerprint"] == fingerprint
    assert candidate["next_executable_owner"] == "write"
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["provider_attempt_or_lease_required"] is True
    assert candidate["currentness_basis"]["work_unit_id"] == "medical_prose_write_repair"
    assert candidate["currentness_basis"]["work_unit_fingerprint"] == fingerprint

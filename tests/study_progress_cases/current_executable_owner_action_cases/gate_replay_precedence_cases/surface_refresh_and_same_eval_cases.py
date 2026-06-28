from __future__ import annotations

from tests.study_progress_cases import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_refresh_current_execution_surfaces_promotes_live_gate_followthrough_over_gate_replay_blocker() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_eval_id": source_eval_id,
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
        },
        "target_surface": {
            "ref_kind": "publication_work_unit",
            "route_target": "write",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        },
        "target_surface_specificity": "gate_followthrough_actionable_publication_work_unit",
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "current_executable_owner_action": action,
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        status={"study_id": study_id},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "blocked_reason": "publication_gate_replay_blocked",
            "next_owner": "publication_gate",
            "latest_typed_owner_callable_closeout": {
                "stage_attempt_id": "sat_d2b4c700b31294ab17c225d4",
                "status": "typed_blocker",
                "blocked_reason": "publication_gate_replay_blocked",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                "action_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                "source_fingerprint": "truth-snapshot::eb10e8316639d4839970dc15",
                "idempotency_key": "idem_c84ba9b663a6b466165b652f",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                },
            },
        },
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006833-7bb5776c1cb9e961"
        },
    )

    assert result["current_executable_owner_action"] == action
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "write"
    assert result["current_work_unit"]["action_type"] == "run_quality_repair_batch"
    assert result["current_work_unit"]["work_unit_id"] == "medical_prose_write_repair"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["current_execution_envelope"]["owner"] == "write"


def test_refresh_current_execution_surfaces_rebuilds_selected_successor_over_stale_handoff_blocker() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stale_fingerprint = "publication-blockers::0915410f804b3697"
    selected_fingerprint = "publication-blockers::2a234f3e48d8beb5"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "003-dpcc-primary-care-phenotype-treatment-gap::2026-06-20T05:46:03+00:00"
    )

    result = surfaces.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "selected_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": "publication-blockers::2a234f3e48d8beb5",
                    "current_work_unit_fingerprint": stale_fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "explicit_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
            },
            "publication_eval": {
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "next_work_unit": {
                            "unit_id": "analysis_claim_evidence_repair",
                            "lane": "analysis-campaign",
                        },
                        "specificity_targets": [
                            {
                                "target_kind": "table",
                                "target_id": "submission_minimal_authority",
                                "source_path": "/tmp/submission_manifest.json",
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                            {
                                "target_kind": "claim",
                                "target_id": "review_ledger",
                                "source_path": "/tmp/review_ledger.json",
                                "blocking_reason": "reviewer_first_concerns_unresolved",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": "/tmp/figure_catalog.json",
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                        ],
                        "blockers": [
                            "stale_submission_minimal_authority",
                            "medical_publication_surface_blocked",
                            "reviewer_first_concerns_unresolved",
                            "submission_hardening_incomplete",
                        ],
                    },
                ],
            },
        },
        status={"study_id": study_id},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
            "next_owner": "one-person-lab",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": {
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": stale_fingerprint,
                    },
                },
            },
            "typed_blocker": {
                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": stale_fingerprint,
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                    "owner": "one-person-lab",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": stale_fingerprint,
                },
            },
        },
        runtime_health_snapshot={},
    )

    action = result["current_executable_owner_action"]
    assert action["next_owner"] == "analysis-campaign"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert action["work_unit_fingerprint"] == selected_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "analysis-campaign"
    assert result["current_work_unit"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["current_execution_envelope"]["owner"] == "analysis-campaign"


def test_gate_followthrough_action_suppressed_after_quality_batch_consumes_same_eval() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "003-dpcc-primary-care-phenotype-treatment-gap::2026-06-20T07:41:48+00:00"
    )
    stale_fingerprint = "publication-blockers::0915410f804b3697"
    selected_fingerprint = "publication-blockers::5d99b7c4019bd601"

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "selected_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": "publication-blockers::2a234f3e48d8beb5",
                    "current_work_unit_fingerprint": stale_fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "explicit_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
            },
            "quality_repair_batch_followthrough": {
                "surface_kind": "quality_repair_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "gate_replay_status": "blocked",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "work_unit_currentness": {
                    "selected_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_work_unit_fingerprint": stale_fingerprint,
                },
            },
            "publication_eval": {
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "work_unit_fingerprint": selected_fingerprint,
                        "next_work_unit": {
                            "unit_id": "analysis_claim_evidence_repair",
                            "lane": "analysis-campaign",
                        },
                    },
                ],
            },
        }
    )

    assert action is None


def test_publication_eval_repair_action_survives_zero_selected_materialized_dispatch_blocker() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )

    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source_surface": "publication_eval.recommended_actions.readiness_blocker_repair",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "quality_re_review",
        "work_unit_fingerprint": "publication-blockers::quality-re-review",
        "action_fingerprint": "publication-blockers::quality-re-review",
        "target_surface": {
            "ref_kind": "publication_eval_recommended_action",
            "route_target": "write",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "next_work_unit": {
                "unit_id": "quality_re_review",
                "lane": "write",
            },
        },
        "target_surface_specificity": "publication_eval_readiness_blocker_derived_repair",
    }

    aligned = surfaces.current_action_aligned_with_execution_envelope(
        action=action,
        envelope={
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "quality_re_review",
                "work_unit_fingerprint": "publication-blockers::quality-re-review",
            },
        },
    )

    assert aligned == action


def test_existing_projection_refresh_promotes_gate_followthrough_over_terminal_gate_blocker(
    monkeypatch,
    tmp_path,
) -> None:
    projection = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    fingerprint = "publication-blockers::497d1260db522f01"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_quality_repair_batch.json"
    )
    dispatch_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "analysis-campaign",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
        },
    )
    monkeypatch.setattr(
        projection,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = projection._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "analysis_claim_evidence_repair",
                "owner_action": {
                    "next_owner": "analysis-campaign",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                },
            },
            "gate_clearing_batch_followthrough": {
                "status": "executed",
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["claim_evidence_consistency_failed"],
                "latest_record_path": (
                    str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json")
                ),
                "source_eval_id": "eval-current",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_work_unit_fingerprint": fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence blockers.",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:gate-replay-old",
                "action_fingerprint": "sha256:gate-replay-old",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_current_selected_dispatch",
                        "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:gate-replay-old",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                    "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-old",
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "running_provider_attempt": False,
                "blocked_reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                "next_owner": "one-person-lab",
                "latest_typed_owner_callable_closeout": {
                    "stage_attempt_id": "sat_gate",
                    "status": "typed_blocker",
                    "blocked_reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-old",
                    "action_fingerprint": "sha256:gate-replay-old",
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_current_selected_dispatch",
                        "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                        "owner": "one-person-lab",
                    },
                },
            },
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "analysis-campaign"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "analysis-campaign"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert result["transition_request_candidates"][0]["work_unit_id"] == "analysis_claim_evidence_repair"


def test_gate_followthrough_same_explicit_current_work_unit_still_routes_to_repair() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    fingerprint = "publication-blockers::0915410f804b3697"
    gate_record = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/gate_clearing_batch/latest.json"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::003::current",
                "latest_record_path": gate_record,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "lacks_specific_blocker_object": False,
                    "current_actionability_status": "actionable",
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting.",
                },
                "gate_replay_status": "blocked",
                "blocking_issue_count": 4,
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
            },
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:old-repair-progress-followup",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": [gate_record],
                "ai_reviewer_recheck_done": True,
            },
        }
    )

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == fingerprint


def test_same_eval_repair_delta_routes_to_gate_replay_not_repeat_write_repair() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    fingerprint = "sha256:repair-execution-evidence-current"
    gate_record = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/gate_clearing_batch/latest.json"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "latest_record_path": gate_record,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": fingerprint,
                    "current_work_unit_fingerprint": fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "lacks_specific_blocker_object": False,
                    "current_actionability_status": "actionable",
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_eval_id": source_eval_id,
                "source_fingerprint": fingerprint,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/quality_repair_batch/latest.json",
                "gate_replay_done": True,
                "gate_replay_refs": [
                    gate_record,
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
                "ai_reviewer_recheck_required": True,
                "ai_reviewer_recheck_done": True,
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["repair_progress_precedence"]["source_work_unit_id"] == "medical_prose_write_repair"


def test_gate_followthrough_does_not_supersede_different_repair_progress_gate_ref() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::003::current",
                "latest_record_path": "artifacts/controller/gate_clearing_batch/current.json",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
            },
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:old-repair-progress-followup",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_replay_requests/previous.json"],
                "ai_reviewer_recheck_done": True,
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["action_type"] == "run_gate_clearing_batch"

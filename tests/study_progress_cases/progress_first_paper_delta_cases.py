from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_terminal_stage_paper_delta_counts_in_top_level_progress_first_projection() -> None:
    assembly = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )
    handoff = {
        "latest_terminal_stage_log": {
            "stage_attempt_id": "sat-003",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "executed",
            "missing_user_stage_log_fields": ["progress_delta_classification"],
            "missing_observability_fields": ["duration", "token_usage", "cost"],
            "paper_stage_log": {
                "stage_work_done": ["Recorded paper-facing artifact changes."],
                "paper_work_done": ["Recorded paper-facing artifact changes."],
                "changed_stage_surfaces": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                ],
                "changed_paper_surfaces": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                ],
                "semantic_delta_refs": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md#semantic-delta",
                ],
                "remaining_blockers": [],
            },
        },
    }

    progress_delta = assembly._progress_delta_metrics(
        quality_repair_batch_followthrough={},
        gate_clearing_batch_followthrough={},
        opl_current_control_state_handoff=handoff,
        runtime_efficiency={"token_usage": {"total_tokens": 1200}},
    )
    result = projection.build_progress_first_projection(
        {
            **progress_delta,
            "opl_current_control_state_handoff": handoff,
        }
    )

    assert progress_delta["deliverable_progress_delta"] == {
        "count": 1,
        "token_usage_total": 1200,
        "sources": ["opl_current_control_state.latest_terminal_stage_log.paper_stage_log"],
    }
    assert progress_delta["paper_progress_delta"] == progress_delta["deliverable_progress_delta"]
    assert progress_delta["platform_repair_delta"]["count"] == 0
    assert progress_delta["progress_delta_classification"] == "deliverable_progress"
    assert result["progress_first_sprint_state"]["classification"] == "deliverable_progress"
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is True
    assert result["next_forced_delta"]["required_delta_kind"] == "review_current_paper_delta"


def test_terminal_stage_log_without_backing_refs_is_observability_not_paper_delta() -> None:
    assembly = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )
    handoff = {
        "latest_terminal_stage_log": {
            "stage_attempt_id": "sat-003",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "executed",
            "missing_user_stage_log_fields": ["progress_delta_classification"],
            "paper_stage_log": {
                "stage_work_done": ["Observed paper-facing artifact paths."],
                "paper_work_done": ["Observed paper-facing artifact paths."],
                "changed_paper_surfaces": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/claim_evidence_map.json",
                ],
                "remaining_blockers": [],
            },
        },
    }

    progress_delta = assembly._progress_delta_metrics(
        quality_repair_batch_followthrough={},
        gate_clearing_batch_followthrough={},
        opl_current_control_state_handoff=handoff,
        runtime_efficiency={"token_usage": {"total_tokens": 1200}},
    )
    result = projection.build_progress_first_projection(
        {
            **progress_delta,
            "opl_current_control_state_handoff": handoff,
        }
    )

    assert progress_delta["deliverable_progress_delta"] == {
        "count": 0,
        "token_usage_total": 0,
        "sources": [],
    }
    assert progress_delta["paper_progress_delta"] == progress_delta["deliverable_progress_delta"]
    assert progress_delta["progress_delta_classification"] == "typed_blocker"
    assert result["progress_first_sprint_state"]["classification"] == "typed_blocker"
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is False


def test_repair_execution_evidence_counts_as_current_paper_delta_and_drops_stale_readiness_queue(
    tmp_path: Path,
) -> None:
    assembly = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )
    repair_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.repair_progress_projection"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    draft = paper_root / "draft.md"
    review = paper_root / "build" / "review_manuscript.md"
    evidence_ledger = paper_root / "evidence_ledger.json"
    review_ledger = paper_root / "review" / "review_ledger.json"
    for path in (draft, review, evidence_ledger, review_ledger):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    gate_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    ai_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "repair-source-current",
            "repair_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "source_eval_id": "eval-current",
            },
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(review), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                    {"path": str(review_ledger), "artifact_role": "review_ledger"},
                ],
            },
            "changed_artifact_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "gate_replay_refs": [str(gate_request)],
            "ai_reviewer_recheck_request_ref": str(ai_request),
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "medical_prose_write_repair",
            "execution_status": "progress_delta_candidate",
            "canonical_artifact_delta_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                {"path": str(review), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "repair_execution_evidence_ref": str(evidence_path),
            "gate_replay_request_ref": str(gate_request),
            "ai_reviewer_recheck_request_ref": str(ai_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )

    repair_progress = repair_projection.build_repair_progress_projection(study_root=study_root)
    progress_delta = assembly._progress_delta_metrics(
        quality_repair_batch_followthrough={},
        gate_clearing_batch_followthrough={},
        opl_current_control_state_handoff={
            "running_provider_attempt": False,
            "action_queue": [
                {
                    "action_type": "complete_medical_paper_readiness_surface",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "fingerprint": "complete_medical_paper_readiness_surface::medical_paper_readiness_missing",
                }
            ],
        },
        runtime_efficiency={"token_usage": {"total_tokens": 0}},
        repair_progress_projection=repair_progress,
    )
    result = projection.build_progress_first_projection(
        {
            **progress_delta,
            "repair_progress_projection": repair_progress,
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "action_queue": [
                    {
                        "action_type": "complete_medical_paper_readiness_surface",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    }
                ],
            },
        }
    )

    assert repair_progress["paper_delta_observed"] is True
    assert progress_delta["paper_progress_delta"]["count"] == 1
    assert progress_delta["paper_progress_delta"]["sources"] == [
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    ]
    assert str(draft) in progress_delta["paper_progress_delta"]["refs"]
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is True
    assert result["next_forced_delta"]["required_delta_kind"] == "review_current_paper_delta"
    assert result["next_forced_delta"]["owner_action"]["allowed_actions"] == []


def test_repair_progress_current_action_survives_runtime_recovery_typed_blocker() -> None:
    assembly = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    action = {
        "surface_kind": "current_executable_owner_action",
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "next_owner": "ai_reviewer",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "action_type": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
    }

    aligned = assembly._current_action_aligned_with_execution_envelope(
        action=action,
        envelope={
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": {"blocker_type": "runtime_recovery_not_authorized"},
        },
    )

    assert aligned == action


def test_repair_progress_gate_replay_survives_identity_different_terminal_handoff_closeout() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    gate_replay_fingerprint = (
        "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"
    )
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "next_owner": "gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": gate_replay_fingerprint,
        "action_fingerprint": gate_replay_fingerprint,
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "repair_progress_precedence": {
            "paper_delta_observed": True,
            "accepted_owner_receipt": True,
            "source_work_unit_id": "analysis_claim_evidence_repair",
            "source_fingerprint": gate_replay_fingerprint,
            "superseded_stage_native_action": "run_quality_repair_batch",
        },
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_executable_owner_action": current_action,
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": gate_replay_fingerprint,
            },
        },
        status={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
        },
        handoff={
            "running_provider_attempt": False,
            "latest_typed_default_executor_closeout": {
                "status": "typed_blocker",
                "blocked_reason": (
                    "domain_owner_dispatch_zero_selected_after_materialized_current_request"
                ),
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "action_fingerprint": "publication-blockers::497d1260db522f01",
                "source_fingerprint": "publication-blockers::497d1260db522f01",
                "stage_attempt_id": "sat_9bbb471b55ad5ceda9d8495e",
                "receipt_ref": (
                    "artifacts/supervision/consumer/default_executor_execution/"
                    "sat_9bbb471b55ad5ceda9d8495e.closeout.json"
                ),
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                    "reason": (
                        "domain_owner_dispatch_zero_selected_after_materialized_current_request"
                    ),
                    "owner": "one-person-lab",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                },
            },
        },
        runtime_health_snapshot={},
    )

    assert result["current_executable_owner_action"] == current_action
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["action_type"] == "run_gate_clearing_batch"
    assert result["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"


def test_consumed_provider_completion_blocker_promotes_domain_transition_successor() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"

    result = surfaces.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
        status={"study_id": study_id, "quest_id": study_id},
        handoff={
            "running_provider_attempt": False,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "med-autoscience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": {
                        "blocker_type": "provider_completion_is_not_domain_ready",
                        "owner": "med-autoscience",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "med-autoscience",
                "source": "accepted_closeout_consumed_pending",
                "typed_blocker": {
                    "blocker_type": "provider_completion_is_not_domain_ready",
                    "owner": "med-autoscience",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
        runtime_health_snapshot={},
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "domain_transition"
    assert action["next_owner"] == "ai_reviewer"
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"


def test_gate_followthrough_action_does_not_survive_identity_mismatched_current_blocker() -> None:
    assembly = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    action = {
        "surface_kind": "current_executable_owner_action",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "status": "ready",
        "next_owner": "analysis-campaign",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
        "action_fingerprint": "publication-blockers::497d1260db522f01",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
    }

    aligned = assembly._current_action_aligned_with_execution_envelope(
        action=action,
        envelope={
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": {
                "blocker_type": "stage_packet_not_current_selected_dispatch",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": (
                    "owner-route::write::manuscript_story_surface_delta_missing::"
                    "run_quality_repair_batch"
                ),
                "currentness_basis": {
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": (
                        "owner-route::write::manuscript_story_surface_delta_missing::"
                        "run_quality_repair_batch"
                    ),
                },
            },
        },
    )

    assert aligned is None

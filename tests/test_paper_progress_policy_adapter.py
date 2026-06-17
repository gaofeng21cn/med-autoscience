from __future__ import annotations

import importlib


OPL_RUNTIME_FIELDS = {
    "current_control_command",
    "current_control_command_outbox_record",
    "opl_domain_progress_command",
    "opl_domain_progress_command_outbox_record",
    "opl_domain_progress_transition_event",
    "opl_domain_progress_transition_outbox_item",
    "opl_event_log_record",
    "opl_outbox_record",
    "projection_metadata",
    "read_model_generation_metadata",
    "stage_run",
    "stage_run_identity",
    "fixed_point_reconciler_state",
}


def _assert_clean_opl_transition_request(result: dict) -> None:
    request = result["opl_domain_progress_transition_request"]
    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["mas_can_create_opl_outbox_record"] is False
    assert request["mas_can_create_opl_event"] is False
    assert request["mas_can_create_opl_stage_run"] is False
    assert request["provider_admission_requires_opl_readback_shape"] == {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "required_sections": [
            "identity",
            "causality",
            "authority_boundary",
            "exactly_one_outcome",
            "projection_metadata",
        ],
        "required_runtime_refs": [
            "event_id",
            "outbox_item_id",
            "stage_run_identity",
        ],
        "accepted_outcome_kind": "provider_admission_pending",
        "deprecated_projection_fields_not_authority": [
            "stage_run_id",
            "event_id_without_causality",
            "outbox_item_id_without_authority_boundary",
        ],
    }
    assert OPL_RUNTIME_FIELDS.isdisjoint(request)


def _assert_mas_adapter_authority_only(result: dict) -> None:
    boundary = result["authority_boundary"]
    assert boundary["mas_can_authorize_provider_admission"] is False
    assert boundary["mas_can_run_fixed_point_reconciler"] is False
    assert boundary["mas_can_own_event_log_or_outbox"] is False
    assert boundary["mas_can_append_opl_event_log"] is False
    assert boundary["mas_can_emit_opl_outbox_item"] is False
    assert boundary["mas_can_create_opl_outbox_record"] is False
    assert boundary["mas_can_create_opl_event"] is False
    assert boundary["mas_can_create_opl_stage_run"] is False
    assert boundary["opl_owns_transition_runtime"] is True
    assert result["projection_metadata"]["authority"] is False
    assert OPL_RUNTIME_FIELDS.issubset(set(result["forbidden_runtime_fields"]))
    _assert_clean_opl_transition_request(result)


def test_policy_adapter_emits_opl_transition_request_without_claiming_runtime_authority() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "owner_receipt_recorded",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "currentness_basis": {
                    "truth_epoch": "truth-event-1",
                    "runtime_health_epoch": "runtime-event-1",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    },
                },
            },
        },
        source="test",
    )

    assert result["surface_kind"] == "paper_progress_policy_adapter_result"
    assert result["authority"] == "med_autoscience.paper_progress_policy_adapter"
    assert result["authority_role"] == "paper_domain_policy_adapter_only"
    assert result["recommended_opl_transition_kind"] == "MaterializeOwnerAction"
    assert result["policy_outcome_kind"] == "owner_action_requested"
    assert result["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert result["authority_boundary"]["opl_owns_transition_runtime"] is True
    assert result["authority_boundary"]["mas_can_create_opl_outbox_record"] is False
    assert result["provider_completion_is_domain_completion"] is False
    assert result["projection_metadata"]["authority"] is False
    assert result["projection_metadata"]["fixed_point_runtime_owner"] == "one-person-lab"
    assert result["projection_metadata"]["derived_from_event_id"] is None
    assert result["projection_metadata"]["observed_generation"] == "truth-event-1"
    assert result["paper_policy_verdict"]["provider_admission_allowed"] is False
    assert "opl_domain_progress_command" not in result
    assert "opl_domain_progress_command_outbox_record" not in result
    forbidden_fields = result["forbidden_runtime_fields"]
    assert OPL_RUNTIME_FIELDS.issubset(set(forbidden_fields))
    request = result["opl_domain_progress_transition_request"]
    assert request["recommended_transition_kind"] == "MaterializeOwnerAction"
    assert request["required_postcondition"]["kind"] == "owner_action_ref"
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_rejects_provider_admission_for_owner_callable_recovery() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "run_mas_owner_callable",
                    "owner": "write",
                    "provider_admission_allowed": False,
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "MaterializeOwnerAction"
    assert result["policy_outcome_kind"] == "owner_action_requested"
    assert result["paper_policy_verdict"]["provider_admission_allowed"] is False
    assert result["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == "owner_action_ref"
    assert "opl_domain_progress_command_outbox_record" not in result
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_materializes_executable_owner_action_as_mas_transition_request() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_mas_transition_request_or_owner_callable",
                    "owner": "write",
                    "provider_admission_allowed": True,
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "MaterializeOwnerAction"
    assert result["policy_outcome_kind"] == "owner_action_requested"
    assert result["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert result["authority_boundary"]["mas_can_create_opl_outbox_record"] is False
    request = result["opl_domain_progress_transition_request"]
    assert request["recommended_transition_kind"] == "MaterializeOwnerAction"
    assert request["required_postcondition"]["kind"] == "owner_action_ref"
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_classifies_domain_owner_results_without_runtime_fields() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "typed_blocker_ref": "typed_blocker:003",
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "RecordTypedBlocker"
    assert result["policy_outcome_kind"] == "typed_blocker"
    assert result["paper_policy_verdict"]["typed_blocker_ref"] == "typed_blocker:003"
    assert result["paper_policy_verdict"]["paper_progress_credit_allowed"] is True
    assert result["authority_boundary"]["mas_can_create_domain_typed_blocker"] is True
    assert "opl_domain_progress_transition_event" not in result
    assert "opl_domain_progress_transition_outbox_item" not in result
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_non_advancing_apply_requires_typed_blocker_projection() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_non_advancing_policy_blocker(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
        }
    )

    assert result["recommended_opl_transition_kind"] == "NonAdvancingApply"
    assert result["policy_outcome_kind"] == "non_advancing_apply_typed_blocker"
    assert result["paper_policy_verdict"] == {
        "verdict": "stable_typed_blocker_required",
        "typed_blocker_type": "non_advancing_apply",
        "reason": "fresh_readback_did_not_advance_same_aggregate",
    }
    assert result["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "non_advancing_apply_typed_blocker_ref"
    )
    assert result["projection_metadata"]["authority"] is False
    assert "opl_domain_progress_transition_event" not in result
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_projection_metadata_keeps_event_and_generation_diagnostic_only() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "owner_receipt_recorded",
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "owner-receipt::dm003",
                "currentness_basis": {
                    "truth_epoch": "truth::dm003::owner-receipt",
                    "derived_from_event_id": "opl-event:dm003:owner-receipt",
                    "observed_generation": "runtime-generation:dm003:17",
                },
            },
            "paper_recovery_state": {
                "phase": "owner_receipt_recorded",
                "owner_receipt_ref": "owner_receipt:dm003:publication_gate_replay",
                "next_safe_action": {
                    "kind": "consume_owner_receipt",
                    "owner_receipt_ref": "owner_receipt:dm003:publication_gate_replay",
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "ConsumeOwnerReceipt"
    assert result["projection_metadata"] == {
        "authority": False,
        "projection_owner": "med-autoscience",
        "fixed_point_runtime_owner": "one-person-lab",
        "derived_from_event_id": "opl-event:dm003:owner-receipt",
        "observed_generation": "runtime-generation:dm003:17",
    }
    request = result["opl_domain_progress_transition_request"]
    assert "projection_metadata" not in request
    assert "derived_from_event_id" not in request
    assert "observed_generation" not in request
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_consumes_owner_receipt_as_mas_result_shape() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "owner_receipt_recorded",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "currentness_basis": {"truth_epoch": "truth-event-owner-receipt"},
            },
            "paper_recovery_state": {
                "phase": "owner_receipt_recorded",
                "owner_receipt_ref": "owner_receipt:003/write/receipt.json",
                "next_safe_action": {
                    "kind": "consume_owner_receipt",
                    "owner_receipt_ref": "owner_receipt:003/write/receipt.json",
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "ConsumeOwnerReceipt"
    assert result["policy_outcome_kind"] == "owner_receipt"
    assert result["paper_policy_verdict"] == {
        "verdict": "mas_owner_receipt_consumption_required",
        "owner_receipt_ref": "owner_receipt:003/write/receipt.json",
        "paper_progress_credit_allowed": True,
    }
    assert result["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "owner_receipt_consumed"
    )
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_covers_human_gate_and_route_back_result_shapes() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    human_gate = adapter.build_policy_result(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "status": "waiting_for_owner",
                "owner": "human",
                "action_type": "resolve_publication_gate",
                "work_unit_id": "publication_gate_human_review",
                "work_unit_fingerprint": "human-gate::002",
            },
            "paper_recovery_state": {
                "phase": "human_gate",
                "human_gate_ref": "human_gate:002/publication_gate",
                "next_safe_action": {
                    "kind": "record_human_or_owner_gate",
                    "owner": "human",
                    "human_gate_ref": "human_gate:002/publication_gate",
                },
            },
        },
        source="test",
    )
    route_back = adapter.build_policy_result(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "status": "route_back_recorded",
                "owner": "review",
                "action_type": "consume_route_back",
                "work_unit_id": "ai_reviewer_route_back",
                "work_unit_fingerprint": "route-back::002",
            },
            "paper_recovery_state": {
                "phase": "route_back",
                "route_back_evidence_ref": "route_back:002/reviewer/latest.json",
                "next_safe_action": {
                    "kind": "route_back_to_owner_or_repair_materialization",
                    "owner": "review",
                    "route_back_evidence_ref": "route_back:002/reviewer/latest.json",
                },
            },
        },
        source="test",
    )

    assert human_gate["recommended_opl_transition_kind"] == "OpenHumanGate"
    assert human_gate["policy_outcome_kind"] == "human_gate"
    assert human_gate["paper_policy_verdict"]["human_gate_ref"] == "human_gate:002/publication_gate"
    assert human_gate["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "human_gate_ref"
    )
    assert route_back["recommended_opl_transition_kind"] == "AdoptRouteBackEvidence"
    assert route_back["policy_outcome_kind"] == "route_back_evidence"
    assert route_back["paper_policy_verdict"]["route_back_evidence_ref"] == (
        "route_back:002/reviewer/latest.json"
    )
    assert route_back["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "route_back_evidence_ref"
    )
    _assert_mas_adapter_authority_only(human_gate)
    _assert_mas_adapter_authority_only(route_back)


def test_policy_adapter_accepts_publication_gate_and_paper_delta_refs_without_runtime_authority() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "paper_delta_detected",
                "owner": "write",
                "action_type": "adopt_quality_gate_delta",
                "work_unit_id": "publication_gate_delta",
                "work_unit_fingerprint": "paper-delta::003",
            },
            "paper_recovery_state": {
                "phase": "paper_delta",
                "publication_gate_receipt_ref": "publication_gate:003/latest.json",
                "next_safe_action": {
                    "kind": "adopt_paper_delta",
                    "paper_delta_refs": [
                        "paper_delta:003/manuscript.md",
                        "quality_gate:003/reviewer.json",
                    ],
                    "artifact_delta_ref": "artifact_delta:003/package.zip",
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "AdoptPaperDelta"
    assert result["policy_outcome_kind"] == "paper_delta"
    assert result["paper_policy_verdict"]["verdict"] == "paper_gate_or_artifact_delta_required"
    assert result["paper_policy_verdict"]["paper_delta_refs"] == [
        "artifact_delta:003/package.zip",
        "publication_gate:003/latest.json",
        "paper_delta:003/manuscript.md",
        "quality_gate:003/reviewer.json",
    ]
    assert result["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "paper_delta_refs"
    )
    _assert_mas_adapter_authority_only(result)


def test_policy_adapter_turns_forbidden_write_into_stable_typed_blocker_shape() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "forbidden-write::003",
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_mas_transition_request_or_owner_callable",
                    "owner": "write",
                    "forbidden_write_detected": True,
                    "forbidden_write_ref": "forbidden_write:003/publication_eval/latest.json",
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "RecordTypedBlocker"
    assert result["policy_outcome_kind"] == "typed_blocker"
    assert result["paper_policy_verdict"] == {
        "verdict": "forbidden_write_typed_blocker_required",
        "typed_blocker_type": "forbidden_write",
        "forbidden_write_refs": ["forbidden_write:003/publication_eval/latest.json"],
        "paper_progress_credit_allowed": False,
        "forbidden_write_blocks_domain_progress": True,
    }
    assert result["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "typed_blocker_ref"
    )
    _assert_mas_adapter_authority_only(result)

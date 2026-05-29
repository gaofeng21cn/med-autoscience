from __future__ import annotations

import importlib


def test_owner_route_protocol_attaches_registered_reason_and_priority_lattice() -> None:
    owner_route_module = importlib.import_module("med_autoscience.runtime_control.owner_route")

    status = {
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002",
            "source_signature": "truth-source-dm002",
        },
        "runtime_health_snapshot": {"runtime_health_epoch": "runtime-health-dm002"},
        "quest_status": "running",
    }
    actions = [
        {
            "action_type": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "reason": "ai_reviewer_request_pending",
            "work_unit_fingerprint": "ai-reviewer-request::dm002::current",
        }
    ]

    route = owner_route_module.build_owner_route(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        status=status,
        progress={},
        actions=actions,
        blocked_reason="ai_reviewer_request_pending",
        next_owner="ai_reviewer",
        active_run_id=None,
    )

    assert route["owner_route_attempt_protocol"]["version"] == "mas-owner-route-attempt-protocol.v1"
    assert route["owner_reason_contract"]["reason"] == "ai_reviewer_request_pending"
    assert route["owner_reason_contract"]["owner"] == "ai_reviewer"
    assert route["owner_reason_contract"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert route["owner_reason_contract"]["required_output"] == "artifacts/publication_eval/latest.json"
    assert route["owner_reason_contract"]["priority_class"] == "ai_reviewer_currentness"
    assert route["priority_lattice"] == [
        "hard_methodology_or_source_blocker",
        "pending_ai_reviewer_request",
        "ai_reviewer_currentness",
        "write_route_back",
        "package_freshness",
        "delivery_or_human_handoff",
    ]
    assert route["currentness_contract"]["status"] == "currentness_basis_required"
    assert "owner_route_currentness_basis" in route["source_refs"]


def test_owner_route_normalization_preserves_embedded_currentness_work_unit_id() -> None:
    owner_route_module = importlib.import_module("med_autoscience.runtime_control.owner_route")

    route = owner_route_module.ensure_owner_route_v2(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-dm002",
            "truth_epoch": "truth-event-000017",
            "route_epoch": "truth-event-000017",
            "runtime_health_epoch": "runtime-health-event-006191",
            "source_fingerprint": "truth-snapshot::dm002-current-publication-hardening",
            "work_unit_fingerprint": "truth-snapshot::dm002-current-publication-hardening",
            "current_owner": "mas_controller",
            "next_owner": "write",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "allowed_actions": ["run_quality_repair_batch"],
            "idempotency_key": "owner-route::dm002::write::current-publication-hardening",
            "source_refs": {
                "owner_route_currentness_basis": {
                    "work_unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
                    "work_unit_fingerprint": "truth-snapshot::dm002-current-publication-hardening",
                    "truth_epoch": "truth-event-000017",
                    "runtime_health_epoch": "runtime-health-event-006191",
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                }
            },
        }
    )

    basis = route["source_refs"]["owner_route_currentness_basis"]
    assert basis["work_unit_id"] == "dm002_current_publication_hardening_after_ai_reviewer_eval"
    assert "owner_reason" not in basis
    assert route["currentness_contract"]["missing_required_fields"] == []


def test_owner_route_protocol_treats_unregistered_reason_as_diagnostic_when_route_is_complete() -> None:
    owner_route_module = importlib.import_module("med_autoscience.runtime_control.owner_route")

    route = owner_route_module.build_owner_route(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        status={
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch",
                "source_signature": "truth-source",
            },
            "runtime_health_snapshot": {"runtime_health_epoch": "runtime-health-epoch"},
        },
        progress={},
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "reason": "unregistered_local_reason",
                "work_unit_id": "current_manuscript_repair",
                "work_unit_fingerprint": "work-unit::current-manuscript-repair",
            }
        ],
        blocked_reason="unregistered_local_reason",
        next_owner="write",
        active_run_id=None,
    )

    assert route["owner_reason_contract"]["registered"] is False
    assert route["owner_route_attempt_protocol"]["dispatchable"] is True
    assert route["allowed_actions"] == ["run_quality_repair_batch"]


def test_default_executor_attempt_envelope_declares_domain_intent_and_authority_boundary() -> None:
    protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")

    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "002-dm-china-us-mortality-attribution",
        "quest_id": "quest-dm002",
        "truth_epoch": "publication-eval::dm002::current",
        "route_epoch": "publication-eval::dm002::current",
        "runtime_health_epoch": "runtime-health::dm002::current",
        "source_fingerprint": "truth-source::dm002::current",
        "work_unit_fingerprint": "work-unit::dm002::current-publication-hardening",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "allowed_actions": ["run_quality_repair_batch"],
        "idempotency_key": "owner-route::dm002::write::current-publication-hardening",
        "source_refs": {
            "source_eval_id": "publication-eval::dm002::current",
            "work_unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
            "work_unit_fingerprint": "work-unit::dm002::current-publication-hardening",
            "study_truth_epoch": "publication-eval::dm002::current",
            "runtime_health_epoch": "runtime-health::dm002::current",
        },
    }

    envelope = protocol.default_executor_attempt_envelope(
        dispatch={
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": owner_route,
            "allowed_write_surfaces": ["paper/draft.md", "paper/build/review_manuscript.md"],
            "forbidden_surfaces": ["artifacts/publication_eval/latest.json"],
            "required_closeout_packet": {
                "typed_closeout_required_for_completion": True,
                "free_text_closeout_accepted": False,
                "accepted_surface_kinds": ["stage_attempt_closeout_packet"],
                "completion_boundary": {"provider_completion_is_domain_ready": False},
            },
            "provider_completion": "succeeded",
            "running_worker": True,
            "queue_status": "succeeded",
            "retry_budget_remaining": 0,
        }
    )

    assert envelope["dispatchable"] is True
    assert envelope["authority_boundary"] == {
        "opl_owns": [
            "queue",
            "attempt",
            "retry",
            "dead_letter",
            "provider_liveness",
        ],
        "mas_owns": [
            "domain_truth",
            "ai_reviewer",
            "publication_gate",
            "artifact_authority",
            "owner_receipt",
            "typed_blocker",
        ],
    }
    assert envelope["runtime_completion_guard"] == {
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_stage_state": False,
        "running_worker_is_stage_state": False,
        "queue_succeeded_is_domain_completion": False,
        "retry_budget_is_domain_completion": False,
        "stage_state_owner": "one-person-lab",
        "domain_completion_owner": "med-autoscience",
        "domain_completion_requires": [
            "mas_owner_receipt_ref",
            "mas_typed_blocker_ref",
            "ai_reviewer_or_publication_gate_ref",
        ],
    }
    domain_intent = envelope["domain_intent"]
    assert domain_intent["surface_kind"] == "mas_domain_intent_v1"
    assert domain_intent["source_fingerprint"] == "truth-source::dm002::current"
    assert domain_intent["route_epoch"] == "publication-eval::dm002::current"
    assert domain_intent["truth_epoch"] == "publication-eval::dm002::current"
    assert domain_intent["idempotency_key"] == "owner-route::dm002::write::current-publication-hardening"
    assert domain_intent["owner_route_currentness_basis"] == envelope["owner_route_currentness_basis"]
    assert domain_intent["required_closeout_packet"] == envelope["required_closeout_packet"]
    assert domain_intent["lifecycle_contract"]["fail_closed_when_missing"] is True
    assert domain_intent["missing_required_fields"] == []


def test_default_executor_attempt_envelope_accepts_eval_bound_writer_route_without_runtime_health() -> None:
    protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")

    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-current-manuscript::20260528T125118Z"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "truth_epoch": source_eval_id,
        "route_epoch": source_eval_id,
        "source_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "current_owner": "quality_repair_batch",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "allowed_actions": ["run_quality_repair_batch"],
        "idempotency_key": (
            "quality-repair-writer-handoff::003-dpcc-primary-care-phenotype-treatment-gap::"
            "domain-transition::route_back_same_line::medical_prose_write_repair"
        ),
        "source_refs": {
            "source_eval_id": source_eval_id,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            "study_truth_epoch": source_eval_id,
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "owner_route_currentness_basis": {
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "truth_epoch": source_eval_id,
                "owner_reason": "manuscript_story_surface_delta_missing",
            },
        },
    }

    envelope = protocol.default_executor_attempt_envelope(
        dispatch={
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": owner_route,
            "allowed_write_surfaces": ["paper/draft.md", "paper/build/review_manuscript.md"],
            "forbidden_surfaces": ["artifacts/publication_eval/latest.json"],
        }
    )

    assert envelope["dispatchable"] is True
    assert envelope["source_eval_id"] == source_eval_id
    assert "owner_reason" not in envelope["owner_route_currentness_basis"]
    assert envelope["domain_intent"]["missing_required_fields"] == []


def test_default_executor_attempt_envelope_fails_closed_without_domain_intent_required_fields() -> None:
    protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")

    envelope = protocol.default_executor_attempt_envelope(
        dispatch={
            "action_type": "return_to_ai_reviewer_workflow",
            "next_executable_owner": "ai_reviewer",
            "owner_route": {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "next_owner": "ai_reviewer",
                "owner_reason": "ai_reviewer_request_pending",
                "failure_signature": "ai_reviewer_request_pending",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "source_refs": {"work_unit_id": "ai_reviewer_medical_prose_quality_review"},
            },
            "required_closeout_packet": {
                "typed_closeout_required_for_completion": True,
                "free_text_closeout_accepted": False,
            },
        }
    )

    assert envelope["dispatchable"] is False
    assert "owner_route_currentness_basis.owner_reason" not in envelope["domain_intent"]["missing_required_fields"]
    assert set(envelope["domain_intent"]["missing_required_fields"]) >= {
        "source_fingerprint",
        "route_epoch",
        "truth_epoch",
        "idempotency_key",
        "owner_route_currentness_basis.work_unit_fingerprint",
        "owner_route_currentness_basis.runtime_health_epoch_or_source_eval_id",
    }

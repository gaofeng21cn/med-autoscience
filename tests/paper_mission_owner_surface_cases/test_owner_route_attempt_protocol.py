from __future__ import annotations

import importlib


def test_owner_route_protocol_uses_one_opl_transport_ref_without_lifecycle_internals() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    boundary = protocol._authority_boundary()

    assert boundary["runtime_transport_ref"] == "opl-generated:family-runtime/current-control"
    assert boundary["stage_run_ref_contract"] == "opl-generated:family-runtime/stage-run"
    assert boundary["state_index_ref_contract"] == "opl-generated:state-index/source-ref"
    assert boundary["transport_owner"] == "one-person-lab"
    assert boundary["mas_can_write_runtime_transport"] is False
    assert boundary["mas_can_authorize_provider_attempt"] is False
    assert "opl_owns" not in boundary


def test_owner_route_protocol_projects_nonbinding_codex_route_context() -> None:
    owner_route_module = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_policy")

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
    assert route["owner_reason_contract"]["binding"] is False
    assert route["owner_reason_contract"]["route_selection_owner"] == "codex_cli"
    assert route["owner_reason_contract"]["codex_selected_action"] == "return_to_ai_reviewer_workflow"
    assert route["owner_reason_contract"]["can_reject_codex_route"] is False
    assert "priority_lattice" not in route
    assert route["currentness_contract"]["status"] == "currentness_basis_required"
    assert "owner_route_currentness_basis" in route["source_refs"]


def test_owner_route_registers_dm002_clean_migration_publication_gate_replay() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "002-dm-china-us-mortality-attribution",
        "quest_id": "002-dm-china-us-mortality-attribution",
        "truth_epoch": "publication-eval::dm002::current-ai-reviewer",
        "runtime_health_epoch": "runtime-health::dm002::current",
        "source_fingerprint": "truth-source::dm002::current-ai-reviewer",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::publication_gate_replay_after_clean_migration"
        ),
        "current_owner": "mas_controller",
        "next_owner": "gate_clearing_batch",
        "owner_reason": "publication_gate_replay_after_clean_migration",
        "failure_signature": "publication_gate_replay_after_clean_migration",
        "allowed_actions": ["run_gate_clearing_batch"],
        "idempotency_key": "owner-route::dm002::clean-migration-gate-replay",
        "source_refs": {
            "source_eval_id": "publication-eval::dm002::current-ai-reviewer",
            "work_unit_id": "publication_gate_replay_after_clean_migration",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::publication_gate_replay_after_clean_migration"
            ),
            "study_truth_epoch": "publication-eval::dm002::current-ai-reviewer",
            "runtime_health_epoch": "runtime-health::dm002::current",
        },
    }

    decorated = protocol.decorate_owner_route(owner_route)

    assert decorated["owner_reason_contract"]["binding"] is False
    assert decorated["owner_reason_contract"]["owner"] == "gate_clearing_batch"
    assert decorated["owner_reason_contract"]["codex_selected_action"] == "run_gate_clearing_batch"
    assert decorated["owner_route_attempt_protocol"]["dispatchable"] is True
    assert decorated["owner_route_attempt_protocol"]["route_to_attempt_contract"] == {
        "surface_kind": "mas_route_to_attempt_contract",
        "version": "mas-route-to-attempt-contract.v1",
        "when_dispatchable": "materialize_running_provider_attempt_or_executable_owner_action_or_typed_blocker",
        "allowed_current_execution_state_kinds": [
            "running_provider_attempt",
            "executable_owner_action",
            "typed_blocker",
        ],
        "forbidden_idle_states": [
            "parked_without_human_gate",
            "quest_marked_running_but_no_live_session",
            "stale_handoff_only",
            "downstream_bundle_only_idle",
        ],
        "human_gate_exception_requires_typed_blocker": True,
    }


def test_owner_route_registers_dm002_ai_reviewer_record_gate_consumption() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    decorated = protocol.decorate_owner_route(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "truth_epoch": "publication-eval::dm002::current-ai-reviewer-record",
            "runtime_health_epoch": "runtime-health::dm002::current",
            "source_fingerprint": "truth-source::dm002::current-ai-reviewer-record",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption",
            "current_owner": "mas_controller",
            "next_owner": "gate_clearing_batch",
            "owner_reason": "ai_reviewer_record_gate_consumption",
            "failure_signature": "ai_reviewer_record_gate_consumption",
            "allowed_actions": ["run_gate_clearing_batch"],
            "source_refs": {
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption",
            },
        }
    )

    assert decorated["owner_reason_contract"]["binding"] is False
    assert decorated["owner_reason_contract"]["owner"] == "gate_clearing_batch"
    assert decorated["owner_reason_contract"]["codex_selected_action"] == "run_gate_clearing_batch"
    assert decorated["owner_route_attempt_protocol"]["dispatchable"] is True


def test_owner_route_registers_paper_clean_room_rebuild_action() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    decorated = protocol.decorate_owner_route(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "truth_epoch": "truth-epoch::dm003::clean-room",
            "runtime_health_epoch": "runtime-health::dm003::clean-room",
            "source_fingerprint": "truth-source::dm003::clean-room",
            "work_unit_fingerprint": "paper-clean-room::dm003::current",
            "next_owner": "MedAutoScience",
            "owner_reason": "paper_clean_room_rebuild_required",
            "failure_signature": "paper_clean_room_rebuild_required",
            "allowed_actions": ["paper_clean_room_rebuild_required"],
            "idempotency_key": "owner-route::dm003::paper-clean-room",
            "source_refs": {
                "work_unit_id": "paper_clean_room_rebuild",
                "work_unit_fingerprint": "paper-clean-room::dm003::current",
                "runtime_health_epoch": "runtime-health::dm003::clean-room",
            },
        }
    )

    assert decorated["owner_reason_contract"]["binding"] is False
    assert decorated["owner_reason_contract"]["owner"] == "MedAutoScience"
    assert decorated["owner_reason_contract"]["codex_selected_action"] == "paper_clean_room_rebuild_required"
    assert decorated["owner_route_attempt_protocol"]["dispatchable"] is True


def test_owner_route_executable_identity_ignores_projection_counter_churn() -> None:
    owner_route_module = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_policy")

    status = {
        "study_truth_snapshot": {"truth_epoch": "truth-epoch-dm002"},
        "runtime_health_snapshot": {"runtime_health_epoch": "runtime-health-1"},
        "quest_status": "running",
        "active_run_id": "run-volatile-1",
    }
    action = {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "reason": "manuscript_story_surface_delta_missing",
        "work_unit_id": "dm002_current_story_surface_repair",
        "work_unit_fingerprint": "work-unit::dm002-story-surface",
        "projection_counter": 1,
        "read_model_revision": 41,
        "generated_at": "2026-05-31T01:00:00+00:00",
    }

    first = owner_route_module.build_owner_route(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        status=status,
        progress={"current_stage": "publication_revision", "paper_stage": "draft"},
        actions=[action],
        blocked_reason="manuscript_story_surface_delta_missing",
        next_owner="write",
        active_run_id="run-volatile-1",
    )
    second = owner_route_module.build_owner_route(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        status={**status, "active_run_id": "run-volatile-2"},
        progress={
            "current_stage": "publication_revision",
            "paper_stage": "draft",
            "projection_counter": 2,
        },
        actions=[
            {
                **action,
                "projection_counter": 2,
                "read_model_revision": 42,
                "generated_at": "2026-05-31T01:02:00+00:00",
            }
        ],
        blocked_reason="manuscript_story_surface_delta_missing",
        next_owner="write",
        active_run_id="run-volatile-2",
    )

    assert first["source_fingerprint"] == second["source_fingerprint"]
    assert first["trace_id"] == second["trace_id"]
    assert first["idempotency_key"] == second["idempotency_key"]
    assert first["source_refs"]["owner_route_currentness_basis"]["work_unit_fingerprint"] == (
        "work-unit::dm002-story-surface"
    )
    assert first["source_refs"]["currentness_digest_basis"]["stable_truth_digest"] == (
        second["source_refs"]["currentness_digest_basis"]["stable_truth_digest"]
    )
    assert first["source_refs"]["currentness_digest_basis"]["work_unit_digest"] == (
        second["source_refs"]["currentness_digest_basis"]["work_unit_digest"]
    )
    assert first["source_refs"]["currentness_digest_basis"]["volatile_projection_digest"] != (
        second["source_refs"]["currentness_digest_basis"]["volatile_projection_digest"]
    )
    assert first["source_refs"]["currentness_digest_basis"]["runtime_digest"] != (
        second["source_refs"]["currentness_digest_basis"]["runtime_digest"]
    )


def test_owner_route_normalization_preserves_embedded_currentness_work_unit_id() -> None:
    owner_route_module = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_policy")

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
            "owner_reason": "opl_stage_attempt_admission_required",
            "failure_signature": "opl_stage_attempt_admission_required",
            "allowed_actions": ["run_quality_repair_batch"],
            "idempotency_key": "owner-route::dm002::write::current-publication-hardening",
            "source_refs": {
                "owner_route_currentness_basis": {
                    "work_unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
                    "work_unit_fingerprint": "truth-snapshot::dm002-current-publication-hardening",
                    "truth_epoch": "truth-event-000017",
                    "runtime_health_epoch": "runtime-health-event-006191",
                    "owner_reason": "opl_stage_attempt_admission_required",
                }
            },
        }
    )

    basis = route["source_refs"]["owner_route_currentness_basis"]
    assert basis["work_unit_id"] == "dm002_current_publication_hardening_after_ai_reviewer_eval"
    assert "owner_reason" not in basis
    assert route["currentness_contract"]["missing_required_fields"] == []


def test_owner_route_currentness_basis_preserves_embedded_action_source_identity() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    basis = protocol.currentness_basis(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "source_refs": {
                "owner_route_currentness_basis": {
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "source_fingerprint": "publication-blockers::0915410f804b3697",
                    "action_fingerprint": "publication-blockers::0915410f804b3697",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                }
            },
        }
    )

    assert basis == {
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_fingerprint": "publication-blockers::0915410f804b3697",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
        "truth_epoch": "truth-event-current",
        "runtime_health_epoch": "runtime-health-current",
    }


def test_owner_route_protocol_normalizes_publication_eval_ref_as_source_eval_currentness() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    route = protocol.decorate_owner_route(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "truth_epoch": "truth-event-dm002-current-eval",
            "route_epoch": "truth-event-dm002-current-eval",
            "source_fingerprint": "truth-source-dm002-current-eval",
            "work_unit_fingerprint": "work-unit::dm002-current-ai-reviewer",
            "current_owner": "mas_controller",
            "next_owner": "ai_reviewer",
            "owner_reason": "domain_transition_ai_reviewer_re_eval",
            "failure_signature": "domain_transition_ai_reviewer_re_eval",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "idempotency_key": "owner-route::dm002::current-ai-reviewer",
            "source_refs": {
                "publication_eval_ref": {
                    "eval_id": "publication-eval::dm002::current-ai-reviewer",
                    "artifact_path": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                },
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "work-unit::dm002-current-ai-reviewer",
                "study_truth_epoch": "truth-event-dm002-current-eval",
            },
        }
    )

    basis = route["source_refs"]["owner_route_currentness_basis"]
    assert basis["source_eval_id"] == "publication-eval::dm002::current-ai-reviewer"
    assert route["currentness_contract"]["missing_required_fields"] == []
    assert route["owner_route_attempt_protocol"]["dispatchable"] is True


def test_owner_route_protocol_treats_unregistered_reason_as_diagnostic_when_route_is_complete() -> None:
    owner_route_module = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_policy")

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

    assert route["owner_reason_contract"]["binding"] is False
    assert route["owner_reason_contract"]["can_reject_codex_route"] is False
    assert route["owner_route_attempt_protocol"]["dispatchable"] is True
    assert route["allowed_actions"] == ["run_quality_repair_batch"]


def test_owner_callable_attempt_envelope_declares_domain_intent_and_authority_boundary() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

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

    envelope = protocol.owner_callable_attempt_envelope(
        dispatch={
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": owner_route,
            "allowed_write_surfaces": ["paper/draft.md", "paper/build/review_manuscript.md"],
            "forbidden_surfaces": ["artifacts/publication_eval/latest.json"],
            "required_closeout_packet": {
                "typed_closeout_is_optional_quality_projection": True,
                "free_text_closeout_accepted": False,
                "accepted_surface_kinds": ["stage_attempt_closeout_packet"],
                "completion_boundary": {"provider_completion_is_domain_ready": False},
            },
            "provider_completion": "succeeded",
            "running_worker": True,
        }
    )

    assert envelope["dispatchable"] is True
    assert envelope["search_boundaries"]["surface"] == "owner_callable_search_discipline.v1"
    assert "grep -R" in envelope["search_boundaries"]["forbidden_command_patterns"]
    assert "runtime/.ds/**" in envelope["tool_discipline"]["forbidden_path_globs"]
    assert envelope["authority_boundary"] == {
        "runtime_transport_ref": "opl-generated:family-runtime/current-control",
        "stage_run_ref_contract": "opl-generated:family-runtime/stage-run",
        "state_index_ref_contract": "opl-generated:state-index/source-ref",
        "transport_owner": "one-person-lab",
        "mas_can_write_runtime_transport": False,
        "mas_can_authorize_provider_attempt": False,
    }
    assert envelope["runtime_completion_guard"] == {
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_stage_state": False,
        "running_worker_is_stage_state": False,
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
    assert domain_intent["lifecycle_contract"]["stage_run_ref_contract"] == (
        "opl-generated:family-runtime/stage-run"
    )
    assert domain_intent["lifecycle_contract"]["state_index_ref_contract"] == (
        "opl-generated:state-index/source-ref"
    )
    assert domain_intent["missing_required_fields"] == []


def test_owner_callable_attempt_envelope_accepts_eval_bound_writer_route_without_runtime_health() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

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

    envelope = protocol.owner_callable_attempt_envelope(
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


def test_owner_callable_attempt_envelope_preallocates_closeout_first_contract() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    envelope = protocol.owner_callable_attempt_envelope(
        dispatch={
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "dispatch_ref": (
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/owner_callable_adapters/immutable/run_quality_repair_batch/abc123.json"
            ),
            "owner_route": {
                "surface": "domain_route_owner_route",
                "schema_version": 2,
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "route_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006254-fresh",
                "source_fingerprint": "truth-snapshot::current-methods-reporting",
                "work_unit_fingerprint": "work-unit::methods-reporting",
                "current_owner": "mas_controller",
                "next_owner": "write",
                "owner_reason": "opl_stage_attempt_admission_required",
                "failure_signature": "opl_stage_attempt_admission_required",
                "allowed_actions": ["run_quality_repair_batch"],
                "idempotency_key": "owner-route::dm002::methods-reporting",
                "source_refs": {
                    "work_unit_id": "dm002_current_manuscript_methods_reporting",
                    "work_unit_fingerprint": "work-unit::methods-reporting",
                    "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
                    "runtime_health_epoch": "runtime-health-event-006254-fresh",
                },
            },
        }
    )

    contract = envelope["closeout_first_contract"]
    assert contract["surface_kind"] == "mas_stage_outcome_opl_handoff_closeout_first_contract"
    assert contract["preallocated_closeout_ref"] == (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/owner_callable_adapter_receipt/<stage_attempt_id>.closeout.json"
    )
    assert contract["required_schema"] == {
        "surface_kind": "stage_attempt_closeout_packet",
        "schema_version": 1,
        "stage_id": "stage_outcome/opl-handoff",
        "required_ref_field": "closeout_refs",
        "minimum_closeout_refs": 0,
    }
    assert contract["required_paper_stage_log_field"] == "paper_stage_log"
    assert "evidence_refs" in contract["required_paper_stage_log_fields"]
    assert contract["evidence_refs_expectation"] == {
        "required_ref_field": "closeout_refs",
        "minimum_closeout_refs": 0,
        "missing_refs_closeout": "completed_with_quality_debt",
        "typed_blocker_reason": None,
    }
    assert contract["terminal_outcomes"] == [
        "typed_blocker",
        "owner_receipt",
        "human_gate",
        "progress_delta",
    ]
    assert envelope["required_closeout_packet"]["preallocated_closeout_ref"] == (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/owner_callable_adapter_receipt/<stage_attempt_id>.closeout.json"
    )


def test_owner_callable_attempt_envelope_fails_closed_without_domain_intent_required_fields() -> None:
    protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")

    envelope = protocol.owner_callable_attempt_envelope(
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
                "typed_closeout_is_optional_quality_projection": True,
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

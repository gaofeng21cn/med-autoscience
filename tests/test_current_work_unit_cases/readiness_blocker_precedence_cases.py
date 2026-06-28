from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_projects_next_forced_story_repair_over_stage_readiness_blocker_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": "manuscript_story_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "canonical manuscript story-surface delta or typed blocker:manuscript_story_surface_delta_missing",
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_projects_current_dpcc_gate_replay_over_stage_readiness_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "review_current_paper_delta",
            "target_surface": {
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "finalize"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_matching_current_control_repair_over_stage_readiness_blocker_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "manuscript_story_repair",
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                },
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "manuscript_story_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "owner_receipt_required": True,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "next_work_unit": "manuscript_story_repair",
                "action_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                "authority": "observability_only",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "manuscript_story_repair"
    assert work_unit["state"]["source"] == "opl_current_control_state_action_queue"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_preserves_readiness_blocker_over_mismatched_current_control_repair_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "manuscript_story_repair",
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "manuscript_story_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "stale_writer_repair",
                "next_work_unit": "stale_writer_repair",
                "authority": "observability_only",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["source"] == "stage_owner_answer"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_projects_matching_current_control_repair_over_prior_action_blocker_after_paper_delta() -> None:
    module = _module()

    for blocked_reason in (
        "domain_owner_action_dispatch_execution_count_zero",
        "no_selected_dispatch_for_requested_action_types",
        "stage_packet_superseded_by_current_consumed_domain_transition",
        "stale_stage_attempt_current_owner_route_superseded",
        "stale_stage_packet_current_owner_route_changed",
    ):
        work_unit = module.build_current_work_unit(
            progress={
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "current_stage": "publication_supervision",
                "progress_first_sprint_state": {"paper_progress_delta_counted": True},
                "next_forced_delta": {
                    "required_delta_kind": "review_current_paper_delta",
                    "reason": "paper_progress_delta_observed",
                    "work_unit_id": "manuscript_story_repair",
                    "owner_action": {
                        "next_owner": "write",
                        "work_unit_id": "manuscript_story_repair",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "owner_receipt_required": True,
                    },
                },
                "stage_kernel_projection": {
                    "current_owner_delta": {
                        "owner": "MedAutoScience",
                        "action": "complete_medical_paper_readiness_surface",
                        "reason": "medical_paper_readiness_missing",
                        "source_ref": (
                            "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
                        ),
                        "source_kind": "typed_blocker",
                        "latest_owner_answer_kind": "typed_blocker",
                        "hard_gate": {"state": "domain_owner_answer_recorded"},
                    }
                },
            },
            actions=[
                {
                    "source": "opl_current_control_state_action_queue",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "manuscript_story_repair",
                    "next_work_unit": "manuscript_story_repair",
                    "action_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                    "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                    "authority": "observability_only",
                }
            ],
            blocked_reason=blocked_reason,
            next_owner="write",
        )

        _assert_contract_shape(work_unit)
        assert work_unit["status"] == "executable_owner_action"
        assert work_unit["owner"] == "write"
        assert work_unit["action_type"] == "run_quality_repair_batch"
        assert work_unit["work_unit_id"] == "manuscript_story_repair"
        assert work_unit["state"]["source"] == "opl_current_control_state_action_queue"
        assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_gate_replay_when_stale_quality_repair_closeout_is_superseded() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "current_owner_action_or_typed_blocker",
                "reason": "publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "finalize",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "action_fingerprint": (
                    "study-progress-current-owner-ticket::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
                ),
                "work_unit_fingerprint": (
                    "study-progress-current-owner-ticket::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
                ),
                "authority": "observability_only",
            }
        ],
        typed_blocker={
            "blocker_type": "stale_stage_packet_current_owner_route_changed",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == (
        "stale_stage_packet_current_owner_route_changed"
    )


def test_current_work_unit_preserves_prior_action_blocker_over_mismatched_current_control_repair() -> None:
    module = _module()

    for blocked_reason in (
        "domain_owner_action_dispatch_execution_count_zero",
        "no_selected_dispatch_for_requested_action_types",
        "stage_packet_superseded_by_current_consumed_domain_transition",
    ):
        work_unit = module.build_current_work_unit(
            progress={
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "current_stage": "publication_supervision",
                "progress_first_sprint_state": {"paper_progress_delta_counted": True},
                "next_forced_delta": {
                    "required_delta_kind": "review_current_paper_delta",
                    "reason": "paper_progress_delta_observed",
                    "work_unit_id": "manuscript_story_repair",
                    "owner_action": {
                        "next_owner": "write",
                        "work_unit_id": "manuscript_story_repair",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "owner_receipt_required": True,
                    },
                },
            },
            actions=[
                {
                    "source": "opl_current_control_state_action_queue",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "stale_writer_repair",
                    "next_work_unit": "stale_writer_repair",
                    "authority": "observability_only",
                }
            ],
            blocked_reason=blocked_reason,
            next_owner="write",
        )

        _assert_contract_shape(work_unit)
        assert work_unit["status"] == "typed_blocker"
        assert work_unit["owner"] == "write"
        assert work_unit["work_unit_id"] is None
        assert work_unit["state"]["typed_blocker"]["blocker_type"] == blocked_reason


def test_current_work_unit_keeps_canonical_readiness_blocker_over_stale_readiness_queue() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "current_work_unit": {
                "status": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
        },
        actions=[
            {
                "source": "opl_current_control_state.action_queue",
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
            }
        ],
        typed_blocker={
            "blocker_type": "medical_paper_readiness_missing",
            "owner": "MedAutoScience",
            "work_unit_id": "complete_medical_paper_readiness_surface",
        },
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"
    assert work_unit["work_unit_id"] == "complete_medical_paper_readiness_surface"


def test_current_work_unit_does_not_turn_stage_kernel_readiness_blocker_into_self_authorized_action() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "medical_paper_readiness": {"overall_status": "not_ready"},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": "readiness-blocker::current",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_ignores_stale_terminal_closeout_for_new_current_identity() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "status": "blocked",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::old",
                    "source_eval_id": "publication-eval::old",
                    "typed_blocker": {
                        "blocker_type": "manuscript_story_surface_delta_missing",
                        "owner": "write",
                    },
                },
            },
        },
        actions=[
            {
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_fingerprint": "publication-blockers::new",
                "action_fingerprint": "publication-blockers::new",
                "source_eval_id": "publication-eval::new",
                "owner_route_currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::new",
                    "source_eval_id": "publication-eval::new",
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
                "target_surface": {
                    "next_work_unit": {
                        "unit_id": "medical_prose_write_repair",
                        "lane": "write",
                    }
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::new"
    assert "typed_blocker" not in work_unit["state"]

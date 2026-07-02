from __future__ import annotations

import importlib


def test_current_owner_action_projects_typed_blocker_resolution_next_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    action = module.build_canonical_owner_action_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.package.submission_minimal",
                "action_type": "consume_submission_ready_package_authority_or_human_gate",
                "allowed_actions": [
                    "consume_submission_ready_package_authority_or_human_gate"
                ],
                "action_id": "next-action-typed-blocker",
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "owner": "mas_authority_kernel",
                "outcome_ref": (
                    "/workspace/ops/medautoscience/"
                    "paper_mission_typed_blocker_resolution/003/"
                    "typed_blocker_resolution.json"
                ),
                "work_unit_id": "submission_authority_owner_verdict",
                "work_unit_fingerprint": "sha256:resolution",
                "paper_facing_delta": {
                    "delta_kind": "submission_authority_owner_verdict",
                    "paper_surface": "manuscript/current_package",
                },
                "accepted_answer_shape": {
                    "shape_kind": "owner_receipt_or_human_gate",
                    "accepted_statuses": ["owner_receipt", "human_gate", "route_back"],
                },
                "route_back": {
                    "route_back_to": "paper-mission inspect",
                    "expected_readback_fields": [
                        "next_action",
                        "current_executable_owner_action",
                    ],
                },
                "verification": {
                    "owner_readback_command": (
                        "paper-mission inspect --request-opl-runtime-readback "
                        "--study-id 003-dpcc-primary-care-phenotype-treatment-gap "
                        "--format json"
                    ),
                },
                "diagnostic_refs": [
                    {
                        "role": "typed_blocker_resolution",
                        "ref": "/workspace/ops/medautoscience/resolution.json",
                    }
                ],
            },
        }
    )

    assert action is not None
    assert action["surface_kind"] == "current_executable_owner_action"
    assert action["source"] == "paper_mission.next_action.owner_successor"
    assert action["next_owner"] == "mas_authority_kernel"
    assert action["action_type"] == "consume_submission_ready_package_authority_or_human_gate"
    assert action["allowed_actions"] == [
        "consume_submission_ready_package_authority_or_human_gate"
    ]
    assert action["work_unit_id"] == "submission_authority_owner_verdict"
    assert action["paper_facing_delta"]["delta_kind"] == (
        "submission_authority_owner_verdict"
    )
    assert action["accepted_answer_shape"]["shape_kind"] == (
        "owner_receipt_or_human_gate"
    )
    assert action["route_back"]["route_back_to"] == "paper-mission inspect"
    assert action["verification"]["owner_readback_command"].endswith("--format json")
    assert action["authority_boundary"]["can_write_owner_receipt"] is False
    assert action["authority_boundary"]["can_write_typed_blocker"] is False
    assert action["authority_boundary"]["can_write_human_gate"] is False


def test_current_owner_action_projects_submission_authority_owner_gate_surface() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    action = module.build_canonical_owner_action_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.package.submission_minimal",
                "action_type": "materialize_submission_ready_owner_verdict_or_human_gate",
                "allowed_actions": [
                    "materialize_submission_ready_owner_verdict_or_human_gate"
                ],
                "action_id": "next-action-submission-authority",
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "owner": "mas_authority_kernel",
                "outcome_ref": (
                    "/workspace/ops/medautoscience/"
                    "paper_mission_typed_blocker_resolution/003/"
                    "typed_blocker_resolution.json"
                ),
                "work_unit_id": "submission_ready_authority_closeout",
                "work_unit_fingerprint": "sha256:submission-authority",
            },
        }
    )

    assert action is not None
    assert action["required_delta_kind"] == "submission_authority_owner_gate_decision"
    assert action["target_surface"] == {
        "ref_kind": "mas_study_owner_gate_decision",
        "surface_ref": "study-owner-gate-decision",
        "source_ref": (
            "/workspace/ops/medautoscience/"
            "paper_mission_typed_blocker_resolution/003/"
            "typed_blocker_resolution.json"
        ),
    }
    assert action["target_surface_specificity"] == (
        "submission_authority_owner_gate_decision"
    )
    assert action["acceptance_refs"][-1] == "study_owner_gate_decision_ref"


def test_current_owner_action_retired_after_matching_submission_authority_gate_event() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "paper.package.submission_minimal",
            "action_type": "materialize_submission_ready_owner_verdict_or_human_gate",
            "allowed_actions": [
                "materialize_submission_ready_owner_verdict_or_human_gate"
            ],
            "action_id": "next-action-submission-authority",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "owner": "mas_authority_kernel",
            "work_unit_id": "submission_ready_authority_closeout",
            "work_unit_fingerprint": "ebf3e5131f6ae95c6ea25409",
        },
        "study_intervention_events": [
            {
                "event_id": "intervention-event-000007-ccabaeed588b377f",
                "intent": "owner_gate_decision",
                "recorded_at": "2026-06-30T02:32:16+00:00",
                "source": "codex",
                "payload": {
                    "owner_gate_kind": "submission_authority_gate",
                    "decision": "accept_submission_ready_authority_closeout",
                    "current_required_action": (
                        "materialize_submission_ready_owner_verdict_or_human_gate"
                    ),
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:6fdb7ea34759cefc9ff10aa9"
                    ),
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:6fdb7ea34759cefc9ff10aa9"
                    ),
                    "current_owner_identity": {
                        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                        "action_type": (
                            "materialize_submission_ready_owner_verdict_or_human_gate"
                        ),
                        "work_unit_id": "submission_ready_authority_closeout",
                        "work_unit_fingerprint": "ebf3e5131f6ae95c6ea25409",
                    },
                    "submission_authority_closeout": {
                        "status": "owner_gate_recorded",
                        "authority_materialized": False,
                        "writes_owner_receipt": False,
                        "writes_human_gate_authority": False,
                        "writes_current_package": False,
                        "writes_publication_eval": False,
                        "writes_controller_decision": False,
                    },
                },
            }
        ],
    }

    assert module.build_canonical_owner_action_projection(payload) is None
    readback = module.submission_authority_owner_gate_readback(
        payload,
        next_action=payload["next_action"],
    )

    assert readback is not None
    assert readback["status"] == "owner_gate_recorded"
    assert readback["duplicate_owner_gate_action_retired"] is True
    assert readback["authority_materialized"] is False
    assert readback["writes_owner_receipt"] is False
    assert readback["human_gate_ref"] == (
        "human_gate:owner-gate-decision:6fdb7ea34759cefc9ff10aa9"
    )


def test_submission_authority_gate_readback_projects_terminal_closeout_event() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "paper.package.submission_minimal",
            "action_type": "materialize_submission_ready_owner_verdict_or_human_gate",
            "allowed_actions": [
                "materialize_submission_ready_owner_verdict_or_human_gate"
            ],
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_id": "submission_ready_authority_closeout",
            "work_unit_fingerprint": "ebf3e5131f6ae95c6ea25409",
        },
        "study_intervention_events": [
            {
                "event_id": "intervention-event-000007-ccabaeed588b377f",
                "intent": "owner_gate_decision",
                "recorded_at": "2026-06-30T02:32:16+00:00",
                "source": "codex",
                "payload": {
                    "owner_gate_kind": "submission_authority_gate",
                    "decision": "accept_submission_ready_authority_closeout",
                    "current_required_action": (
                        "materialize_submission_ready_owner_verdict_or_human_gate"
                    ),
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:6fdb7ea34759cefc9ff10aa9"
                    ),
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:6fdb7ea34759cefc9ff10aa9"
                    ),
                    "current_owner_identity": {
                        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                        "action_type": (
                            "materialize_submission_ready_owner_verdict_or_human_gate"
                        ),
                        "work_unit_id": "submission_ready_authority_closeout",
                        "work_unit_fingerprint": "ebf3e5131f6ae95c6ea25409",
                    },
                    "submission_authority_closeout": {
                        "status": "owner_gate_recorded",
                        "authority_materialized": False,
                    },
                },
            },
            {
                "event_id": "intervention-event-000008-closeout",
                "intent": "submission_authority_closeout",
                "recorded_at": "2026-06-30T02:40:00+00:00",
                "source": "codex",
                "payload": {
                    "owner_gate_kind": "submission_authority_gate_closeout",
                    "decision": "accept_submission_ready_authority_closeout",
                    "current_required_action": (
                        "submission_ready_authority_closeout_recorded"
                    ),
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:6fdb7ea34759cefc9ff10aa9"
                    ),
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:6fdb7ea34759cefc9ff10aa9"
                    ),
                    "current_owner_identity": {
                        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                        "action_type": (
                            "materialize_submission_ready_owner_verdict_or_human_gate"
                        ),
                        "work_unit_id": "submission_ready_authority_closeout",
                        "work_unit_fingerprint": "ebf3e5131f6ae95c6ea25409",
                    },
                    "submission_authority_closeout": {
                        "status": "submission_ready_authority_closeout_recorded",
                        "authority_materialized": True,
                        "terminal_gate_materialized": True,
                        "submission_ready_claim_authorized": True,
                        "human_gate_required": False,
                        "writes_owner_receipt": False,
                        "writes_human_gate_authority": False,
                        "writes_current_package": False,
                        "writes_publication_eval": False,
                        "writes_controller_decision": False,
                    },
                },
            },
        ],
    }

    assert module.build_canonical_owner_action_projection(payload) is None
    readback = module.submission_authority_owner_gate_readback(
        payload,
        next_action=payload["next_action"],
    )

    assert readback is not None
    assert readback["status"] == "submission_ready_authority_closeout_recorded"
    assert readback["authority_materialized"] is True
    assert readback["terminal_gate_materialized"] is True
    assert readback["submission_ready_claim_authorized"] is True
    assert readback["next_legal_action"] == "submission_authority_or_human_gate_closed"


def test_submission_authority_gate_does_not_retire_unrelated_reviewer_route() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    payload = {
        "study_id": "obesity_multicenter_phenotype_atlas",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "runtime.opl_route",
            "action_kind": "submit_to_opl_runtime",
            "study_id": "obesity_multicenter_phenotype_atlas",
            "owner": "one-person-lab",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            "action_id": "next-action-reviewer-revision",
        },
        "study_intervention_events": [
            {
                "event_id": "intervention-event-000008-closeout",
                "intent": "submission_authority_closeout",
                "recorded_at": "2026-06-30T02:40:00+00:00",
                "source": "codex",
                "payload": {
                    "owner_gate_decision_ref": "owner-gate-decision:submission",
                    "submission_authority_closeout": {
                        "status": "submission_blocker_human_gate_recorded",
                        "authority_materialized": True,
                    },
                },
            }
        ],
    }

    assert module.submission_authority_owner_gate_readback(
        payload,
        next_action=payload["next_action"],
    ) is None


def test_submission_blocker_gate_does_not_retire_quality_repair_successor_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    payload = {
        "study_id": "obesity_multicenter_phenotype_atlas",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "paper.package.submission_minimal",
            "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
            "allowed_actions": [
                "classify_quality_blockers_or_materialize_degraded_handoff_gate"
            ],
            "study_id": "obesity_multicenter_phenotype_atlas",
            "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
            "work_unit_fingerprint": "7ca5e4d5e993dd9304f45400",
        },
        "study_intervention_events": [
            {
                "event_id": "intervention-event-000005-6184dcc4d3988930",
                "intent": "owner_gate_decision",
                "recorded_at": "2026-07-01T15:03:32+00:00",
                "source": "codex",
                "payload": {
                    "owner_gate_kind": "submission_authority_gate",
                    "decision": "request_submission_blocker_human_gate",
                    "current_required_action": (
                        "await_human_or_mas_authority_decision_for_submission_blocker"
                    ),
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:5e98e1fda062290f848cd795"
                    ),
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:5e98e1fda062290f848cd795"
                    ),
                    "current_owner_identity": {
                        "study_id": "obesity_multicenter_phenotype_atlas",
                        "action_type": (
                            "classify_quality_blockers_or_materialize_degraded_handoff_gate"
                        ),
                        "work_unit_id": (
                            "submission_blocker_degraded_handoff_or_quality_repair"
                        ),
                        "work_unit_fingerprint": "7ca5e4d5e993dd9304f45400",
                    },
                    "submission_authority_closeout": {
                        "status": "owner_gate_recorded",
                        "authority_materialized": False,
                        "writes_owner_receipt": False,
                        "writes_human_gate_authority": False,
                        "writes_current_package": False,
                        "writes_publication_eval": False,
                        "writes_controller_decision": False,
                    },
                },
            }
        ],
    }

    action = module.build_canonical_owner_action_projection(payload)
    assert action is not None
    assert action["required_delta_kind"] == "typed_blocker_resolution_owner_action"
    assert action["target_surface_specificity"] == "typed_blocker_resolution"
    assert action["work_unit_id"] == (
        "submission_blocker_degraded_handoff_or_quality_repair"
    )
    readback = module.submission_authority_owner_gate_readback(
        payload,
        next_action=payload["next_action"],
    )

    assert readback is None


def test_submission_blocker_gate_readback_ignores_stale_submission_ready_closeout() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    payload = {
        "study_id": "obesity_multicenter_phenotype_atlas",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "paper.package.submission_minimal",
            "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
            "allowed_actions": [
                "classify_quality_blockers_or_materialize_degraded_handoff_gate"
            ],
            "study_id": "obesity_multicenter_phenotype_atlas",
            "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
            "work_unit_fingerprint": "7ca5e4d5e993dd9304f45400",
        },
        "study_intervention_events": [
            {
                "event_id": "intervention-event-000004-closeout",
                "intent": "submission_authority_closeout",
                "recorded_at": "2026-07-01T10:35:46+00:00",
                "source": "cli:drive:mas-owner-materialization",
                "payload": {
                    "owner_gate_kind": "submission_authority_gate_closeout",
                    "decision": "accept_submission_ready_authority_closeout",
                    "current_required_action": "submission_ready_authority_closeout_recorded",
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:c232a4e55761e603577f3fd0"
                    ),
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:c232a4e55761e603577f3fd0"
                    ),
                    "current_owner_identity": {
                        "study_id": "obesity_multicenter_phenotype_atlas",
                        "action_type": (
                            "materialize_submission_ready_owner_verdict_or_human_gate"
                        ),
                        "work_unit_id": (
                            "submission_milestone_candidate::followthrough::followthrough-01"
                        ),
                        "work_unit_fingerprint": "older-submission-ready-fingerprint",
                    },
                    "submission_authority_closeout": {
                        "status": "submission_ready_authority_closeout_recorded",
                        "authority_materialized": True,
                    },
                },
            },
            {
                "event_id": "intervention-event-000005-6184dcc4d3988930",
                "intent": "owner_gate_decision",
                "recorded_at": "2026-07-01T15:03:32+00:00",
                "source": "codex",
                "payload": {
                    "owner_gate_kind": "submission_authority_gate",
                    "decision": "request_submission_blocker_human_gate",
                    "current_required_action": (
                        "await_human_or_mas_authority_decision_for_submission_blocker"
                    ),
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:5e98e1fda062290f848cd795"
                    ),
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:5e98e1fda062290f848cd795"
                    ),
                    "current_owner_identity": {
                        "study_id": "obesity_multicenter_phenotype_atlas",
                        "action_type": (
                            "classify_quality_blockers_or_materialize_degraded_handoff_gate"
                        ),
                        "work_unit_id": (
                            "submission_blocker_degraded_handoff_or_quality_repair"
                        ),
                        "work_unit_fingerprint": "7ca5e4d5e993dd9304f45400",
                    },
                    "submission_authority_closeout": {
                        "status": "owner_gate_recorded",
                        "authority_materialized": False,
                    },
                },
            },
        ],
    }

    readback = module.submission_authority_owner_gate_readback(
        payload,
        next_action=payload["next_action"],
    )

    assert readback is None

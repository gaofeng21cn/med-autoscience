from __future__ import annotations

from med_autoscience.controllers.domain_owner_action_dispatch_parts import (
    consumed_transition_currentness,
    fresh_progress_owner_actions,
)


def test_owner_action_dispatch_requires_source_eval_when_current_route_has_eval() -> None:
    route = {
        "next_owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "source_refs": {
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "work_unit_fingerprint": "sha256:current",
            "source_eval_id": "publication-eval::current",
            "owner_route_currentness_basis": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "work_unit_fingerprint": "sha256:current",
                "source_eval_id": "publication-eval::current",
            },
        },
    }
    dispatch_without_eval = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "action_type": "return_to_ai_reviewer_workflow",
        "next_executable_owner": "ai_reviewer",
        "owner_route": {
            "next_owner": "ai_reviewer",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "work_unit_fingerprint": "sha256:current",
                "owner_route_currentness_basis": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "work_unit_fingerprint": "sha256:current",
                },
            },
        },
    }

    assert not consumed_transition_currentness.owner_action_matches_dispatch(
        dispatch=dispatch_without_eval,
        route=route,
    )


def test_fresh_progress_current_owner_action_requires_shared_fingerprint() -> None:
    progress = {"study_id": "003-dpcc-primary-care-phenotype-treatment-gap"}
    action = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "action_type": "return_to_ai_reviewer_workflow",
        "next_owner": "ai_reviewer",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "work_unit_fingerprint": "sha256:current",
        "source_eval_id": "publication-eval::current",
    }
    dispatch_without_fingerprint = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "action_type": "return_to_ai_reviewer_workflow",
        "next_executable_owner": "ai_reviewer",
        "owner_route": {
            "next_owner": "ai_reviewer",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "source_eval_id": "publication-eval::current",
                "owner_route_currentness_basis": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "source_eval_id": "publication-eval::current",
                },
            },
        },
    }
    dispatch_with_fingerprint = {
        **dispatch_without_fingerprint,
        "owner_route": {
            **dispatch_without_fingerprint["owner_route"],
            "source_refs": {
                **dispatch_without_fingerprint["owner_route"]["source_refs"],
                "work_unit_fingerprint": "sha256:current",
                "owner_route_currentness_basis": {
                    **dispatch_without_fingerprint["owner_route"]["source_refs"][
                        "owner_route_currentness_basis"
                    ],
                    "work_unit_fingerprint": "sha256:current",
                },
            },
        },
    }

    assert not fresh_progress_owner_actions.current_owner_action_identity_matches_dispatch(
        progress=progress,
        action=action,
        dispatch=dispatch_without_fingerprint,
    )
    assert fresh_progress_owner_actions.current_owner_action_identity_matches_dispatch(
        progress=progress,
        action=action,
        dispatch=dispatch_with_fingerprint,
    )

from __future__ import annotations

import importlib


def _module():
    return importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_work_unit_action"
    )


def test_canonical_current_work_unit_action_rejects_readiness_typed_blocker_identity() -> None:
    action = _module().canonical_current_work_unit_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": (
                    "current-readiness-typed-blocker::"
                    "003-dpcc-primary-care-phenotype-treatment-gap::current"
                ),
                "currentness_basis": {
                    "source": "stage_owner_answer.typed_blocker",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": (
                        "current-readiness-typed-blocker::"
                        "003-dpcc-primary-care-phenotype-treatment-gap::current"
                    ),
                },
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    },
                },
            },
            "current_executable_owner_action": {},
            "owner_route": {
                "schema_version": 2,
                "next_owner": "MedAutoScience",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "source_refs": {
                    "owner_route_currentness_basis": {
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "work_unit_fingerprint": (
                            "current-readiness-typed-blocker::"
                            "003-dpcc-primary-care-phenotype-treatment-gap::current"
                        ),
                    }
                },
            },
        }
    )

    assert action is None

from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import (
    _clear_readiness_report,
    make_profile,
    write_study,
    write_text,
)

def test_study_soak_replay_case_captures_recent_003_and_004_failure_patterns() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_soak_replay")

    diabetes_case = module.build_study_soak_replay_case(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "bottlenecks": [{"bottleneck_id": "opl_runtime_owner_handoff_required"}],
            "runtime_failure_classification": {
                "blocker_class": "external_provider_account_blocker",
                "action_mode": "external_fix_required",
            },
        }
    )
    pituitary_case = module.build_study_soak_replay_case(
        {
            "study_id": "004-invasive-architecture",
            "bottlenecks": [{"bottleneck_id": "publication_gate_blocked"}],
            "gate_blocker_summary": {
                "current_blockers": ["submission_surface_qc_failure_present"],
                "next_work_unit": {"unit_id": "create_submission_minimal_package"},
            },
        }
    )

    assert diabetes_case["case_family"] == "opl_runtime_owner_handoff_hydration"
    assert diabetes_case["must_assert"] == [
        "external_runtime_blocker_is_not_retried_as_mas_work",
        "opl_current_control_state_hydrates_owner_handoff",
        "quality_gate_relaxation_allowed_false",
        "same_study_progress_truth_surfaces_present",
    ]
    assert pituitary_case["case_family"] == "same_line_quality_gate_fast_lane"
    assert "artifacts/controller/gate_clearing_batch/latest.json" in pituitary_case["required_truth_surfaces"]

from __future__ import annotations

from med_autoscience.controllers.agent_lab_medical_manuscript_quality.quality_boundary import (
    OWNER_CHAIN_REGRESSION_FAMILY,
)


def test_agent_lab_quality_suite_projects_owner_chain_regression_family() -> None:
    required = {
        "owner_chain_authority_monotonicity",
        "quality_repair_writer_handoff_currentness",
        "publication_work_unit_registry_consistency",
        "story_surface_delta_or_typed_blocker",
    }

    assert OWNER_CHAIN_REGRESSION_FAMILY["surface_kind"] == (
        "mas_agent_lab_owner_chain_regression_family"
    )
    assert required <= set(
        OWNER_CHAIN_REGRESSION_FAMILY["required_regression_targets"]
    )

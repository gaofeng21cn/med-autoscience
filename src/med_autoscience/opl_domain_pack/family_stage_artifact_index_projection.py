from __future__ import annotations

from typing import Any


STAGE_ARTIFACT_INDEX_PROJECTION_REF = (
    "med_autoscience.controllers.stage_artifact_index.build_stage_artifact_index"
)


def stage_artifact_index_projection_descriptor() -> dict[str, Any]:
    return {
        "surface_kind": "stage_artifact_index_projection_descriptor",
        "projection_surface_kind": "stage_artifact_index",
        "builder_ref": STAGE_ARTIFACT_INDEX_PROJECTION_REF,
        "payload_fields": [
            "surface_kind",
            "current_stage",
            "next_owner_action",
            "stale_platform_repairs",
            "stages",
        ],
        "consumer_surfaces": [
            "study_progress.stage_artifact_index",
            "mas_opl_runtime_workbench_projection.studies[*].stage_artifact_index",
            "mas_opl_workbench_reference_projection.lanes.stage_artifact_index",
        ],
        "authority_boundary": {
            "opl_role": "projection_consumer_only",
            "writes_mas_truth": False,
            "can_authorize_artifact_authority": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
    }


__all__ = [
    "STAGE_ARTIFACT_INDEX_PROJECTION_REF",
    "stage_artifact_index_projection_descriptor",
]

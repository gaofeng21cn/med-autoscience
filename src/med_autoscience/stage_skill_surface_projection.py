from __future__ import annotations

from typing import Any

from med_autoscience import stage_quality_contract


SURFACE_KIND = "stage_skill_surface_projection"
VERSION = "stage-skill-surface-projection.v1"
CONTRACT_REF = "med_autoscience.stage_skill_surface_projection.build_stage_skill_surface_projection"
REPO_PATH = "src/med_autoscience/stage_skill_surface_projection.py"
DEFAULT_STAGE_CARD_REF = "/product_entry_manifest/family_stage_control_plane/stages"


def build_stage_skill_surface_projection(*, stage_id: str | None = None) -> dict[str, Any]:
    stage_ref = DEFAULT_STAGE_CARD_REF
    if stage_id:
        stage_ref = f"{DEFAULT_STAGE_CARD_REF}/{stage_id}"
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "skill_locator": {
            "ref_kind": "json_pointer",
            "ref": "/skill_catalog/skills/0",
            "role": "mas_domain_skill_descriptor",
        },
        "freshness": {
            "freshness_kind": "product_entry_manifest_projection",
            "refresh_policy": stage_quality_contract.REFRESH_POLICY,
            "source_ref": REPO_PATH,
            "stale_if_projection_source_missing": True,
        },
        "quality_pack_refs": list(stage_quality_contract.REQUIRED_STAGE_QUALITY_PACK_IDS),
        "stage_card_ref": {
            "ref_kind": "json_pointer",
            "ref": stage_ref,
            "role": "family_stage_card_descriptor",
        },
        "authority_boundary": {
            "truth_owner": "MedAutoScience",
            "quality_owner": "MedAutoScience",
            "publication_readiness_owner": "MedAutoScience",
            "opl_role": "descriptor_ref_freshness_locator_consumer",
            "allowed_fields": [
                "skill_locator",
                "freshness",
                "quality_pack_refs",
                "stage_card_ref",
                "authority_boundary",
            ],
            "can_write_mas_truth": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_readiness": False,
            "can_close_paper": False,
        },
    }


__all__ = [
    "CONTRACT_REF",
    "DEFAULT_STAGE_CARD_REF",
    "REPO_PATH",
    "SURFACE_KIND",
    "VERSION",
    "build_stage_skill_surface_projection",
]

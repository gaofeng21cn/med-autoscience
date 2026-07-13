from __future__ import annotations

from med_autoscience.kdense_byok_catalog_surfaces import (
    build_kdense_byok_catalog_surfaces,
)


FORBIDDEN_AUTHORITY_FIELDS = {
    "can_write_study_truth",
    "can_write_source_truth",
    "can_write_paper_body",
    "can_write_artifact_body",
    "can_write_publication_eval",
    "can_write_controller_decisions",
    "can_write_current_package",
    "can_sign_owner_receipt",
    "can_create_typed_blocker",
    "can_create_human_gate",
    "can_authorize_source_readiness",
    "can_authorize_quality_verdict",
    "can_authorize_publication_readiness",
    "can_authorize_submission_readiness",
    "can_authorize_provider_attempt",
    "can_close_stage",
}


def _surfaces() -> dict[str, object]:
    return build_kdense_byok_catalog_surfaces(
        {
            "action_id": "kdense_catalog_projection",
            "action_type": "catalog_projection",
            "owner_route": {
                "owner": "MedAutoScience",
                "work_unit_id": "kdense_byok_catalog_surfaces",
            },
        }
    )


def test_kdense_catalog_surfaces_keep_source_counts_and_closed_authority() -> None:
    payload = _surfaces()
    surfaces = payload["surfaces"]

    assert payload["source_contract_ref"] == (
        "contracts/kdense_byok_external_intake.json"
    )
    assert payload["source_pin"]["kdense_byok_commit"] == (
        "dccc7ec4d034a00d7662eaabb3f5916bc3d00602"
    )
    assert payload["source_pin"]["scientific_agent_skills_commit"] == (
        "1e024ea8547ada12039edbe8197aaa959d97763f"
    )
    assert surfaces["stagecraft_recipe_catalog"]["template_count"] == 326
    assert surfaces["atlas_source_ref_catalog"]["source_ref_count"] == 229
    roles = surfaces["codex_specialist_roster"]["role_descriptors"]
    assert {"database-lookup", "paper-lookup", "scanpy", "pydeseq2"} <= {
        item["skill_id"] for item in roles
    }

    for output in (payload, *surfaces.values()):
        assert output["refs_only"] is True
        assert output["advisory_only"] is True
        assert output["nonblocking"] is True
        assert output["fail_open"] is True
        assert output["body_included"] is False
        assert output["allowed_writes"] == []
        authority = output["forbidden_authority"]
        assert set(authority) == FORBIDDEN_AUTHORITY_FIELDS
        assert not any(authority.values())


def test_kdense_catalog_surfaces_missing_dispatch_stays_fail_open() -> None:
    payload = build_kdense_byok_catalog_surfaces()

    assert payload["fail_open"] is True
    assert payload["diagnostic"] == {"reason": "missing_or_invalid_dispatch"}
    assert payload["current_owner_action"]["action_id"] is None

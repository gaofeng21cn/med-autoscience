from __future__ import annotations

from med_autoscience.kdense_byok_catalog_surfaces import (
    build_kdense_byok_catalog_surfaces,
)


def _surfaces() -> dict[str, object]:
    return build_kdense_byok_catalog_surfaces(
        {
            "action_id": "kdense_catalog_projection",
            "action_type": "catalog_projection",
            "owner_route": {
                "owner": "MedAutoScience",
                "work_unit_id": "kdense_byok_catalog_surfaces",
            },
            "refs": {"dispatch_path": "contracts/kdense_byok_external_intake.json"},
        }
    )


def test_kdense_catalog_surfaces_project_counts_and_source_pins() -> None:
    payload = _surfaces()
    surfaces = payload["surfaces"]
    stagecraft = surfaces["stagecraft_recipe_catalog"]
    atlas = surfaces["atlas_source_ref_catalog"]

    assert payload["source_contract_ref"] == "contracts/kdense_byok_external_intake.json"
    assert payload["source_pin"] == {
        "kdense_byok_repo": "https://github.com/K-Dense-AI/k-dense-byok",
        "kdense_byok_commit": "dccc7ec4d034a00d7662eaabb3f5916bc3d00602",
        "kdense_byok_release": "v0.6.0",
        "scientific_agent_skills_repo": (
            "https://github.com/K-Dense-AI/scientific-agent-skills"
        ),
        "scientific_agent_skills_commit": (
            "1e024ea8547ada12039edbe8197aaa959d97763f"
        ),
    }
    assert stagecraft["template_count"] == 326
    assert stagecraft["source_ref"] == (
        "external_repo:K-Dense-AI/k-dense-byok@"
        "dccc7ec4d034a00d7662eaabb3f5916bc3d00602/web/src/data/workflows.json"
    )
    assert stagecraft["execution_authority"] is False
    assert atlas["source_ref_count"] == 229
    assert atlas["source_ref"] == (
        "external_repo:K-Dense-AI/k-dense-byok@"
        "dccc7ec4d034a00d7662eaabb3f5916bc3d00602/web/src/data/databases.json"
    )
    assert atlas["endpoint_provenance"]["required_fields"] == [
        "endpoint",
        "params",
        "access_date",
        "count_reconciliation",
        "local_filters",
    ]
    assert atlas["access_date_required"] is True
    assert atlas["source_readiness_authority"] is False


def test_kdense_catalog_surfaces_project_allowlist_to_codex_roles() -> None:
    roster = _surfaces()["surfaces"]["codex_specialist_roster"]
    roles = roster["role_descriptors"]
    by_skill = {role["skill_id"]: role for role in roles}

    assert roster["upstream_specialist_count"] == 21
    assert roster["allowlist_source_count"] == 149
    assert roster["role_descriptor_count"] == len(roles)
    assert len(roles) >= 16
    assert {
        "database-lookup",
        "paper-lookup",
        "citation-management",
        "scanpy",
        "pydeseq2",
    } <= set(by_skill)
    assert by_skill["database-lookup"] == {
        "role_id": "codex-specialist:database-lookup",
        "skill_id": "database-lookup",
        "source_ref": (
            "external_repo:K-Dense-AI/scientific-agent-skills@"
            "1e024ea8547ada12039edbe8197aaa959d97763f/skills/"
            "database-lookup/SKILL.md"
        ),
        "module_id": "mas-scholar-skills.data",
        "owner_surface": "OPL Atlas / OPL Connect",
        "use_when": "named_public_database_lookup_gap",
        "completion_gate": (
            "database_retrieval_contract_ref_and_endpoint_provenance_ref"
        ),
        "independent_invocation_required": True,
        "reviewer_receipt_candidate_only": True,
        "body_included": False,
    }
    assert all(role["independent_invocation_required"] is True for role in roles)
    assert all(role["reviewer_receipt_candidate_only"] is True for role in roles)


def test_kdense_catalog_surfaces_are_refs_only_non_authority_outputs() -> None:
    payload = _surfaces()
    outputs = [payload, *payload["surfaces"].values()]

    for output in outputs:
        assert output["refs_only"] is True
        assert output["advisory_only"] is True
        assert output["nonblocking"] is True
        assert output["fail_open"] is True
        assert output["body_included"] is False
        assert output["allowed_writes"] == []
        false_authority = [
            value
            for value in output["forbidden_authority"].values()
            if isinstance(value, bool)
        ]
        assert false_authority
        assert not any(false_authority)

    preview = payload["surfaces"]["workspace_artifact_preview"]
    assert preview["source_refs"] == [
        "web/src/components/file-preview-panel.tsx",
        "web/src/components/latex-editor.tsx",
        "web/src/components/tool-activity.tsx",
    ]
    assert preview["manifest_ref_required"] is True
    assert preview["checksum_ref_required"] is True
    assert preview["preview_ref_required"] is True
    assert preview["artifact_authority"] is False


def test_kdense_catalog_surfaces_missing_dispatch_stays_fail_open() -> None:
    payload = build_kdense_byok_catalog_surfaces()

    assert payload["fail_open"] is True
    assert payload["diagnostic"] == {"reason": "missing_or_invalid_dispatch"}
    assert payload["current_owner_action"] == {
        "action_type": None,
        "action_id": None,
        "owner": None,
        "work_unit_id": None,
        "work_unit_fingerprint": None,
        "dispatch_path": None,
    }
    assert all(surface["fail_open"] is True for surface in payload["surfaces"].values())

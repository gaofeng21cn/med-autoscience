from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from med_autoscience.authority_handlers._generation_manifest import (
    build_review_input_snapshot_materialization_request,
    review_scope_member_projection,
)

ROOT = Path(__file__).resolve().parents[1]


def _display_case(
    authority_records: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    paper_request = authority_records.paper_request(manifest_version=2)
    manifest = paper_request["generation_manifest"]
    scope = next(
        item for item in manifest["review_scopes"] if item["review_lane"] == "display"
    )
    source_refs = {
        item["member_id"]: f"file:///workspace/review-inputs/{item['member_id']}"
        for item in reversed(scope["reviewed_members"])
    }
    return paper_request, scope, source_refs


def test_build_snapshot_request_projects_exact_scope_in_canonical_order(
    authority_records: Any,
) -> None:
    paper_request, scope, source_refs = _display_case(authority_records)

    request = build_review_input_snapshot_materialization_request(
        generation_manifest=paper_request["generation_manifest"],
        review_lane=" display ",
        generation_ref=f" {paper_request['generation_manifest_ref']['ref']} ",
        workspace_root=" /workspace ",
        source_refs_by_member_id=source_refs,
        authority_issuer=authority_records.review_snapshot_authority_issuer(),
    )

    expected_members = review_scope_member_projection(scope["reviewed_members"])
    request_members = [
        {
            **item,
            "owner_ref": next(
                member["ref"]
                for member in scope["reviewed_members"]
                if member["member_id"] == item["member_id"]
            ),
            "source_ref": source_refs[item["member_id"]],
        }
        for item in expected_members
    ]
    authority_record = {
        "surface_kind": "mas_review_input_snapshot_authority",
        "schema_version": 2,
        "issuer": authority_records.review_snapshot_authority_issuer(),
        "generation_ref": paper_request["generation_manifest_ref"]["ref"],
        "review_lane": "display",
        "scope_policy_id": "mas_review_scope_dependency_map",
        "scope_policy_version": 2,
        "review_scope_sha256": scope["review_scope_sha256"],
        "members": [
            {key: value for key, value in item.items() if key != "source_ref"}
            for item in request_members
        ],
    }
    authority_sha256 = authority_records.fingerprint(authority_record)
    assert request == {
        "surface_kind": "opl_reviewer_input_snapshot_materialization_request",
        "schema_version": 1,
        "generation_ref": paper_request["generation_manifest_ref"]["ref"],
        "review_lane": "display",
        "review_scope_sha256": scope["review_scope_sha256"],
        "workspace_root": "/workspace",
        "members": request_members,
        "mas_authority_record_ref": {
            "kind": "mas_review_input_snapshot_authority",
            "ref": (
                "mas-review-input-snapshot-authority:"
                f"{authority_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(authority_records.canonical_bytes(authority_record)),
            "sha256": authority_sha256,
        },
        "mas_authority_record": authority_record,
    }
    assert [item["member_id"] for item in request["members"]] == [
        item["member_id"] for item in expected_members
    ]
    schema = json.loads(
        (
            ROOT
            / "contracts/schemas/v2/mas-review-input-snapshot-authority-v2.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(request["mas_authority_record"])

    moved_sources = {
        member_id: source_ref.replace("/review-inputs/", "/moved/")
        for member_id, source_ref in source_refs.items()
    }
    moved_request = build_review_input_snapshot_materialization_request(
        generation_manifest=paper_request["generation_manifest"],
        review_lane="display",
        generation_ref=paper_request["generation_manifest_ref"]["ref"],
        workspace_root="/workspace",
        source_refs_by_member_id=moved_sources,
        authority_issuer=authority_records.review_snapshot_authority_issuer(),
    )
    assert moved_request["review_scope_sha256"] == request["review_scope_sha256"]
    assert moved_request["mas_authority_record"] == request["mas_authority_record"]
    assert moved_request["mas_authority_record_ref"] == request[
        "mas_authority_record_ref"
    ]
    assert [
        {key: value for key, value in member.items() if key != "source_ref"}
        for member in moved_request["members"]
    ] == [
        {key: value for key, value in member.items() if key != "source_ref"}
        for member in request["members"]
    ]


def test_exact_byte_snapshot_request_keeps_owner_ref_separate_from_source_locator(
    authority_records: Any,
) -> None:
    paper_request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
    )
    scope = next(
        item
        for item in paper_request["generation_manifest"]["review_scopes"]
        if item["review_lane"] == "exact_byte_package"
    )
    source_refs = {
        item["member_id"]: f"file:///workspace/materialized/{item['member_id']}"
        for item in scope["reviewed_members"]
    }

    request = build_review_input_snapshot_materialization_request(
        generation_manifest=paper_request["generation_manifest"],
        review_lane="exact_byte_package",
        generation_ref=paper_request["generation_manifest_ref"]["ref"],
        workspace_root="/workspace",
        source_refs_by_member_id=source_refs,
        authority_issuer=authority_records.review_snapshot_authority_issuer(),
    )

    owner_refs = {
        item["member_id"]: item["ref"] for item in scope["reviewed_members"]
    }
    assert request["review_scope_sha256"] == scope["review_scope_sha256"]
    assert request["members"]
    for member in request["members"]:
        assert member["owner_ref"] == owner_refs[member["member_id"]]
        assert member["source_ref"] == source_refs[member["member_id"]]
        assert member["owner_ref"] != member["source_ref"]


@pytest.mark.parametrize("mapping_case", ["missing", "extra", "wrong_identity"])
def test_build_snapshot_request_rejects_non_exact_source_member_mapping(
    authority_records: Any,
    mapping_case: str,
) -> None:
    paper_request, _, source_refs = _display_case(authority_records)
    changed = dict(source_refs)
    member_id = next(iter(changed))
    source_ref = changed.pop(member_id)
    if mapping_case == "extra":
        changed[member_id] = source_ref
        changed["unknown-member"] = "file:///workspace/unknown-member"
    elif mapping_case == "wrong_identity":
        changed["wrong-member"] = source_ref

    with pytest.raises(ValueError, match="must exactly match the MAS-owned review scope"):
        build_review_input_snapshot_materialization_request(
            generation_manifest=paper_request["generation_manifest"],
            review_lane="display",
            generation_ref=paper_request["generation_manifest_ref"]["ref"],
            workspace_root="/workspace",
            source_refs_by_member_id=changed,
            authority_issuer=authority_records.review_snapshot_authority_issuer(),
        )


def test_build_snapshot_request_rejects_wrong_manifest_or_locator_shape(
    authority_records: Any,
) -> None:
    paper_request, _, source_refs = _display_case(authority_records)

    v1_request = authority_records.paper_request(manifest_version=1)
    with pytest.raises(ValueError, match="schema_version must be integer 2"):
        build_review_input_snapshot_materialization_request(
            generation_manifest=v1_request["generation_manifest"],
            review_lane="display",
            generation_ref=v1_request["generation_manifest_ref"]["ref"],
            workspace_root="/workspace",
            source_refs_by_member_id=source_refs,
            authority_issuer=authority_records.review_snapshot_authority_issuer(),
        )

    analysis_request = authority_records.paper_request(
        scope="analysis_generation",
        stage_id="bounded_analysis_campaign",
        manifest_version=2,
    )
    with pytest.raises(ValueError, match="is not declared"):
        build_review_input_snapshot_materialization_request(
            generation_manifest=analysis_request["generation_manifest"],
            review_lane="display",
            generation_ref=analysis_request["generation_manifest_ref"]["ref"],
            workspace_root="/workspace",
            source_refs_by_member_id={},
            authority_issuer=authority_records.review_snapshot_authority_issuer(),
        )

    blank_ref_mapping = dict(source_refs)
    blank_ref_mapping[next(iter(blank_ref_mapping))] = " "
    with pytest.raises(ValueError, match="must be a non-empty string"):
        build_review_input_snapshot_materialization_request(
            generation_manifest=paper_request["generation_manifest"],
            review_lane="display",
            generation_ref=paper_request["generation_manifest_ref"]["ref"],
            workspace_root="/workspace",
            source_refs_by_member_id=blank_ref_mapping,
            authority_issuer=authority_records.review_snapshot_authority_issuer(),
        )

    member_id = next(iter(source_refs))
    duplicate_normalized_mapping = {
        **source_refs,
        f" {member_id} ": "file:///workspace/duplicate-normalized-member",
    }
    with pytest.raises(ValueError, match="duplicate normalized member_id"):
        build_review_input_snapshot_materialization_request(
            generation_manifest=paper_request["generation_manifest"],
            review_lane="display",
            generation_ref=paper_request["generation_manifest_ref"]["ref"],
            workspace_root="/workspace",
            source_refs_by_member_id=duplicate_normalized_mapping,
            authority_issuer=authority_records.review_snapshot_authority_issuer(),
        )


def test_build_snapshot_request_rejects_unbound_authority_issuer(
    authority_records: Any,
) -> None:
    paper_request, _, source_refs = _display_case(authority_records)
    invalid_issuer = authority_records.review_snapshot_authority_issuer()
    invalid_issuer["package_id"] = "other-agent"

    with pytest.raises(ValueError, match="authority_issuer.package_id must be mas"):
        build_review_input_snapshot_materialization_request(
            generation_manifest=paper_request["generation_manifest"],
            review_lane="display",
            generation_ref=paper_request["generation_manifest_ref"]["ref"],
            workspace_root="/workspace",
            source_refs_by_member_id=source_refs,
            authority_issuer=invalid_issuer,
        )

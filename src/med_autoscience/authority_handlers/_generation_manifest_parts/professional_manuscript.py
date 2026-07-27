"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)

from .constants import (
    FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL,
)
from .professional_skill import (
    _normalize_professional_invocation_ref,
    _normalize_professional_skill_artifact_binding,
    _normalize_professional_skill_input_bindings,
    _normalize_professional_skill_invocation,
)
from .professional_table import (
    _normalize_table_quality_application,
)

def _normalize_professional_skill_invocations(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact_by_member_id = {
        item["member_id"]: item for item in artifacts if "member_id" in item
    }
    invocations = []
    for index, item in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        if mapping(item, item_field).get("surface_kind") == (
            "mas_professional_manuscript_skill_invocation_candidate"
        ):
            normalized = _normalize_professional_manuscript_skill_invocation(
                item,
                item_field,
                artifact_by_member_id=artifact_by_member_id,
            )
        else:
            normalized = _normalize_professional_skill_invocation(
                item,
                item_field,
                artifact_by_member_id=artifact_by_member_id,
            )
        invocations.append(normalized)
    identities = [
        (item["surface_kind"], item.get("figure_id"), item["skill_id"])
        for item in invocations
    ]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate target/skill receipts")
    member_owner: dict[str, str] = {}
    for invocation in invocations:
        if "figure_id" not in invocation:
            continue
        for binding in invocation["output_artifact_bindings"]:
            member_id = binding["member_id"]
            prior_figure = member_owner.setdefault(member_id, invocation["figure_id"])
            if prior_figure != invocation["figure_id"]:
                raise RequestShapeError(
                    f"{field} binds figure artifact {member_id} to multiple figures"
                )
    invocations.sort(
        key=lambda item: (
            item["surface_kind"],
            item.get("figure_id", ""),
            item["skill_id"],
        )
    )
    return invocations


def _normalize_professional_manuscript_skill_invocation(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    keys = {
        "surface_kind",
        "schema_version",
        "receipt_id",
        "skill_id",
        "package_id",
        "package_version",
        "package_source_ref",
        "package_source_sha256",
        "skill_source_ref",
        "skill_source_sha256",
        "invocation_id",
        "input_contract_ref",
        "input_sha256",
        "consumed_rule_refs",
        "output_artifact_bindings",
        "template_substitution",
        "status",
        "refs_only",
        "authority",
        "publication_ready",
    }
    semantic_fields = {
        "semantic_policy_id",
        "semantic_validator_id",
        "semantic_policy_ref",
        "semantic_candidate_ref",
    }
    has_semantic_binding = any(field_name in payload for field_name in semantic_fields)
    if schema_version == 2:
        keys.update({"invocation_ref", "receipt_ref", "input_artifact_bindings"})
        if has_semantic_binding:
            keys.update(
                semantic_fields
            )
    if (
        payload.get("skill_id") == "medical-table-design"
        and "table_quality_application" in payload
    ):
        keys.add("table_quality_application")
    exact_keys(payload, keys, field)
    skill_id = enum_text(
        payload.get("skill_id"),
        f"{field}.skill_id",
        set(PROFESSIONAL_MANUSCRIPT_SKILL_ROLES),
    )
    if payload.get("surface_kind") != (
        "mas_professional_manuscript_skill_invocation_candidate"
    ):
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("package_id") != "mas-scholar-skills":
        raise RequestShapeError(f"{field}.package_id must be mas-scholar-skills")
    if payload.get("template_substitution") is not False:
        raise RequestShapeError(f"{field}.template_substitution must be false")
    if payload.get("status") != "completed" or payload.get("refs_only") is not True:
        raise RequestShapeError(f"{field} must be completed refs-only evidence")
    if (
        payload.get("authority") is not False
        or payload.get("publication_ready") is not False
    ):
        raise RequestShapeError(
            f"{field} cannot grant authority or publication readiness"
        )
    bindings = [
        _normalize_professional_skill_artifact_binding(
            item,
            f"{field}.output_artifact_bindings[{index}]",
            artifact_by_member_id=artifact_by_member_id,
            allowed_roles=PROFESSIONAL_MANUSCRIPT_SKILL_ROLES[skill_id],
        )
        for index, item in enumerate(
            sequence(
                payload.get("output_artifact_bindings"),
                f"{field}.output_artifact_bindings",
            )
        )
    ]
    if not bindings:
        raise RequestShapeError(f"{field}.output_artifact_bindings must not be empty")
    rules = text_list(payload.get("consumed_rule_refs"), f"{field}.consumed_rule_refs")
    if not rules:
        raise RequestShapeError(f"{field}.consumed_rule_refs must not be empty")
    normalized = {
        "surface_kind": "mas_professional_manuscript_skill_invocation_candidate",
        "schema_version": schema_version,
        "receipt_id": text(payload.get("receipt_id"), f"{field}.receipt_id"),
        "skill_id": skill_id,
        "package_id": "mas-scholar-skills",
        "package_version": text(
            payload.get("package_version"), f"{field}.package_version"
        ),
        "package_source_ref": text(
            payload.get("package_source_ref"), f"{field}.package_source_ref"
        ),
        "package_source_sha256": sha256(
            payload.get("package_source_sha256"), f"{field}.package_source_sha256"
        ),
        "skill_source_ref": text(
            payload.get("skill_source_ref"), f"{field}.skill_source_ref"
        ),
        "skill_source_sha256": sha256(
            payload.get("skill_source_sha256"), f"{field}.skill_source_sha256"
        ),
        "invocation_id": text(payload.get("invocation_id"), f"{field}.invocation_id"),
        "input_contract_ref": text(
            payload.get("input_contract_ref"), f"{field}.input_contract_ref"
        ),
        "input_sha256": sha256(payload.get("input_sha256"), f"{field}.input_sha256"),
        "consumed_rule_refs": rules,
        "output_artifact_bindings": sorted(
            bindings, key=lambda item: item["member_id"]
        ),
        "template_substitution": False,
        "status": "completed",
        "refs_only": True,
        "authority": False,
        "publication_ready": False,
    }
    if has_semantic_binding and (
        schema_version != 2 or skill_id not in SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL
    ):
        raise RequestShapeError(
            f"{field} semantic fields require a current Scholar policy-bearing invocation"
        )
    if has_semantic_binding:
        policy = SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL[skill_id]
        if payload.get("semantic_policy_id") != policy["policy_id"]:
            raise RequestShapeError(
                f"{field}.semantic_policy_id must bind the current Scholar policy"
            )
        if payload.get("semantic_validator_id") != policy["validator_id"]:
            raise RequestShapeError(
                f"{field}.semantic_validator_id must bind the current Scholar validator"
            )
        required_rules = {
            policy["policy_id"],
            f"validator:{policy['validator_id']}",
        }
        if not required_rules.issubset(set(rules)):
            raise RequestShapeError(
                f"{field}.consumed_rule_refs must consume the exact semantic policy and validator"
            )
        semantic_candidate_ref = _exact_ref(
            payload.get("semantic_candidate_ref"),
            f"{field}.semantic_candidate_ref",
            "mas_artifact",
        )
        expected_role = FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD[
            policy["candidate_ref_field"]
        ]
        if not any(
            binding["role"] == expected_role
            and all(
                semantic_candidate_ref[key] == binding[key]
                for key in ("ref", "size_bytes", "sha256")
            )
            for binding in bindings
        ):
            raise RequestShapeError(
                f"{field}.semantic_candidate_ref must bind the current output candidate member"
            )
        normalized.update(
            {
                "semantic_policy_id": policy["policy_id"],
                "semantic_validator_id": policy["validator_id"],
                "semantic_policy_ref": _exact_ref(
                    payload.get("semantic_policy_ref"),
                    f"{field}.semantic_policy_ref",
                    "scholarskills_semantic_policy",
                ),
                "semantic_candidate_ref": semantic_candidate_ref,
            }
        )
    if skill_id == "medical-table-design" and payload.get(
        "table_quality_application"
    ) is not None:
        normalized["table_quality_application"] = (
            _normalize_table_quality_application(
                payload["table_quality_application"],
                f"{field}.table_quality_application",
            )
        )
    if schema_version == 2:
        receipt_ref = _exact_ref(
            payload.get("receipt_ref"),
            f"{field}.receipt_ref",
            "scholarskills_professional_skill_receipt",
        )
        if normalized["receipt_id"] != receipt_ref["ref"]:
            raise RequestShapeError(f"{field}.receipt_id must equal receipt_ref.ref")
        input_bindings = _normalize_professional_skill_input_bindings(
            payload.get("input_artifact_bindings"),
            f"{field}.input_artifact_bindings",
            artifact_by_member_id=artifact_by_member_id,
        )
        normalized["receipt_ref"] = receipt_ref
        normalized["input_artifact_bindings"] = input_bindings
        if has_semantic_binding:
            semantic_receipt_core = {
                "skill_id": skill_id,
                "skill_source_sha256": normalized["skill_source_sha256"],
                "input_artifact_bindings": input_bindings,
                "output_artifact_bindings": normalized[
                    "output_artifact_bindings"
                ],
                "consumed_rule_refs": normalized["consumed_rule_refs"],
                "semantic_policy_id": normalized["semantic_policy_id"],
                "semantic_validator_id": normalized["semantic_validator_id"],
                "semantic_policy_ref": normalized["semantic_policy_ref"],
                "semantic_candidate_ref": normalized[
                    "semantic_candidate_ref"
                ],
                "status": "completed",
            }
            receipt_fingerprint = fingerprint(semantic_receipt_core)
            expected_receipt_ref = {
                "kind": "scholarskills_professional_skill_receipt",
                "ref": (
                    "scholarskills-professional-skill-receipt:"
                    f"{receipt_fingerprint.removeprefix('sha256:')}"
                ),
                "size_bytes": len(canonical_json_bytes(semantic_receipt_core)),
                "sha256": receipt_fingerprint,
            }
            if receipt_ref != expected_receipt_ref:
                raise RequestShapeError(
                    f"{field}.receipt_ref does not bind the Scholar v2 semantic receipt bytes"
                )
        normalized["invocation_ref"] = _normalize_professional_invocation_ref(
            payload.get("invocation_ref"),
            f"{field}.invocation_ref",
            invocation_core=normalized,
        )
    return normalized

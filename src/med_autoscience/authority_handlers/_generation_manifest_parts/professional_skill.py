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



def _normalize_professional_skill_invocation(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    skill_id = enum_text(
        payload.get("skill_id"),
        f"{field}.skill_id",
        {
            "medical-figure-design",
            "medical-figure-style",
            "medical-figure-composer",
        },
    )
    keys = {
        "surface_kind",
        "schema_version",
        "receipt_id",
        "figure_id",
        "figure_kind",
        "composition_mode",
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
        "status",
        "refs_only",
        "authority",
        "publication_ready",
    }
    if schema_version == 2:
        keys.update({"invocation_ref", "receipt_ref", "input_artifact_bindings"})
    if skill_id == "medical-figure-design":
        keys.update({"template_usage", "figure_text_policy"})
    exact_keys(payload, keys, field)
    if (
        payload.get("surface_kind")
        != "mas_professional_figure_skill_invocation_candidate"
    ):
        raise RequestShapeError(
            f"{field}.surface_kind must be "
            "mas_professional_figure_skill_invocation_candidate"
        )
    if payload.get("package_id") != "mas-scholar-skills":
        raise RequestShapeError(f"{field}.package_id must be mas-scholar-skills")
    if payload.get("status") != "completed":
        raise RequestShapeError(f"{field}.status must be completed")
    if payload.get("refs_only") is not True:
        raise RequestShapeError(f"{field}.refs_only must be true")
    for key in ("authority", "publication_ready"):
        if payload.get(key) is not False:
            raise RequestShapeError(f"{field}.{key} must be false")
    consumed_rule_refs = text_list(
        payload.get("consumed_rule_refs"), f"{field}.consumed_rule_refs"
    )
    if not consumed_rule_refs:
        raise RequestShapeError(f"{field}.consumed_rule_refs must not be empty")
    output_bindings = [
        _normalize_professional_skill_artifact_binding(
            item,
            f"{field}.output_artifact_bindings[{index}]",
            artifact_by_member_id=artifact_by_member_id,
        )
        for index, item in enumerate(
            sequence(
                payload.get("output_artifact_bindings"),
                f"{field}.output_artifact_bindings",
            )
        )
    ]
    if not output_bindings:
        raise RequestShapeError(
            f"{field}.output_artifact_bindings must bind at least one final figure artifact"
        )
    member_ids = [item["member_id"] for item in output_bindings]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(
            f"{field}.output_artifact_bindings contains duplicate members"
        )
    normalized = {
        "surface_kind": "mas_professional_figure_skill_invocation_candidate",
        "schema_version": schema_version,
        "receipt_id": text(payload.get("receipt_id"), f"{field}.receipt_id"),
        "figure_id": text(payload.get("figure_id"), f"{field}.figure_id"),
        "figure_kind": enum_text(
            payload.get("figure_kind"),
            f"{field}.figure_kind",
            {"evidence_figure", "graphical_abstract"},
        ),
        "composition_mode": enum_text(
            payload.get("composition_mode"),
            f"{field}.composition_mode",
            {"single_canvas_direct", "assembled_panels"},
        ),
        "skill_id": skill_id,
        "package_id": "mas-scholar-skills",
        "package_version": text(
            payload.get("package_version"), f"{field}.package_version"
        ),
        "package_source_ref": text(
            payload.get("package_source_ref"), f"{field}.package_source_ref"
        ),
        "package_source_sha256": sha256(
            payload.get("package_source_sha256"),
            f"{field}.package_source_sha256",
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
        "consumed_rule_refs": consumed_rule_refs,
        "output_artifact_bindings": sorted(
            output_bindings, key=lambda item: item["member_id"]
        ),
        "status": "completed",
        "refs_only": True,
        "authority": False,
        "publication_ready": False,
    }
    if skill_id == "medical-figure-design":
        normalized["template_usage"] = _normalize_figure_template_usage(
            payload.get("template_usage"), f"{field}.template_usage"
        )
        normalized["figure_text_policy"] = _normalize_figure_text_policy(
            payload.get("figure_text_policy"),
            f"{field}.figure_text_policy",
            figure_kind=normalized["figure_kind"],
        )
    if schema_version == 2:
        receipt_ref = _exact_ref(
            payload.get("receipt_ref"),
            f"{field}.receipt_ref",
            "scholarskills_professional_skill_receipt",
        )
        if normalized["receipt_id"] != receipt_ref["ref"]:
            raise RequestShapeError(f"{field}.receipt_id must equal receipt_ref.ref")
        normalized["receipt_ref"] = receipt_ref
        normalized["input_artifact_bindings"] = (
            _normalize_professional_skill_input_bindings(
                payload.get("input_artifact_bindings"),
                f"{field}.input_artifact_bindings",
                artifact_by_member_id=artifact_by_member_id,
            )
        )
        normalized["invocation_ref"] = _normalize_professional_invocation_ref(
            payload.get("invocation_ref"),
            f"{field}.invocation_ref",
            invocation_core=normalized,
        )
    return normalized


def _normalize_professional_skill_artifact_binding(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
    allowed_roles: frozenset[str] = frozenset({"figure_file"}),
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"member_id", "role", "ref", "size_bytes", "sha256"}, field)
    member_id = text(payload.get("member_id"), f"{field}.member_id")
    normalized = {
        "member_id": member_id,
        "role": enum_text(payload.get("role"), f"{field}.role", set(allowed_roles)),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    expected = artifact_by_member_id.get(member_id)
    if expected is None or expected.get("role") not in allowed_roles:
        raise RequestShapeError(f"{field} must name an allowed generation artifact")
    return normalized


def _normalize_professional_skill_input_bindings(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    allowed_roles = frozenset(
        item["role"] for item in artifact_by_member_id.values()
    )
    bindings = [
        _normalize_professional_skill_artifact_binding(
            item,
            f"{field}[{index}]",
            artifact_by_member_id=artifact_by_member_id,
            allowed_roles=allowed_roles,
        )
        for index, item in enumerate(sequence(value, field))
    ]
    if not bindings:
        raise RequestShapeError(f"{field} must not be empty")
    member_ids = [item["member_id"] for item in bindings]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(f"{field} contains duplicate members")
    for binding in bindings:
        expected = artifact_by_member_id[binding["member_id"]]
        if any(
            binding[key] != expected[key]
            for key in ("role", "ref", "size_bytes", "sha256")
        ):
            raise RequestShapeError(
                f"{field} does not match the exact generation input artifacts"
            )
    return sorted(bindings, key=lambda item: item["member_id"])


def _normalize_professional_invocation_ref(
    value: Any,
    field: str,
    *,
    invocation_core: Mapping[str, Any],
) -> dict[str, Any]:
    invocation_ref = _exact_ref(
        value,
        field,
        "mas_professional_skill_invocation",
    )
    expected_sha256 = fingerprint(invocation_core)
    expected_size = len(canonical_json_bytes(invocation_core))
    expected_ref = (
        "mas-professional-skill-invocation:"
        f"{expected_sha256.removeprefix('sha256:')}"
    )
    if invocation_ref != {
        "kind": "mas_professional_skill_invocation",
        "ref": expected_ref,
        "size_bytes": expected_size,
        "sha256": expected_sha256,
    }:
        raise RequestShapeError(f"{field} does not match canonical invocation bytes")
    return invocation_ref


def _normalize_figure_template_usage(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    if payload.get("used") is False:
        exact_keys(payload, {"used", "decision_reason"}, field)
        return {
            "used": False,
            "decision_reason": text(
                payload.get("decision_reason"), f"{field}.decision_reason"
            ),
        }
    if payload.get("used") is not True:
        raise RequestShapeError(f"{field}.used must be boolean")
    exact_keys(
        payload,
        {
            "used",
            "template_id",
            "template_ref",
            "adaptation_mode",
            "semantic_match_ref",
            "transform_delta_ref",
        },
        field,
    )
    return {
        "used": True,
        "template_id": text(payload.get("template_id"), f"{field}.template_id"),
        "template_ref": text(payload.get("template_ref"), f"{field}.template_ref"),
        "adaptation_mode": enum_text(
            payload.get("adaptation_mode"),
            f"{field}.adaptation_mode",
            {
                "declared_template",
                "schema_adapted_template",
                "reference_guided_new_render",
            },
        ),
        "semantic_match_ref": text(
            payload.get("semantic_match_ref"), f"{field}.semantic_match_ref"
        ),
        "transform_delta_ref": text(
            payload.get("transform_delta_ref"), f"{field}.transform_delta_ref"
        ),
    }


def _normalize_figure_text_policy(
    value: Any,
    field: str,
    *,
    figure_kind: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "embedded_title",
            "embedded_subtitle",
            "embedded_prose_footer",
            "allowed_text_roles",
        },
        field,
    )
    for key in ("embedded_title", "embedded_subtitle", "embedded_prose_footer"):
        if not isinstance(payload.get(key), bool):
            raise RequestShapeError(f"{field}.{key} must be boolean")
    allowed_text_roles = text_list(
        payload.get("allowed_text_roles"), f"{field}.allowed_text_roles"
    )
    evidence_roles = {
        "panel_label",
        "axis_label",
        "tick_label",
        "legend",
        "necessary_statistical_annotation",
    }
    allowed_roles = evidence_roles | {"graphical_abstract_copy"}
    if not set(allowed_text_roles).issubset(allowed_roles):
        raise RequestShapeError(
            f"{field}.allowed_text_roles contains unsupported roles"
        )
    if figure_kind == "evidence_figure":
        for key in ("embedded_title", "embedded_subtitle", "embedded_prose_footer"):
            if payload.get(key) is not False:
                raise RequestShapeError(
                    f"{field}.{key} must be false for evidence figures"
                )
        if set(allowed_text_roles) != evidence_roles:
            raise RequestShapeError(
                f"{field}.allowed_text_roles must equal the evidence-figure text policy"
            )
    return {
        "embedded_title": payload["embedded_title"],
        "embedded_subtitle": payload["embedded_subtitle"],
        "embedded_prose_footer": payload["embedded_prose_footer"],
        "allowed_text_roles": allowed_text_roles,
    }

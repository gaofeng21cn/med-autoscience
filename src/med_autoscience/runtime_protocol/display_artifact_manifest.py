from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


DISPLAY_ARTIFACT_MANIFEST_SCHEMA_VERSION = 1
DISPLAY_ARTIFACT_MANIFEST_SURFACE = "display_artifact_manifest"
DISPLAY_ARTIFACT_MANIFEST_CONTRACT_SURFACE = "mas_display_artifact_manifest_contract"
MAS_OWNER = "MedAutoScience"
PAGE_ADJUSTMENT_AUTHORIZED_FIELDS = ("density", "layout", "placement")
ARK_SOURCE_PROJECT = "kaust-ark/ARK"
REQUIRED_FIELDS = (
    "artifact_id",
    "artifact_kind",
    "source_data_refs",
    "source_data_digests",
    "claim_refs",
    "statistical_value_refs",
    "rendered_artifact_ref",
    "rendered_artifact_digest",
    "placement",
    "scalable",
    "protected",
    "mutation_authority",
    "visual_qa_receipt_refs",
    "currentness",
)
REQUIRED_DISPLAY_ARTIFACT_FIELDS = REQUIRED_FIELDS


def build_display_artifact_manifest_contract() -> dict[str, object]:
    return {
        "surface_kind": DISPLAY_ARTIFACT_MANIFEST_CONTRACT_SURFACE,
        "version": "mas-display-artifact-manifest-contract.v1",
        "owner": MAS_OWNER,
        "contract_ref": (
            "med_autoscience.runtime_protocol.display_artifact_manifest."
            "build_display_artifact_manifest_contract"
        ),
        "clean_room_absorption": {
            "source_project": ARK_SOURCE_PROJECT,
            "source_pattern": "figure_manifest_and_page_adjustment",
            "absorbed_as": "mas_native_display_artifact_contract",
            "runtime_dependency": False,
            "vendor_dependency": False,
            "foreign_artifact_authority": False,
        },
        "authority_boundary": {
            "display_artifact_truth_owner": MAS_OWNER,
            "artifact_body_owner": MAS_OWNER,
            "medical_data_truth_owner": MAS_OWNER,
            "claim_truth_owner": MAS_OWNER,
            "statistical_value_truth_owner": MAS_OWNER,
            "opl_role": "refs_index_and_projection_only",
            "opl_can_mutate_artifact_body": False,
            "opl_can_authorize_medical_data_truth": False,
            "opl_can_authorize_claim_truth": False,
            "opl_can_authorize_statistical_value_truth": False,
            "layout_adjustment_can_change_data": False,
        },
        "manifest_entry": {
            "required_fields": list(REQUIRED_DISPLAY_ARTIFACT_FIELDS),
            "mutation_blocker_fields": [
                "source_data_digests",
                "rendered_artifact_digest",
                "visual_qa_receipt_refs",
                "mutation_authority",
                "currentness",
            ],
            "allowed_placements": ["single_column", "full_width", "appendix", "table_inline"],
            "protected_meaning": "artifact_requires_mas_authority_before_body_mutation",
            "scalable_meaning": "layout_scaling_allowed_without_data_or_claim_change",
        },
        "page_adjustment_policy": {
            "allowed_changes": ["layout", "placement", "density", "caption_length"],
            "forbidden_changes": ["source_data", "claim_refs", "statistical_values", "result_values"],
            "missing_digest_behavior": "mutation_blocker",
            "missing_visual_qa_behavior": "mutation_blocker",
            "may_authorize_artifact_mutation": False,
        },
        "outputs": [
            "display_artifact_manifest_ref",
            "visual_qa_receipt_ref",
            "artifact_mutation_blocker_ref",
            "layout_adjustment_work_unit_ref",
        ],
    }


def build_display_artifact_manifest(
    *,
    artifact_id: str,
    artifact_kind: str,
    source_data_refs: Sequence[str],
    source_data_digests: Mapping[str, str],
    claim_refs: Sequence[str],
    statistical_value_refs: Sequence[str],
    rendered_artifact_ref: str,
    rendered_artifact_digest: str,
    placement: Mapping[str, object],
    scalable: bool,
    protected: bool,
    visual_qa_receipt_refs: Sequence[str],
    currentness: Mapping[str, object],
    mutation_authority: Mapping[str, object] | None = None,
) -> dict[str, object]:
    authority = _normalize_mutation_authority(mutation_authority)
    manifest: dict[str, object] = {
        "schema_version": DISPLAY_ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "surface": DISPLAY_ARTIFACT_MANIFEST_SURFACE,
        "owner": MAS_OWNER,
        "artifact_id": _require_text(artifact_id, "artifact_id"),
        "artifact_kind": _require_text(artifact_kind, "artifact_kind"),
        "source_data_refs": _text_list(source_data_refs, "source_data_refs"),
        "source_data_digests": _text_mapping(source_data_digests, "source_data_digests"),
        "claim_refs": _text_list(claim_refs, "claim_refs"),
        "statistical_value_refs": _text_list(statistical_value_refs, "statistical_value_refs"),
        "rendered_artifact_ref": _require_text(rendered_artifact_ref, "rendered_artifact_ref"),
        "rendered_artifact_digest": _require_text(rendered_artifact_digest, "rendered_artifact_digest"),
        "placement": dict(placement),
        "scalable": _require_bool(scalable, "scalable"),
        "protected": _require_bool(protected, "protected"),
        "mutation_authority": authority,
        "visual_qa_receipt_refs": _text_list(visual_qa_receipt_refs, "visual_qa_receipt_refs"),
        "currentness": dict(currentness),
    }
    validation = validate_display_artifact_manifest(manifest)
    if validation["status"] != "valid":
        blockers = ", ".join(str(item) for item in validation["mutation_blockers"])
        raise ValueError(f"display artifact manifest is mutation-blocked: {blockers}")
    return manifest


def validate_display_artifact_manifest(manifest: Mapping[str, object]) -> dict[str, object]:
    mutation_blockers: list[str] = []
    if not isinstance(manifest, Mapping):
        return _validation_result(["invalid_manifest_payload"])

    for field in REQUIRED_FIELDS:
        if field not in manifest:
            mutation_blockers.append(f"missing_{field}")

    if _text_value(manifest.get("artifact_id")) is None:
        mutation_blockers.append("missing_artifact_id")
    if _text_value(manifest.get("artifact_kind")) is None:
        mutation_blockers.append("missing_artifact_kind")
    if _text_value(manifest.get("rendered_artifact_ref")) is None:
        mutation_blockers.append("missing_rendered_artifact_ref")
    if _text_value(manifest.get("rendered_artifact_digest")) is None:
        mutation_blockers.append("missing_rendered_artifact_digest")

    source_data_refs = _text_sequence_value(manifest.get("source_data_refs"))
    if not source_data_refs:
        mutation_blockers.append("missing_source_data_ref")
    source_data_digests = _text_mapping_value(manifest.get("source_data_digests"))
    if not source_data_digests or any(ref not in source_data_digests for ref in source_data_refs):
        mutation_blockers.append("missing_source_data_digest")

    if not _text_sequence_value(manifest.get("claim_refs")):
        mutation_blockers.append("missing_claim_ref")
    if not _text_sequence_value(manifest.get("statistical_value_refs")):
        mutation_blockers.append("missing_statistical_value_ref")
    if not isinstance(manifest.get("placement"), Mapping) or not manifest.get("placement"):
        mutation_blockers.append("missing_placement")
    if not isinstance(manifest.get("scalable"), bool):
        mutation_blockers.append("missing_scalable")
    if not isinstance(manifest.get("protected"), bool):
        mutation_blockers.append("missing_protected")
    if not _text_sequence_value(manifest.get("visual_qa_receipt_refs")):
        mutation_blockers.append("missing_visual_qa_receipt_ref")
    if not isinstance(manifest.get("currentness"), Mapping) or not manifest.get("currentness"):
        mutation_blockers.append("missing_currentness")
    if _text_value(manifest.get("owner")) != MAS_OWNER:
        mutation_blockers.append("invalid_display_artifact_owner")
    if not _mutation_authority_is_mas_owned(manifest.get("mutation_authority")):
        mutation_blockers.append("invalid_mutation_authority_boundary")

    return _validation_result(_dedupe(mutation_blockers))


def validate_display_artifact_manifest_entry(entry: Mapping[str, object]) -> dict[str, object]:
    normalized_entry = _normalize_contract_entry(entry)
    validation = validate_display_artifact_manifest(
        {
            "schema_version": DISPLAY_ARTIFACT_MANIFEST_SCHEMA_VERSION,
            "surface": DISPLAY_ARTIFACT_MANIFEST_SURFACE,
            "owner": MAS_OWNER,
            **normalized_entry,
            "mutation_authority": _coerce_entry_mutation_authority(normalized_entry.get("mutation_authority")),
        }
    )
    blockers = _entry_blockers(validation["mutation_blockers"])
    return {
        "status": "blocked" if blockers else "valid",
        "blockers": blockers,
        "may_authorize_artifact_mutation": False,
    }


def validate_page_adjustment_policy(
    manifest: Mapping[str, object],
    *,
    requested_changes: Sequence[str],
) -> dict[str, object]:
    validation = validate_display_artifact_manifest(manifest)
    mutation_blockers = list(validation["mutation_blockers"])
    for field in sorted(set(_text_list(requested_changes, "requested_changes"))):
        if field not in PAGE_ADJUSTMENT_AUTHORIZED_FIELDS:
            mutation_blockers.append(f"page_adjustment_cannot_change_{field}")
    return _validation_result(_dedupe(mutation_blockers))


def _default_mutation_authority() -> dict[str, object]:
    return {
        "owner": MAS_OWNER,
        "artifact_body_owner": MAS_OWNER,
        "medical_data_truth_owner": MAS_OWNER,
        "claim_truth_owner": MAS_OWNER,
        "statistical_value_truth_owner": MAS_OWNER,
        "opl_can_index_refs": True,
        "opl_can_display_refs": True,
        "opl_can_mutate_artifact_body": False,
        "opl_can_authorize_medical_data_truth": False,
        "opl_can_authorize_claim_truth": False,
        "opl_can_authorize_statistical_value_truth": False,
        "page_adjustment_authorized_fields": list(PAGE_ADJUSTMENT_AUTHORIZED_FIELDS),
    }


def _coerce_entry_mutation_authority(authority: object) -> object:
    if authority == "mas_artifact_authority_required":
        return _default_mutation_authority()
    return authority


def _normalize_contract_entry(entry: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(entry)
    source_refs = _text_sequence_value(normalized.get("source_data_refs"))
    source_digests = normalized.get("source_data_digests")
    if isinstance(source_digests, Sequence) and not isinstance(source_digests, str):
        digest_values = _text_sequence_value(source_digests)
        if source_refs and digest_values and len(source_refs) == len(digest_values):
            normalized["source_data_digests"] = dict(zip(source_refs, digest_values, strict=True))
    placement = normalized.get("placement")
    if isinstance(placement, str) and placement.strip():
        normalized["placement"] = {"slot": placement.strip()}
    return normalized


def _entry_blockers(mutation_blockers: object) -> list[str]:
    if not isinstance(mutation_blockers, Sequence) or isinstance(mutation_blockers, str):
        return ["invalid_validation_result"]
    mapping = {
        "missing_source_data_digest": "source_data_digest_missing",
        "missing_rendered_artifact_digest": "rendered_artifact_digest_missing",
        "missing_visual_qa_receipt_ref": "visual_qa_receipt_missing",
        "invalid_mutation_authority_boundary": "mutation_authority_boundary_invalid",
    }
    return [mapping.get(str(blocker), str(blocker)) for blocker in mutation_blockers]


def _normalize_mutation_authority(authority: Mapping[str, object] | None) -> dict[str, object]:
    normalized = _default_mutation_authority()
    if authority is None:
        return normalized
    if not isinstance(authority, Mapping):
        raise ValueError("mutation_authority must be a mapping")
    normalized.update(dict(authority))
    if not _mutation_authority_is_mas_owned(normalized):
        raise ValueError("mutation_authority must preserve MAS owner boundary")
    return normalized


def _mutation_authority_is_mas_owned(authority: object) -> bool:
    if not isinstance(authority, Mapping):
        return False
    owner_fields = (
        "owner",
        "artifact_body_owner",
        "medical_data_truth_owner",
        "claim_truth_owner",
        "statistical_value_truth_owner",
    )
    if any(_text_value(authority.get(field)) != MAS_OWNER for field in owner_fields):
        return False
    if authority.get("opl_can_index_refs") is not True:
        return False
    if authority.get("opl_can_display_refs") is not True:
        return False
    forbidden_grants = (
        "opl_can_mutate_artifact_body",
        "opl_can_authorize_medical_data_truth",
        "opl_can_authorize_claim_truth",
        "opl_can_authorize_statistical_value_truth",
    )
    if any(authority.get(field) is not False for field in forbidden_grants):
        return False
    return _text_sequence_value(authority.get("page_adjustment_authorized_fields")) == list(
        PAGE_ADJUSTMENT_AUTHORIZED_FIELDS
    )


def _validation_result(mutation_blockers: Sequence[str]) -> dict[str, object]:
    blockers = list(mutation_blockers)
    return {
        "status": "mutation_blocked" if blockers else "valid",
        "mutation_blockers": blockers,
        "warnings": [],
    }


def _require_text(value: str, field: str) -> str:
    text = _text_value(value)
    if text is None:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _require_bool(value: bool, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a bool")
    return value


def _text_list(values: Sequence[str], field: str) -> list[str]:
    text_values = _text_sequence_value(values)
    if not text_values:
        raise ValueError(f"{field} must be a non-empty sequence of strings")
    return text_values


def _text_mapping(values: Mapping[str, str], field: str) -> dict[str, str]:
    text_values = _text_mapping_value(values)
    if not text_values:
        raise ValueError(f"{field} must be a non-empty string mapping")
    return text_values


def _text_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _text_sequence_value(values: object) -> list[str]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        return []
    result: list[str] = []
    for value in values:
        text = _text_value(value)
        if text is None:
            return []
        result.append(text)
    return result


def _text_mapping_value(values: object) -> dict[str, str]:
    if not isinstance(values, Mapping):
        return {}
    result: dict[str, str] = {}
    for key, value in values.items():
        text_key = _text_value(key)
        text_value = _text_value(value)
        if text_key is None or text_value is None:
            return {}
        result[text_key] = text_value
    return result


def _dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


__all__ = [
    "DISPLAY_ARTIFACT_MANIFEST_SCHEMA_VERSION",
    "DISPLAY_ARTIFACT_MANIFEST_SURFACE",
    "DISPLAY_ARTIFACT_MANIFEST_CONTRACT_SURFACE",
    "MAS_OWNER",
    "PAGE_ADJUSTMENT_AUTHORIZED_FIELDS",
    "REQUIRED_DISPLAY_ARTIFACT_FIELDS",
    "REQUIRED_FIELDS",
    "build_display_artifact_manifest",
    "build_display_artifact_manifest_contract",
    "validate_display_artifact_manifest",
    "validate_display_artifact_manifest_entry",
    "validate_page_adjustment_policy",
]

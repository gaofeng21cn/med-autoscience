from __future__ import annotations

from med_autoscience.stage_quality_contract_parts.pack_data import (
    _JOURNAL_ACCEPTANCE_EVIDENCE_FIELDS,
    _JOURNAL_REQUIRED_REVIEWER_OUTPUTS,
    _PACK_REQUIRED_REFS,
)


def journal_acceptance_evidence_fields(pack_id: str) -> list[dict[str, object]]:
    return [
        field(field_id, role)
        for field_id, role in _JOURNAL_ACCEPTANCE_EVIDENCE_FIELDS[pack_id]
    ]


def journal_required_reviewer_output(pack_id: str) -> list[dict[str, object]]:
    return [
        {
            "output_id": output_id,
            "role": role,
            "required": True,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        }
        for output_id, role in _JOURNAL_REQUIRED_REVIEWER_OUTPUTS[pack_id]
    ]


def journal_forbidden_authority() -> list[dict[str, object]]:
    return [
        {
            "authority_id": authority_id,
            "forbidden": True,
            "reason": reason,
        }
        for authority_id, reason in (
            ("vendor_skill_authority", "clean_room_pattern_only"),
            ("runtime_authority", "opl_descriptor_ref_locator_only"),
            ("default_skill_authority", "journal_pack_must_be_explicitly_consumed"),
            ("publication_readiness_authority", "mas_owner_receipt_or_reviewer_record_required"),
            ("quality_verdict_authority", "mas_quality_owner_closure_required"),
            ("mas_truth_write_authority", "pack_is_reviewer_rubric_not_truth_writer"),
        )
    ]


def journal_quality_pack_consumption(pack_id: str) -> dict[str, object]:
    return {
        "consumer_roles": ["reviewer_agent", "auditor_agent"],
        "consumed_as": "explicit_quality_pack_descriptor",
        "required_contract_refs": [ref["ref"] for ref in _PACK_REQUIRED_REFS[pack_id]],
        "required_output_classes": [
            output_id for output_id, _role in _JOURNAL_REQUIRED_REVIEWER_OUTPUTS[pack_id]
        ],
        "opl_consumption_role": "descriptor_ref_freshness_locator_only",
        "opl_may_authorize_quality_verdict": False,
        "opl_may_authorize_publication_readiness": False,
        "opl_may_write_mas_truth": False,
    }


def field(field_id: str, role: str) -> dict[str, object]:
    return {"field_id": field_id, "role": role, "required": True}

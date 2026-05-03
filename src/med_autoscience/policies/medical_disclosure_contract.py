from __future__ import annotations

from med_autoscience.policies.medical_publication_surface import _missing_required_fields


STRUCTURED_DISCLOSURE_AUDIT_BASENAME = "structured_disclosure_audit.json"
REQUIRED_DISCLOSURE_SECTIONS = (
    "ethics",
    "privacy",
    "data_availability",
    "ai_disclosure",
)
REQUIRED_DISCLOSURE_SECTION_FIELDS = ("statement", "evidence_refs", "manuscript_action")
REQUIRED_DATA_ASSET_EVIDENCE_FIELDS = (
    "registry_refs",
    "access_evidence",
    "privacy_evidence",
    "license_evidence",
)


def _validate_disclosure_sections(payload: dict) -> list[str]:
    missing_sections = [
        section
        for section in REQUIRED_DISCLOSURE_SECTIONS
        if not isinstance(payload.get(section), dict)
    ]
    if missing_sections:
        return [f"missing disclosure sections: {', '.join(missing_sections)}"]

    for section_name in REQUIRED_DISCLOSURE_SECTIONS:
        section = payload[section_name]
        missing_fields = _missing_required_fields(section, REQUIRED_DISCLOSURE_SECTION_FIELDS)
        if missing_fields:
            return [f"missing {section_name} fields: {', '.join(missing_fields)}"]
        if str(section.get("status") or "").strip() not in {"pass", "acceptable_with_boundary"}:
            return [f"{section_name} status must be pass or acceptable_with_boundary"]
    return []


def _validate_data_asset_evidence(payload: dict) -> list[str]:
    data_asset_evidence = payload.get("data_asset_evidence")
    if not isinstance(data_asset_evidence, dict):
        return ["data_asset_evidence must be an object"]
    missing_evidence_fields = _missing_required_fields(data_asset_evidence, REQUIRED_DATA_ASSET_EVIDENCE_FIELDS)
    if missing_evidence_fields:
        return [f"missing data_asset_evidence fields: {', '.join(missing_evidence_fields)}"]
    return []


def validate_structured_disclosure_audit(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    if str(payload.get("status") or "").strip() != "resolved":
        return ["status must be resolved"]
    section_errors = _validate_disclosure_sections(payload)
    if section_errors:
        return section_errors
    return _validate_data_asset_evidence(payload)

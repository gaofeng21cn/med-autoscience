from __future__ import annotations

from med_autoscience.policies.medical_publication_surface import _missing_required_fields


STRUCTURED_DISCLOSURE_AUDIT_BASENAME = "structured_disclosure_audit.json"


def validate_structured_disclosure_audit(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    if str(payload.get("status") or "").strip() != "resolved":
        return ["status must be resolved"]
    required_sections = (
        "ethics",
        "privacy",
        "data_availability",
        "ai_disclosure",
    )
    missing_sections = [section for section in required_sections if not isinstance(payload.get(section), dict)]
    if missing_sections:
        return [f"missing disclosure sections: {', '.join(missing_sections)}"]

    required_fields = ("statement", "evidence_refs", "manuscript_action")
    for section_name in required_sections:
        section = payload[section_name]
        missing_fields = _missing_required_fields(section, required_fields)
        if missing_fields:
            return [f"missing {section_name} fields: {', '.join(missing_fields)}"]
        if str(section.get("status") or "").strip() not in {"pass", "acceptable_with_boundary"}:
            return [f"{section_name} status must be pass or acceptable_with_boundary"]

    data_asset_evidence = payload.get("data_asset_evidence")
    if not isinstance(data_asset_evidence, dict):
        return ["data_asset_evidence must be an object"]
    required_evidence_fields = (
        "registry_refs",
        "access_evidence",
        "privacy_evidence",
        "license_evidence",
    )
    missing_evidence_fields = _missing_required_fields(data_asset_evidence, required_evidence_fields)
    if missing_evidence_fields:
        return [f"missing data_asset_evidence fields: {', '.join(missing_evidence_fields)}"]
    return []

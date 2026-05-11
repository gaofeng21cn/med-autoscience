from __future__ import annotations

NUMERIC_TRACE_BASENAME = "numeric_trace.json"


def _non_empty_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value) and bool(value)


def _missing_required_fields(item: object, fields: tuple[str, ...]) -> list[str]:
    if not isinstance(item, dict):
        return list(fields)
    missing: list[str] = []
    for field in fields:
        value = item.get(field)
        if isinstance(value, list):
            if not value:
                missing.append(field)
        elif not str(value or "").strip():
            missing.append(field)
    return missing


def validate_claim_evidence_numeric_trace_refs(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        return []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            continue
        evidence_items = claim.get("evidence_items")
        if not isinstance(evidence_items, list):
            continue
        for evidence_index, evidence_item in enumerate(evidence_items):
            if (
                isinstance(evidence_item, dict)
                and "numeric_trace_refs" in evidence_item
                and not _non_empty_string_list(evidence_item.get("numeric_trace_refs"))
            ):
                return [
                    f"claims[{index}].evidence_items[{evidence_index}].numeric_trace_refs "
                    "must contain at least one non-empty string"
                ]
    return []


def validate_numeric_trace(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    traces = payload.get("traces")
    if not isinstance(traces, list) or not traces:
        return ["traces must contain at least one numeric trace entry"]
    required_fields = (
        "trace_id",
        "claim_id",
        "reported_value",
        "statistic_kind",
        "source_paths",
        "source_field",
        "rounding_rule",
        "manuscript_refs",
        "verification_status",
        "evidence_refs",
    )
    allowed_statuses = {"verified", "needs_review", "blocked"}
    trace_ids: set[str] = set()
    for index, trace in enumerate(traces):
        missing_fields = _missing_required_fields(trace, required_fields)
        if missing_fields:
            return [f"missing traces[{index}] fields: {', '.join(missing_fields)}"]
        if not isinstance(trace, dict):
            return [f"traces[{index}] must be a JSON object"]
        trace_id = str(trace.get("trace_id") or "").strip()
        if trace_id in trace_ids:
            return [f"traces[{index}].trace_id duplicates `{trace_id}`"]
        trace_ids.add(trace_id)
        for field in ("source_paths", "manuscript_refs", "evidence_refs"):
            if not _non_empty_string_list(trace.get(field)):
                return [f"traces[{index}].{field} must contain at least one non-empty string"]
        verification_status = str(trace.get("verification_status") or "").strip()
        if verification_status not in allowed_statuses:
            return [
                f"traces[{index}].verification_status must be one of: "
                f"{', '.join(sorted(allowed_statuses))}"
            ]
        if verification_status != "verified":
            return [f"traces[{index}].verification_status must be verified"]
    return []

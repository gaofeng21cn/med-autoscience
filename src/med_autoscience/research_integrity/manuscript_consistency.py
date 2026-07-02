from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any


SURFACE_KIND = "manuscript_consistency_meta_review"
SCHEMA_VERSION = 1
MANUSCRIPT_SECTIONS = ("abstract", "results", "tables", "figures")
CONTEXT_FIELDS = ("unit", "population", "window")
VALUE_FIELDS = ("reported_value", "value", "numeric_value", "estimate")
FACT_ID_FIELDS = ("fact_id", "claim_id", "metric_id", "trace_id", "id", "key")
LOGIC_ID_FIELDS = ("logic_id", "claim_id", "argument_id", "id", "key")
HARD_FINDING_CODES = frozenset(
    {
        "numeric_fact_inconsistent",
        "unit_population_window_mismatch",
        "display_to_claim_mismatch",
        "section_logic_contradiction",
        "reporting_guideline_checklist_gap",
    }
)


def build_manuscript_consistency_meta_review(
    *,
    manuscript_sections: Mapping[str, Any],
    numeric_facts: object = (),
    display_facts: object = (),
    reporting_checklist_expectations: object = (),
) -> dict[str, Any]:
    facts = _manuscript_facts(manuscript_sections) + _fact_items(numeric_facts, source_kind="numeric_fact")
    displays = _display_fact_items(display_facts)
    findings = (
        _numeric_findings(facts)
        + _display_findings(facts, displays)
        + _logic_findings(manuscript_sections)
        + _checklist_findings(reporting_checklist_expectations)
    )
    findings = sorted(findings, key=_finding_key)
    blocker_candidates = [
        _blocker_candidate(finding)
        for finding in findings
        if finding["code"] in HARD_FINDING_CODES and finding["severity"] == "blocker"
    ]
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": _status(findings=findings, blocker_candidates=blocker_candidates),
        "findings": findings,
        "blocker_candidates": blocker_candidates,
        "authority_boundary": authority_boundary(),
    }


def authority_boundary() -> dict[str, bool]:
    return {
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_mutate_manuscript": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
    }


def _status(*, findings: list[dict[str, Any]], blocker_candidates: list[dict[str, Any]]) -> str:
    if blocker_candidates:
        return "blocked"
    if findings:
        return "needs_review"
    return "clear"


def _manuscript_facts(manuscript_sections: Mapping[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for section in MANUSCRIPT_SECTIONS:
        for fact in _fact_items(manuscript_sections.get(section), source_kind="manuscript_section"):
            fact.setdefault("section", section)
            facts.append(fact)
    return facts


def _fact_items(value: object, *, source_kind: str) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        for key in ("numeric_facts", "facts", "claims", "traces"):
            if key in value:
                return _fact_items(value[key], source_kind=source_kind)
        return [_normalized_fact(value, source_kind=source_kind)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _normalized_fact(item, source_kind=source_kind)
            for item in value
            if isinstance(item, Mapping)
        ]
    return []


def _display_fact_items(value: object) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        for key in ("display_facts", "facts", "claims"):
            if key in value:
                return _display_fact_items(value[key])
        flattened: list[dict[str, Any]] = []
        for key in ("tables", "figures", "displays"):
            flattened.extend(_display_entries(value.get(key)))
        if flattened:
            return flattened
        return [_normalized_fact(value, source_kind="display_fact")]
    return _display_entries(value)


def _display_entries(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    facts: list[dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            continue
        display_id = _text(entry.get("display_id") or entry.get("table_id") or entry.get("figure_id"))
        nested = entry.get("facts") or entry.get("numeric_facts")
        if nested is None:
            fact = _normalized_fact(entry, source_kind="display_fact")
            if display_id and not fact.get("display_id"):
                fact["display_id"] = display_id
            facts.append(fact)
            continue
        for fact in _fact_items(nested, source_kind="display_fact"):
            if display_id and not fact.get("display_id"):
                fact["display_id"] = display_id
            facts.append(fact)
    return facts


def _normalized_fact(value: Mapping[str, Any], *, source_kind: str) -> dict[str, Any]:
    fact = {
        "fact_id": _first_text(value, FACT_ID_FIELDS),
        "value": _normalized_scalar(_first_value(value, VALUE_FIELDS)),
        "unit": _text(value.get("unit") or value.get("units")),
        "population": _text(value.get("population") or value.get("cohort")),
        "window": _text(value.get("window") or value.get("time_window") or value.get("period")),
        "section": _text(value.get("section")),
        "source_kind": source_kind,
        "source_ref": _text(value.get("source_ref") or value.get("ref")),
        "display_id": _text(value.get("display_id") or value.get("table_id") or value.get("figure_id")),
    }
    return {key: item for key, item in fact.items() if item is not None}


def _numeric_findings(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for fact_id, grouped in _group_by_fact_id(facts).items():
        value_variants = _variants(grouped, "value")
        if _has_conflicting_values(value_variants):
            findings.append(
                _finding(
                    "numeric_fact_inconsistent",
                    fact_id=fact_id,
                    severity="blocker",
                    message="Numeric fact differs across manuscript, result, table, or figure surfaces.",
                    evidence={"field": "value", "variants": value_variants},
                )
            )
        context_variants = {
            field: variants
            for field in CONTEXT_FIELDS
            if _has_conflicting_values(variants := _variants(grouped, field))
        }
        if context_variants:
            findings.append(
                _finding(
                    "unit_population_window_mismatch",
                    fact_id=fact_id,
                    severity="blocker",
                    message="Fact context differs by unit, population, or time window.",
                    evidence={"context_variants": context_variants},
                )
            )
    return findings


def _display_findings(
    facts: list[dict[str, Any]],
    display_facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    facts_by_id = _group_by_fact_id(facts)
    for display_fact in display_facts:
        fact_id = _text(display_fact.get("fact_id"))
        if fact_id is None or fact_id not in facts_by_id:
            continue
        for field in ("value", *CONTEXT_FIELDS):
            claim_values = {item[field] for item in facts_by_id[fact_id] if field in item}
            display_value = display_fact.get(field)
            if display_value is not None and claim_values and display_value not in claim_values:
                findings.append(
                    _finding(
                        "display_to_claim_mismatch",
                        fact_id=fact_id,
                        severity="blocker",
                        message="Display fact does not match the corresponding manuscript claim.",
                        evidence={
                            "field": field,
                            "display_id": display_fact.get("display_id"),
                            "display_value": display_value,
                            "claim_values": sorted(claim_values),
                        },
                    )
                )
    return findings


def _logic_findings(manuscript_sections: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims: dict[str, dict[str, list[str]]] = {}
    for section in MANUSCRIPT_SECTIONS:
        raw_section = manuscript_sections.get(section)
        if not isinstance(raw_section, Mapping):
            continue
        for item in _logic_items(raw_section.get("logic_claims") or raw_section.get("logical_claims")):
            logic_id = _first_text(item, LOGIC_ID_FIELDS)
            polarity = _text(item.get("polarity") or item.get("direction") or item.get("conclusion"))
            if logic_id is None or polarity is None:
                continue
            claims.setdefault(logic_id, {}).setdefault(polarity, []).append(section)
    findings: list[dict[str, Any]] = []
    for logic_id, polarities in sorted(claims.items()):
        if len(polarities) > 1:
            findings.append(
                _finding(
                    "section_logic_contradiction",
                    fact_id=logic_id,
                    severity="blocker",
                    message="Manuscript sections assert contradictory logic for the same claim.",
                    evidence={"polarities": {key: sorted(value) for key, value in polarities.items()}},
                )
            )
    return findings


def _checklist_findings(expectations: object) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in _checklist_items(expectations):
        item_id = _text(item.get("item_id") or item.get("key") or item.get("id"))
        if item_id is None:
            continue
        status = _text(item.get("status")) or ("present" if item.get("present") is True else "missing")
        if _closed(status):
            continue
        required = item.get("required") is not False
        findings.append(
            _finding(
                "reporting_guideline_checklist_gap",
                fact_id=item_id,
                severity="blocker" if required else "review",
                message="Reporting guideline checklist expectation is not closed.",
                evidence={"status": status, "required": required},
            )
        )
    return findings


def _checklist_items(expectations: object) -> list[dict[str, Any]]:
    if isinstance(expectations, Mapping):
        if isinstance(expectations.get("expectations"), Sequence):
            return [dict(item) for item in expectations["expectations"] if isinstance(item, Mapping)]
        items: list[dict[str, Any]] = []
        for key, value in expectations.items():
            if isinstance(value, Mapping):
                item = dict(value)
                item.setdefault("item_id", str(key))
            else:
                item = {"item_id": str(key), "status": value}
            items.append(item)
        return items
    if isinstance(expectations, Sequence) and not isinstance(expectations, (str, bytes, bytearray)):
        return [dict(item) for item in expectations if isinstance(item, Mapping)]
    return []


def _logic_items(value: object) -> list[Mapping[str, Any]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _group_by_fact_id(facts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        fact_id = _text(fact.get("fact_id"))
        if fact_id is not None:
            grouped.setdefault(fact_id, []).append(fact)
    return dict(sorted(grouped.items()))


def _variants(facts: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    variants: list[dict[str, Any]] = []
    for fact in facts:
        value = fact.get(field)
        if value is None:
            continue
        key = (str(value), str(fact.get("section") or ""), str(fact.get("source_kind") or ""))
        if key in seen:
            continue
        seen.add(key)
        variants.append(
            {
                "value": value,
                "section": fact.get("section"),
                "source_kind": fact.get("source_kind"),
                "source_ref": fact.get("source_ref"),
            }
        )
    return variants


def _has_conflicting_values(variants: list[dict[str, Any]]) -> bool:
    return len({variant["value"] for variant in variants}) > 1


def _blocker_candidate(finding: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_ref": f"manuscript-consistency:{finding['code']}:{finding['fact_id']}",
        "blocker_type": "manuscript_consistency_meta_review_candidate",
        "reason": finding["code"],
        "fact_id": finding["fact_id"],
        "refs_only": True,
        "can_block_current_owner_action": False,
        "authority_boundary": authority_boundary(),
    }


def _finding(
    code: str,
    *,
    fact_id: str,
    severity: str,
    message: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "fact_id": fact_id,
        "message": message,
        "evidence": evidence,
    }


def _finding_key(finding: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(finding.get("code") or ""),
        str(finding.get("fact_id") or ""),
        str(finding.get("severity") or ""),
    )


def _first_text(value: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        text = _text(value.get(key))
        if text is not None:
            return text
    return None


def _first_value(value: Mapping[str, Any], keys: tuple[str, ...]) -> object:
    for key in keys:
        if key in value:
            return value[key]
    return None


def _normalized_scalar(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return str(Decimal(text).normalize())
    except InvalidOperation:
        return text


def _closed(status: str) -> bool:
    return status.strip().lower() in {
        "closed",
        "complete",
        "clear",
        "present",
        "not_applicable_with_rationale",
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "authority_boundary",
    "build_manuscript_consistency_meta_review",
]

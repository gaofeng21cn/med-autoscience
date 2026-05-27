from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


PASSPORT_SURFACE_KIND = "medical_material_passport"
PASSPORT_SCHEMA_VERSION = "mas-medical-material-passport.v1"
SOURCE_PROJECT = "academic-research-skills pattern-only"
TRUTH_OWNER = "MedAutoScience"

SOURCE_ADAPTER_OUTPUT_SCHEMA_VERSION = "mas-source-adapter-output.v1"
SOURCE_ADAPTER_REJECTION_LOG_SCHEMA_VERSION = "mas-source-adapter-rejection-log.v1"
SOURCE_ADAPTER_REJECTION_REASONS = [
    "missing_required_field",
    "invalid_field_format",
    "duplicate_citation_key",
    "unresolvable_source_pointer",
    "year_unparseable",
    "authors_unparseable",
    "adapter_error",
    "other",
]
LIFE_SCIENCE_SOURCE_ADAPTER_REQUIRED_METADATA = (
    "source_family_id",
    "provider_id",
    "accessed_at",
    "query_fingerprint",
    "checked_at",
    "expires_or_stale_after",
)

_PASSPORT_SECTION_ROLES = {
    "source_readiness_refs": "source_readiness_ref",
    "claim_evidence_refs": "claim_evidence_ref",
    "review_contract_refs": "review_contract_ref",
    "artifact_rebuild_refs": "artifact_rebuild_ref",
    "human_decision_refs": "human_decision_ref",
    "owner_receipt_refs": "owner_receipt_ref",
}
_AUTHORITY_BOUNDARY = {
    "can_write_mas_truth": False,
    "can_write_evidence_ledger": False,
    "can_write_review_ledger": False,
    "can_write_publication_eval": False,
    "can_write_controller_decisions": False,
    "can_authorize_publication_quality": False,
    "can_authorize_submission_readiness": False,
}
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "body",
        "payload",
        "artifact_body",
        "memory_body",
        "evidence_ledger_body",
        "review_ledger_body",
        "publication_verdict_body",
        "paper_body",
        "package_body",
    }
)


def build_medical_material_passport(
    *,
    source_readiness_refs: Sequence[str | Path | Mapping[str, Any]] = (),
    claim_evidence_refs: Sequence[str | Path | Mapping[str, Any]] = (),
    review_contract_refs: Sequence[str | Path | Mapping[str, Any]] = (),
    artifact_rebuild_refs: Sequence[str | Path | Mapping[str, Any]] = (),
    human_decision_refs: Sequence[str | Path | Mapping[str, Any]] = (),
    owner_receipt_refs: Sequence[str | Path | Mapping[str, Any]] = (),
) -> dict[str, Any]:
    sections = {
        "source_readiness_refs": _refs_section(source_readiness_refs, role="source_readiness_ref"),
        "claim_evidence_refs": _refs_section(claim_evidence_refs, role="claim_evidence_ref"),
        "review_contract_refs": _refs_section(review_contract_refs, role="review_contract_ref"),
        "artifact_rebuild_refs": _refs_section(artifact_rebuild_refs, role="artifact_rebuild_ref"),
        "human_decision_refs": _refs_section(human_decision_refs, role="human_decision_ref"),
        "owner_receipt_refs": _refs_section(owner_receipt_refs, role="owner_receipt_ref"),
    }
    passport = {
        "surface_kind": PASSPORT_SURFACE_KIND,
        "schema_version": PASSPORT_SCHEMA_VERSION,
        "truth_owner": TRUTH_OWNER,
        "source_project": SOURCE_PROJECT,
        "body_included": False,
        "sections": sections,
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
        "source_pattern_refs": {
            "material_passport": "academic-pipeline/references/passport_as_reset_boundary.md",
            "literature_corpus_adapter": "academic-pipeline/references/adapters/overview.md",
            "handoff_schema": "shared/handoff_schemas.md",
        },
    }
    validate_medical_material_passport(passport)
    return passport


def build_source_adapter_output(
    *,
    adapter_name: str,
    adapter_version: str,
    records: Sequence[Mapping[str, Any]],
    rejected: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    adapter_name_text = _required_text("adapter_name", adapter_name)
    adapter_version_text = _required_text("adapter_version", adapter_version)
    output = {
        "surface_kind": "mas_source_adapter_output",
        "schema_version": SOURCE_ADAPTER_OUTPUT_SCHEMA_VERSION,
        "truth_owner": TRUTH_OWNER,
        "adapter_name": adapter_name_text,
        "adapter_version": adapter_version_text,
        "adapter_authority": "records_and_rejection_log_only",
        "records_write_mas_truth": False,
        "records": [_record_projection(record) for record in records],
        "rejection_log": build_source_adapter_rejection_log(
            adapter_name=adapter_name_text,
            adapter_version=adapter_version_text,
            rejected=rejected,
        ),
        "entry_level_reject_continues": True,
        "adapter_level_failure_loud": True,
        "adapter_level_failure_contract": {
            "emit_partial_passport_on_adapter_failure": False,
            "write_mas_truth_on_adapter_failure": False,
            "failure_mode": "raise_loud_error_before_projection",
        },
    }
    validate_source_adapter_output(output)
    return output


def build_life_science_source_adapter_output(
    *,
    adapter_name: str,
    adapter_version: str,
    records: Sequence[Mapping[str, Any]],
    rejected: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    output = build_source_adapter_output(
        adapter_name=adapter_name,
        adapter_version=adapter_version,
        records=[_life_science_record(record) for record in records],
        rejected=rejected,
    )
    output["source_pattern"] = "openai_life_science_research_clean_room"
    output["source_pattern_boundary"] = {
        "source_repository": "https://github.com/openai/plugins",
        "source_path": "plugins/life-science-research",
        "copy_external_plugin_code": False,
        "default_skill_source": False,
        "runtime_dependency": False,
    }
    output["authority_boundary"] = {
        "can_write_mas_truth": False,
        "can_authorize_source_readiness_verdict": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
    }
    validate_source_adapter_output(output)
    return output


def build_source_adapter_rejection_log(
    *,
    adapter_name: str,
    adapter_version: str,
    rejected: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_source_adapter_rejection_log",
        "schema_version": SOURCE_ADAPTER_REJECTION_LOG_SCHEMA_VERSION,
        "adapter_name": _required_text("adapter_name", adapter_name),
        "adapter_version": _required_text("adapter_version", adapter_version),
        "closed_reasons": list(SOURCE_ADAPTER_REJECTION_REASONS),
        "rejected": [_rejection_entry(entry) for entry in rejected],
    }


def validate_medical_material_passport(passport: Mapping[str, Any]) -> None:
    if passport.get("surface_kind") != PASSPORT_SURFACE_KIND:
        raise ValueError("medical material passport surface_kind is invalid")
    if passport.get("schema_version") != PASSPORT_SCHEMA_VERSION:
        raise ValueError("medical material passport schema_version is invalid")
    if passport.get("truth_owner") != TRUTH_OWNER:
        raise ValueError("medical material passport truth_owner must be MedAutoScience")
    if passport.get("source_project") != SOURCE_PROJECT:
        raise ValueError("medical material passport source_project must remain pattern-only")
    if passport.get("body_included") is not False:
        raise ValueError("medical material passport must be refs-only")
    sections = passport.get("sections")
    if not isinstance(sections, Mapping) or set(sections) != set(_PASSPORT_SECTION_ROLES):
        raise ValueError("medical material passport sections must match the required refs-only sections")
    for section_key, expected_role in _PASSPORT_SECTION_ROLES.items():
        entries = sections.get(section_key)
        if not isinstance(entries, list):
            raise ValueError(f"{section_key} must be a list")
        for entry in entries:
            _validate_ref_entry(entry, expected_role=expected_role)
    if passport.get("authority_boundary") != _AUTHORITY_BOUNDARY:
        raise ValueError("medical material passport authority boundary drifted")
    forbidden = sorted(_find_forbidden_body_keys(passport))
    if forbidden:
        raise ValueError(f"medical material passport contains forbidden body fields: {forbidden}")


def validate_source_adapter_output(output: Mapping[str, Any]) -> None:
    if output.get("surface_kind") != "mas_source_adapter_output":
        raise ValueError("source adapter output surface_kind is invalid")
    if output.get("schema_version") != SOURCE_ADAPTER_OUTPUT_SCHEMA_VERSION:
        raise ValueError("source adapter output schema_version is invalid")
    if output.get("truth_owner") != TRUTH_OWNER:
        raise ValueError("source adapter output truth_owner must be MedAutoScience")
    if output.get("adapter_authority") != "records_and_rejection_log_only":
        raise ValueError("source adapter output authority must stay records + rejection log only")
    if output.get("records_write_mas_truth") is not False:
        raise ValueError("source adapter records must not write MAS truth")
    if output.get("entry_level_reject_continues") is not True:
        raise ValueError("source adapter entry-level rejects must continue")
    if output.get("adapter_level_failure_loud") is not True:
        raise ValueError("source adapter adapter-level failures must be loud")
    records = output.get("records")
    if not isinstance(records, list):
        raise ValueError("source adapter output records must be a list")
    for record in records:
        _validate_record_projection(record)
    _validate_rejection_log(output.get("rejection_log"))


def _refs_section(refs: Sequence[str | Path | Mapping[str, Any]], *, role: str) -> list[dict[str, Any]]:
    return [_ref_entry(ref, role=role) for ref in refs]


def _ref_entry(ref: str | Path | Mapping[str, Any], *, role: str) -> dict[str, Any]:
    if isinstance(ref, Mapping):
        ref_text = _required_text("ref", ref.get("ref"))
        role_text = _required_text("role", ref.get("role", role))
        if role_text != role:
            raise ValueError(f"ref role must be {role}")
        entry = {
            "ref": ref_text,
            "role": role_text,
            "body_included": False,
            "write_permitted": False,
            "truth_owner": TRUTH_OWNER,
        }
        if "ref_kind" in ref:
            entry["ref_kind"] = _required_text("ref_kind", ref.get("ref_kind"))
        if "exists" in ref:
            entry["exists"] = ref.get("exists") is True
        return entry
    return {
        "ref": _required_text("ref", ref),
        "role": role,
        "body_included": False,
        "write_permitted": False,
        "truth_owner": TRUTH_OWNER,
    }


def _record_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError("source adapter record must be a mapping")
    record_id = _required_text("record_id", record.get("record_id"))
    source_pointer = _required_text("source_pointer", record.get("source_pointer"))
    refs = record.get("refs")
    if not isinstance(refs, list) or not refs:
        raise ValueError("source adapter record refs must be a non-empty list")
    projection = {
        "record_id": record_id,
        "source_pointer": source_pointer,
        "refs": [_required_text("record_ref", ref) for ref in refs],
        "body_included": False,
        "write_mas_truth": False,
    }
    if "metadata" in record:
        metadata = record.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("source adapter record metadata must be a mapping")
        projection["metadata"] = dict(metadata)
    forbidden = sorted(_find_forbidden_body_keys(projection))
    if forbidden:
        raise ValueError(f"source adapter record contains forbidden body fields: {forbidden}")
    return projection


def _life_science_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError("life science source adapter record must be a mapping")
    metadata = record.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("life science source adapter record metadata must be a mapping")
    normalized_metadata = dict(metadata)
    for field in LIFE_SCIENCE_SOURCE_ADAPTER_REQUIRED_METADATA:
        _required_text(f"metadata requires {field}", normalized_metadata.get(field))
    return {**dict(record), "metadata": normalized_metadata}


def _rejection_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(entry, Mapping):
        raise ValueError("source adapter rejection entry must be a mapping")
    source = _required_text("source", entry.get("source"))
    reason = _required_text("reason", entry.get("reason"))
    if reason not in SOURCE_ADAPTER_REJECTION_REASONS:
        raise ValueError(f"source adapter rejection uses non-closed rejection reason: {reason}")
    detail = _text(entry.get("detail"))
    if reason == "other" and detail is None:
        raise ValueError("source adapter rejection detail is required when reason=other")
    rejected = {"source": source, "reason": reason}
    if detail is not None:
        rejected["detail"] = detail
    missing_fields = entry.get("missing_fields")
    if missing_fields is not None:
        if not isinstance(missing_fields, list):
            raise ValueError("source adapter rejection missing_fields must be a list")
        rejected["missing_fields"] = [_required_text("missing_field", field) for field in missing_fields]
    raw = entry.get("raw")
    if raw is not None:
        if not isinstance(raw, (Mapping, str)):
            raise ValueError("source adapter rejection raw must be a mapping or string")
        rejected["raw"] = dict(raw) if isinstance(raw, Mapping) else raw
    return rejected


def _validate_ref_entry(entry: object, *, expected_role: str) -> None:
    if not isinstance(entry, Mapping):
        raise ValueError("passport ref entry must be a mapping")
    if _text(entry.get("ref")) is None:
        raise ValueError("passport ref entry requires ref")
    if entry.get("role") != expected_role:
        raise ValueError(f"passport ref entry role must be {expected_role}")
    if entry.get("body_included") is not False or entry.get("write_permitted") is not False:
        raise ValueError("passport ref entry must be body-free and write-disabled")
    if entry.get("truth_owner") != TRUTH_OWNER:
        raise ValueError("passport ref entry truth_owner must be MedAutoScience")


def _validate_record_projection(record: object) -> None:
    if not isinstance(record, Mapping):
        raise ValueError("source adapter record projection must be a mapping")
    if _text(record.get("record_id")) is None or _text(record.get("source_pointer")) is None:
        raise ValueError("source adapter record projection requires record_id and source_pointer")
    refs = record.get("refs")
    if not isinstance(refs, list) or not refs:
        raise ValueError("source adapter record projection requires refs")
    if record.get("body_included") is not False or record.get("write_mas_truth") is not False:
        raise ValueError("source adapter record projection must be body-free and write-disabled")


def _validate_rejection_log(log: object) -> None:
    if not isinstance(log, Mapping):
        raise ValueError("source adapter output must always include a rejection_log")
    if log.get("surface_kind") != "mas_source_adapter_rejection_log":
        raise ValueError("source adapter rejection_log surface_kind is invalid")
    if log.get("schema_version") != SOURCE_ADAPTER_REJECTION_LOG_SCHEMA_VERSION:
        raise ValueError("source adapter rejection_log schema_version is invalid")
    if log.get("closed_reasons") != SOURCE_ADAPTER_REJECTION_REASONS:
        raise ValueError("source adapter rejection_log closed reasons drifted")
    rejected = log.get("rejected")
    if not isinstance(rejected, list):
        raise ValueError("source adapter rejection_log rejected must be a list")
    for entry in rejected:
        _rejection_entry(entry)


def _find_forbidden_body_keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_BODY_KEYS:
                found.add(key_text)
            found.update(_find_forbidden_body_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_find_forbidden_body_keys(child))
    return found


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "PASSPORT_SCHEMA_VERSION",
    "PASSPORT_SURFACE_KIND",
    "SOURCE_ADAPTER_OUTPUT_SCHEMA_VERSION",
    "SOURCE_ADAPTER_REJECTION_LOG_SCHEMA_VERSION",
    "SOURCE_ADAPTER_REJECTION_REASONS",
    "SOURCE_PROJECT",
    "TRUTH_OWNER",
    "build_medical_material_passport",
    "build_life_science_source_adapter_output",
    "build_source_adapter_output",
    "build_source_adapter_rejection_log",
    "validate_medical_material_passport",
    "validate_source_adapter_output",
]

from __future__ import annotations

from typing import Any

from .shared import _mapping_copy, _non_empty_text


def build_research_pack_progress_summary_projection(
    *,
    opl_current_control_state_handoff: dict[str, Any] | None,
) -> dict[str, Any]:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    terminal = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    evidence_summary = _mapping_copy(paper_stage_log.get("research_evidence_pack_summary")) or _mapping_copy(
        handoff.get("research_evidence_pack_summary")
    )
    pack = (
        _mapping_copy(paper_stage_log.get("research_pack_progress_summary"))
        or _mapping_copy(evidence_summary.get("progress_summary"))
        or evidence_summary
        or _mapping_copy(handoff.get("research_pack_progress_summary"))
    )
    if not isinstance(pack, dict) or not pack:
        return {}
    deliverable = _mapping_copy(pack.get("deliverable_progress_delta") or pack.get("paper_progress_delta"))
    paper = _mapping_copy(pack.get("paper_progress_delta") or deliverable)
    platform = _mapping_copy(pack.get("platform_repair_delta"))
    blocker = _mapping_copy(pack.get("single_next_owner_blocker"))
    schema_validation = _mapping_copy(pack.get("schema_validation")) or _mapping_copy(
        evidence_summary.get("schema_validation")
    )
    return {
        "surface_kind": "mas_research_pack_progress_summary_projection",
        "body_included": False,
        "paper_body_included": False,
        "paper_progress_delta": _progress_summary_delta(paper),
        "deliverable_progress_delta": _progress_summary_delta(deliverable),
        "platform_repair_delta": {
            **_progress_summary_delta(platform),
            "counts_as_paper_progress": False,
        },
        "negative_result_count": _progress_summary_count(
            pack.get("negative_result_count"),
            pack.get("negative_failed_path_refs"),
        ),
        "route_switch_count": _progress_summary_count(
            pack.get("route_switch_count"),
            pack.get("route_switch_refs"),
        ),
        "missing_reproducibility_refs": _progress_summary_string_list(
            pack.get("missing_reproducibility_refs")
        ),
        "single_next_owner_blocker": {
            "status": _non_empty_text(blocker.get("status")) or "clear",
            "ref": _non_empty_text(blocker.get("ref")),
            "candidate_count": _number(blocker.get("candidate_count")) or 0,
            "body_included": False,
            "is_route_authority": False,
        },
        "ref_family_status": _ref_family_status(pack=pack, schema_validation=schema_validation),
        "schema_validation": _schema_validation_projection(schema_validation),
        "authority": {
            "read_model_only": True,
            "body_free": True,
            "is_route_authority": False,
            "can_authorize_route_switch": False,
            "can_authorize_artifact_mutation": False,
            "can_authorize_publication_readiness": False,
            "platform_repair_counts_as_paper_progress": False,
        },
    }


def _progress_summary_delta(value: dict[str, Any]) -> dict[str, Any]:
    refs = _progress_summary_string_list(value.get("refs"))
    return {
        "count": _number(value.get("count")) or len(refs),
        "refs": refs,
    }


def _progress_summary_count(value: object, refs: object) -> int:
    return _number(value) or len(_progress_summary_string_list(refs))


def _progress_summary_string_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _number(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None
    return None


def _ref_family_status(
    *,
    pack: dict[str, Any],
    schema_validation: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    source = _mapping_copy(schema_validation.get("ref_family_status")) or _mapping_copy(
        pack.get("ref_family_status")
    )
    result: dict[str, dict[str, Any]] = {}
    if source:
        for family, payload in source.items():
            family_id = _non_empty_text(family)
            if family_id is None:
                continue
            family_payload = _mapping_copy(payload)
            refs = _progress_summary_string_list(family_payload.get("refs"))
            result[family_id] = {
                "status": _non_empty_text(family_payload.get("status")) or ("present" if refs else "missing"),
                "ref_count": _number(family_payload.get("ref_count")) or len(refs),
                "refs": refs,
                "body_included": False,
            }
        return result
    mapping = {
        "run_manifest_ref": [pack.get("run_manifest_ref")],
        "negative_failed_path_refs": pack.get("negative_failed_path_refs"),
        "decision_trace_refs": pack.get("decision_trace_refs"),
        "artifact_lineage_refs": pack.get("artifact_lineage_refs"),
        "reproducibility_refs": pack.get("reproducibility_refs"),
        "owner_receipt_or_typed_blocker_refs": [
            *_progress_summary_string_list(pack.get("owner_receipt_refs")),
            *_progress_summary_string_list(pack.get("typed_blocker_refs")),
        ],
    }
    missing = set(_progress_summary_string_list(pack.get("missing_required_evidence_families")))
    blocker_refs = _progress_summary_string_list(pack.get("typed_blocker_refs"))
    for family, raw_refs in mapping.items():
        refs = _progress_summary_string_list(raw_refs)
        status = "present" if refs else "missing"
        if family == "owner_receipt_or_typed_blocker_refs" and blocker_refs:
            status = "blocker"
        elif family in missing and blocker_refs:
            status = "blocker"
        result[family] = {
            "status": status,
            "ref_count": len(refs),
            "refs": refs,
            "body_included": False,
        }
    return result


def _schema_validation_projection(schema_validation: dict[str, Any]) -> dict[str, Any]:
    if not schema_validation:
        return {}
    return {
        "status": _non_empty_text(schema_validation.get("status")),
        "missing_required_evidence_families": _progress_summary_string_list(
            schema_validation.get("missing_required_evidence_families")
        ),
        "fail_closed_reasons": _progress_summary_string_list(
            schema_validation.get("fail_closed_reasons")
        ),
        "placeholder_ref_families": _progress_summary_string_list(
            schema_validation.get("placeholder_ref_families")
        ),
        "forbidden_write_refs": _progress_summary_string_list(
            schema_validation.get("forbidden_write_refs")
        ),
        "owner_route_mismatch_refs": _progress_summary_string_list(
            schema_validation.get("owner_route_mismatch_refs")
        ),
        "body_free_payload": schema_validation.get("body_free_payload") is not False,
        "non_body_free_payload_detected": schema_validation.get("non_body_free_payload_detected") is True,
        "body_included": False,
    }

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.progress_portal_parts.source_refs import source_ref_allowed


def build_stage_log_summary(
    *,
    explicit: Mapping[str, Any],
    progress: Mapping[str, Any],
    row: Mapping[str, Any] | None,
    stage: str | None,
    source_refs: Iterable[object],
) -> dict[str, Any]:
    explicit_summary = _mapping(
        explicit.get("stage_log_summary")
        or explicit.get("paper_facing_stage_log_summary")
        or progress.get("stage_log_summary")
        or progress.get("paper_facing_stage_log_summary")
    )
    if explicit_summary:
        return _normalize_explicit_stage_log_summary(
            explicit_summary,
            fallback_stage=stage,
            fallback_row=row,
            fallback_source_refs=source_refs,
        )
    return _derived_stage_log_summary(
        progress=progress,
        row=row,
        stage=stage,
        source_refs=source_refs,
    )


def runtime_stage_log_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    summary = _mapping(value)
    return {
        "status": _text(summary.get("status")) or "missing",
        "stage_name": _text(summary.get("stage_name")),
        "current_owner": _text(summary.get("current_owner")),
        "problem_summary": _text(summary.get("problem_summary")),
        "stage_goal": _text(summary.get("stage_goal")),
        "paper_work_done": _string_list(summary.get("paper_work_done")),
        "changed_paper_surfaces": _string_list(summary.get("changed_paper_surfaces")),
        "outcome": _text(summary.get("outcome")),
        "progress_delta_classification": _text(summary.get("progress_delta_classification")),
        "deliverable_progress_delta": _mapping(
            summary.get("deliverable_progress_delta") or summary.get("paper_progress_delta")
        ),
        "paper_progress_delta": _mapping(summary.get("paper_progress_delta")),
        "platform_repair_delta": _mapping(summary.get("platform_repair_delta")),
        "remaining_blockers": _string_list(summary.get("remaining_blockers")),
        "evidence_refs": _dedupe_refs(summary.get("evidence_refs") or []),
        "research_pack_progress_summary": _research_pack_progress_summary(summary),
        "language_boundary": _mapping(summary.get("language_boundary")) or _language_boundary(),
        "authority": _mapping(summary.get("authority")) or _authority(),
    }


def _normalize_explicit_stage_log_summary(
    value: Mapping[str, Any],
    *,
    fallback_stage: str | None,
    fallback_row: Mapping[str, Any] | None,
    fallback_source_refs: Iterable[object],
) -> dict[str, Any]:
    row = _mapping(fallback_row)
    next_owner = _mapping(row.get("next_owner"))
    progress_delta = _progress_delta_projection(
        stage_log=_mapping(value),
        evidence={},
        quality_repair={},
        paper_asset_delta={},
        changed_paper_surfaces=_string_list(value.get("changed_paper_surfaces")),
    )
    return {
        "surface_kind": "mas_paper_facing_stage_log_summary",
        "schema_version": 1,
        "status": _text(value.get("status")) or "available",
        "stage_name": _text(value.get("stage_name")) or _text(value.get("current_stage")) or fallback_stage,
        "current_owner": _text(value.get("current_owner")) or _text(value.get("owner")) or _text(next_owner.get("owner")),
        "problem_summary": _text(value.get("problem_summary")),
        "stage_goal": _text(value.get("stage_goal")),
        "paper_work_done": _string_list(value.get("paper_work_done")),
        "changed_paper_surfaces": _string_list(value.get("changed_paper_surfaces")),
        "outcome": _text(value.get("outcome")),
        "progress_delta_classification": _text(progress_delta.get("classification")),
        "deliverable_progress_delta": _mapping(progress_delta.get("deliverable_progress_delta")),
        "paper_progress_delta": _mapping(progress_delta.get("paper_progress_delta")),
        "platform_repair_delta": _mapping(progress_delta.get("platform_repair_delta")),
        "remaining_blockers": _string_list(value.get("remaining_blockers")) or _string_list(row.get("blockers")),
        "evidence_refs": _dedupe_refs(
            [
                *_string_list(value.get("evidence_refs")),
                *_string_list(value.get("source_refs")),
                *fallback_source_refs,
            ]
        ),
        "research_pack_progress_summary": _research_pack_progress_summary(value),
        "language_boundary": _language_boundary(),
        "authority": _authority(),
    }


def _derived_stage_log_summary(
    *,
    progress: Mapping[str, Any],
    row: Mapping[str, Any] | None,
    stage: str | None,
    source_refs: Iterable[object],
) -> dict[str, Any]:
    normalized_row = _mapping(row)
    evidence = _first_mapping(
        progress.get("repair_execution_evidence"),
        _mapping(progress.get("quality_repair_batch_followthrough")).get("repair_execution_evidence"),
        _mapping(progress.get("quality_repair_batch")).get("repair_execution_evidence"),
        _mapping(progress.get("latest_quality_repair_batch")).get("repair_execution_evidence"),
    )
    quality_repair = _first_mapping(
        progress.get("quality_repair_batch_followthrough"),
        progress.get("quality_repair_batch"),
        progress.get("latest_quality_repair_batch"),
    )
    user_visible = _mapping(progress.get("user_visible_projection"))
    paper_asset_delta = _mapping(normalized_row.get("paper_asset_delta"))
    canonical_delta = _mapping(evidence.get("canonical_artifact_delta"))
    manuscript_hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    next_owner = _mapping(normalized_row.get("next_owner"))
    changed_surfaces = _changed_paper_surfaces(
        paper_asset_delta=paper_asset_delta,
        canonical_delta=canonical_delta,
        evidence=evidence,
    )
    blockers = _dedupe_texts(
        [
            *_string_list(normalized_row.get("blockers")),
            *_string_list(evidence.get("blockers")),
            *_string_list(manuscript_hygiene.get("blockers")),
        ]
    )
    evidence_refs = _dedupe_refs(
        [
            *source_refs,
            *_string_list(evidence.get("source_refs")),
            *_paths_from_ref_dicts(canonical_delta.get("artifact_refs")),
            _text(evidence.get("evidence_ledger_ref")),
            _text(evidence.get("review_ledger_ref")),
            _text(evidence.get("ai_reviewer_recheck_request_ref")),
            _text(quality_repair.get("latest_record_path")),
            _text(quality_repair.get("repair_execution_evidence_path")),
        ]
    )
    stage_log = _mapping(progress.get("stage_log_summary")) or _mapping(progress.get("paper_facing_stage_log_summary"))
    progress_delta = _progress_delta_projection(
        stage_log=stage_log,
        evidence=evidence,
        quality_repair=quality_repair,
        paper_asset_delta=paper_asset_delta,
        changed_paper_surfaces=changed_surfaces,
    )
    return {
        "surface_kind": "mas_paper_facing_stage_log_summary",
        "schema_version": 1,
        "status": "available" if evidence or normalized_row else "missing",
        "stage_name": stage,
        "current_owner": _text(next_owner.get("owner")) or _text(quality_repair.get("next_owner")),
        "problem_summary": _first_text(
            user_visible.get("current_stage_summary"),
            user_visible.get("state_summary"),
            quality_repair.get("summary"),
        ),
        "stage_goal": _first_text(
            user_visible.get("next_system_action"),
            quality_repair.get("next_confirmation_signal"),
        ),
        "paper_work_done": _paper_work_done(
            evidence=evidence,
            paper_asset_delta=paper_asset_delta,
            quality_repair=quality_repair,
        ),
        "changed_paper_surfaces": changed_surfaces,
        "outcome": _outcome(evidence=evidence, quality_repair=quality_repair),
        "progress_delta_classification": _text(progress_delta.get("classification")),
        "deliverable_progress_delta": _mapping(progress_delta.get("deliverable_progress_delta")),
        "paper_progress_delta": _mapping(progress_delta.get("paper_progress_delta")),
        "platform_repair_delta": _mapping(progress_delta.get("platform_repair_delta")),
        "remaining_blockers": blockers,
        "evidence_refs": evidence_refs,
        "research_pack_progress_summary": _research_pack_progress_summary(
            _first_mapping(
                progress.get("research_evidence_pack_summary"),
                _mapping(progress.get("domain_dispatch_evidence_record_payload")).get("research_evidence_pack_summary"),
                _mapping(_mapping(progress.get("domain_dispatch_evidence_record_payload")).get("record_payload")).get(
                    "research_evidence_pack_summary"
                ),
                _mapping(quality_repair.get("domain_dispatch_evidence_record_payload")).get(
                    "research_evidence_pack_summary"
                ),
                _mapping(_mapping(quality_repair.get("domain_dispatch_evidence_record_payload")).get("record_payload")).get(
                    "research_evidence_pack_summary"
                ),
                evidence.get("research_evidence_pack_summary"),
            )
        ),
        "language_boundary": _language_boundary(),
        "authority": _authority(),
    }


def _paper_work_done(
    *,
    evidence: Mapping[str, Any],
    paper_asset_delta: Mapping[str, Any],
    quality_repair: Mapping[str, Any],
) -> list[str]:
    explicit = _string_list(quality_repair.get("paper_work_done"))
    if explicit:
        return explicit
    result: list[str] = []
    for delta_type in _string_list(paper_asset_delta.get("delta_types")):
        result.append(f"{delta_type} surface updated")
    canonical_delta = _mapping(evidence.get("canonical_artifact_delta"))
    if canonical_delta.get("meaningful_artifact_delta") is True:
        result.append("canonical paper evidence delta recorded")
    if evidence.get("evidence_ledger_update_done") is True:
        result.append("evidence ledger updated")
    if evidence.get("review_ledger_update_done") is True:
        result.append("review ledger updated")
    if evidence.get("ai_reviewer_recheck_done") is True:
        result.append("AI reviewer recheck request recorded")
    return _dedupe_texts(result)


def _changed_paper_surfaces(
    *,
    paper_asset_delta: Mapping[str, Any],
    canonical_delta: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> list[str]:
    return _dedupe_refs(
        [
            *_string_list(paper_asset_delta.get("refs")),
            *_paths_from_ref_dicts(canonical_delta.get("artifact_refs")),
            _text(evidence.get("evidence_ledger_ref")),
            _text(evidence.get("review_ledger_ref")),
        ]
    )


def _outcome(*, evidence: Mapping[str, Any], quality_repair: Mapping[str, Any]) -> str | None:
    status = _text(evidence.get("status")) or _text(quality_repair.get("status"))
    if status == "progress_delta_candidate":
        return "paper_progress_delta_recorded"
    if status == "controller_progress_delta_candidate":
        return "controller_progress_delta_recorded"
    if status == "handoff_ready":
        return "writer_handoff_ready"
    if status == "pending":
        return "pending_required_followthrough"
    return status


def _progress_delta_projection(
    *,
    stage_log: Mapping[str, Any],
    evidence: Mapping[str, Any],
    quality_repair: Mapping[str, Any],
    paper_asset_delta: Mapping[str, Any],
    changed_paper_surfaces: list[str],
) -> dict[str, Any]:
    token_usage_total = _token_usage_total(stage_log, evidence, quality_repair)
    paper_delta = _is_paper_progress_delta(
        stage_log=stage_log,
        evidence=evidence,
        quality_repair=quality_repair,
        paper_asset_delta=paper_asset_delta,
        changed_paper_surfaces=changed_paper_surfaces,
    )
    platform_delta = _is_platform_repair_delta(
        stage_log=stage_log,
        evidence=evidence,
        quality_repair=quality_repair,
    )
    if paper_delta and not platform_delta:
        classification = "deliverable_progress"
    elif platform_delta and not paper_delta:
        classification = "platform_repair"
    elif paper_delta and platform_delta:
        classification = "mixed"
    else:
        classification = "typed_blocker"
    paper_tokens = token_usage_total if paper_delta and not platform_delta else 0
    platform_tokens = token_usage_total if platform_delta else 0
    return {
        "classification": classification,
        "deliverable_progress_delta": {
            "count": 1 if paper_delta else 0,
            "token_usage_total": paper_tokens,
        },
        "paper_progress_delta": {
            "count": 1 if paper_delta else 0,
            "token_usage_total": paper_tokens,
        },
        "platform_repair_delta": {
            "count": 1 if platform_delta else 0,
            "token_usage_total": platform_tokens,
        },
    }


def _research_pack_progress_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    pack = _mapping(value.get("research_pack_progress_summary")) or _mapping(
        value.get("progress_summary")
    )
    source = value
    if not pack and _text(value.get("surface_kind")) == "mas_research_evidence_pack_summary":
        pack = _mapping(value.get("progress_summary"))
        source = value
    if not pack:
        return {}
    deliverable = _mapping(pack.get("deliverable_progress_delta") or pack.get("paper_progress_delta"))
    paper = _mapping(pack.get("paper_progress_delta") or deliverable)
    platform = _mapping(pack.get("platform_repair_delta"))
    owner_blocker = _mapping(pack.get("single_next_owner_blocker"))
    return {
        "surface_kind": "mas_research_pack_progress_summary_projection",
        "body_included": False,
        "paper_body_included": False,
        "paper_progress_delta": _delta_count_and_refs(paper),
        "deliverable_progress_delta": _delta_count_and_refs(deliverable),
        "platform_repair_delta": {
            **_delta_count_and_refs(platform),
            "counts_as_paper_progress": False,
        },
        "negative_result_count": _count_field(
            pack.get("negative_result_count"),
            _string_list(pack.get("negative_failed_path_refs")),
        ),
        "route_switch_count": _count_field(
            pack.get("route_switch_count"),
            _string_list(pack.get("route_switch_refs")),
        ),
        "missing_reproducibility_refs": _dedupe_texts(_string_list(pack.get("missing_reproducibility_refs"))),
        "single_next_owner_blocker": {
            "status": _text(owner_blocker.get("status")) or "clear",
            "ref": _text(owner_blocker.get("ref")),
            "candidate_count": _number(owner_blocker.get("candidate_count")) or 0,
            "body_included": False,
            "is_route_authority": False,
        },
        "ref_family_status": _ref_family_status(
            pack=pack,
            schema_validation=_mapping(pack.get("schema_validation")) or _mapping(source.get("schema_validation")),
        ),
        "schema_validation": _schema_validation_projection(
            _mapping(pack.get("schema_validation")) or _mapping(source.get("schema_validation"))
        ),
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


def _delta_count_and_refs(value: Mapping[str, Any]) -> dict[str, Any]:
    refs = _dedupe_refs(_string_list(value.get("refs")))
    return {
        "count": _number(value.get("count")) or len(refs),
        "refs": refs,
    }


def _count_field(value: object, refs: Sequence[str]) -> int:
    number = _number(value)
    if number is not None:
        return number
    return len(refs)


def _ref_family_status(
    *,
    pack: Mapping[str, Any],
    schema_validation: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    source = _mapping(schema_validation.get("ref_family_status")) or _mapping(pack.get("ref_family_status"))
    result: dict[str, dict[str, Any]] = {}
    if source:
        for family, payload in source.items():
            family_id = _text(family)
            if family_id is None:
                continue
            family_payload = _mapping(payload)
            refs = _dedupe_refs(_string_list(family_payload.get("refs")))
            result[family_id] = {
                "status": _text(family_payload.get("status")) or ("present" if refs else "missing"),
                "ref_count": _number(family_payload.get("ref_count")) or len(refs),
                "refs": refs,
                "body_included": False,
            }
        return result
    blocker_refs = _dedupe_refs(_string_list(pack.get("typed_blocker_refs")))
    missing = set(_string_list(pack.get("missing_required_evidence_families")))
    families = {
        "run_manifest_ref": [pack.get("run_manifest_ref")],
        "negative_failed_path_refs": pack.get("negative_failed_path_refs"),
        "decision_trace_refs": pack.get("decision_trace_refs"),
        "artifact_lineage_refs": pack.get("artifact_lineage_refs"),
        "reproducibility_refs": pack.get("reproducibility_refs"),
        "owner_receipt_or_typed_blocker_refs": [
            *_string_list(pack.get("owner_receipt_refs")),
            *blocker_refs,
        ],
    }
    for family, raw_refs in families.items():
        refs = _dedupe_refs(_string_list(raw_refs))
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


def _schema_validation_projection(schema_validation: Mapping[str, Any]) -> dict[str, Any]:
    if not schema_validation:
        return {}
    return {
        "status": _text(schema_validation.get("status")),
        "missing_required_evidence_families": _dedupe_refs(
            _string_list(schema_validation.get("missing_required_evidence_families"))
        ),
        "fail_closed_reasons": _dedupe_refs(_string_list(schema_validation.get("fail_closed_reasons"))),
        "placeholder_ref_families": _dedupe_refs(
            _string_list(schema_validation.get("placeholder_ref_families"))
        ),
        "forbidden_write_refs": _dedupe_refs(_string_list(schema_validation.get("forbidden_write_refs"))),
        "owner_route_mismatch_refs": _dedupe_refs(
            _string_list(schema_validation.get("owner_route_mismatch_refs"))
        ),
        "body_free_payload": schema_validation.get("body_free_payload") is not False,
        "non_body_free_payload_detected": schema_validation.get("non_body_free_payload_detected") is True,
        "body_included": False,
    }


def _token_usage_total(
    stage_log: Mapping[str, Any],
    evidence: Mapping[str, Any],
    quality_repair: Mapping[str, Any],
) -> int:
    for value in (stage_log, evidence, quality_repair):
        token_usage = _mapping(value.get("token_usage")) or _mapping(value.get("usage"))
        total = _first_number(
            token_usage.get("total_tokens"),
            token_usage.get("total"),
            token_usage.get("token_total"),
            value.get("token_total"),
            value.get("token_count"),
        )
        if total is not None:
            return total
        partial = _sum_numbers(
            token_usage.get("input_tokens"),
            token_usage.get("cached_input_tokens"),
            token_usage.get("output_tokens"),
            token_usage.get("reasoning_tokens"),
        )
        if partial is not None:
            return partial
    return 0


def _is_paper_progress_delta(
    *,
    stage_log: Mapping[str, Any],
    evidence: Mapping[str, Any],
    quality_repair: Mapping[str, Any],
    paper_asset_delta: Mapping[str, Any],
    changed_paper_surfaces: list[str],
) -> bool:
    if _text(_outcome(evidence=evidence, quality_repair=quality_repair)) == "paper_progress_delta_recorded":
        return True
    if _text(evidence.get("status")) == "progress_delta_candidate":
        return True
    if _text(quality_repair.get("route_outcome")) == "write_repair_delta_recorded":
        return True
    if _text(quality_repair.get("gate_replay_status")) is not None:
        return True
    if evidence.get("ai_reviewer_recheck_done") is True or _text(evidence.get("ai_reviewer_recheck_request_ref")) is not None:
        return True
    if changed_paper_surfaces:
        return True
    if _string_list(paper_asset_delta.get("delta_types")):
        return True
    canonical_delta = _mapping(evidence.get("canonical_artifact_delta"))
    return canonical_delta.get("meaningful_artifact_delta") is True


def _is_platform_repair_delta(
    *,
    stage_log: Mapping[str, Any],
    evidence: Mapping[str, Any],
    quality_repair: Mapping[str, Any],
) -> bool:
    if _text(_outcome(evidence=evidence, quality_repair=quality_repair)) == "controller_progress_delta_recorded":
        return True
    if _text(evidence.get("status")) == "controller_progress_delta_candidate":
        return True
    blocker_text = " ".join(_string_list(stage_log.get("remaining_blockers"))).lower()
    if any(
        keyword in blocker_text
        for keyword in (
            "runtime_recovery",
            "currentness",
            "controller",
            "read_model",
            "provider",
            "opl_stage_attempt_admission_required",
        )
    ):
        return True
    text_hints = " ".join(
        text
        for text in (
            _text(stage_log.get("stage_goal")),
            _text(stage_log.get("problem_summary")),
            _text(stage_log.get("outcome")),
            _text(quality_repair.get("summary")),
            _text(quality_repair.get("route_outcome")),
            _text(evidence.get("status")),
        )
        if text is not None
    ).lower()
    return any(
        keyword in text_hints
        for keyword in (
            "controller",
            "read_model",
            "currentness",
            "provider",
            "runtime_recovery",
            "opl_stage_attempt_admission_required",
        )
    )


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


def _first_number(*values: object) -> int | None:
    for value in values:
        number = _number(value)
        if number is not None:
            return number
    return None


def _sum_numbers(*values: object) -> int | None:
    numbers = [_number(value) for value in values]
    present = [number for number in numbers if number is not None]
    if not present:
        return None
    return sum(present)


def _first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        mapped = _mapping(value)
        if mapped:
            return mapped
    return {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _paths_from_ref_dicts(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    paths: list[str] = []
    for item in value:
        mapped = _mapping(item)
        if path := _text(mapped.get("path")):
            paths.append(path)
    return paths


def _authority() -> dict[str, Any]:
    return {
        "kind": "read_only_paper_facing_stage_log_projection",
        "writes_authority_surface": False,
        "truth_owner": "MedAutoScience",
        "can_write_paper": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
    }


def _language_boundary() -> dict[str, Any]:
    return {
        "paper_body_included": False,
        "paper_body_target": False,
        "internal_review_language_allowed_in_paper_body": False,
        "summary_scope": "stage_log_read_model_only",
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


def _dedupe_refs(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if text is None or text in seen or not source_ref_allowed(text):
            continue
        seen.add(text)
        result.append(text)
    return result


def _dedupe_texts(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "build_stage_log_summary",
    "runtime_stage_log_summary",
]

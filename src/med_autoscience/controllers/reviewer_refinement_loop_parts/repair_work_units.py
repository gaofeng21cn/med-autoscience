from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.runtime_control.owner_callable_registry import owner_callable_registry


EXECUTION_CONTRACT: dict[str, Any] = {
    "contract_id": "reviewer_refinement_repair_work_units_v1",
    "dispatch_surface": "repair_work_units",
    "dispatch_authority": "owner_route_or_domain_handler",
    "direct_package_mutation_allowed": False,
    "current_package_mutation_allowed": False,
    "quality_authorization_allowed": False,
    "submission_authorization_allowed": False,
    "terminal_success_requires": [
        "owner_receipt",
        "required_outputs",
        "artifact_delta_or_gate_replay_result",
    ],
}

_PROHIBITED_OUTPUTS = [
    "paper/current_package",
    "manuscript/current_package",
    "quality_override",
    "submission_authorization",
]

_BLOCKING_GAP_SEVERITIES = {"must_fix", "important"}

_UNIT_ORDER = {
    "analysis_repair": 0,
    "text_repair": 1,
    "evidence_ledger_repair": 2,
    "review_ledger_repair": 3,
    "claim_downgrade": 4,
    "ai_reviewer_recheck": 5,
}


def build_repair_work_units(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
    worklog: list[dict[str, Any]],
    action_matrix: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    worklog_by_concern = {_text(item.get("concern_id")): item for item in worklog}
    units: list[dict[str, Any]] = []
    for action in action_matrix:
        comment_id = _text(action.get("comment_id"))
        worklog_item = worklog_by_concern.get(comment_id, {})
        if not _is_executable_finding(worklog_item):
            continue
        for work_unit_type, unit_source in _required_unit_sources(action):
            units.append(
                _repair_work_unit(
                    publication_eval=publication_eval,
                    publication_eval_path=publication_eval_path,
                    worklog_item=worklog_item,
                    action=action,
                    work_unit_type=work_unit_type,
                    unit_source=unit_source,
                )
            )
    return _batch_units_by_callable_surface(publication_eval=publication_eval, units=_dedupe_units(units))


def _is_executable_finding(worklog_item: Mapping[str, Any]) -> bool:
    kind = _text(worklog_item.get("kind"))
    if kind == "quality_dimension":
        return _text(worklog_item.get("status")) not in {"", "ready"}
    if kind == "publication_gap":
        return _text(worklog_item.get("severity")) in _BLOCKING_GAP_SEVERITIES
    return False


def _required_unit_sources(action: Mapping[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    sources: list[tuple[str, dict[str, Any]]] = []
    work_units = _mapping(action.get("work_units"))
    for work_unit_type in (
        "analysis_repair",
        "text_repair",
        "evidence_ledger_repair",
        "review_ledger_repair",
        "claim_downgrade",
        "ai_reviewer_recheck",
    ):
        source = _mapping(work_units.get(work_unit_type))
        if source and source.get("required") is True:
            sources.append((work_unit_type, source))
    if sources:
        return sources
    repair_routes = _mapping(action.get("repair_routes"))
    for work_unit_type in (
        "analysis_repair",
        "text_repair",
        "ai_reviewer_recheck",
    ):
        source = _mapping(repair_routes.get(work_unit_type))
        if source and source.get("required") is True:
            sources.append((work_unit_type, source))
    return sources


def _repair_work_unit(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
    worklog_item: Mapping[str, Any],
    action: Mapping[str, Any],
    work_unit_type: str,
    unit_source: Mapping[str, Any],
) -> dict[str, Any]:
    comment_id = _text(action.get("comment_id"))
    source_refs = _source_refs(
        publication_eval_path=publication_eval_path,
        worklog_item=worklog_item,
        unit_source=unit_source,
    )
    source_fingerprint = _source_fingerprint(
        publication_eval=publication_eval,
        action=action,
        worklog_item=worklog_item,
        work_unit_type=work_unit_type,
        source_refs=source_refs,
    )
    contract = _owner_contract(work_unit_type)
    unit_id = _unit_id(
        publication_eval=publication_eval,
        comment_id=comment_id,
        work_unit_type=work_unit_type,
    )
    return {
        "unit_id": unit_id,
        "work_unit_type": work_unit_type,
        "owner": _text(contract.get("owner")),
        "callable_surface": _text(contract.get("callable_surface")),
        "required_inputs": _required_inputs(
            publication_eval_path=publication_eval_path,
            source_refs=source_refs,
            work_unit_type=work_unit_type,
        ),
        "required_outputs": _required_outputs(work_unit_type),
        "artifact_delta_predicate": _artifact_delta_predicate(work_unit_type),
        "gate_replay_target": _gate_replay_target(work_unit_type),
        "idempotency_key": f"reviewer_refinement_loop:{unit_id}:{source_fingerprint}",
        "source_fingerprint": source_fingerprint,
        "source_refs": source_refs,
        "retry_budget": {
            "max_attempts": 2,
            "remaining_attempts": 2,
            "retry_policy": "idempotent_owner_replay_only",
        },
        "source_comment_id": comment_id,
        "target_section": _text(unit_source.get("target_section")) or _text(action.get("target_section")),
        "target_claim": _text(unit_source.get("target_claim")) or None,
        "direct_package_mutation_allowed": False,
        "current_package_mutation_allowed": False,
        "quality_authorization_allowed": False,
        "submission_authorization_allowed": False,
        "prohibited_outputs": list(_PROHIBITED_OUTPUTS),
    }


def _owner_contract(work_unit_type: str) -> dict[str, Any]:
    registry = owner_callable_registry()
    if work_unit_type == "ai_reviewer_recheck":
        return dict(registry["ai_reviewer"])
    return dict(registry["quality_repair_batch"])


def _required_inputs(
    *,
    publication_eval_path: Path,
    source_refs: list[str],
    work_unit_type: str,
) -> list[str]:
    inputs = ["publication_eval/latest.json"]
    if work_unit_type == "ai_reviewer_recheck":
        inputs.extend(ref for ref in source_refs if ref != str(publication_eval_path))
    else:
        inputs.extend(ref for ref in source_refs[1:] if ref != str(publication_eval_path))
    return _dedupe_text(inputs)


def _required_outputs(work_unit_type: str) -> list[str]:
    if work_unit_type == "ai_reviewer_recheck":
        return ["artifacts/publication_eval/latest.json"]
    if work_unit_type == "text_repair":
        return [
            "paper/manuscript.md",
            "paper/review/review_ledger.json",
            "artifacts/controller/quality_repair_batch/latest.json",
        ]
    if work_unit_type == "claim_downgrade":
        return [
            "paper/manuscript.md",
            "paper/claim_evidence_map.json",
            "artifacts/controller/quality_repair_batch/latest.json",
        ]
    if work_unit_type == "evidence_ledger_repair":
        return [
            "paper/evidence_ledger.json",
            "artifacts/controller/quality_repair_batch/latest.json",
        ]
    if work_unit_type == "review_ledger_repair":
        return [
            "paper/review/review_ledger.json",
            "artifacts/controller/quality_repair_batch/latest.json",
        ]
    return [
        "artifacts/results/main_result.json",
        "paper/evidence_ledger.json",
        "artifacts/controller/quality_repair_batch/latest.json",
    ]


def _artifact_delta_predicate(work_unit_type: str) -> str:
    if work_unit_type == "ai_reviewer_recheck":
        return "ai_reviewer_judgement_updated"
    if work_unit_type == "text_repair":
        return "manuscript_or_review_ledger_delta_without_package_mutation"
    if work_unit_type == "claim_downgrade":
        return "claim_wording_or_claim_map_delta_without_package_mutation"
    if work_unit_type == "evidence_ledger_repair":
        return "evidence_ledger_delta_without_package_mutation"
    if work_unit_type == "review_ledger_repair":
        return "review_ledger_delta_without_package_mutation"
    return "analysis_result_or_evidence_ledger_delta_without_package_mutation"


def _gate_replay_target(work_unit_type: str) -> str:
    if work_unit_type == "ai_reviewer_recheck":
        return "controller_decisions/latest.json"
    return "publication_eval/latest.json"


def _source_refs(
    *,
    publication_eval_path: Path,
    worklog_item: Mapping[str, Any],
    unit_source: Mapping[str, Any],
) -> list[str]:
    refs = [str(publication_eval_path)]
    refs.extend(_text_list(unit_source.get("ledger_refs")))
    refs.extend(_text_list(worklog_item.get("artifact_refs")))
    refs.extend(_text_list(worklog_item.get("evidence_refs")))
    for snapshot in _list_of_mappings(worklog_item.get("snapshot_refs")):
        refs.append(_text(snapshot.get("source_artifact_path")))
    return _dedupe_text(refs)


def _source_fingerprint(
    *,
    publication_eval: Mapping[str, Any],
    action: Mapping[str, Any],
    worklog_item: Mapping[str, Any],
    work_unit_type: str,
    source_refs: list[str],
) -> str:
    payload = {
        "source_eval_id": _text(publication_eval.get("eval_id")),
        "study_id": _text(publication_eval.get("study_id")),
        "quest_id": _text(publication_eval.get("quest_id")),
        "comment_id": _text(action.get("comment_id")),
        "work_unit_type": work_unit_type,
        "action_type": _text(action.get("action_type")),
        "reviewer_concern": _text(worklog_item.get("reviewer_concern")),
        "source_refs": source_refs,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _unit_id(
    *,
    publication_eval: Mapping[str, Any],
    comment_id: str,
    work_unit_type: str,
) -> str:
    study_id = _slug(_text(publication_eval.get("study_id")) or "unknown-study")
    quest_id = _slug(_text(publication_eval.get("quest_id")) or "unknown-quest")
    comment_slug = _slug(comment_id or "unknown-comment")
    return f"{study_id}::{quest_id}::{comment_slug}::{work_unit_type}"


def _dedupe_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for unit in units:
        key = (str(unit["unit_id"]), str(unit["source_fingerprint"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(unit)
    return deduped


def _batch_units_by_callable_surface(
    *,
    publication_eval: Mapping[str, Any],
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        callable_surface = _text(unit.get("callable_surface"))
        if not callable_surface:
            continue
        grouped.setdefault(callable_surface, []).append(unit)
    batches = [
        _batch_unit_for_callable_surface(
            publication_eval=publication_eval,
            callable_surface=callable_surface,
            units=group,
        )
        for callable_surface, group in grouped.items()
    ]
    return sorted(
        batches,
        key=lambda item: (
            0 if item.get("owner") == "quality_repair_batch" else 1,
            str(item["callable_surface"]),
        ),
    )


def _batch_unit_for_callable_surface(
    *,
    publication_eval: Mapping[str, Any],
    callable_surface: str,
    units: list[dict[str, Any]],
) -> dict[str, Any]:
    ordered_units = sorted(
        units,
        key=lambda item: (
            _UNIT_ORDER.get(str(item["work_unit_type"]), 99),
            str(item["source_comment_id"]),
            str(item["unit_id"]),
        ),
    )
    first = dict(ordered_units[0])
    source_comment_ids = _dedupe_text([_text(unit.get("source_comment_id")) for unit in units])
    source_refs: list[str] = []
    required_inputs: list[str] = []
    required_outputs: list[str] = []
    work_unit_types: list[str] = []
    for unit in ordered_units:
        source_refs.extend(_text_list(unit.get("source_refs")))
        required_inputs.extend(_text_list(unit.get("required_inputs")))
        required_outputs.extend(_text_list(unit.get("required_outputs")))
        work_unit_types.append(_text(unit.get("work_unit_type")))
    source_refs = _dedupe_text(source_refs)
    required_inputs = _dedupe_text(required_inputs)
    required_outputs = _dedupe_text(required_outputs)
    unit_id = _batch_unit_id(publication_eval=publication_eval, callable_surface=callable_surface)
    source_fingerprint = _batch_source_fingerprint(
        publication_eval=publication_eval,
        callable_surface=callable_surface,
        source_comment_ids=source_comment_ids,
        source_refs=source_refs,
        units=ordered_units,
    )
    first.update(
        {
            "unit_id": unit_id,
            "work_unit_type": "ai_reviewer_recheck"
            if first.get("owner") == "ai_reviewer"
            else "quality_repair_batch",
            "required_inputs": required_inputs,
            "required_outputs": required_outputs,
            "idempotency_key": f"reviewer_refinement_loop:{unit_id}:{source_fingerprint}",
            "source_fingerprint": source_fingerprint,
            "source_refs": source_refs,
            "retry_budget": {
                "max_attempts": 1,
                "remaining_attempts": 1,
                "retry_policy": "single_batch_owner_replay_only",
            },
            "source_comment_id": f"batch:{callable_surface}",
            "source_comment_ids": source_comment_ids,
            "batch_scope": "study_callable_surface",
            "batched_work_unit_count": len(ordered_units),
            "batched_work_unit_types": _dedupe_text(work_unit_types),
            "batched_work_units": [
                {
                    "unit_id": _text(unit.get("unit_id")),
                    "work_unit_type": _text(unit.get("work_unit_type")),
                    "source_comment_id": _text(unit.get("source_comment_id")),
                    "target_section": _text(unit.get("target_section")),
                    "target_claim": _text(unit.get("target_claim")) or None,
                    "source_fingerprint": _text(unit.get("source_fingerprint")),
                    "source_refs": _text_list(unit.get("source_refs")),
                    "required_outputs": _text_list(unit.get("required_outputs")),
                }
                for unit in ordered_units
            ],
        }
    )
    return first


def _batch_unit_id(*, publication_eval: Mapping[str, Any], callable_surface: str) -> str:
    study_id = _slug(_text(publication_eval.get("study_id")) or "unknown-study")
    quest_id = _slug(_text(publication_eval.get("quest_id")) or "unknown-quest")
    surface = _slug(callable_surface)
    return f"{study_id}::{quest_id}::{surface}::batch"


def _batch_source_fingerprint(
    *,
    publication_eval: Mapping[str, Any],
    callable_surface: str,
    source_comment_ids: list[str],
    source_refs: list[str],
    units: list[dict[str, Any]],
) -> str:
    payload = {
        "source_eval_id": _text(publication_eval.get("eval_id")),
        "study_id": _text(publication_eval.get("study_id")),
        "quest_id": _text(publication_eval.get("quest_id")),
        "callable_surface": callable_surface,
        "source_comment_ids": source_comment_ids,
        "source_refs": source_refs,
        "unit_fingerprints": [_text(unit.get("source_fingerprint")) for unit in units],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _dedupe_text(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    normalized = normalized.replace(".", "_")
    return normalized.strip("_") or "unknown"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


__all__ = [
    "EXECUTION_CONTRACT",
    "build_repair_work_units",
]

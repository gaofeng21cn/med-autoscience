from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.study_domain_transition_table_parts import ai_reviewer_transitions
from med_autoscience.controllers.study_domain_transition_table_parts import family_transition_spec


SURFACE = "study_domain_transition_table"
SCHEMA_VERSION = 1


def build_domain_transition_table(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_rows = [dict(row) for row in rows]
    counts: dict[str, int] = {}
    for row in normalized_rows:
        decision_type = _text(row.get("decision_type")) or "unknown"
        counts[decision_type] = counts.get(decision_type, 0) + 1
    family_spec = build_family_transition_spec(normalized_rows)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "table_role": "domain_transition_read_model_oracle",
        "authority_boundary": {
            "owner": "MedAutoScience",
            "runner_owner": "OPL Framework",
            "can_write_domain_truth": False,
            "can_execute_generic_state_machine": False,
            "purpose": "MAS-owned domain transition spec/read model; OPL remains responsible for generic runner execution.",
        },
        "counts": counts,
        "rows": normalized_rows,
        "family_transition_spec": family_spec,
        "family_transition_matrix_cases": build_family_transition_matrix_cases(normalized_rows),
    }


build_family_transition_spec = family_transition_spec.build_family_transition_spec
build_family_transition_matrix_cases = family_transition_spec.build_family_transition_matrix_cases
build_family_transition_spec_descriptor = family_transition_spec.build_family_transition_spec_descriptor


def transition(
    *,
    study_id: str,
    decision_type: str,
    route_target: str,
    next_work_unit: Mapping[str, Any],
    controller_action: str,
    owner: str,
    typed_blocker: Mapping[str, Any] | None,
    guard_boundary: Mapping[str, Any],
    source_refs: Iterable[str],
    completion_receipt_consumption: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    materialized_source_refs = list(source_refs)
    payload = {
        "study_id": study_id,
        "decision_type": decision_type,
        "route_target": route_target,
        "next_work_unit": dict(next_work_unit),
        "controller_action": controller_action,
        "owner": owner,
        "typed_blocker": dict(typed_blocker) if typed_blocker else None,
        "guard_boundary": dict(guard_boundary),
        "source_refs": materialized_source_refs,
    }
    if decision_type == "ai_reviewer_re_eval":
        payload["next_action"] = ai_reviewer_transitions.build_ai_reviewer_next_action(
            study_id=study_id,
            next_work_unit=next_work_unit,
            controller_action=controller_action,
            owner=owner,
            guard_boundary=guard_boundary,
            source_refs=materialized_source_refs,
        )
    elif decision_type == "route_back_same_line":
        payload["next_action"] = ai_reviewer_transitions.build_route_back_next_action(
            study_id=study_id,
            route_target=route_target,
            next_work_unit=next_work_unit,
            controller_action=controller_action,
            owner=owner,
            guard_boundary=guard_boundary,
            source_refs=materialized_source_refs,
        )
    if completion_receipt_consumption:
        payload["completion_receipt_consumption"] = dict(completion_receipt_consumption)
    return payload


def work_unit(unit_id: str, lane: str, summary: str) -> dict[str, str]:
    return {"unit_id": unit_id, "lane": lane, "summary": summary}


def typed_blocker(
    *,
    blocker_id: str,
    blocker_type: str,
    summary: str,
    required_owner_surface: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "blocker_type": blocker_type,
        "summary": summary,
        "required_owner_surface": required_owner_surface,
        "write_permitted": False,
    }


def guard_boundary(
    *,
    required_owner_surface: str | None = None,
    mas_owner_apply_receipt_required: bool = False,
    opl_generic_runner_may_resume: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "runner_boundary": "mas_domain_read_model_only",
        "can_write_domain_truth": False,
        "can_execute_generic_state_machine": False,
        "opl_generic_runner_may_resume": opl_generic_runner_may_resume,
        "mas_owner_apply_receipt_required": mas_owner_apply_receipt_required,
    }
    if required_owner_surface:
        payload["required_owner_surface"] = required_owner_surface
    return payload


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE",
    "build_domain_transition_table",
    "build_family_transition_matrix_cases",
    "build_family_transition_spec",
    "build_family_transition_spec_descriptor",
    "guard_boundary",
    "transition",
    "typed_blocker",
    "work_unit",
]

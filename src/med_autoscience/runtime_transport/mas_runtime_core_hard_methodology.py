from __future__ import annotations

from collections.abc import Mapping
from typing import Any


HARD_METHODOLOGY_TOKENS = frozenset(
    {
        "hdl_unit_standardized_sensitivity",
        "unit_standardized_model_application_or_sensitivity",
        "unit_harmonized_external_validation_rerun",
        "unit_harmonized_validation_uncertainty_and_grouped_calibration",
        "unit_harmonized_rerun_required",
        "unit_harmonization",
        "unit_harmonized",
        "unit_standardized",
        "unit-standardized",
        "unit-harmonized",
        "harmonization_route_back",
        "provenance_limited_harmonization_audit",
        "methodology_reframe_route_decision",
        "methodology_reframe_required",
        "terminal_source_provenance_blocker_consumed",
        "current_transport_claim_must_not_be_used_as_medical_conclusion",
    }
)


def contract_prompt_section(
    *,
    authorization: Mapping[str, Any],
    work_unit_ids: list[str],
) -> str:
    if not authorization_has_hard_methodology_target(authorization):
        return ""
    next_work_unit = _mapping(authorization.get("next_work_unit"))
    if _text(next_work_unit.get("selected_route_option")) == "provenance_limited_harmonization_audit":
        return (
            "Hard methodology/provenance-limited reframe contract:\n"
            "- This work unit has already consumed the terminal HDL/unit-harmonization and transported-model "
            "source-provenance blockers. Do not re-run the contaminated transported-score analysis and do not "
            "treat the current transportability failure estimates as medical conclusions.\n"
            "- Materialize a provenance-limited harmonization audit and a concrete reproducible-model rebuild, "
            "stop-loss, or human-gate route before manuscript claim work.\n"
            "- A prose/source-documentation note, AI-reviewer rerun, package refresh, or generic completed closeout "
            "is not sufficient for this target.\n"
            "- If no valid rebuild/audit route can be completed in this turn, write a blocked closeout naming the "
            "missing MAS owner surface and preserve the terminal source-provenance blocker.\n\n"
        )
    if "methodology_reframe_route_decision" in work_unit_ids:
        return (
            "Hard methodology/source-provenance terminal blocker contract:\n"
            "- The source provenance owner has completed bounded search and could not recover the original "
            "transported Cox model provenance. Do not route back to `source_provenance_owner` for the same "
            "search unless a newer analysis-harmonization handoff supersedes that result.\n"
            "- Invoke `decision.methodology_reframe_route_decision` so MAS selects a stop-loss, "
            "provenance-limited harmonization audit, clean reproducible-model rebuild, or human gate route.\n"
            "- Do not write the paper body, package surfaces, publication quality verdict, or medical "
            "transportability conclusion in this turn.\n"
            "- If the decision owner callable is unavailable, write a blocked closeout with "
            "blocked_reason=owner_callable_surface_missing and next_owner=MAS/controller.\n\n"
        )
    return (
        "Hard methodology/unit-harmonization contract:\n"
        "- This work unit contains a hard HDL/unit-standardization or variable-harmonization target. "
        "The next valid domain step is `unit_harmonized_external_validation_rerun` under "
        "`analysis_harmonization_owner`, or an explicit typed blocker for that owner.\n"
        "- The MAS owner callable surface is "
        "`analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`.\n"
        "- A prose/source-documentation note or generic completed closeout is not sufficient for this target.\n"
        "- Invoke the MAS owner callable before deciding the turn closeout owner. If the owner result returns "
        "`blocking_owner_route.next_owner=source_provenance_owner` and "
        "`blocking_owner_route.next_work_unit=recover_transport_model_provenance`, write the blocked closeout with "
        "blocked_reason=unit_harmonized_rerun_required, next_owner=source_provenance_owner, and include "
        "next_work_unit=recover_transport_model_provenance in the durable handoff payload when the surface supports "
        "it.\n"
        "- If the owner result keeps the block inside analysis harmonization, write the blocked closeout with "
        "blocked_reason=unit_harmonized_rerun_required, next_owner=analysis_harmonization_owner, and include "
        "next_work_unit=unit_harmonized_external_validation_rerun in the durable handoff payload when the surface "
        "supports it.\n"
        "- Do not route back to publication_gate, AI reviewer, package build, or manuscript polish until this hard "
        "methodology target has rerun evidence or the typed owner handoff is recorded.\n\n"
    )


def authorization_has_hard_methodology_target(authorization: Mapping[str, Any]) -> bool:
    values: list[str] = []
    for key in ("work_unit_id", "route_key_question", "route_rationale", "source_route_key_question"):
        if text := _text(authorization.get(key)):
            values.append(text.lower())
    next_work_unit = _mapping(authorization.get("next_work_unit"))
    for key in (
        "unit_id",
        "summary",
        "required_owner",
        "required_next_work_unit",
        "typed_blocker",
        "selected_route_option",
        "required_output",
    ):
        if text := _text(next_work_unit.get(key)):
            values.append(text.lower())
    if next_work_unit.get("terminal_source_provenance_blocker_consumed") is True:
        values.append("terminal_source_provenance_blocker_consumed")
    if next_work_unit.get("current_transport_claim_must_not_be_used_as_medical_conclusion") is True:
        values.append("current_transport_claim_must_not_be_used_as_medical_conclusion")
    for target in authorization.get("specificity_targets") or []:
        if not isinstance(target, Mapping):
            continue
        for key in ("target_id", "blocking_reason", "source_path"):
            if text := _text(target.get(key)):
                values.append(text.lower())
    return any(any(token in value for token in HARD_METHODOLOGY_TOKENS) for value in values)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "HARD_METHODOLOGY_TOKENS",
    "authorization_has_hard_methodology_target",
    "contract_prompt_section",
]

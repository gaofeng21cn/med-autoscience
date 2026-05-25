from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def prompt_contract_error(prompt_contract: Mapping[str, Any], *, forbidden_surfaces: Iterable[str]) -> str | None:
    for key in ("prompt_budget", "compact_evidence_packet_ref", "do_not_repeat", "repeat_suppression_key"):
        if key not in prompt_contract:
            return f"{key}_missing"
    if prompt_contract.get("do_not_repeat") is not True:
        return "do_not_repeat_guard_missing"
    story_surface_write_handoff = _story_surface_write_handoff_prompt_contract(prompt_contract)
    for key in (
        "paper_package_mutation_allowed",
        "quality_gate_relaxation_allowed",
        "manual_study_patch_allowed",
        "medical_claim_authoring_allowed",
    ):
        if key == "medical_claim_authoring_allowed" and story_surface_write_handoff:
            if prompt_contract.get(key) is not True:
                return f"{key}_guard_missing"
            continue
        if prompt_contract.get(key) is not False:
            return f"{key}_guard_missing"
    forbidden = {
        text
        for item in prompt_contract.get("forbidden_surfaces") or []
        if (text := _text(item)) is not None
    }
    if _record_only_ai_reviewer_handoff_prompt_contract(prompt_contract):
        if not _record_only_ai_reviewer_handoff_forbidden_surfaces(forbidden):
            return "forbidden_surfaces_incomplete"
        return None
    if story_surface_write_handoff:
        if not _story_surface_write_handoff_forbidden_surfaces(forbidden):
            return "forbidden_surfaces_incomplete"
        return None
    if not set(forbidden_surfaces).issubset(forbidden):
        return "forbidden_surfaces_incomplete"
    return None


def _story_surface_write_handoff_prompt_contract(prompt_contract: Mapping[str, Any]) -> bool:
    if _text(prompt_contract.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(prompt_contract.get("next_executable_owner")) != "write":
        return False
    route = _mapping(prompt_contract.get("owner_route"))
    if _text(route.get("next_owner")) != "write":
        return False
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if route_reason != "manuscript_story_surface_delta_missing":
        return False
    if "run_quality_repair_batch" not in {
        text for value in route.get("allowed_actions") or [] if (text := _text(value)) is not None
    }:
        return False
    allowed = {
        text
        for item in prompt_contract.get("allowed_write_surfaces") or []
        if (text := _text(item)) is not None
    }
    return allowed.issubset(
        {
            "paper/draft.md",
            "paper/build/review_manuscript.md",
            "paper/claim_evidence_map.json",
            "paper/evidence_ledger.json",
            "paper/review/**",
        }
    )


def _story_surface_write_handoff_forbidden_surfaces(forbidden: set[str]) -> bool:
    return {
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    }.issubset(forbidden)


def _record_only_ai_reviewer_handoff_prompt_contract(prompt_contract: Mapping[str, Any]) -> bool:
    if _text(prompt_contract.get("action_type")) != "return_to_ai_reviewer_workflow":
        return False
    if _text(prompt_contract.get("next_executable_owner")) != "ai_reviewer":
        return False
    if _text(prompt_contract.get("required_output_surface")) != (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    ):
        return False
    request = _mapping(prompt_contract.get("ai_reviewer_record_production_request"))
    authority = _mapping(request.get("authority_contract"))
    if authority.get("record_only_surface") is not True:
        return False
    if authority.get("publication_eval_latest_write_allowed") is not False:
        return False
    if authority.get("controller_decision_write_allowed") is not False:
        return False
    allowed = {
        text
        for item in prompt_contract.get("allowed_write_surfaces") or []
        if (text := _text(item)) is not None
    }
    return allowed == {"artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"}


def _record_only_ai_reviewer_handoff_forbidden_surfaces(forbidden: set[str]) -> bool:
    return {
        "paper/**",
        "manuscript/**",
        "paper/submission_minimal/**",
        "manuscript/current_package/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
        ".ds/**",
    }.issubset(forbidden)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["prompt_contract_error"]

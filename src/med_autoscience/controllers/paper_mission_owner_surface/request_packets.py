from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_action_requests
from med_autoscience.controllers import stage_knowledge_entry
from med_autoscience.controllers.ai_reviewer_publication_eval.input_contract import (
    default_ai_reviewer_request_input_refs,
)
from med_autoscience.controllers.ai_reviewer_publication_eval.record_contracts import (
    ai_reviewer_request_with_latest_record,
)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def publication_eval_source_action(publication_eval_payload: Mapping[str, Any]) -> dict[str, Any]:
    actions = publication_eval_payload.get("recommended_actions")
    if isinstance(actions, list):
        for action in actions:
            if isinstance(action, Mapping):
                return dict(action)
    return {
        "action_id": "publication-gate-specificity-required",
        "next_work_unit": {"unit_id": "gate_needs_specificity"},
        "work_unit_fingerprint": "publication-blockers::specificity_required",
    }


def materialize_request_packets(
    *,
    study_root: Path,
    workspace_root: Path,
    study_id: str,
    quest_id: str | None,
    quest_root: Path | None = None,
    publication_eval_payload: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> None:
    action_types = {_text(action.get("action_type")) for action in actions}
    if "publication_gate_specificity_required" in action_types:
        blocking_gaps = publication_eval_payload.get("gaps")
        packet = domain_action_requests.build_publication_gate_specificity_request(
            study_id=study_id,
            quest_id=quest_id,
            source_surface="publication_eval/latest.json",
            source_action=publication_eval_source_action(publication_eval_payload),
            blocking_gaps=[
                gap for gap in blocking_gaps
                if isinstance(gap, Mapping)
            ] if isinstance(blocking_gaps, list) else [],
        )
        packet["required_target_kinds"] = list(packet.get("requested_target_types") or [])
        packet["request_visibility"] = "owner_visible_checklist"
        _write_json(
            study_root / "artifacts" / "supervision" / "requests" / "publication_gate_specificity" / "latest.json",
            packet,
        )
    if "return_to_ai_reviewer_workflow" in action_types:
        reviewer_action = _first_action(actions, "return_to_ai_reviewer_workflow")
        stage_entry = stage_knowledge_entry.build_stage_knowledge_entry(
            study_id=study_id,
            stage="review",
            stage_folder_refs=_mapping_list(publication_eval_payload.get("stage_folder_refs")),
            state_index_refs=_mapping_list(publication_eval_payload.get("state_index_refs")),
        )
        handoff_reason = _text(reviewer_action.get("reason"))
        route_back_target = (
            _text(reviewer_action.get("request_owner"))
            or _text(reviewer_action.get("recommended_owner"))
            or _text(reviewer_action.get("owner"))
            or "ai_reviewer"
        )
        packet = domain_action_requests.build_ai_reviewer_publication_eval_request(
            study_id=study_id,
            quest_id=quest_id,
            source_surface="paper_mission_owner_surface",
            workflow_state={
                "quality_authority": {
                    "owner": _text(_mapping(publication_eval_payload.get("assessment_provenance")).get("owner")),
                    "state": "projection_only",
                },
                "route_back": {
                    "required": True,
                    "target": "ai_reviewer",
                },
                "blockers": ["publication_eval_not_ai_reviewer_authority"],
            },
            input_refs=default_ai_reviewer_request_input_refs(
                study_root=study_root,
            ),
        )
        packet = stage_knowledge_entry.inject_stage_knowledge_entry(packet, stage_entry=stage_entry)
        packet["target_assessment_owner"] = "ai_reviewer"
        packet["may_authorize_quality_gate"] = False
        if handoff_reason:
            packet["blockers"] = [handoff_reason]
        if handoff_reason == "analysis_harmonization_completed_ai_reviewer_review_required":
            lifecycle = dict(_mapping(packet.get("record_requirements")))
            lifecycle["blocked_reason"] = "ai_reviewer_record_stale_after_unit_harmonized_rerun"
            if required_refs := [
                ref for ref in reviewer_action.get("required_currentness_refs") or [] if _text(ref)
            ]:
                lifecycle["required_currentness_refs"] = required_refs
            if source_ref := _text(reviewer_action.get("source_ref")):
                lifecycle["source_ref"] = source_ref
            packet["record_requirements"] = lifecycle
        if handoff_reason == "ai_reviewer_record_stale_after_current_manuscript":
            lifecycle = dict(_mapping(packet.get("record_requirements")))
            lifecycle["blocked_reason"] = "ai_reviewer_record_stale_after_current_manuscript"
            if stale_record_ref := _text(reviewer_action.get("stale_record_ref")):
                lifecycle["stale_record_ref"] = stale_record_ref
            if required_refs := [
                ref for ref in reviewer_action.get("required_currentness_refs") or [] if _text(ref)
            ]:
                lifecycle["required_currentness_refs"] = required_refs
            if source_ref := _text(reviewer_action.get("source_ref")):
                lifecycle["source_ref"] = source_ref
            packet["record_requirements"] = lifecycle
        if handoff_reason == "ai_reviewer_record_stale_after_current_inputs":
            lifecycle = dict(_mapping(packet.get("record_requirements")))
            lifecycle["blocked_reason"] = "ai_reviewer_record_stale_after_current_inputs"
            if stale_record_ref := _text(reviewer_action.get("stale_record_ref")):
                lifecycle["stale_record_ref"] = stale_record_ref
            if required_refs := [
                ref for ref in reviewer_action.get("required_currentness_refs") or [] if _text(ref)
            ]:
                lifecycle["required_currentness_refs"] = required_refs
            if source_ref := _text(reviewer_action.get("source_ref")):
                lifecycle["source_ref"] = source_ref
            packet["record_requirements"] = lifecycle
        if next_work_unit := _text(reviewer_action.get("next_work_unit")):
            packet["source_workflow_ref"] = {
                **_mapping(packet.get("source_workflow_ref")),
                "next_work_unit": next_work_unit,
                "route_back_target": route_back_target,
            }
        ai_reviewer_request_with_latest_record(
            study_root=study_root,
            packet=packet,
        )


def _first_action(actions: list[dict[str, Any]], action_type: str) -> dict[str, Any]:
    for action in actions:
        if _text(action.get("action_type")) == action_type:
            return dict(action)
    return {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]

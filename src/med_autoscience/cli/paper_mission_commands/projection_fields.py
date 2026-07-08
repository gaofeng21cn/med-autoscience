from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _compact_mapping,
    _compact_non_null_mapping,
    _first_mapping,
    _first_text,
    _load_json_object,
    _mapping,
    _mapping_list,
    _optional_text,
    _text_list,
)
from med_autoscience.cli.paper_mission_commands.materialized_readback_context import (
    materialized_mission_path_matches,
)
from med_autoscience.cli.paper_mission_output_roots import (
    PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH,
    PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH,
)


def paper_mission_inspect_projection_fields(
    *,
    stage_closure_decision: Mapping[str, Any],
    projection_fields: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _mapping(stage_closure_decision)
    outcome = _mapping(decision.get("outcome"))
    return _compact_mapping(
        {
            "repair_budget": _first_mapping(
                _mapping(decision.get("repair_budget")),
                _mapping(projection_fields.get("repair_budget")),
                _mapping(projection_fields.get("route_back_budget")),
            )
            or None,
            "stage_closure": _compact_mapping(
                {
                    "projection_status": decision.get("projection_status"),
                    "decision_ref": decision.get("decision_ref"),
                    "outcome": outcome or None,
                    "outcome_kind": _first_text(
                        decision.get("outcome_kind"),
                        outcome.get("kind"),
                    ),
                    "next_transition": _first_text(
                        _mapping(outcome.get("next_transition")).get("transition_kind"),
                        outcome.get("transition_kind"),
                        outcome.get("next_action"),
                    ),
                    "package_kind": _first_text(
                        decision.get("package_kind"),
                        outcome.get("package_kind"),
                    ),
                    "known_blockers": _text_list(decision.get("known_blockers")),
                    "repair_budget": _first_mapping(
                        _mapping(decision.get("repair_budget")),
                        _mapping(projection_fields.get("repair_budget")),
                        _mapping(projection_fields.get("route_back_budget")),
                    )
                    or None,
                }
            )
            or None,
            "current_package": paper_mission_current_package_projection(projection_fields),
        }
    )


def paper_mission_current_package_projection(
    projection_fields: Mapping[str, Any],
) -> dict[str, Any]:
    current = _mapping(projection_fields.get("current_package"))
    if current:
        return current
    return {
        "status": "missing",
        "package_kind": "current_package",
        "can_submit": False,
        "known_blockers": ["current_package_missing"],
    }


def paper_mission_delivery_projection_fields(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_root: Path,
) -> dict[str, Any]:
    from med_autoscience.controllers.study_progress.delivery_inspection import (
        read_delivery_inspection_projection,
    )

    delivery = read_delivery_inspection_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )
    current_package = _mapping(_mapping(delivery).get("current_package"))
    return {"current_package": current_package} if current_package else {}


def paper_mission_materialized_projection_fields(
    *,
    transaction_readback: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    owner_answer = _mapping(
        transaction_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    next_decision = _mapping(transaction_readback.get("next_owner_or_human_decision"))
    artifact_delta_refs = _mapping_list(transaction.get("artifact_delta_refs"))
    return _compact_non_null_mapping(
        {
            "artifact_delta_refs": artifact_delta_refs or None,
            "owner_answer_shape": _first_text(
                owner_answer.get("owner_answer_shape"),
                decision.get("owner_answer_shape"),
                decision.get("decision_kind"),
            ),
            "paper_facing_delta_ref": _first_text(
                owner_answer.get("paper_facing_delta_ref"),
                decision.get("paper_facing_delta_ref"),
            ),
            "semantic_progress_signature": owner_answer.get(
                "semantic_progress_signature"
            ),
            "route_back_budget": owner_answer.get("route_back_budget"),
            "mission_executor_fallback_action": owner_answer.get(
                "mission_executor_fallback_action"
            ),
            "carry_forward_risk_receipt_ref": owner_answer.get(
                "carry_forward_risk_receipt_ref"
            ),
            "next_owner": _first_text(
                next_decision.get("next_owner"),
                decision.get("next_owner"),
            ),
        }
    )


def latest_materialized_mission_path(
    *,
    workspace_root: Path,
    study_id: str,
) -> Path | None:
    root = workspace_root.expanduser().resolve() / PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH
    if not root.exists():
        return None
    candidates = sorted(
        (
            path
            for path in root.glob("*/*/paper_mission_run.json")
            if path.is_file()
            and materialized_mission_path_matches(
                path,
                requested_study_id=study_id,
                load_json_object=_load_json_object,
            )
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def latest_candidate_package_manifest_path(
    *,
    workspace_root: Path,
    study_id: str,
) -> Path | None:
    root = (
        workspace_root.expanduser().resolve()
        / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH
    )
    if not root.exists():
        return None
    candidates = sorted(
        (
            path
            for path in root.glob("*/**/package_manifest.json")
            if path.is_file()
            and materialized_mission_path_matches(
                path,
                requested_study_id=study_id,
                load_json_object=_load_json_object,
            )
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def resolve_consume_candidate_ref(
    *,
    profile: Any,
    study_id: str,
    candidate: str | Path | None,
) -> str | None:
    explicit = _optional_text(candidate)
    if explicit is not None:
        return explicit
    candidate_package = latest_candidate_package_manifest_path(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    return str(candidate_package) if candidate_package is not None else None


__all__ = [
    "latest_candidate_package_manifest_path",
    "latest_materialized_mission_path",
    "paper_mission_current_package_projection",
    "paper_mission_delivery_projection_fields",
    "paper_mission_inspect_projection_fields",
    "paper_mission_materialized_projection_fields",
    "resolve_consume_candidate_ref",
]

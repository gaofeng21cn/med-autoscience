from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_output_roots import (
    PAPER_MISSION_STAGE_CLOSURE_RELPATH,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
    stage_closure_signature,
    terminalize_stage_closure,
)


def stage_closure_terminalizer_output_root(
    *,
    profile: Any,
    output_root: str | Path | None,
) -> Path:
    if output_root is not None:
        return Path(output_root).expanduser().resolve()
    workspace_root = Path(profile.workspace_root).expanduser().resolve()
    return (
        workspace_root
        / PAPER_MISSION_STAGE_CLOSURE_RELPATH
        / "paper_mission_terminalize_stage"
    )


def stage_closure_decision_requires_reterminalize(
    decision: Mapping[str, Any],
    *,
    current_package: Mapping[str, Any] | None = None,
) -> bool:
    outcome = _mapping(decision.get("outcome"))
    opl_closeout = _mapping(decision.get("opl_closeout"))
    observability_gaps = _text_list(decision.get("observability_gaps"))
    boundary = _mapping(decision.get("authority_boundary"))
    if (
        decision.get("authority_materialized") is True
        and decision.get("counts_as_typed_blocker") is True
        and boundary.get("surface_role") == "paper_mission_receipt_owner_consumption"
        and outcome.get("kind") == "typed_blocker"
    ):
        return False
    if current_package_is_submission_ready_clear(_mapping(current_package)):
        return True
    if decision.get("source_surface_kind") == "paper_mission_stage_closure_ledger":
        return False
    if _optional_text(opl_closeout.get("status")) == "waiting_for_opl_runtime_live_readback":
        return True
    if outcome.get("transition_kind") == "route_back_candidate_checkpoint":
        return True
    if any(
        gap in observability_gaps
        for gap in (
            "duration_missing",
            "duration_ms_missing",
            "token_usage_missing",
            "cost_missing",
            "cost_usd_missing",
        )
    ):
        return True
    if outcome.get("next_action") == "continue_same_stage":
        return True
    return False


def terminalize_stage_closure_from_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(readback.get("paper_mission_transaction"))
    stage_decision = _mapping(readback.get("stage_terminal_decision"))
    outcome = _mapping(_mapping(readback.get("stage_closure_decision")).get("outcome"))
    current_package = _mapping(readback.get("current_package"))
    current_package_clear = current_package_is_submission_ready_clear(current_package)
    repair_budget = _mapping(readback.get("route_back_budget")) or _mapping(
        _mapping(readback.get("stage_closure_decision")).get("repair_budget")
    )
    gate_replay = {
        "status": _first_text(
            _current_package_quality_gate_status(current_package)
            if current_package_clear
            else None,
            stage_decision.get("status"),
            readback.get("consume_candidate_status"),
            outcome.get("kind"),
        ),
        "gate_replay_status": (
            _current_package_quality_gate_status(current_package)
            if current_package_clear
            else (
                "blocked"
                if stage_closure_decision_missing(
                    _mapping(readback.get("stage_closure_decision"))
                )
                else _first_text(outcome.get("kind"), "observed")
            )
        ),
        "gate_replay_blockers": (
            [] if current_package_clear else stage_closure_readback_blockers(readback)
        ),
    }
    study_id = str(readback.get("study_id") or transaction.get("study_id") or "")
    stage_id = str(
        transaction.get("stage_id") or stage_decision.get("target_stage_id") or "paper_mission"
    )
    work_unit_id = str(
        _first_text(
            transaction.get("stage_id"),
            stage_decision.get("target_stage_id"),
            readback.get("objective"),
            "paper_mission_stage",
        )
    )
    work_unit_fingerprint = _first_text(
        transaction.get("transaction_id"),
        readback.get("mission_id"),
    )
    semantic_delta = stage_closure_semantic_delta(readback)
    previous_signature = _previous_stage_closure_signature_for_reterminalize(
        readback=readback,
        study_id=study_id,
        stage_id=stage_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        blockers=gate_replay["gate_replay_blockers"],
        semantic_delta=semantic_delta,
    )
    return terminalize_stage_closure(
        study_id=study_id,
        stage_id=stage_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        identity={
            "mission_id": readback.get("mission_id"),
            "paper_mission_transaction_ref": transaction.get("transaction_id"),
            "consume_candidate_status": readback.get("consume_candidate_status"),
            "transaction_state": readback.get("transaction_state"),
        },
        inputs={
            "materialized_mission_ref": readback.get("materialized_mission_ref"),
            "candidate_ref": readback.get("candidate_ref"),
            "source_ref": readback.get("source_ref"),
        },
        gate_replay=gate_replay,
        delivery_readback=stage_closure_delivery_readback(readback),
        opl_closeout=stage_closure_opl_closeout(readback),
        semantic_delta=semantic_delta,
        repair_budget=repair_budget,
        previous_signature=previous_signature,
    )


def stage_closure_source_readback_summary(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _mapping(readback.get("stage_closure_decision"))
    return _compact_mapping(
        {
            "surface_kind": readback.get("surface_kind"),
            "mission_id": readback.get("mission_id"),
            "mission_state": readback.get("mission_state"),
            "consume_candidate_status": readback.get("consume_candidate_status"),
            "transaction_state": readback.get("transaction_state"),
            "stage_closure_projection_status": decision.get("projection_status"),
            "stage_closure_outcome": _mapping(decision.get("outcome")).get("kind"),
            "materialized_mission_ref": readback.get("materialized_mission_ref"),
        }
    )


def stage_closure_readback_blockers(readback: Mapping[str, Any]) -> list[str]:
    decision = _mapping(readback.get("stage_closure_decision"))
    terminal_gate = _mapping(readback.get("terminal_owner_gate"))
    return _dedupe_optional_texts(
        [
            readback.get("blocked_reason"),
            readback.get("consume_candidate_status"),
            readback.get("transaction_state"),
            _mapping(readback.get("stage_terminal_decision")).get("reason"),
            _mapping(readback.get("stage_terminal_decision")).get("blocker_id"),
            terminal_gate.get("blocked_reason"),
            *(_text_list(decision.get("known_blockers"))),
        ]
    )


def stage_closure_delivery_readback(readback: Mapping[str, Any]) -> dict[str, Any]:
    candidate = _mapping(readback.get("candidate_manifest"))
    output = _mapping(readback.get("output_manifest"))
    current_package = _mapping(readback.get("current_package"))
    return _compact_mapping(
        {
            "package_kind": _first_text(
                current_package.get("package_kind"),
                readback.get("package_kind"),
                candidate.get("package_kind"),
                output.get("milestone_kind"),
            ),
            "can_submit": _current_package_can_submit(current_package),
            "quality_gate_status": _current_package_quality_gate_status(current_package),
            "known_blockers": _text_list(current_package.get("known_blockers")),
            "generated_from_current_source": current_package.get(
                "generated_from_current_source"
            ),
            "source_signature": current_package.get("source_signature"),
            "freshness": _first_text(
                "current"
                if current_package_is_submission_ready_clear(current_package)
                else None,
                current_package.get("freshness"),
                current_package.get("status"),
                readback.get("freshness"),
                output.get("freshness"),
            ),
            "blocked_reason": _first_text(
                readback.get("blocked_reason"),
                _mapping(readback.get("terminal_owner_gate")).get("blocked_reason"),
            ),
            "current_package_exists": (
                bool(current_package) or output.get("current_package_exists")
            ),
            "bundle_build_allowed": output.get("bundle_build_allowed"),
            "root": current_package.get("root"),
            "zip_path": current_package.get("zip_path"),
            "zip_exists": current_package.get("zip_exists"),
        }
    )


def stage_closure_opl_closeout(readback: Mapping[str, Any]) -> dict[str, Any]:
    carrier = _mapping(readback.get("opl_runtime_carrier_readback"))
    terminal_closeout = _mapping(carrier.get("terminal_closeout"))
    return _compact_mapping(
        {
            "status": _first_text(
                readback.get("opl_runtime_readback_status"),
                carrier.get("carrier_status"),
                terminal_closeout.get("status"),
            ),
            "stage_attempt_id": terminal_closeout.get("stage_attempt_id"),
            "work_unit_id": terminal_closeout.get("work_unit_id"),
            "duration": _first_mapping(
                _mapping(terminal_closeout.get("duration")),
                _mapping(readback.get("duration")),
            ),
            "token_usage": _first_mapping(
                _mapping(terminal_closeout.get("token_usage")),
                _mapping(readback.get("token_usage")),
            ),
            "cost": _first_mapping(
                _mapping(terminal_closeout.get("cost")),
                _mapping(readback.get("cost")),
            ),
            "terminal_closeout": terminal_closeout,
        }
    )


def stage_closure_semantic_delta(readback: Mapping[str, Any]) -> dict[str, Any]:
    refs = []
    for key in ("candidate_ref", "candidate_manifest_ref", "materialized_mission_ref"):
        text = _optional_text(readback.get(key))
        if text is not None:
            refs.append(text)
    delivery_refs = []
    current_package = _mapping(readback.get("current_package"))
    for key in ("source_signature", "root", "zip_path"):
        text = _optional_text(current_package.get(key))
        if text is not None:
            refs.append(text)
            delivery_refs.append(text)
    for item in _mapping_list(
        _mapping(readback.get("paper_mission_run")).get("artifact_delta_ledger")
    ):
        ref = _first_text(item.get("artifact_ref"), item.get("delta_id"))
        if ref is not None:
            refs.append(ref)
    return _compact_mapping(
        {
            "semantic_delta_observed": bool(refs),
            "semantic_delta_refs": sorted(set(refs)),
            "delivery_delta_refs": sorted(set(delivery_refs)),
        }
    )


def current_package_is_submission_ready_clear(
    current_package: Mapping[str, Any],
) -> bool:
    gate_status = _current_package_quality_gate_status(current_package)
    package_status = _first_text(
        current_package.get("status"),
        current_package.get("freshness_status"),
        current_package.get("delivery_status"),
    )
    return (
        package_status in {"current", "fresh", "synced"}
        and current_package.get("package_kind") == "submission_ready_package"
        and current_package.get("can_submit") is True
        and gate_status in {"clear", "passed", "cleared"}
        and current_package.get("generated_from_current_source") is True
        and bool(_optional_text(current_package.get("root")))
        and current_package.get("zip_exists") is True
        and not _text_list(current_package.get("known_blockers"))
    )


def _previous_stage_closure_signature_for_reterminalize(
    *,
    readback: Mapping[str, Any],
    study_id: str,
    stage_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str | None,
    blockers: list[str],
    semantic_delta: Mapping[str, Any],
) -> str | None:
    existing_decision = _mapping(readback.get("stage_closure_decision"))
    previous_signature = _optional_text(existing_decision.get("decision_signature"))
    outcome = _mapping(existing_decision.get("outcome"))
    if (
        outcome.get("transition_kind") == "route_back_candidate_checkpoint"
        and not _stage_closure_semantic_delta_has_refs(semantic_delta)
    ):
        return stage_closure_signature(
            study_id=study_id,
            stage_id=stage_id,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            blockers=blockers,
            semantic_delta=semantic_delta,
        )
    return previous_signature


def _stage_closure_semantic_delta_has_refs(
    semantic_delta: Mapping[str, Any],
) -> bool:
    return any(
        _text_list(semantic_delta.get(key))
        for key in (
            "paper_delta_refs",
            "reviewer_delta_refs",
            "gate_delta_refs",
            "delivery_delta_refs",
            "owner_decision_refs",
        )
    )


def _current_package_quality_gate_status(current_package: Mapping[str, Any]) -> str | None:
    return _first_text(
        current_package.get("quality_gate_status"),
        current_package.get("gate_status"),
    )


def _current_package_can_submit(current_package: Mapping[str, Any]) -> bool | None:
    if not current_package:
        return None
    return current_package.get("can_submit") is True


def _first_mapping(*values: dict[str, Any]) -> dict[str, Any]:
    for value in values:
        if value:
            return value
    return {}


def _compact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    items: list[str] = []
    for item in value:
        text = _optional_text(item)
        if text is not None:
            items.append(text)
    return items


def _dedupe_optional_texts(values: list[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _optional_text(value)
        if text is None or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


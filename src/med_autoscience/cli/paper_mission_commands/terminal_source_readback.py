from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _mapping,
    _optional_text,
)
from med_autoscience.cli.paper_mission_commands.stage_packet_route_back_readback import (
    _first_non_empty_text,
)
from med_autoscience.paper_mission_opl_readback.route_identity import (
    route_ref_matches,
)


def _terminal_source_readback_newer(
    *,
    candidate: Mapping[str, Any],
    current: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    candidate_closeout = _mapping(
        _mapping(candidate.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    current_closeout = _mapping(
        _mapping(current.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    return _terminal_closeout_newer(
        candidate=candidate_closeout,
        current=current_closeout,
        workspace_root=workspace_root,
    )


def _stage_closure_matches_current_transaction_with_terminal_closeout(
    readback: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> bool:
    if _optional_text(readback.get("consume_candidate_status")) in {
        "not_consumed",
        "not_applicable",
    }:
        return False
    if _optional_text(readback.get("mission_state")) in {"planned", "draft"}:
        return False
    stage_closure = _mapping(readback.get("stage_closure_decision"))
    transaction = _mapping(readback.get("paper_mission_transaction"))
    transaction_ref = _optional_text(transaction.get("transaction_id"))
    closure_ref = _optional_text(
        _mapping(stage_closure.get("identity")).get("paper_mission_transaction_ref")
    ) or _optional_text(stage_closure.get("paper_mission_transaction_ref"))
    if transaction_ref is None or closure_ref != transaction_ref:
        return False
    opl_closeout = _mapping(stage_closure.get("opl_closeout"))
    stage_attempt_id = _optional_text(opl_closeout.get("stage_attempt_id"))
    live_terminal_closeout = _mapping(
        _mapping(readback.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    live_stage_attempt_id = _optional_text(live_terminal_closeout.get("stage_attempt_id"))
    if not _terminal_closeout_uses_stage_attempt_packet(live_terminal_closeout):
        return False
    direct_terminal_closeout = _mapping(
        _mapping(readback.get("current_opl_runtime_carrier_readback")).get(
            "terminal_closeout"
        )
    )
    if _terminal_closeout_newer(
        candidate=direct_terminal_closeout,
        current=live_terminal_closeout,
        workspace_root=workspace_root,
    ):
        return False
    return (
        stage_attempt_id is not None
        and stage_attempt_id == live_stage_attempt_id
        and _optional_text(opl_closeout.get("status"))
        == "opl_runtime_terminal_readback_observed"
    )


def _readback_has_current_transaction_terminal_closeout(
    readback: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> bool:
    if _optional_text(readback.get("consume_candidate_status")) in {
        "not_consumed",
        "not_applicable",
    }:
        return False
    if _optional_text(readback.get("mission_state")) in {"planned", "draft"}:
        return False
    transaction_ref = _optional_text(
        _mapping(readback.get("paper_mission_transaction")).get("transaction_id")
    )
    if transaction_ref is None:
        return False
    terminal_closeout = _mapping(
        _mapping(readback.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    if not _terminal_closeout_uses_stage_attempt_packet(terminal_closeout):
        return False
    if _terminal_closeout_mtime(terminal_closeout, workspace_root=workspace_root) is None:
        return False
    closeout_transaction_ref = _first_non_empty_text(
        terminal_closeout.get("paper_mission_transaction_ref"),
        terminal_closeout.get("stage_packet_ref"),
    )
    return route_ref_matches(closeout_transaction_ref, transaction_ref)


def _stage_closure_decision_uses_stale_terminal_closeout(
    *,
    existing_decision: Mapping[str, Any],
    source_readback: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    if not _readback_has_current_transaction_terminal_closeout(
        source_readback,
        workspace_root=workspace_root,
    ):
        return False
    current_stage_attempt_id = _optional_text(
        _mapping(
            _mapping(source_readback.get("opl_runtime_carrier_readback")).get(
                "terminal_closeout"
            )
        ).get("stage_attempt_id")
    )
    existing_stage_attempt_id = _optional_text(
        _mapping(existing_decision.get("opl_closeout")).get("stage_attempt_id")
    )
    return (
        current_stage_attempt_id is not None
        and existing_stage_attempt_id is not None
        and current_stage_attempt_id != existing_stage_attempt_id
    )


def _terminal_closeout_uses_stage_attempt_packet(closeout: Mapping[str, Any]) -> bool:
    refs = [_optional_text(closeout.get("closeout_ref"))]
    closeout_refs = closeout.get("closeout_refs")
    if isinstance(closeout_refs, (list, tuple)):
        refs.extend(_optional_text(item) for item in closeout_refs)
    return any(
        ref is not None
        and "paper_mission_stage_attempts" in ref
        and ref.endswith("stage_attempt_closeout_packet.json")
        for ref in refs
    )


def _terminal_closeout_newer(
    *,
    candidate: Mapping[str, Any],
    current: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    candidate_mtime = _terminal_closeout_mtime(candidate, workspace_root=workspace_root)
    current_mtime = _terminal_closeout_mtime(current, workspace_root=workspace_root)
    if candidate_mtime is None:
        return False
    if current_mtime is None:
        return True
    return candidate_mtime > current_mtime


def _terminal_closeout_mtime(
    closeout: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> float | None:
    refs = [_optional_text(closeout.get("closeout_ref"))]
    closeout_refs = closeout.get("closeout_refs")
    if isinstance(closeout_refs, (list, tuple)):
        refs.extend(_optional_text(item) for item in closeout_refs)
    for ref in refs:
        if ref is None or ref.startswith(("opl://", "temporal://")):
            continue
        path = Path(ref).expanduser()
        if not path.is_absolute():
            path = workspace_root.expanduser().resolve() / path
        try:
            return path.stat().st_mtime
        except OSError:
            continue
    return None

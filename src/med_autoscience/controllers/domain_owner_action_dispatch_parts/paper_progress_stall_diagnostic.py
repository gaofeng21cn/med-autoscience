from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part

from . import terminal_stall_handoff


def block_from_diagnostic(diagnostic: Mapping[str, Any]) -> tuple[str | None, bool]:
    return _text(diagnostic.get("blocked_reason")), bool(diagnostic.get("handoff_allowed"))


def diagnostic(
    *,
    action_type: str,
    dispatch: Mapping[str, Any],
    current_study: Mapping[str, Any] | None,
    current_route: Mapping[str, Any] | None,
    required_output_pending: bool,
) -> dict[str, Any]:
    if action_type == "return_to_ai_reviewer_workflow" and owner_route_part.route_allows_action(
        action=dispatch,
        owner_route=current_route,
    ):
        return _stall_diagnostic(status="owner_authorized_bypass", blocking=False, handoff_allowed=True)
    if (
        action_type in {"current_package_freshness_required", "canonical_paper_inputs_rehydrate_required"}
        and required_output_pending
        and owner_route_part.route_allows_action(action=dispatch, owner_route=current_route)
    ):
        return _stall_diagnostic(status="required_output_pending_bypass", blocking=False, handoff_allowed=True)
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    dispatch_stall = _mapping(dispatch.get("paper_progress_stall")) or _mapping(prompt_contract.get("paper_progress_stall"))
    if not dispatch_stall:
        return _stall_diagnostic(status="missing", blocking=False, handoff_allowed=False)
    current_stall = _mapping(_mapping(current_study).get("paper_progress_stall"))
    if not current_stall:
        return _stall_diagnostic(
            status="current_missing",
            blocking=True,
            blocked_reason="paper_progress_stall_current_missing",
            handoff_allowed=False,
            dispatch_stall=dispatch_stall,
        )
    if current_stall.get("terminal") is True:
        if terminal_stall_handoff.owner_handoff_allowed(
            action_type=action_type,
            dispatch=dispatch,
            current_study=current_study,
            current_route=current_route,
        ):
            return _stall_diagnostic(
                status="terminal_owner_handoff_allowed",
                blocking=False,
                handoff_allowed=True,
                dispatch_stall=dispatch_stall,
                current_stall=current_stall,
            )
        return _stall_diagnostic(
            status="terminal_blocking",
            blocking=True,
            blocked_reason="paper_progress_stall_terminal",
            handoff_allowed=False,
            dispatch_stall=dispatch_stall,
            current_stall=current_stall,
        )
    dispatch_fingerprint = _text(dispatch_stall.get("action_fingerprint")) or _text(dispatch.get("action_fingerprint"))
    current_fingerprint = _text(current_stall.get("action_fingerprint"))
    if dispatch_fingerprint is not None and current_fingerprint is not None and dispatch_fingerprint != current_fingerprint:
        if current_stall.get("stalled") is False and current_stall.get("terminal") is False:
            return _stall_diagnostic(
                status="fingerprint_stale_after_progress_refresh",
                blocking=False,
                handoff_allowed=True,
                dispatch_stall=dispatch_stall,
                current_stall=current_stall,
            )
        if (
            current_stall.get("terminal") is not True
            and terminal_stall_handoff.owner_handoff_allowed(
                action_type=action_type,
                dispatch=dispatch,
                current_study=current_study,
                current_route=current_route,
            )
        ):
            return _stall_diagnostic(
                status="nonterminal_fingerprint_stale_diagnostic",
                blocking=False,
                handoff_allowed=True,
                dispatch_stall=dispatch_stall,
                current_stall=current_stall,
            )
        return _stall_diagnostic(
            status="paper_progress_stall_fingerprint_stale",
            blocking=True,
            blocked_reason="paper_progress_stall_fingerprint_stale",
            handoff_allowed=False,
            dispatch_stall=dispatch_stall,
            current_stall=current_stall,
        )
    return _stall_diagnostic(
        status="current",
        blocking=False,
        handoff_allowed=False,
        dispatch_stall=dispatch_stall,
        current_stall=current_stall,
    )


def _stall_diagnostic(
    *,
    status: str,
    blocking: bool,
    handoff_allowed: bool,
    blocked_reason: str | None = None,
    dispatch_stall: Mapping[str, Any] | None = None,
    current_stall: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_progress_stall_diagnostic",
        "status": status,
        "blocking": bool(blocking),
        "blocked_reason": blocked_reason,
        "handoff_allowed": bool(handoff_allowed),
        "dispatch_action_fingerprint": _text(_mapping(dispatch_stall).get("action_fingerprint")),
        "current_action_fingerprint": _text(_mapping(current_stall).get("action_fingerprint")),
        "current_terminal": _mapping(current_stall).get("terminal"),
        "current_stalled": _mapping(current_stall).get("stalled"),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None

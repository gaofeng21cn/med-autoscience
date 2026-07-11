from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_domain.common import _mapping, _optional_text
from med_autoscience.paper_mission_domain.direct_next_action_handoff import (
    build_direct_next_action_handoff,
)
from med_autoscience.paper_mission_domain.readback_next_action_precedence import (
    _domain_transition_next_action_requests_stage_attempt,
)
from med_autoscience.paper_mission_domain.stage_closure_next_action import (
    next_action_for_stage_closure_decision as _next_action_for_stage_closure_decision,
)
from med_autoscience.paper_mission_domain.stage_closure_terminalizer import (
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
)
from med_autoscience.paper_mission_opl_readback import (
    paper_mission_opl_runtime_carrier_readback,
)


def _typed_blocker_resolution_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None = None,
) -> bool:
    if not typed_blocker_resolution_readback:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if outcome.get("kind") != "typed_blocker":
        return False
    return bool(_mapping(typed_blocker_resolution_readback.get("next_owner_action")))


def _domain_transition_direct_next_action_runtime_readback(
    *,
    profile: Any,
    study_id: str,
    study_root: Path,
    inspect_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
    canonical_next_action_source: str | None,
    enable_opl_live_probe: bool,
    opl_bin: str | Path | None,
) -> dict[str, Any]:
    if canonical_next_action_source not in {
        "domain_transition.next_action",
        "paper_mission_next_action_envelope",
    }:
        return {}
    if not _domain_transition_next_action_requests_stage_attempt(next_action):
        return {}
    handoff = build_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback=inspect_readback,
        next_action=next_action,
    )
    carrier = _mapping(handoff.get("opl_runtime_carrier"))
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    return {
        "surface_kind": "paper_mission_domain_transition_direct_stage_attempt_readback",
        "schema_version": 1,
        "canonical_next_action_source": canonical_next_action_source,
        "next_action": dict(next_action),
        "opl_route_handoff": handoff,
        "paper_mission_transaction": handoff["paper_mission_transaction"],
        "stage_terminal_decision": handoff["stage_terminal_decision"],
        "opl_route_command": handoff["opl_route_command"],
        "opl_runtime_carrier": carrier,
        "opl_runtime_carrier_readback": carrier_readback,
        "opl_runtime_readback_status": carrier_readback["carrier_status"],
        "transaction_state": "domain_transition_direct_stage_attempt",
        "consume_candidate_status": "not_applicable_domain_transition_direct",
        "authority_boundary": {
            "surface_role": "current_next_action_runtime_projection",
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
    }


def _override_next_action_from_direct_terminal_closeout(
    *,
    direct_next_action_runtime: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
    next_action_override: Mapping[str, Any] | None,
    canonical_next_action_source: str | None,
    terminalize_stage_closure_from_readback: Callable[[Mapping[str, Any]], Mapping[str, Any]]
    | None = None,
    next_action_for_stage_closure_decision: Callable[..., Mapping[str, Any] | None] | None = None,
) -> tuple[Mapping[str, Any], Mapping[str, Any] | None, str | None]:
    direct = _mapping(direct_next_action_runtime)
    if _optional_text(direct.get("opl_runtime_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return stage_closure_decision, next_action_override, canonical_next_action_source
    carrier_readback = _mapping(direct.get("opl_runtime_carrier_readback"))
    if _optional_text(_mapping(carrier_readback.get("mas_receipt_consumption")).get("status")) != (
        "requires_mas_owner_consumption"
    ):
        return stage_closure_decision, next_action_override, canonical_next_action_source
    terminalize = terminalize_stage_closure_from_readback or _terminalize_stage_closure_from_readback
    next_action_for_decision = (
        next_action_for_stage_closure_decision
        or _next_action_for_stage_closure_decision
    )
    refreshed_stage_closure_decision = terminalize(direct)
    refreshed_next_action = next_action_for_decision(
        stage_closure_decision=refreshed_stage_closure_decision,
        transaction_readback=transaction_readback,
        typed_blocker_resolution_readback=typed_blocker_resolution_readback,
    )
    return (
        refreshed_stage_closure_decision,
        refreshed_next_action,
        "stage_closure.next_action" if refreshed_next_action is not None else canonical_next_action_source,
    )

from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_opl_readback_parts.closeout_discovery import (
    matching_terminal_closeout as _discover_matching_terminal_closeout,
)
from med_autoscience.paper_mission_opl_readback_parts.next_action_envelope import (
    attach_paper_mission_next_action,
    paper_mission_next_action_envelope,
)
from med_autoscience.paper_mission_opl_readback_parts.opl_cli_probe import (
    DEFAULT_OPL_READBACK_TIMEOUT_SECONDS,
    DEV_OPL_BIN,
    PACKAGED_OPL_BIN,
    PATH_OPL_BIN,
    ranked_opl_bin_candidates,
    remaining_seconds,
    run_opl_json,
)
from med_autoscience.paper_mission_opl_readback_parts.opl_task_readback import (
    OPL_DOMAIN_ID,
    OPL_STAGE_ROUTE_TASK_KIND,
    matching_opl_runtime_payload_closeout as _matching_opl_runtime_payload_closeout,
    matching_opl_runtime_payload_running_attempt as _matching_opl_runtime_payload_running_attempt,
    matching_opl_tasks_from_list as _matching_opl_tasks_from_list,
    ranked_opl_probe_tasks as _ranked_opl_probe_tasks,
)
from med_autoscience.paper_mission_opl_readback_parts.primitives import (
    first_text as _first_text,
    mapping as _mapping,
    text_list as _text_list,
    text_value as _text,
)
from med_autoscience.paper_mission_opl_readback_parts.receipt_events import (
    carrier_route_target as _carrier_route_target,
    matches_mas_impact_receipt as _matches_mas_impact_receipt,
    matches_opl_transition_receipt as _matches_opl_transition_receipt,
)
from med_autoscience.paper_mission_opl_readback_parts.route_identity import (
    carrier_has_opl_route_identity as _carrier_has_opl_route_identity,
    closeout_binds_exact_route_identity as _closeout_binds_exact_route_identity,
    closeout_has_route_back_evidence as _closeout_has_route_back_evidence,
    closeout_is_record_only as _closeout_is_record_only,
    matches_carrier as _matches_carrier,
    non_current_closeout_reason as _non_current_closeout_reason,
    payload_binds_route_identity as _payload_binds_route_identity,
    route_ref_matches as _route_ref_matches,
)
from med_autoscience.paper_mission_opl_readback_parts.runtime_readback_payloads import (
    mas_receipt_consumption_readback as _mas_receipt_consumption_readback,
    opl_transition_receipt_readback as _opl_transition_receipt_readback,
    receipt_evidence_readback as _receipt_evidence_readback,
    running_attempt_readback as _running_attempt_readback,
    terminal_closeout_readback as _terminal_closeout_readback,
)


CLOSEOUT_RELATIVE_ROOTS = (
    Path("artifacts/supervision/consumer/owner_callable_adapter_receipt"),
    Path("artifacts/supervision/consumer/stage_attempt_closeouts"),
)
WORKSPACE_CLOSEOUT_RELATIVE_ROOTS = (
    Path("ops/medautoscience/paper_mission_consumption_ledger"),
    Path("ops/medautoscience/paper_mission_stage_attempts"),
)
TERMINAL_READBACK_STATUS = "opl_runtime_terminal_readback_observed"
RUNNING_READBACK_STATUS = "opl_runtime_attempt_running_observed"
WAITING_READBACK_STATUS = "waiting_for_opl_runtime_live_readback"
DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS = 30.0
DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT = 2

def paper_mission_opl_runtime_carrier_readback(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
    opl_runtime_payload: Mapping[str, Any] | None = None,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any]:
    live_probe = None
    live_probe_attempted = False
    if opl_runtime_payload is None and enable_opl_live_probe:
        live_probe_attempted = True
        live_probe = _matching_opl_runtime_live_probe(carrier=carrier, opl_bin=opl_bin)
    running = None
    if live_probe is not None and live_probe[0] == "running":
        running = (live_probe[1], live_probe[2])
    elif not live_probe_attempted:
        running = _matching_opl_runtime_running_attempt(
            carrier=carrier,
            opl_runtime_payload=opl_runtime_payload,
            enable_opl_live_probe=enable_opl_live_probe,
        )
    if running is not None:
        attempt, attempt_ref = running
        matched = _matching_terminal_closeout_for_running_attempt(
            carrier=carrier,
            study_root=study_root,
            attempt=attempt,
        )
        if matched is not None:
            local_matched = _matching_terminal_closeout(
                carrier=carrier,
                study_root=study_root,
            )
            if _local_route_back_closeout_supersedes_live_terminal(
                live_matched=matched,
                local_matched=local_matched,
            ):
                matched = local_matched
        if matched is None:
            return {
                "surface_kind": "paper_mission_opl_runtime_carrier_readback",
                "schema_version": 1,
                "carrier_status": RUNNING_READBACK_STATUS,
                "runtime_readback_status": "running_attempt_observed",
                "dispatch_status": "provider_attempt_running",
                "domain_ready_verdict": "opl_runtime_attempt_running",
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "can_claim_provider_running": True,
                "can_claim_paper_progress": False,
                "can_claim_runtime_ready": False,
                "authority_materialized": False,
                "request_carrier_preserved": True,
                "running_attempt": _running_attempt_readback(
                    attempt=attempt,
                    attempt_ref=attempt_ref,
                ),
            }
    else:
        matched = None
    if live_probe is not None and live_probe[0] == "terminal":
        matched = (live_probe[1], live_probe[2])
        same_attempt_local = _matching_terminal_closeout_for_running_attempt(
            carrier=carrier,
            study_root=study_root,
            attempt=live_probe[1],
        )
        local_matched = (
            same_attempt_local
            if same_attempt_local is not None
            and _closeout_has_route_back_evidence(same_attempt_local[0])
            else _matching_terminal_closeout(
                carrier=carrier,
                study_root=study_root,
            )
        )
        if _local_route_back_closeout_supersedes_live_terminal(
            live_matched=matched,
            local_matched=local_matched,
        ):
            matched = local_matched
    if matched is None:
        matched = _matching_terminal_closeout(carrier=carrier, study_root=study_root)
    if matched is None:
        if not live_probe_attempted:
            matched = _matching_opl_runtime_terminal_closeout(
                carrier=carrier,
                opl_runtime_payload=opl_runtime_payload,
                enable_opl_live_probe=enable_opl_live_probe,
            )
    if matched is None:
        return {
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "schema_version": 1,
            "carrier_status": WAITING_READBACK_STATUS,
            "runtime_readback_status": "missing",
            "dispatch_status": _text(carrier.get("dispatch_status"))
            or "transition_request_pending",
            "domain_ready_verdict": "opl_runtime_readback_missing",
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "request_carrier_preserved": True,
        }

    closeout, closeout_ref = matched
    terminal_closeout = _terminal_closeout_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
    )
    opl_transition_receipt = _opl_transition_receipt_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
    )
    receipt_evidence = _receipt_evidence_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
        opl_transition_receipt=opl_transition_receipt,
    )
    mas_receipt_consumption = _mas_receipt_consumption_readback(
        receipt_evidence=receipt_evidence,
    )
    return {
        "surface_kind": "paper_mission_opl_runtime_carrier_readback",
        "schema_version": 1,
        "carrier_status": TERMINAL_READBACK_STATUS,
        "runtime_readback_status": "terminal_closeout_observed",
        "dispatch_status": "terminal_closeout_observed",
        "domain_ready_verdict": "domain_gate_pending",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "request_carrier_preserved": True,
        "terminal_closeout": terminal_closeout,
        **(
            {"opl_transition_receipt": opl_transition_receipt}
            if opl_transition_receipt
            else {}
        ),
        **({"receipt_evidence": receipt_evidence} if receipt_evidence else {}),
        **(
            {"mas_receipt_consumption": mas_receipt_consumption}
            if mas_receipt_consumption
            else {}
        ),
    }

def attach_opl_runtime_carrier_readback(
    *,
    readback: Mapping[str, Any],
    study_root: Path,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any]:
    result = dict(readback)
    carrier = _mapping(result.get("opl_runtime_carrier"))
    if not carrier:
        return result
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    result["opl_runtime_carrier_readback"] = carrier_readback
    result["opl_runtime_readback_status"] = carrier_readback["carrier_status"]
    return result

def _matching_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
) -> tuple[dict[str, Any], str] | None:
    return _discover_matching_terminal_closeout(
        carrier=carrier,
        study_root=study_root,
        closeout_relative_roots=CLOSEOUT_RELATIVE_ROOTS,
        workspace_closeout_relative_roots=WORKSPACE_CLOSEOUT_RELATIVE_ROOTS,
        matches_carrier=_matches_carrier,
        candidate_priority=_closeout_candidate_priority,
    )


def _matching_terminal_closeout_for_running_attempt(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
    attempt: Mapping[str, Any],
) -> tuple[dict[str, Any], str] | None:
    stage_attempt_id = _first_text(
        attempt.get("stage_attempt_id"),
        attempt.get("active_stage_attempt_id"),
        _mapping(attempt.get("linked_stage_attempt_liveness")).get("stage_attempt_id"),
    )
    if stage_attempt_id is None:
        return None
    return _discover_matching_terminal_closeout(
        carrier=carrier,
        study_root=study_root,
        closeout_relative_roots=CLOSEOUT_RELATIVE_ROOTS,
        workspace_closeout_relative_roots=WORKSPACE_CLOSEOUT_RELATIVE_ROOTS,
        matches_carrier=lambda closeout, carrier, route_back=None: (
            _matches_running_attempt_closeout(
                closeout=closeout,
                carrier=carrier,
                stage_attempt_id=stage_attempt_id,
            )
        ),
        candidate_priority=_closeout_candidate_priority,
    )


def _local_route_back_closeout_supersedes_live_terminal(
    *,
    live_matched: tuple[dict[str, Any], str] | None,
    local_matched: tuple[dict[str, Any], str] | None,
) -> bool:
    if live_matched is None or local_matched is None:
        return False
    live_closeout, live_ref = live_matched
    local_closeout, local_ref = local_matched
    if local_ref == live_ref:
        return False
    if not _closeout_has_route_back_evidence(local_closeout):
        return False
    if _text(local_closeout.get("stage_attempt_id")) == _text(
        live_closeout.get("stage_attempt_id")
    ):
        return not _closeout_has_route_back_evidence(live_closeout)
    if _closeout_is_live_runtime_terminal(
        closeout=live_closeout,
        closeout_ref=live_ref,
    ) and not _followthrough_route_back_supersedes_live_terminal(
        live_closeout=live_closeout,
        local_closeout=local_closeout,
    ):
        return False
    return True


def _closeout_is_live_runtime_terminal(
    *,
    closeout: Mapping[str, Any],
    closeout_ref: str,
) -> bool:
    if _text(closeout.get("runtime_readback_source")) in {
        "opl_family_runtime_queue_inspect",
        "opl_family_runtime_queue_list",
    }:
        return True
    return closeout_ref.startswith("opl://family-runtime/tasks/")


def _matches_running_attempt_closeout(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    stage_attempt_id: str,
) -> bool:
    if _text(closeout.get("surface_kind")) != "stage_attempt_closeout_packet":
        return False
    if _text(closeout.get("stage_attempt_id")) != stage_attempt_id:
        return False
    if _text(closeout.get("study_id")) != _text(carrier.get("study_id")):
        return False
    closeout_work_unit_id = _text(closeout.get("work_unit_id"))
    if (
        closeout_work_unit_id is not None
        and closeout_work_unit_id != _text(carrier.get("work_unit_id"))
    ):
        return False
    closeout_fingerprint = _text(closeout.get("work_unit_fingerprint"))
    if closeout_fingerprint is not None and closeout_fingerprint != _text(
        carrier.get("work_unit_fingerprint")
    ):
        return False
    route_target = _carrier_route_target(carrier)
    if route_target is not None and _text(closeout.get("stage_id")) != route_target:
        if _text(closeout.get("work_unit_id")) != _text(carrier.get("work_unit_id")):
            return False
    if closeout.get("provider_completion_is_domain_completion") is True:
        return False
    if closeout.get("provider_completion_is_domain_ready") is True:
        return False
    if closeout.get("domain_completion_claimed") is True:
        return False
    if closeout.get("domain_ready_claimed") is True:
        return False
    return _closeout_is_record_only(closeout)


def _closeout_candidate_priority(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    closeout_path: Path,
    closeout_ref: str,
    route_back: Mapping[str, Any] | None = None,
) -> tuple[int, float, int, int]:
    route_back = _mapping(route_back)
    return (
        1 if _closeout_prefers_followthrough_identity(closeout, route_back) else 0,
        closeout_path.stat().st_mtime,
        1
        if _closeout_binds_exact_route_identity(
            closeout=closeout,
            carrier=carrier,
            route_back=route_back,
        )
        else 0,
        _closeout_semantic_priority(closeout, route_back),
    )


def _closeout_prefers_followthrough_identity(
    closeout: Mapping[str, Any],
    route_back: Mapping[str, Any],
) -> bool:
    refs = {
        ref
        for ref in (
            _text(closeout.get("paper_mission_transaction_ref")),
            _text(closeout.get("stage_packet_ref")),
            _text(route_back.get("paper_mission_transaction_ref")),
            _text(route_back.get("stage_packet_ref")),
        )
        if ref is not None
    }
    return any("::followthrough::" in ref for ref in refs)


def _closeout_semantic_priority(
    closeout: Mapping[str, Any],
    route_back: Mapping[str, Any],
) -> int:
    score = 0
    route_impact = _mapping(closeout.get("route_impact"))
    closeout_refs = _text_list(closeout.get("closeout_refs"))
    if _first_text(
        route_impact.get("paper_facing_delta_ref"),
        closeout.get("paper_facing_delta_ref"),
    ):
        score += 2
    if _first_text(
        closeout.get("candidate_manifest_ref"),
        route_back.get("candidate_manifest_ref"),
    ) or any("candidate_manifest.json" in ref for ref in closeout_refs):
        score += 1
    if (
        _mapping(route_impact.get("stage_log_summary"))
        or _mapping(route_impact.get("user_stage_log"))
        or _text(route_impact.get("human_stage_log")) is not None
    ):
        score += 1
    if any("progress_events" in ref for ref in closeout_refs):
        score += 1
    if _text(route_back.get("owner_gate_verdict")) is not None:
        score += 1
    if _text(route_back.get("next_forced_paper_action")) is not None:
        score += 1
    if (
        _mapping(route_back.get("source_evidence"))
        or _text(route_back.get("source_readiness_checklist_ref")) is not None
    ):
        score += 1
    if _first_text(
        route_back.get("remaining_blocker"),
        route_back.get("remaining_blockers"),
    ):
        score += 1
    return score


def _followthrough_route_back_supersedes_live_terminal(
    *,
    live_closeout: Mapping[str, Any],
    local_closeout: Mapping[str, Any],
) -> bool:
    if not _closeout_has_route_back_evidence(local_closeout):
        return False
    local_route_ref = _first_text(
        local_closeout.get("stage_packet_ref"),
        local_closeout.get("paper_mission_transaction_ref"),
    )
    live_route_ref = _first_text(
        live_closeout.get("stage_packet_ref"),
        live_closeout.get("paper_mission_transaction_ref"),
    )
    if not _route_ref_matches(local_route_ref, live_route_ref):
        return False
    if local_route_ref is None or "::followthrough::" not in local_route_ref:
        return False
    return _closeout_semantic_priority(local_closeout, {}) >= _closeout_semantic_priority(
        live_closeout,
        {},
    )


def _matching_opl_runtime_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    opl_runtime_payload: Mapping[str, Any] | None,
    enable_opl_live_probe: bool,
) -> tuple[dict[str, Any], str] | None:
    if not _carrier_has_opl_route_identity(carrier):
        return None
    if opl_runtime_payload is not None:
        return _matching_opl_runtime_payload_closeout(
            carrier=carrier,
            payload=opl_runtime_payload,
        )
    if not enable_opl_live_probe:
        return None
    deadline = time.monotonic() + DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS
    list_args = (
        "family-runtime",
        "queue",
        "list",
        "--domain",
        OPL_DOMAIN_ID,
        "--study",
        _text(carrier.get("study_id")) or "",
        "--task-kind",
        OPL_STAGE_ROUTE_TASK_KIND,
        "--json",
    )
    inspect_args_prefix = (
        "family-runtime",
        "queue",
        "inspect",
    )
    for candidate in _ranked_opl_bin_candidates():
        if not candidate.exists():
            continue
        list_payload = _run_opl_json(
            candidate,
            list_args,
            timeout_seconds=remaining_seconds(deadline),
        )
        for task in _matching_opl_tasks_from_list(
            carrier=carrier,
            payload=list_payload,
        )[:DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT]:
            task_id = _text(task.get("task_id"))
            if task_id is None:
                continue
            inspect_payload = _run_opl_json(
                candidate,
                (
                    *inspect_args_prefix,
                    task_id,
                    "--json",
                ),
                timeout_seconds=remaining_seconds(deadline),
            )
            matched = _matching_opl_runtime_payload_closeout(
                carrier=carrier,
                payload=inspect_payload,
            )
            if matched is not None:
                return matched
    return None

def _matching_opl_runtime_live_probe(
    *,
    carrier: Mapping[str, Any],
    opl_bin: str | Path | None = None,
) -> tuple[str, dict[str, Any], str] | None:
    if not _carrier_has_opl_route_identity(carrier):
        return None
    deadline = time.monotonic() + DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS
    list_args = (
        "family-runtime",
        "queue",
        "list",
        "--domain",
        OPL_DOMAIN_ID,
        "--study",
        _text(carrier.get("study_id")) or "",
        "--task-kind",
        OPL_STAGE_ROUTE_TASK_KIND,
        "--json",
    )
    terminal_match: tuple[dict[str, Any], str] | None = None
    inspect_args_prefix = (
        "family-runtime",
        "queue",
        "inspect",
    )
    for candidate in _ranked_opl_live_probe_bin_candidates(opl_bin=opl_bin):
        if not candidate.exists():
            continue
        list_payload = _run_opl_json(
            candidate,
            list_args,
            timeout_seconds=remaining_seconds(deadline),
        )
        matched_running = _matching_opl_runtime_payload_running_attempt(
            carrier=carrier,
            payload=list_payload,
        )
        if matched_running is not None:
            attempt, attempt_ref = matched_running
            return "running", attempt, attempt_ref
        terminal_match = _matching_opl_runtime_payload_closeout(
            carrier=carrier,
            payload=list_payload,
        )
        if terminal_match is not None:
            closeout, closeout_ref = terminal_match
            return "terminal", closeout, closeout_ref
        for task in _ranked_opl_probe_tasks(
            _matching_opl_tasks_from_list(carrier=carrier, payload=list_payload),
            carrier=carrier,
        )[:DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT]:
            task_id = _text(task.get("task_id"))
            if task_id is None:
                continue
            inspect_payload = _run_opl_json(
                candidate,
                (
                    *inspect_args_prefix,
                    task_id,
                    "--json",
                ),
                timeout_seconds=remaining_seconds(deadline),
            )
            matched_terminal = _matching_opl_runtime_payload_closeout(
                carrier=carrier,
                payload=inspect_payload,
            )
            if matched_terminal is not None:
                closeout, closeout_ref = matched_terminal
                return "terminal", closeout, closeout_ref
            inspected_running = _matching_opl_runtime_payload_running_attempt(
                carrier=carrier,
                payload=inspect_payload,
            )
            if inspected_running is not None:
                matched_running = inspected_running
        if matched_running is not None:
            attempt, attempt_ref = matched_running
            return "running", attempt, attempt_ref
        if terminal_match is not None:
            closeout, closeout_ref = terminal_match
            return "terminal", closeout, closeout_ref
    return None

def _matching_opl_runtime_running_attempt(
    *,
    carrier: Mapping[str, Any],
    opl_runtime_payload: Mapping[str, Any] | None,
    enable_opl_live_probe: bool,
) -> tuple[dict[str, Any], str] | None:
    if not _carrier_has_opl_route_identity(carrier):
        return None
    if opl_runtime_payload is not None:
        return _matching_opl_runtime_payload_running_attempt(
            carrier=carrier,
            payload=opl_runtime_payload,
        )
    if not enable_opl_live_probe:
        return None
    deadline = time.monotonic() + DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS
    list_args = (
        "family-runtime",
        "queue",
        "list",
        "--domain",
        OPL_DOMAIN_ID,
        "--study",
        _text(carrier.get("study_id")) or "",
        "--task-kind",
        OPL_STAGE_ROUTE_TASK_KIND,
        "--json",
    )
    inspect_args_prefix = (
        "family-runtime",
        "queue",
        "inspect",
    )
    for candidate in _ranked_opl_bin_candidates():
        if not candidate.exists():
            continue
        list_payload = _run_opl_json(
            candidate,
            list_args,
            timeout_seconds=remaining_seconds(deadline),
        )
        matched = _matching_opl_runtime_payload_running_attempt(
            carrier=carrier,
            payload=list_payload,
        )
        if matched is not None:
            return matched
        for task in _matching_opl_tasks_from_list(
            carrier=carrier,
            payload=list_payload,
        )[:DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT]:
            task_id = _text(task.get("task_id"))
            if task_id is None:
                continue
            inspect_payload = _run_opl_json(
                candidate,
                (
                    *inspect_args_prefix,
                    task_id,
                    "--json",
                ),
                timeout_seconds=remaining_seconds(deadline),
            )
            matched = _matching_opl_runtime_payload_running_attempt(
                carrier=carrier,
                payload=inspect_payload,
            )
            if matched is not None:
                return matched
    return None

def _ranked_opl_bin_candidates(opl_bin: str | Path | None = None) -> list[Path]:
    return ranked_opl_bin_candidates(opl_bin=opl_bin)

def _ranked_opl_live_probe_bin_candidates(
    *, opl_bin: str | Path | None = None
) -> list[Path]:
    try:
        return _ranked_opl_bin_candidates(opl_bin=opl_bin)
    except TypeError:
        return _ranked_opl_bin_candidates()

def _run_opl_json(
    opl_bin: Path,
    args: tuple[str, ...],
    *,
    timeout_seconds: float = DEFAULT_OPL_READBACK_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    return run_opl_json(opl_bin, args, timeout_seconds=timeout_seconds)


__all__ = [
    "RUNNING_READBACK_STATUS",
    "TERMINAL_READBACK_STATUS",
    "WAITING_READBACK_STATUS",
    "attach_opl_runtime_carrier_readback",
    "attach_paper_mission_next_action",
    "paper_mission_opl_runtime_carrier_readback",
    "paper_mission_next_action_envelope",
]

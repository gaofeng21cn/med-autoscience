from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
)

SUPPORTED_APPLY_MODES = ("route_redesign", "owner_decision", "human_gate")

APPLIED_RESOLUTION_STATUSES = (
    "owner_route_redesign_applied",
    "owner_decision_resolution_packet_materialized",
    "human_gate_resolution_packet_materialized",
)


def diagnose_typed_blocker_resolution_gap(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
    profile_ref: str,
    source: str = "unknown",
) -> dict[str, Any]:
    return materialize_typed_blocker_resolution(
        paper_mission_readback=paper_mission_readback,
        study_id=study_id,
        profile_ref=profile_ref,
        source=source,
    )


def materialize_typed_blocker_resolution(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
    profile_ref: str,
    output_root: Path | None = None,
    apply_mode: str | None = None,
    source: str = "unknown",
) -> dict[str, Any]:
    validation = _validate_readback(
        paper_mission_readback=paper_mission_readback,
        study_id=study_id,
    )
    if validation["valid"] is not True:
        result = {
            "surface_kind": "paper_mission_typed_blocker_resolution",
            "schema_version": 1,
            "status": "blocked_missing_consumed_typed_blocker_readback",
            "study_id": study_id,
            "profile_ref": profile_ref,
            "source": source,
            "write_permitted": False,
            "authority_materialized": False,
            "readback_validation": validation,
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        }
        return _maybe_attach_output_manifest(
            result,
            output_root=output_root,
            study_id=study_id,
        )

    package = _current_package_summary(paper_mission_readback)
    receipt = _mapping(paper_mission_readback.get("receipt_owner_consumption_readback"))
    decision = _mapping(paper_mission_readback.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    consumption = _mapping(receipt.get("mas_receipt_consumption"))
    typed_ref = _first_text(
        consumption.get("typed_blocker_evidence_ref"),
        consumption.get("typed_runtime_blocker_ref"),
        outcome.get("typed_blocker_evidence_ref"),
    )
    blocker = _first_text(outcome.get("blocker_type"), "paper_mission_typed_blocker")
    if apply_mode is not None:
        result = _apply_typed_blocker_resolution(
            study_id=study_id,
            profile_ref=profile_ref,
            source=source,
            validation=validation,
            package=package,
            receipt=receipt,
            outcome=outcome,
            consumption=consumption,
            typed_ref=typed_ref,
            blocker=blocker,
            apply_mode=apply_mode,
        )
        return _maybe_attach_output_manifest(
            result,
            output_root=output_root,
            study_id=study_id,
        )
    result = {
        "surface_kind": "paper_mission_typed_blocker_resolution",
        "schema_version": 1,
        "status": "blocked_missing_typed_blocker_resolution_surface",
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "write_permitted": False,
        "authority_materialized": False,
        "paper_ready_claim_authorized": False,
        "publication_ready_claim_authorized": False,
        "submission_ready_claim_authorized": False,
        "readback_validation": validation,
        "typed_blocker": {
            "blocker_type": blocker,
            "next_owner": _text(outcome.get("next_owner")) or "MedAutoScience",
            "next_action": _text(outcome.get("next_action"))
            or "resolve_typed_blocker_or_route_redesign",
            "typed_blocker_evidence_ref": typed_ref,
        },
        "current_package": package,
        "owner_route_defect": {
            "defect_kind": "mas_typed_blocker_resolution_owner_surface_missing",
            "missing_command_or_api": (
                "paper-mission typed-blocker-resolution --apply-owner-decision "
                "| --apply-human-gate | --apply-route-redesign"
            ),
            "required_inputs": [
                "paper-mission inspect --request-opl-runtime-readback JSON",
                "next_action.action_family=blocked.typed",
                "receipt_owner_consumption_readback.status=owner_consumption_applied",
                "receipt_owner_consumption_readback.mas_receipt_consumption.status=owner_consumed_typed_blocker",
                "stage_closure_decision.outcome.kind=typed_blocker",
                "current_package projection",
            ],
            "allowed_write_set": [
                "MAS governed owner decision packet after authority contract exists",
                "MAS governed human gate after authority contract exists",
                "MAS governed route redesign / successor work-unit decision after authority contract exists",
                "non-authority diagnostic JSON returned by this command",
            ],
            "forbidden_write_set": list(FORBIDDEN_AUTHORITY_WRITES),
            "verification": [
                "focused CLI/controller tests",
                "fresh paper-mission inspect readback for DM002 and DM003",
                "fresh delivery-inspect readback before any submission-ready claim",
            ],
        },
        "next_legal_command": (
            "implement MAS typed-blocker resolution apply surface, then rerun "
            "paper-mission typed-blocker-resolution with the matching --apply-* mode"
        ),
        "forbidden_next_actions": [
            "synonymous OPL runtime redrive",
            "paper.gate.publishability_replay without a changed owner decision or source signature",
            "manual Yang authority/current_package/publication_eval/controller_decision edits",
        ],
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }
    return _maybe_attach_output_manifest(
        result,
        output_root=output_root,
        study_id=study_id,
    )


def _apply_typed_blocker_resolution(
    *,
    study_id: str,
    profile_ref: str,
    source: str,
    validation: Mapping[str, Any],
    package: Mapping[str, Any],
    receipt: Mapping[str, Any],
    outcome: Mapping[str, Any],
    consumption: Mapping[str, Any],
    typed_ref: str | None,
    blocker: str | None,
    apply_mode: str,
) -> dict[str, Any]:
    plan = _apply_mode_plan(apply_mode)
    if plan is None:
        return {
            "surface_kind": "paper_mission_typed_blocker_resolution",
            "schema_version": 1,
            "status": "blocked_apply_mode_not_implemented",
            "study_id": study_id,
            "profile_ref": profile_ref,
            "source": source,
            "requested_apply_mode": apply_mode,
            "implemented_apply_modes": list(SUPPORTED_APPLY_MODES),
            "write_permitted": False,
            "authority_materialized": False,
            "paper_ready_claim_authorized": False,
            "publication_ready_claim_authorized": False,
            "submission_ready_claim_authorized": False,
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        }
    generated_at = _utc_now()
    successor = _successor_work_unit(
        study_id=study_id,
        package=package,
        blocker=blocker,
        apply_mode=apply_mode,
    )
    owner_decision_packet = {
        "surface_kind": "paper_mission_typed_blocker_resolution_owner_decision",
        "schema_version": 1,
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "recorded_at": generated_at,
        "decision_kind": plan["decision_kind"],
        "decision_status": plan["status"],
        "typed_blocker_evidence_ref": typed_ref,
        "blocker_type": blocker,
        "next_owner": successor["owner"],
        "next_work_unit": successor["work_unit_id"],
        "next_action": successor["next_action"],
        "current_package": dict(package),
        "source_receipt_owner_consumption": {
            "status": _text(receipt.get("status")),
            "apply_mode": _text(receipt.get("apply_mode")),
            "mas_receipt_consumption_status": _text(consumption.get("status")),
            "next_legal_action": _text(consumption.get("next_legal_action")),
            "forbidden_next_action": _text(consumption.get("forbidden_next_action")),
        },
        "source_stage_outcome": dict(outcome),
        "authority_boundary": _authority_boundary(),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }
    successor_work_unit = {
        "surface_kind": "paper_mission_typed_blocker_resolution_successor_work_unit",
        "schema_version": 1,
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "recorded_at": generated_at,
        **successor,
        "typed_blocker_evidence_ref": typed_ref,
        "blocker_type": blocker,
        "current_package": dict(package),
        "authority_boundary": _authority_boundary(),
    }
    executable_route = _executable_owner_route(
        study_id=study_id,
        typed_ref=typed_ref,
        blocker=blocker,
        successor=successor,
        package=package,
        apply_mode=apply_mode,
    )
    return {
        "surface_kind": "paper_mission_typed_blocker_resolution",
        "schema_version": 1,
        "status": plan["status"],
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "apply_mode": apply_mode,
        "write_permitted": True,
        "resolution_packet_materialized": True,
        "authority_materialized": False,
        "writes_authority": False,
        "paper_ready_claim_authorized": False,
        "publication_ready_claim_authorized": False,
        "submission_ready_claim_authorized": False,
        "readback_validation": dict(validation),
        "typed_blocker": {
            "blocker_type": blocker,
            "typed_blocker_evidence_ref": typed_ref,
            "next_owner": _text(outcome.get("next_owner")) or "MedAutoScience",
            "next_action": _text(outcome.get("next_action"))
            or "resolve_typed_blocker_or_route_redesign",
        },
        "current_package": dict(package),
        "owner_decision_packet": owner_decision_packet,
        "successor_work_unit": successor_work_unit,
        "executable_owner_route": executable_route,
        "next_owner_action": _next_owner_action(
            study_id=study_id,
            typed_ref=typed_ref,
            blocker=blocker,
            successor=successor,
            executable_route=executable_route,
        ),
        "can_claim_submission_ready": False,
        "durable_stop_allowed": False,
        "next_legal_command": successor["resume_command"],
        "forbidden_next_actions": [
            "synonymous OPL runtime redrive",
            "paper.gate.publishability_replay without a changed owner decision or source signature",
            "manual Yang authority/current_package/publication_eval/controller_decision edits",
        ],
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def latest_typed_blocker_resolution_readback(
    *,
    workspace_root: Path,
    study_id: str,
) -> dict[str, Any] | None:
    ledger_root = (
        workspace_root.expanduser().resolve()
        / "ops"
        / "medautoscience"
        / "paper_mission_typed_blocker_resolution"
    )
    if not ledger_root.exists():
        return None
    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for packet_ref in ledger_root.glob(f"**/{study_id}/typed_blocker_resolution.json"):
        payload = _valid_resolution_readback(packet_ref=packet_ref, study_id=study_id)
        if payload is None:
            continue
        try:
            mtime = packet_ref.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append((mtime, str(packet_ref), payload))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def _successor_work_unit(
    *,
    study_id: str,
    package: Mapping[str, Any],
    blocker: str | None,
    apply_mode: str,
) -> dict[str, Any]:
    if apply_mode == "owner_decision":
        return {
            "owner": "mas_authority_kernel",
            "work_unit_id": "submission_ready_authority_closeout",
            "next_action": "materialize_submission_ready_owner_verdict_or_human_gate",
            "successor_reason": "owner_decision_requested_for_submission_authority_closeout",
            "resume_command": (
                "paper-mission typed-blocker-resolution --apply-owner-decision "
                f"--study-id {study_id}"
            ),
        }
    if apply_mode == "human_gate":
        return {
            "owner": "mas_authority_kernel",
            "work_unit_id": "submission_blocker_human_gate",
            "next_action": "await_human_or_mas_authority_decision_for_submission_blocker",
            "successor_reason": blocker or "typed_blocker_requires_human_gate",
            "resume_command": (
                "paper-mission typed-blocker-resolution --apply-human-gate "
                f"--study-id {study_id}"
            ),
        }
    if package.get("can_submit") is True and _text(package.get("package_kind")) == "submission_ready_package":
        return {
            "owner": "mas_authority_kernel",
            "work_unit_id": "submission_authority_owner_verdict",
            "next_action": "consume_submission_ready_package_authority_or_human_gate",
            "successor_reason": "submission_ready_mirror_requires_authority_owner_verdict",
            "resume_command": (
                "paper-mission typed-blocker-resolution --apply-owner-decision "
                f"--study-id {study_id}"
            ),
        }
    return {
        "owner": "mas_authority_kernel",
        "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        "next_action": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
        "successor_reason": blocker or "current_package_not_submission_ready",
        "resume_command": (
            "paper-mission typed-blocker-resolution --apply-human-gate "
            f"--study-id {study_id}"
        ),
    }


def _apply_mode_plan(apply_mode: str) -> dict[str, str] | None:
    if apply_mode == "route_redesign":
        return {
            "status": "owner_route_redesign_applied",
            "decision_kind": "route_redesign",
        }
    if apply_mode == "owner_decision":
        return {
            "status": "owner_decision_resolution_packet_materialized",
            "decision_kind": "owner_decision",
        }
    if apply_mode == "human_gate":
        return {
            "status": "human_gate_resolution_packet_materialized",
            "decision_kind": "human_gate",
        }
    return None


def _next_owner_action(
    *,
    study_id: str,
    typed_ref: str | None,
    blocker: str | None,
    successor: Mapping[str, Any],
    executable_route: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    work_unit_id = _text(successor.get("work_unit_id")) or "paper_mission_typed_blocker_resolution"
    fingerprint = hashlib.sha256(
        json.dumps(
            [study_id, typed_ref, blocker, work_unit_id, successor.get("next_action")],
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:24]
    action_type = _text(successor.get("next_action")) or "resolve_typed_blocker"
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_mission_typed_blocker_resolution",
        "study_id": study_id,
        "next_owner": _text(successor.get("owner")) or "mas_authority_kernel",
        "owner": _text(successor.get("owner")) or "mas_authority_kernel",
        "action_type": action_type,
        "allowed_actions": [action_type],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "required_delta_kind": "typed_blocker_resolution_owner_action",
        "target_surface": {
            "ref_kind": "mas_ops_resolution_packet",
            "surface_ref": "ops/medautoscience/paper_mission_typed_blocker_resolution",
            **({"typed_blocker_evidence_ref": typed_ref} if typed_ref else {}),
        },
        "target_surface_specificity": "typed_blocker_resolution",
        "acceptance_refs": [
            ref
            for ref in (typed_ref, "typed_blocker_resolution_packet_ref")
            if ref
        ],
        **(
            {
                "paper_facing_delta": _mapping(
                    executable_route.get("paper_facing_delta")
                ),
                "accepted_answer_shape": _mapping(
                    executable_route.get("accepted_answer_shape")
                ),
                "route_back": _mapping(executable_route.get("route_back")),
                "verification": _mapping(executable_route.get("verification")),
                "executable_owner_route": dict(executable_route),
            }
            if executable_route
            else {}
        ),
        "owner_receipt_required": True,
        "authority": "study_progress.current_executable_owner_action",
        "authority_boundary": {
            "projection_only": True,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_write_current_package": False,
            "can_start_provider_attempt": False,
        },
    }


def _executable_owner_route(
    *,
    study_id: str,
    typed_ref: str | None,
    blocker: str | None,
    successor: Mapping[str, Any],
    package: Mapping[str, Any],
    apply_mode: str,
) -> dict[str, Any]:
    action_type = _text(successor.get("next_action")) or "resolve_typed_blocker"
    next_owner = _text(successor.get("owner")) or "mas_authority_kernel"
    work_unit_id = _text(successor.get("work_unit_id")) or "paper_mission_typed_blocker_resolution"
    answer_shape = _accepted_answer_shape(action_type)
    return {
        "surface_kind": "paper_mission_executable_owner_route",
        "schema_version": 1,
        "status": "ready_for_owner",
        "study_id": study_id,
        "next_owner": next_owner,
        "work_unit_id": work_unit_id,
        "action_type": action_type,
        "allowed_actions": [action_type],
        "source_apply_mode": apply_mode,
        "typed_blocker_evidence_ref": typed_ref,
        "blocker_type": blocker,
        "paper_facing_delta": _paper_facing_delta(
            package=package,
            successor=successor,
        ),
        "accepted_answer_shape": answer_shape,
        "route_back": {
            "required": True,
            "route_back_to": "paper-mission inspect",
            "route_back_evidence_ref": typed_ref,
            "expected_readback_fields": [
                "next_action",
                "current_executable_owner_action",
                "typed_blocker_resolution_readback",
                "stage_closure_decision",
            ],
        },
        "verification": {
            "repo_focused_tests": [
                "tests/test_cli_cases/paper_mission_command_cases/typed_blocker_resolution.py",
                "tests/test_current_executable_owner_action_canonical.py",
            ],
            "owner_readback_command": (
                "paper-mission inspect --request-opl-runtime-readback "
                f"--study-id {study_id} --format json"
            ),
            "success_condition": (
                "readback projects this work unit as current_executable_owner_action "
                f"and later owner answer matches {answer_shape['shape_kind']}"
            ),
        },
    }


def _paper_facing_delta(
    *,
    package: Mapping[str, Any],
    successor: Mapping[str, Any],
) -> dict[str, Any]:
    can_submit = package.get("can_submit") is True
    action = _text(successor.get("next_action")) or ""
    if can_submit:
        delta_kind = "submission_authority_owner_verdict"
    elif "human" in action:
        delta_kind = "human_gate_decision"
    else:
        delta_kind = "degraded_or_quality_repair_handoff"
    return {
        "delta_kind": delta_kind,
        "paper_surface": "manuscript/current_package",
        "package_kind": _text(package.get("package_kind")),
        "can_submit": can_submit,
        "expected_delta": _text(successor.get("successor_reason"))
        or "typed blocker resolution owner delta",
        "known_blockers": _text_list(package.get("known_blockers")),
    }


def _accepted_answer_shape(action_type: str) -> dict[str, Any]:
    if action_type == "consume_submission_ready_package_authority_or_human_gate":
        return {
            "shape_kind": "owner_receipt_or_human_gate",
            "accepted_statuses": ["owner_receipt", "human_gate", "route_back"],
            "required_refs": [
                "study_owner_gate_decision_ref",
                "current_package_ref",
                "typed_blocker_resolution_packet_ref",
            ],
        }
    if action_type == "materialize_submission_ready_owner_verdict_or_human_gate":
        return {
            "shape_kind": "submission_authority_owner_gate_decision",
            "accepted_statuses": ["owner_receipt", "human_gate", "route_back"],
            "required_refs": [
                "study_owner_gate_decision_ref",
                "current_package_ref",
                "typed_blocker_resolution_packet_ref",
            ],
        }
    if action_type == "await_human_or_mas_authority_decision_for_submission_blocker":
        return {
            "shape_kind": "human_gate_or_degraded_handoff",
            "accepted_statuses": ["human_gate", "route_back", "typed_blocker"],
            "required_refs": [
                "human_gate_question_ref",
                "known_blockers",
                "resume_condition",
            ],
        }
    return {
        "shape_kind": "quality_repair_or_degraded_handoff",
        "accepted_statuses": ["route_back", "typed_blocker", "owner_receipt"],
        "required_refs": [
            "known_blockers",
            "repair_plan_ref",
            "typed_blocker_resolution_packet_ref",
        ],
    }


def _authority_boundary() -> dict[str, bool | str]:
    return {
        "surface_role": "paper_mission_typed_blocker_resolution",
        "resolution_packet_materialized": True,
        "authority_materialized": False,
        "writes_typed_blocker_resolution": True,
        "writes_authority": False,
        "writes_owner_receipt": False,
        "writes_typed_blocker": False,
        "writes_human_gate": False,
        "writes_current_package": False,
        "writes_publication_eval": False,
        "writes_controller_decision": False,
        "writes_runtime_queue_or_provider_attempt": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_submission_ready": False,
    }


def _maybe_attach_output_manifest(
    payload: dict[str, Any],
    *,
    output_root: Path | None,
    study_id: str,
) -> dict[str, Any]:
    if output_root is None:
        return payload
    manifest = _write_output_packet(
        output_root=output_root,
        study_id=study_id,
        payload=payload,
        writes_authority=payload.get("authority_materialized") is True,
    )
    owner_decision = _mapping(payload.get("owner_decision_packet"))
    successor = _mapping(payload.get("successor_work_unit"))
    if owner_decision:
        owner_path = output_root / study_id / "owner_decision_packet.json"
        _write_json(owner_path, owner_decision)
        manifest["owner_decision_packet_ref"] = str(owner_path)
    if successor:
        successor_path = output_root / study_id / "successor_work_unit.json"
        _write_json(successor_path, successor)
        manifest["successor_work_unit_ref"] = str(successor_path)
    return {**payload, "output_manifest": manifest}


def _write_output_packet(
    *,
    output_root: Path,
    study_id: str,
    payload: Mapping[str, Any],
    writes_authority: bool,
) -> dict[str, Any]:
    packet_path = output_root / study_id / "typed_blocker_resolution.json"
    text = _write_json(packet_path, payload)
    return {
        "surface_kind": "paper_mission_typed_blocker_resolution_output_manifest",
        "schema_version": 1,
        "output_root": str(output_root),
        "packet_ref": str(packet_path),
        "packet_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "writes_authority": False,
        "writes_yang_authority": False,
        "writes_owner_decision_packet": bool(
            _mapping(payload.get("owner_decision_packet"))
        ),
        "writes_successor_work_unit": bool(_mapping(payload.get("successor_work_unit"))),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return text


def _valid_resolution_readback(
    *,
    packet_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    try:
        payload = json.loads(packet_ref.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("surface_kind") != "paper_mission_typed_blocker_resolution":
        return None
    if _text(payload.get("study_id")) != study_id:
        return None
    if payload.get("status") not in APPLIED_RESOLUTION_STATUSES:
        return None
    if payload.get("resolution_packet_materialized") is not True:
        return None
    if payload.get("authority_materialized") is True or payload.get("writes_authority") is True:
        return None
    boundary = _mapping(payload.get("authority_boundary"))
    forbidden_flags = (
        "writes_owner_receipt",
        "writes_typed_blocker",
        "writes_human_gate",
        "writes_current_package",
        "writes_publication_eval",
        "writes_controller_decision",
        "writes_runtime_queue_or_provider_attempt",
    )
    if any(boundary.get(flag) is True for flag in forbidden_flags):
        return None
    if payload.get("submission_ready_claim_authorized") is True:
        return None
    if not _mapping(payload.get("next_owner_action")):
        return None
    return {
        **payload,
        "source_ref": str(packet_ref),
        "decision_ref": str(packet_ref),
        "source_surface_kind": "paper_mission_typed_blocker_resolution_ledger",
    }


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_readback(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
) -> dict[str, Any]:
    missing: list[str] = []
    mismatched: list[str] = []
    if _text(paper_mission_readback.get("study_id")) != study_id:
        mismatched.append("study_id")
    next_action = _mapping(paper_mission_readback.get("next_action"))
    action_family = _text(next_action.get("action_family"))
    action_kind = _text(next_action.get("action_kind"))
    allowed_next_actions = {
        ("blocked.typed", "stop_with_typed_blocker"),
        ("paper.package.submission_minimal", "package_materialization"),
    }
    if (action_family, action_kind) not in allowed_next_actions:
        mismatched.append("next_action.action_family")
        mismatched.append("next_action.action_kind")
    if _text(next_action.get("owner")) != "mas_authority_kernel":
        mismatched.append("next_action.owner")

    decision = _mapping(paper_mission_readback.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    if not decision:
        missing.append("stage_closure_decision")
    elif _text(outcome.get("kind")) != "typed_blocker":
        mismatched.append("stage_closure_decision.outcome.kind")

    receipt = _mapping(paper_mission_readback.get("receipt_owner_consumption_readback"))
    if not receipt:
        missing.append("receipt_owner_consumption_readback")
    else:
        if _text(receipt.get("status")) != "owner_consumption_applied":
            mismatched.append("receipt_owner_consumption_readback.status")
        consumption = _mapping(receipt.get("mas_receipt_consumption"))
        if _text(consumption.get("status")) != "owner_consumed_typed_blocker":
            mismatched.append("receipt_owner_consumption_readback.mas_receipt_consumption.status")
    return {
        "valid": not missing and not mismatched,
        "missing_required_fields": missing,
        "mismatched_fields": mismatched,
    }


def _current_package_summary(readback: Mapping[str, Any]) -> dict[str, Any]:
    package = _mapping(readback.get("current_package"))
    return {
        "status": _first_text(package.get("status"), package.get("freshness_status")),
        "package_kind": _text(package.get("package_kind")),
        "can_submit": package.get("can_submit") is True,
        "quality_gate_status": _text(package.get("quality_gate_status")),
        "known_blockers": _text_list(package.get("known_blockers")),
        "root": _text(package.get("root")),
        "zip_path": _text(package.get("zip_path")),
        "zip_exists": package.get("zip_exists") is True,
        "generated_from_current_source": package.get("generated_from_current_source") is True,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text:
            return text
    return None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]

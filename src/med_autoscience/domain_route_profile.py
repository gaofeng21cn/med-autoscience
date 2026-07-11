from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


AGENT_ID = "mas"
DOMAIN_ID = "mas"
LEGACY_DOMAIN_IDS = ("medautoscience", "med-autoscience")
PROFILE_ID = "mas.domain_route.compatibility.v1"
PROFILE_REF = "contracts/domain_route_profile.json"
DOMAIN_ROUTE_TASK_KIND = "domain_route/stage-route"
DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND = "domain_route/start-or-resume"
DOMAIN_ROUTE_RUNTIME_REQUEST_KIND = "domain_route_stage_route"
HANDOFF_INTAKE_SURFACE_KIND = "opl_domain_route_handoff_intake_readback"
RUNTIME_REQUEST_SURFACE_KIND = "opl_domain_route_runtime_request"

TASK_KIND_NORMALIZATION = {
    "paper_mission/start_or_resume": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
    "paper_mission/consume_candidate": "domain_route/consume-candidate",
    "paper_mission/package_candidate": "domain_route/package-candidate",
    "paper_mission/drive": "domain_route/drive",
    "paper_mission/terminalize_stage": "domain_route/terminalize-stage",
    "paper_mission/typed_blocker_resolution": "domain_route/typed-blocker-resolution",
    "paper_mission/inspect": "domain_route/inspect",
    "paper_mission/stage-route": DOMAIN_ROUTE_TASK_KIND,
    "paper_mission/stage-outcome": "domain_route/stage-outcome",
    "paper_autonomy/repair-recheck": "domain_autonomy/repair-recheck",
    "paper_autonomy/ai-reviewer-recheck": "domain_autonomy/ai-reviewer-recheck",
    "paper_autonomy/guarded-apply": "domain_autonomy/guarded-apply",
    "paper_autonomy/supervisor-decision": "domain_autonomy/supervisor-decision",
    "paper_autonomy/gate-replay": "domain_autonomy/gate-replay",
    "paper_autonomy/route-decision": "domain_autonomy/route-decision",
    "publication_aftercare/analysis-queue-progress": (
        "domain_route/analysis-queue-progress"
    ),
    "publication_aftercare/reviewer-refresh": "domain_route/reviewer-refresh",
}
CANONICAL_DOMAIN_TASK_KINDS = tuple(sorted(set(TASK_KIND_NORMALIZATION.values())))

SUPPORTED_COMMAND_KINDS = (
    "start_next_stage",
    "resume_stage",
    "route_back",
    "stop_with_typed_blocker",
    "wait_for_human",
    "complete_mission",
)
RUNTIME_COMMAND_KINDS = frozenset(("start_next_stage", "resume_stage", "route_back"))

_AUTHORITY_BOUNDARY = {
    "writes_domain_truth": False,
    "writes_quality_verdict": False,
    "writes_owner_receipt": False,
    "writes_typed_blocker": False,
    "writes_human_gate": False,
    "writes_current_package": False,
    "writes_artifact_body": False,
    "writes_runtime_queue": False,
    "writes_opl_outbox": False,
    "writes_opl_event": False,
    "writes_opl_stage_run": False,
    "writes_provider_attempt": False,
    "can_claim_runtime_enqueued": False,
    "can_claim_stage_run_created": False,
    "can_claim_provider_running": False,
    "can_claim_domain_progress": False,
    "can_claim_domain_ready": False,
    "can_claim_quality_verdict": False,
    "can_claim_runtime_ready": False,
}
_FORBIDDEN_WRITE_LABELS = tuple(
    key for key, allowed in _AUTHORITY_BOUNDARY.items() if key.startswith("writes_") and not allowed
)
_FORBIDDEN_CLAIM_LABELS = tuple(
    key
    for key, allowed in _AUTHORITY_BOUNDARY.items()
    if key.startswith("can_claim_") and not allowed
)
_RECEIPT_LABELS = {
    "owner_receipt": ["domain_owner_receipt_ref", "owner_receipt_ref"],
    "quality_gate": ["quality_gate_receipt_ref"],
    "typed_blocker": ["domain_typed_blocker_ref", "typed_blocker_ref"],
    "human_gate": ["human_gate_ref", "owner_decision_ref"],
    "route_back": ["route_back_evidence_ref"],
    "lineage": ["owner_chain_ref", "no_regression_ref"],
}


def build_domain_route_profile() -> dict[str, Any]:
    return {
        "surface_kind": "opl_domain_route_profile",
        "schema_version": 1,
        "profile_id": PROFILE_ID,
        "profile_role": "domain_owned_compatibility_profile",
        "agent_id": AGENT_ID,
        "domain_id": DOMAIN_ID,
        "legacy_domain_ids": list(LEGACY_DOMAIN_IDS),
        "domain_truth_owner": "MedAutoScience",
        "substrate_owner": "one-person-lab",
        "canonical_projection": "domain_route",
        "canonical_task_kind": DOMAIN_ROUTE_TASK_KIND,
        "canonical_task_kinds": list(CANONICAL_DOMAIN_TASK_KINDS),
        "runtime_request_kind": DOMAIN_ROUTE_RUNTIME_REQUEST_KIND,
        "handoff_intake_surface_kind": HANDOFF_INTAKE_SURFACE_KIND,
        "runtime_request_surface_kind": RUNTIME_REQUEST_SURFACE_KIND,
        "source_paths": [
            "src/med_autoscience/domain_route_profile.py",
            "src/med_autoscience/paper_mission_opl_carrier.py",
            "src/med_autoscience/paper_mission_domain/opl_runtime_submission.py",
            "src/med_autoscience/controllers/owner_route_handoff/task_kinds.py",
        ],
        "task_kind_normalization": dict(TASK_KIND_NORMALIZATION),
        "field_mapping": {
            "command_kind": ["route_command_kind", "opl_route_command.command_kind"],
            "route_target": ["route_target", "opl_route_command.target"],
            "declarative_target_stage_id": [
                "declarative_target_stage_id",
                "opl_route_command.declarative_target_stage_id",
            ],
            "domain_route_transaction_ref": "paper_mission_transaction_ref",
            "domain_route_command_ref": "opl_route_command_ref",
            "route_identity.route_identity_key": "route_identity_key",
            "route_identity.request_idempotency_key": "request_idempotency_key",
            "attempt_identity.attempt_idempotency_key": "attempt_idempotency_key",
        },
        "authority_refs": [
            "contracts/paper_mission_transaction_contract.json#/authority_boundary",
            "contracts/owner_receipt_contract.json",
            "contracts/domain_descriptor.json#/authority_boundary",
        ],
        "supported_command_kinds": list(SUPPORTED_COMMAND_KINDS),
        "runtime_command_kinds": sorted(RUNTIME_COMMAND_KINDS),
        "legacy_compatibility": {
            "profile_ids": ["mas-paper-mission-route"],
            "task_kinds": sorted(TASK_KIND_NORMALIZATION),
            "handoff_surface_kinds": [
                "mas_paper_mission_opl_route_handoff_record",
                "mas_domain_progress_transition_request",
            ],
            "runtime_request_surface_kinds": [
                "opl_mas_paper_mission_route_runtime_request"
            ],
            "normalization_owner": "MedAutoScience",
        },
        "terminal_sync_contract": {
            "primary_discriminator": "status",
            "secondary_discriminators": ["wait_kind", "command_kind"],
            "provider_projection": {
                "status": "accepted_for_provider_projection",
                "command_kinds": sorted(RUNTIME_COMMAND_KINDS),
            },
            "typed_blocker_wait": {
                "status": "typed_wait",
                "wait_kind": "typed_blocker_authority",
                "command_kind": "stop_with_typed_blocker",
                "required_receipt_labels": [
                    *_RECEIPT_LABELS["typed_blocker"],
                    *_RECEIPT_LABELS["lineage"],
                ],
            },
            "human_gate_wait": {
                "status": "typed_wait",
                "wait_kind": "human_gate_authority",
                "command_kind": "wait_for_human",
                "required_receipt_labels": [
                    *_RECEIPT_LABELS["human_gate"],
                    "owner_chain_ref",
                ],
            },
            "terminal_no_runtime": {
                "status": "terminal_no_runtime",
                "wait_kind": "mission_complete",
                "command_kind": "complete_mission",
                "required_receipt_labels": [
                    *_RECEIPT_LABELS["owner_receipt"],
                    "owner_chain_ref",
                ],
            },
            "rejected": {"status": "rejected"},
        },
        "receipt_labels": {key: list(value) for key, value in _RECEIPT_LABELS.items()},
        "forbidden_writes": list(_FORBIDDEN_WRITE_LABELS),
        "forbidden_claims": list(_FORBIDDEN_CLAIM_LABELS),
        "generic_field_contract": [
            "agent_id",
            "domain_id",
            "domain_truth_owner",
            "runtime_owner",
            "canonical_task_kind",
            "command_kind",
            "route_target",
            "declarative_target_stage_id",
            "route_identity",
            "attempt_identity",
            "domain_route_handoff_ref",
            "domain_route_transaction_ref",
            "domain_route_command_ref",
            "source_refs",
            "authority_boundary",
            "terminal_sync",
        ],
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }


def build_domain_route_handoff_intake_readback(
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    route = _mapping(handoff.get("opl_route_command"))
    command_kind = _first_text(handoff.get("route_command_kind"), route.get("command_kind"))
    route_target = _first_text(handoff.get("route_target"), route.get("target"))
    handoff_target_stage_id = _text(handoff.get("declarative_target_stage_id"))
    route_target_stage_id = _text(route.get("declarative_target_stage_id"))
    declarative_target_stage_id = handoff_target_stage_id or route_target_stage_id
    transaction_ref = _text(handoff.get("domain_route_transaction_ref")) or _text(
        handoff.get("paper_mission_transaction_ref")
    )
    command_ref = _text(handoff.get("domain_route_command_ref")) or _text(
        handoff.get("opl_route_command_ref")
    )
    if command_ref is None and transaction_ref is not None:
        command_ref = f"{transaction_ref}#opl_route_command"
    handoff_ref = _text(handoff.get("domain_route_handoff_ref"))
    if handoff_ref is None and transaction_ref is not None:
        handoff_ref = f"{transaction_ref}#domain_route_handoff"

    request_idempotency_key = _text(handoff.get("request_idempotency_key"))
    route_identity_key = _text(handoff.get("route_identity_key"))
    if route_identity_key is None and transaction_ref is not None:
        route_identity_key = f"{transaction_ref}::route"
    attempt_idempotency_key = _text(handoff.get("attempt_idempotency_key"))
    if attempt_idempotency_key is None and request_idempotency_key is not None:
        attempt_idempotency_key = f"{request_idempotency_key}::attempt"

    source_refs = _source_refs(
        handoff=handoff,
        transaction_ref=transaction_ref,
        command_ref=command_ref,
        handoff_ref=handoff_ref,
    )
    source_fingerprint = _source_fingerprint(handoff=handoff, source_refs=source_refs)
    blockers = _blockers(
        command_kind=command_kind,
        route_target=route_target,
        declarative_target_stage_id=declarative_target_stage_id,
        declarative_target_stage_mismatch=(
            handoff_target_stage_id is not None
            and route_target_stage_id is not None
            and handoff_target_stage_id != route_target_stage_id
        ),
        transaction_ref=transaction_ref,
        command_ref=command_ref,
        handoff_ref=handoff_ref,
        route_identity_key=route_identity_key,
        request_idempotency_key=request_idempotency_key,
        attempt_idempotency_key=attempt_idempotency_key,
    )
    route_identity = _compact(
        {
            "route_identity_key": route_identity_key,
            "request_idempotency_key": request_idempotency_key,
            "source_fingerprint": source_fingerprint,
            "dedupe_key": _dedupe_key(
                command_kind=command_kind,
                request_idempotency_key=request_idempotency_key,
                source_fingerprint=source_fingerprint,
            ),
        }
    )
    attempt_identity = _compact(
        {
            "attempt_idempotency_key": attempt_idempotency_key,
            "stage_run_ref": _text(handoff.get("stage_run_ref")),
        }
    )
    generic = {
        "agent_id": AGENT_ID,
        "domain_id": DOMAIN_ID,
        "domain_truth_owner": "MedAutoScience",
        "runtime_owner": "one-person-lab",
        "canonical_task_kind": DOMAIN_ROUTE_TASK_KIND,
        "command_kind": command_kind,
        "route_target": route_target,
        "declarative_target_stage_id": declarative_target_stage_id,
        "route_identity": route_identity,
        "attempt_identity": attempt_identity,
        "domain_route_handoff_ref": handoff_ref,
        "domain_route_transaction_ref": transaction_ref,
        "domain_route_command_ref": command_ref,
        "source_refs": source_refs,
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    status, wait_kind = _terminal_disposition(
        command_kind=command_kind,
        blockers=blockers,
    )
    terminal_sync = _terminal_sync(
        status=status,
        wait_kind=wait_kind,
        command_kind=command_kind,
    )
    runtime_request = None
    if not blockers and command_kind in RUNTIME_COMMAND_KINDS:
        runtime_request = {
            "surface_kind": RUNTIME_REQUEST_SURFACE_KIND,
            "schema_version": 1,
            "task_kind": DOMAIN_ROUTE_TASK_KIND,
            "runtime_request_kind": DOMAIN_ROUTE_RUNTIME_REQUEST_KIND,
            **generic,
        }
    return {
        "surface_kind": HANDOFF_INTAKE_SURFACE_KIND,
        "schema_version": 1,
        "profile_ref": PROFILE_REF,
        "status": status,
        "wait_kind": wait_kind,
        "can_submit_to_opl_runtime": runtime_request is not None,
        **generic,
        "terminal_sync": terminal_sync,
        "runtime_request": runtime_request,
        "blockers": blockers,
    }


def build_domain_route_runtime_request(
    handoff: Mapping[str, Any],
) -> dict[str, Any] | None:
    return build_domain_route_handoff_intake_readback(handoff)["runtime_request"]


def canonical_domain_task_kind(task_kind: object) -> str | None:
    value = _text(task_kind)
    if value is None:
        return None
    return TASK_KIND_NORMALIZATION.get(value, value)


def _terminal_disposition(
    *,
    command_kind: str | None,
    blockers: list[dict[str, str]],
) -> tuple[str, str | None]:
    if blockers:
        return "rejected", None
    if command_kind in RUNTIME_COMMAND_KINDS:
        return "accepted_for_provider_projection", None
    if command_kind == "stop_with_typed_blocker":
        return "typed_wait", "typed_blocker_authority"
    if command_kind == "wait_for_human":
        return "typed_wait", "human_gate_authority"
    return "terminal_no_runtime", "mission_complete"


def _terminal_sync(
    *,
    status: str,
    wait_kind: str | None,
    command_kind: str | None,
) -> dict[str, Any]:
    required_receipt_labels: list[str] = []
    if wait_kind == "typed_blocker_authority":
        required_receipt_labels = [
            *_RECEIPT_LABELS["typed_blocker"],
            *_RECEIPT_LABELS["lineage"],
        ]
    elif wait_kind == "human_gate_authority":
        required_receipt_labels = [
            *_RECEIPT_LABELS["human_gate"],
            "owner_chain_ref",
        ]
    elif wait_kind == "mission_complete":
        required_receipt_labels = [
            *_RECEIPT_LABELS["owner_receipt"],
            "owner_chain_ref",
        ]
    return {
        "primary_discriminator": status,
        "wait_kind": wait_kind,
        "command_kind": command_kind,
        "required_receipt_labels": required_receipt_labels,
        "forbidden_writes": list(_FORBIDDEN_WRITE_LABELS),
        "forbidden_claims": list(_FORBIDDEN_CLAIM_LABELS),
    }


def _blockers(
    *,
    command_kind: str | None,
    route_target: str | None,
    declarative_target_stage_id: str | None,
    declarative_target_stage_mismatch: bool,
    transaction_ref: str | None,
    command_ref: str | None,
    handoff_ref: str | None,
    route_identity_key: str | None,
    request_idempotency_key: str | None,
    attempt_idempotency_key: str | None,
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    required = {
        "command_kind": command_kind,
        "route_target": route_target,
        "domain_route_transaction_ref": transaction_ref,
        "domain_route_command_ref": command_ref,
        "domain_route_handoff_ref": handoff_ref,
        "route_identity.route_identity_key": route_identity_key,
        "route_identity.request_idempotency_key": request_idempotency_key,
        "attempt_identity.attempt_idempotency_key": attempt_idempotency_key,
    }
    if command_kind in RUNTIME_COMMAND_KINDS:
        required["declarative_target_stage_id"] = declarative_target_stage_id
    for field, value in required.items():
        if value is None:
            blockers.append({"reason": "required_domain_route_field_missing", "field": field})
    if command_kind is not None and command_kind not in SUPPORTED_COMMAND_KINDS:
        blockers.append({"reason": "unsupported_domain_route_command", "field": "command_kind"})
    if declarative_target_stage_mismatch:
        blockers.append(
            {
                "reason": "domain_route_stage_identity_mismatch",
                "field": "declarative_target_stage_id",
            }
        )
    return blockers


def _source_refs(
    *,
    handoff: Mapping[str, Any],
    transaction_ref: str | None,
    command_ref: str | None,
    handoff_ref: str | None,
) -> list[str]:
    task_intake_ref = _mapping(handoff.get("task_intake_ref"))
    values = [
        handoff_ref,
        transaction_ref,
        command_ref,
        _text(handoff.get("candidate_ref")),
        _text(handoff.get("owner_consumption_readback_ref")),
        _text(handoff.get("route_checkpoint_evidence_ref")),
        _text(handoff.get("stage_run_ref")),
        _text(handoff.get("source_ref")),
        _text(task_intake_ref.get("artifact_path")),
    ]
    return list(dict.fromkeys(value for value in values if value is not None))


def _source_fingerprint(*, handoff: Mapping[str, Any], source_refs: list[str]) -> str:
    candidate_ref = _text(handoff.get("candidate_ref"))
    candidate_sha256 = None
    if candidate_ref is not None:
        candidate_path = Path(candidate_ref).expanduser()
        if candidate_path.is_file():
            candidate_sha256 = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    payload = {
        "source_refs": source_refs,
        "candidate_sha256": candidate_sha256,
        "command_kind": _first_text(
            handoff.get("route_command_kind"),
            _mapping(handoff.get("opl_route_command")).get("command_kind"),
        ),
        "route_target": _first_text(
            handoff.get("route_target"),
            _mapping(handoff.get("opl_route_command")).get("target"),
        ),
        "declarative_target_stage_id": _first_text(
            handoff.get("declarative_target_stage_id"),
            _mapping(handoff.get("opl_route_command")).get(
                "declarative_target_stage_id"
            ),
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def _dedupe_key(
    *,
    command_kind: str | None,
    request_idempotency_key: str | None,
    source_fingerprint: str,
) -> str | None:
    if command_kind is None or request_idempotency_key is None:
        return None
    return ":".join(
        (
            "domain-route",
            "v1",
            DOMAIN_ID,
            request_idempotency_key,
            command_kind,
            source_fingerprint.removeprefix("sha256:")[:16],
        )
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _first_text(*values: object) -> str | None:
    return next((text for value in values if (text := _text(value)) is not None), None)


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


__all__ = [
    "AGENT_ID",
    "CANONICAL_DOMAIN_TASK_KINDS",
    "DOMAIN_ID",
    "DOMAIN_ROUTE_RUNTIME_REQUEST_KIND",
    "DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND",
    "DOMAIN_ROUTE_TASK_KIND",
    "HANDOFF_INTAKE_SURFACE_KIND",
    "PROFILE_ID",
    "PROFILE_REF",
    "RUNTIME_REQUEST_SURFACE_KIND",
    "TASK_KIND_NORMALIZATION",
    "build_domain_route_handoff_intake_readback",
    "build_domain_route_profile",
    "build_domain_route_runtime_request",
    "canonical_domain_task_kind",
]

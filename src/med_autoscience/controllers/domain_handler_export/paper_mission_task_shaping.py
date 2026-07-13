from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.paper_mission_domain import (
    DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
    build_paper_mission_readback,
)
from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.controllers.owner_route_handoff.export_study_projection import (
    mapping,
    text,
)
from med_autoscience.paper_mission_stage_run_readback import paper_mission_next_action_envelope
from med_autoscience.profiles import WorkspaceProfile


def paper_mission_start_or_resume_task(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any]:
    dispatch_run_id = _paper_mission_default_dispatch_run_id(study_id)
    readback = build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="start",
        dry_run=True,
        source="domain-handler-export",
    )
    carrier = mapping(readback.get("opl_stage_run_context"))
    route_command = mapping(readback.get("ai_route_context"))
    has_route_identity = bool(
        text(carrier.get("route_identity_key"))
        or (
            text(carrier.get("work_unit_id"))
            and text(carrier.get("work_unit_fingerprint"))
        )
    )
    default_route_handoff = (
        {
            **carrier,
            "opl_stage_run_context": carrier,
            "ai_route_context": route_command,
            "stage_terminal_decision": mapping(
                readback.get("stage_terminal_decision")
            ),
            "handoff_status": "ready_for_ai_route_context",
            "workspace_root": str(profile.workspace_root),
        }
        if carrier and route_command and has_route_identity
        else {}
    )
    stage_packet_refs = _paper_mission_stage_packet_refs(readback)
    payload = {
        "profile": str(profile_ref),
        "profile_ref": str(profile_ref),
        "workspace_root": str(profile.workspace_root),
        "domain_workspace_root": str(profile.workspace_root),
        "repo_root": str(profile.workspace_root),
        "study_id": study_id,
        "paper_mission_command": "drive",
        "run_id": dispatch_run_id,
        "dry_run": False,
        "dispatch_execution_boundary": {
            "mode": "non_authority_candidate_package_and_opl_carrier",
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "runtime_handoff_requires_opl_owner_consumption": True,
        },
        "diagnostic_readback_command": "start",
        "diagnostic_readback_dry_run": True,
        "paper_mission": readback,
    }
    if carrier:
        payload.update(
            {
                "opl_stage_run_context": carrier,
                "ai_route_context": mapping(carrier.get("ai_route_context")) or carrier,
                "dispatch_authority": "paper_mission_transaction",
                "action_type": text(carrier.get("action_type")),
                "work_unit_id": text(carrier.get("work_unit_id")),
                "work_unit_fingerprint": text(carrier.get("work_unit_fingerprint")),
                "action_fingerprint": text(carrier.get("work_unit_fingerprint")),
                "source_fingerprint": text(carrier.get("work_unit_fingerprint")),
                "route_identity_key": text(carrier.get("route_identity_key")),
                "attempt_idempotency_key": text(carrier.get("attempt_idempotency_key")),
                "request_idempotency_key": text(carrier.get("request_idempotency_key")),
                "declarative_target_stage_id": text(
                    carrier.get("declarative_target_stage_id")
                ),
                "next_executable_owner": "med-autoscience",
                "provider_attempt_or_lease_required": False,
                "provider_completion_is_domain_completion": False,
                "semantic_route_boundary": {
                    "owner": "codex_cli",
                    "program_can_execute_or_block_route": False,
                    "transport_authority_boundary": carrier.get("authority_boundary"),
                },
                "stage_packet_refs": stage_packet_refs,
            }
        )
        if stage_packet_refs:
            payload["stage_packet_ref"] = stage_packet_refs[0]
    if default_route_handoff:
        enriched_route_handoff = _enriched_paper_mission_route_handoff(
            route_handoff=default_route_handoff,
            workspace_root=profile.workspace_root,
            profile_ref=profile_ref,
        )
        next_action = paper_mission_next_action_envelope(
            transaction=mapping(readback.get("paper_mission_transaction")),
            stage_terminal_decision=mapping(enriched_route_handoff.get("stage_terminal_decision")),
            ai_route_context=mapping(enriched_route_handoff.get("ai_route_context")),
            opl_stage_run_context=mapping(enriched_route_handoff.get("opl_stage_run_context")),
            opl_route_handoff=enriched_route_handoff,
        )
        payload.update(
            {
                "opl_route_handoff": enriched_route_handoff,
                "opl_route_handoff_record": enriched_route_handoff,
                **({"next_action": next_action} if next_action else {}),
                "paper_mission_default_handoff_source": "opl_stage_run_context",
                "paper_mission_default_handoff_ref": text(default_route_handoff.get("source_ref")),
                "ai_route_context": mapping(enriched_route_handoff.get("ai_route_context")),
                "route_command_kind": text(enriched_route_handoff.get("route_command_kind")),
                "route_target": text(enriched_route_handoff.get("route_target")),
                "paper_mission_transaction_ref": text(
                    enriched_route_handoff.get("paper_mission_transaction_ref")
                ),
                "ai_route_context_ref": text(enriched_route_handoff.get("ai_route_context_ref")),
                "candidate_ref": text(enriched_route_handoff.get("candidate_ref")),
                "source_ref": text(enriched_route_handoff.get("source_ref")),
                "mission_id": text(enriched_route_handoff.get("mission_id")),
                "route_identity_key": text(enriched_route_handoff.get("route_identity_key")),
                "attempt_idempotency_key": text(
                    enriched_route_handoff.get("attempt_idempotency_key")
                ),
                "request_idempotency_key": text(
                    enriched_route_handoff.get("request_idempotency_key")
                ),
                "next_executable_owner": "one-person-lab",
            }
        )
    task = {
        "task_id": f"paper-mission-start-or-resume::{study_id}",
        "domain_id": "medautoscience",
        "task_kind": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
        "recommended_task_kind": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
        "action_intent": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
        "default_paper_mission_entry": True,
        "migration_diagnostic_only": False,
        "source": "mas-domain-handler-export",
        "profile": str(profile_ref),
        "study_id": study_id,
        "payload": payload,
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang": False,
            "forbidden_authority_writes": readback["forbidden_authority_writes"],
        },
    }
    if default_route_handoff:
        task.update(
            {
                "opl_route_handoff": enriched_route_handoff,
                "opl_route_handoff_record": enriched_route_handoff,
                **({"next_action": next_action} if next_action else {}),
                "paper_mission_default_handoff_source": "opl_stage_run_context",
                "paper_mission_default_handoff_ref": text(default_route_handoff.get("source_ref")),
                "route_command_kind": text(enriched_route_handoff.get("route_command_kind")),
                "route_target": text(enriched_route_handoff.get("route_target")),
                "paper_mission_transaction_ref": text(
                    enriched_route_handoff.get("paper_mission_transaction_ref")
                ),
                "ai_route_context_ref": text(enriched_route_handoff.get("ai_route_context_ref")),
                "candidate_ref": text(enriched_route_handoff.get("candidate_ref")),
                "source_ref": text(enriched_route_handoff.get("source_ref")),
                "mission_id": text(enriched_route_handoff.get("mission_id")),
                "route_identity_key": text(enriched_route_handoff.get("route_identity_key")),
                "attempt_idempotency_key": text(
                    enriched_route_handoff.get("attempt_idempotency_key")
                ),
                "request_idempotency_key": text(
                    enriched_route_handoff.get("request_idempotency_key")
                ),
                "workspace_root": str(profile.workspace_root),
                "domain_workspace_root": str(profile.workspace_root),
                "repo_root": str(profile.workspace_root),
                "profile_ref": str(profile_ref),
            }
        )
    return task


def paper_mission_route_handoff_task(
    *,
    enriched_route_handoff: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any]:
    carrier = mapping(enriched_route_handoff.get("opl_stage_run_context"))
    command = mapping(enriched_route_handoff.get("ai_route_context"))
    action_type = text(command.get("command_kind")) or text(
        enriched_route_handoff.get("route_command_kind")
    )
    work_unit_id = text(carrier.get("work_unit_id")) or text(command.get("target"))
    work_unit_fingerprint = text(carrier.get("work_unit_fingerprint")) or text(
        mapping(carrier.get("aggregate_identity")).get("work_unit_fingerprint")
    )
    source_fingerprint = text(carrier.get("idempotency_key")) or _fingerprint(
        enriched_route_handoff
    )
    source_ref = text(enriched_route_handoff.get("source_ref"))
    source_refs = [
        {
            "role": "paper_mission_opl_route_handoff",
            "ref": source_ref,
            "exists": bool(source_ref),
        },
        {
            "role": "paper_mission_transaction",
            "ref": text(enriched_route_handoff.get("paper_mission_transaction_ref")),
            "exists": True,
        },
        {
            "role": "ai_route_context",
            "ref": text(enriched_route_handoff.get("ai_route_context_ref")),
            "exists": True,
        },
    ]
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind="domain_route/stage-outcome",
        study_id=study_id,
        reason="paper_mission_opl_route_handoff_pending",
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    payload = {
        "profile": str(profile_ref),
        "profile_ref": str(profile_ref),
        "workspace_root": str(profile.workspace_root),
        "domain_workspace_root": str(profile.workspace_root),
        "repo_root": str(profile.workspace_root),
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": source_fingerprint,
        "next_executable_owner": "one-person-lab",
        "authority_boundary": "mas_ai_route_context_only",
        "provider_attempt_pending": False,
        "provider_attempt_requires_opl_runtime_result": False,
        "opl_route_handoff": dict(enriched_route_handoff),
        "opl_route_handoff_record": dict(enriched_route_handoff),
        "ai_route_context": command,
        "ai_route_context": mapping(carrier.get("ai_route_context")) or carrier,
        "paper_mission_default_handoff_source": "opl_stage_run_context",
        "paper_mission_default_handoff_ref": source_ref,
    }
    next_action = paper_mission_next_action_envelope(
        stage_terminal_decision=mapping(enriched_route_handoff.get("stage_terminal_decision")),
        ai_route_context=command,
        opl_stage_run_context=carrier,
        opl_route_handoff=enriched_route_handoff,
    )
    if next_action:
        payload["next_action"] = next_action
    return {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/stage-outcome",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "domain_owner": "one-person-lab",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "priority": 80,
        "source": "mas-domain-handler-export",
        "requires_approval": False,
        "dedupe_key": (
            f"mas:{profile.name}:{study_id}:paper-mission-opl-route:"
            f"{source_fingerprint}"
        ),
        "source_fingerprint": source_fingerprint,
        "reason": "paper_mission_opl_route_handoff_pending",
        "payload": {key: value for key, value in payload.items() if value not in (None, "", [], {})},
        "source_refs": [ref for ref in source_refs if ref.get("ref") not in (None, "")],
        "dispatch_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "profile_name": profile.name,
        "provider_attempt_pending": False,
        "provider_attempt_requires_opl_runtime_result": False,
        "ai_route_context": mapping(carrier.get("ai_route_context")) or carrier,
        **({"next_action": next_action} if next_action else {}),
        "opl_route_handoff": dict(enriched_route_handoff),
        "opl_route_handoff_record": dict(enriched_route_handoff),
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
    }


def mark_non_default_paper_mission_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    marked: list[dict[str, Any]] = []
    for task in tasks:
        if (
            text(task.get("task_kind")) == DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND
            and task.get("default_paper_mission_entry") is True
        ):
            marked.append(task)
            continue
        marked.append(
            {
                **task,
                "default_paper_mission_entry": False,
                "paper_mission_default_role": "diagnostic_or_explicit_owner_handoff",
                "can_select_next_paper_stage": False,
                "can_authorize_provider_attempt": False,
                "counts_as_paper_progress": False,
            }
        )
    return marked


def _paper_mission_default_dispatch_run_id(study_id: str) -> str:
    return f"domain-handler-default-drive-{_slug(study_id)}"


def _enriched_paper_mission_route_handoff(
    *,
    route_handoff: Mapping[str, Any],
    workspace_root: Path,
    profile_ref: Path,
) -> dict[str, Any]:
    carrier = mapping(route_handoff.get("opl_stage_run_context"))
    return {
        **dict(route_handoff),
        "workspace_root": str(workspace_root),
        "domain_workspace_root": str(workspace_root),
        "repo_root": str(workspace_root),
        "profile_ref": str(profile_ref),
        "route_identity_key": text(carrier.get("route_identity_key")),
        "attempt_idempotency_key": text(carrier.get("attempt_idempotency_key")),
        "request_idempotency_key": text(carrier.get("request_idempotency_key")),
        "idempotency_key": text(carrier.get("idempotency_key")),
        "action_type": text(carrier.get("action_type")),
        "work_unit_id": text(carrier.get("work_unit_id")),
        "work_unit_fingerprint": text(carrier.get("work_unit_fingerprint")),
        "ai_route_context": mapping(carrier.get("ai_route_context")) or carrier,
    }


def _paper_mission_stage_packet_refs(readback: Mapping[str, Any]) -> list[str]:
    carrier = mapping(readback.get("opl_stage_run_context"))
    refs = [
        text(carrier.get("stage_run_ref")),
        text(readback.get("materialized_mission_ref")),
        text(readback.get("candidate_manifest_ref")),
    ]
    transaction = mapping(readback.get("paper_mission_transaction"))
    refs.extend(
        [
            text(transaction.get("stage_run_ref")),
            text(transaction.get("transaction_id")),
        ]
    )
    return [ref for ref in refs if ref]


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-") or "unknown"

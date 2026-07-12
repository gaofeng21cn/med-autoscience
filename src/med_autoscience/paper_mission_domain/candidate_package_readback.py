from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_output_roots import (
    PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH,
    _is_yang_ops_candidate_package_root,
)
from med_autoscience.paper_mission_domain.candidate_package_context import (
    foreground_owner_decision_summary,
    mission_executor_handoff,
)
from med_autoscience.paper_mission_domain.candidate_package_outputs import (
    write_materialized_candidate_package_outputs,
)
from med_autoscience.paper_mission_domain.command_metadata import (
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
    action_intent as _action_intent,
    mutation_policy as _mutation_policy,
)
from med_autoscience.paper_mission_domain.materialized_mission_readback import (
    build_materialized_mission_readback_if_available,
)
from med_autoscience.paper_mission_domain.transaction_readback import (
    FORBIDDEN_AUTHORITY_CLAIMS,
    _paper_mission_transaction_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.paper_mission import (
    paper_mission_candidate_artifact_delta,
    paper_mission_canary_candidate_manifest,
    paper_mission_owner_decision_packet,
)
from med_autoscience.paper_mission_candidate_materializer import (
    materialized_paper_facing_candidate_delta,
)
from med_autoscience.paper_mission_candidate_package import (
    paper_mission_owner_blocker_packet,
    paper_mission_owner_consumption_request,
)

CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_candidate_package",
)


def consume_candidate_missing_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    source: str,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_consume_candidate_missing_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": paper_mission_command,
        "action_intent": _action_intent(paper_mission_command),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "status": "candidate_package_missing",
        "required_next_command": (
            "paper-mission package-candidate --output-root "
            f"{Path(profile.workspace_root) / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / '<run_id>'}"
        ),
        "authority_consume_readback": {
            "surface_kind": "mas_paper_mission_candidate_consume_readback",
            "schema_version": 1,
            "status": "route_back",
            "selected_outcome": "route_back",
            "consume_result": {
                "status": "route_back",
                "outcome": "route_back",
                "authority_materialized": False,
            },
            "candidate_is_authority": False,
            "route_back": {
                "reason_code": "candidate_package_missing",
                "next_owner": "mission_executor",
                "resume_condition": (
                    "generate a submission_milestone_candidate package before "
                    "MAS authority consumption"
                ),
            },
            "write_plan": {
                "mode": "readback_only",
                "written_files": [],
            },
        },
        "mutation_policy": _mutation_policy(paper_mission_command=paper_mission_command),
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "dispatch_plan": {
            "default_action_intent": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": "candidate_package_missing_no_write",
            "old_owner_callable_dispatch_role": "diagnostic_or_migration_only",
        },
    }


def build_materialized_candidate_package_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    source: str,
    source_readback_override: Mapping[str, Any] | None = None,
    paper_facing_delta_ref: str | Path | None = None,
    inspect_readback_builder: Callable[..., dict[str, Any]] | None = None,
    opl_runtime_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if output_root is None:
        raise ValueError("--output-root is required for package-candidate")
    readback = _explicit_candidate_source_readback(source_readback_override)
    if readback is None:
        readback = build_materialized_mission_readback_if_available(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="package-candidate",
            dry_run=False,
            source=source,
            opl_runtime_payload=opl_runtime_payload,
        )
    if readback is None and inspect_readback_builder is not None:
        inspect_readback = inspect_readback_builder(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="inspect",
            dry_run=False,
            source=f"{source}:package-candidate-source-inspect",
            opl_runtime_payload=opl_runtime_payload,
        )
        readback = _explicit_candidate_source_readback(inspect_readback)
    if readback is None:
        raise ValueError(
            "package-candidate requires a materialized PaperMissionRun under "
            "ops/medautoscience/paper_mission_one_shot_migration"
        )
    mission = dict(readback["paper_mission_run"])
    candidate_manifest = (
        dict(readback["candidate_manifest"])
        if isinstance(readback.get("candidate_manifest"), Mapping)
        else paper_mission_canary_candidate_manifest(mission)
    )
    candidate_artifact_delta = paper_mission_candidate_artifact_delta(mission)
    owner_decision_packet = paper_mission_owner_decision_packet(mission)
    summary = foreground_owner_decision_summary(
        readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        candidate_package_forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    executor_handoff = mission_executor_handoff(
        readback=readback,
        foreground_owner_decision_summary=summary,
        candidate_package_forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    paper_facing_candidate_delta = materialized_paper_facing_candidate_delta(
        readback=readback,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        mission_executor_handoff=executor_handoff,
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    owner_blocker_packet = paper_mission_owner_blocker_packet(
        readback=readback,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=executor_handoff,
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    owner_consumption_request = paper_mission_owner_consumption_request(
        readback=readback,
        candidate_manifest=candidate_manifest,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=executor_handoff,
        paper_facing_candidate_delta=paper_facing_candidate_delta,
        owner_blocker_packet=owner_blocker_packet,
        candidate_refs={},
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    output_manifest = write_materialized_candidate_package_outputs(
        output_root=Path(output_root),
        study_id=str(readback["study_id"]),
        paper_mission_readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=executor_handoff,
        paper_facing_candidate_delta=paper_facing_candidate_delta,
        owner_consumption_request=owner_consumption_request,
        owner_blocker_packet=owner_blocker_packet,
        candidate_package_forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
        adopted_external_paper_delta_ref=(
            str(Path(paper_facing_delta_ref).expanduser().resolve())
            if paper_facing_delta_ref is not None
            else None
        ),
    )
    return {
        "surface_kind": "paper_mission_candidate_package_write_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "package-candidate",
        "action_intent": _action_intent("package-candidate"),
        "source": source,
        "dry_run": False,
        "profile": readback["profile"],
        "requested_study_id": readback["requested_study_id"],
        "study_id": readback["study_id"],
        "study_root": readback["study_root"],
        "study_root_exists": readback["study_root_exists"],
        "mission_id": readback["mission_id"],
        "objective": readback["objective"],
        "materialized_mission_ref": readback["materialized_mission_ref"],
        "stage_terminal_decision": readback["stage_terminal_decision"],
        "ai_route_context": readback["ai_route_context"],
        "opl_stage_attempt_readback_status": readback["opl_stage_attempt_readback_status"],
        "terminal_owner_gate": readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "next_owner_or_human_decision": readback["next_owner_or_human_decision"],
        "transaction_state": readback["transaction_state"],
        "consume_candidate_status": readback["consume_candidate_status"],
        "candidate_manifest": candidate_manifest,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "foreground_owner_decision_summary": summary,
        "mission_executor_handoff": executor_handoff,
        "paper_facing_candidate_delta": paper_facing_candidate_delta,
        "owner_consumption_request": owner_consumption_request,
        "owner_blocker_packet": owner_blocker_packet,
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": _is_yang_ops_candidate_package_root(
                output_root
            ),
            "writes_paper_body": False,
            "writes_candidate_workspace": True,
            "dry_run_only": False,
            "forbidden_authority_writes": list(
                CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "output_manifest": output_manifest,
    }


def _explicit_candidate_source_readback(
    readback: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    payload = dict(readback or {})
    if not isinstance(payload.get("paper_mission_run"), Mapping):
        return None
    if not isinstance(payload.get("paper_mission_transaction"), Mapping):
        return None
    return payload


__all__ = [
    "build_materialized_candidate_package_readback",
    "consume_candidate_missing_readback",
]

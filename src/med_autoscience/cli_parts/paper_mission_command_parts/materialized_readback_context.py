from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_progress_parts.current_executable_owner_action import (
    build_current_executable_owner_action,
    owner_action_next_step,
)


def materialized_mission_path_matches(
    path: Path,
    *,
    requested_study_id: str,
    load_json_object: Callable[[Path], dict[str, Any]],
) -> bool:
    if study_identity_matches(path.parent.name, requested_study_id):
        return True
    try:
        mission = load_json_object(path)
    except (OSError, ValueError):
        return False
    mission_study_id = mission.get("study_id")
    return isinstance(mission_study_id, str) and study_identity_matches(
        mission_study_id,
        requested_study_id,
    )


def normalize_materialized_mission_for_cli_readback(
    *,
    mission: Mapping[str, Any],
    study_id: str,
    paper_mission_command: str,
    paper_audit_pack_families: tuple[str, ...],
) -> dict[str, Any]:
    payload = dict(mission)
    resolved_study_id = _optional_text(payload.get("study_id")) or study_id
    source_refs = _mapping_list(payload.get("source_refs"))
    if "paper_audit_pack" not in payload:
        payload["paper_audit_pack"] = paper_audit_pack_for_cli_readback(
            study_id=resolved_study_id,
            paper_mission_command=paper_mission_command,
            source_refs=source_refs,
            paper_audit_pack_families=paper_audit_pack_families,
        )
    return payload


def materialized_study_id(
    *,
    mission: dict[str, Any],
    requested_study_id: str,
) -> str:
    mission_study_id = mission.get("study_id")
    return (
        mission_study_id
        if isinstance(mission_study_id, str) and mission_study_id.strip()
        else requested_study_id
    )


def materialized_study_root(
    *,
    profile: Any,
    requested_study_id: str,
    mission: dict[str, Any],
    mission_path: Path,
) -> Path:
    studies_root = Path(profile.studies_root)
    identities = [
        materialized_study_id(
            mission=mission,
            requested_study_id=requested_study_id,
        ),
        requested_study_id,
        mission_path.parent.name,
    ]
    for identity in identities:
        candidate = studies_root / identity
        if candidate.exists():
            return candidate
    try:
        study_dirs = sorted(path for path in studies_root.iterdir() if path.is_dir())
    except OSError:
        return studies_root / identities[0]
    for study_dir in study_dirs:
        if any(study_identity_matches(study_dir.name, identity) for identity in identities):
            return study_dir
    return studies_root / identities[0]


def consume_candidate_status(
    mission: dict[str, Any],
    default_readback: dict[str, Any],
) -> str:
    status = default_readback.get("consume_candidate_status")
    if isinstance(status, str) and status:
        return status
    consume_result = mission.get("consume_result")
    if isinstance(consume_result, dict):
        result_status = consume_result.get("status")
        if isinstance(result_status, str) and result_status:
            return result_status
    return "not_consumed"


def materialized_stage_terminal_decision(
    mission: dict[str, Any],
) -> dict[str, Any] | None:
    transaction = mission.get("paper_mission_transaction")
    if isinstance(transaction, dict) and isinstance(
        transaction.get("stage_terminal_decision"),
        dict,
    ):
        return transaction["stage_terminal_decision"]
    readback = mission.get("one_shot_migration_readback")
    if isinstance(readback, dict) and isinstance(
        readback.get("stage_terminal_decision"),
        dict,
    ):
        return readback["stage_terminal_decision"]
    return None


def materialized_opl_route_command(mission: dict[str, Any]) -> dict[str, Any] | None:
    transaction = mission.get("paper_mission_transaction")
    if isinstance(transaction, dict) and isinstance(
        transaction.get("opl_route_command"),
        dict,
    ):
        return transaction["opl_route_command"]
    readback = mission.get("one_shot_migration_readback")
    if isinstance(readback, dict) and isinstance(readback.get("opl_route_command"), dict):
        return readback["opl_route_command"]
    return None


def dispatch_execution_policy(readback: dict[str, Any]) -> str:
    if readback.get("surface_kind") == "paper_mission_drive_readback":
        return "paper_mission_drive_non_authority_candidate_and_ledger"
    if readback.get("surface_kind") == "paper_mission_materialized_readback":
        return "paper_mission_materialized_readback_no_write"
    return "paper_mission_no_write_dry_run"


def recommended_domain_command(
    *,
    profile_ref: object,
    study_id: str,
    readback: dict[str, Any],
) -> str:
    inspect_command = (
        "uv run python -m med_autoscience.cli paper-mission inspect "
        f"--profile {profile_ref} --study-id {study_id} --format json"
    )
    if readback.get("surface_kind") == "paper_mission_drive_readback":
        output_root = _optional_text(readback.get("output_root"))
        output_root_arg = f" --output-root {output_root}" if output_root else ""
        return (
            "uv run python -m med_autoscience.cli paper-mission drive "
            f"--profile {profile_ref} --study-id {study_id}{output_root_arg} "
            "--format json # writes non-authority candidate package and "
            "consumption ledger only"
        )
    if readback.get("surface_kind") == "paper_mission_materialized_readback":
        return f"{inspect_command} # reads materialized PaperMissionRun"
    return inspect_command


def paper_audit_pack_for_cli_readback(
    *,
    study_id: str,
    paper_mission_command: str,
    source_refs: list[dict[str, str]],
    paper_audit_pack_families: tuple[str, ...],
) -> dict[str, Any]:
    refs = list(source_refs) or [
        {
            "ref_id": "paper_mission_cli_readback",
            "ref_kind": "paper_mission_cli_readback",
            "uri": f"paper-mission-cli://{study_id}/{paper_mission_command}",
        }
    ]
    return {
        family: {
            "status": "refs_only_no_write_readback",
            "refs": refs,
        }
        for family in paper_audit_pack_families
    }


def paper_facing_action_fields(*, readback: Mapping[str, Any]) -> dict[str, Any]:
    submission_gate = _mapping(readback.get("submission_authority_owner_gate_readback"))
    if submission_gate:
        return {
            "paper_facing_action": _submission_gate_paper_facing_action(submission_gate)
        }
    current_action = build_current_executable_owner_action(readback)
    if current_action is None:
        return {}
    return {
        "current_executable_owner_action": current_action,
        "paper_facing_action": _owner_action_paper_facing_action(current_action),
    }


def _submission_gate_paper_facing_action(
    submission_gate: Mapping[str, Any],
) -> dict[str, Any]:
    status = _optional_text(submission_gate.get("status"))
    closed = status in {
        "submission_ready_authority_closeout_recorded",
        "submission_blocker_human_gate_recorded",
    }
    return _compact_mapping(
        {
            "surface_kind": "paper_mission_paper_facing_action",
            "schema_version": 1,
            "status": (
                "submission_authority_or_human_gate_closed"
                if closed
                else "awaiting_submission_authority_closeout"
            ),
            "source_surface": "submission_authority_owner_gate_readback",
            "study_id": submission_gate.get("study_id"),
            "decision": submission_gate.get("decision"),
            "current_required_action": submission_gate.get("current_required_action"),
            "next_legal_action": submission_gate.get("next_legal_action"),
            "owner_gate_decision_ref": submission_gate.get("owner_gate_decision_ref"),
            "human_gate_ref": submission_gate.get("human_gate_ref"),
            "event_id": submission_gate.get("event_id"),
            "next_step": (
                "Submission authority or human gate is closed; rerun "
                "paper-mission inspect or study progress to verify the terminal gate."
                if closed
                else "Await MAS submission authority or legal human-gate closeout; "
                "do not replay the retired owner action."
            ),
            "authority_boundary": _paper_facing_action_authority_boundary(
                submission_gate
            ),
        }
    )


def _owner_action_paper_facing_action(action: Mapping[str, Any]) -> dict[str, Any]:
    return _compact_mapping(
        {
            "surface_kind": "paper_mission_paper_facing_action",
            "schema_version": 1,
            "status": "owner_action_ready",
            "source_surface": "paper_mission.next_action",
            "study_id": action.get("study_id"),
            "next_owner": action.get("next_owner") or action.get("owner"),
            "action_type": action.get("action_type"),
            "allowed_actions": action.get("allowed_actions"),
            "work_unit_id": action.get("work_unit_id"),
            "work_unit_fingerprint": action.get("work_unit_fingerprint"),
            "required_delta_kind": action.get("required_delta_kind"),
            "target_surface": action.get("target_surface"),
            "target_surface_specificity": action.get("target_surface_specificity"),
            "paper_facing_delta": action.get("paper_facing_delta"),
            "accepted_answer_shape": action.get("accepted_answer_shape"),
            "route_back": action.get("route_back"),
            "verification": action.get("verification"),
            "next_step": owner_action_next_step(action),
            "authority_boundary": _paper_facing_action_authority_boundary(action),
        }
    )


def _paper_facing_action_authority_boundary(
    source: Mapping[str, Any],
) -> dict[str, Any]:
    boundary = _mapping(source.get("authority_boundary"))
    closeout = _mapping(source.get("submission_authority_closeout"))
    return {
        "projection_only": boundary.get("projection_only", True),
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_current_package": False,
        "can_start_provider_attempt": False,
        "can_claim_submission_ready": bool(
            source.get("submission_ready_claim_authorized") is True
            or closeout.get("submission_ready_claim_authorized") is True
        ),
        "can_claim_publication_ready": False,
        "can_claim_paper_progress": False,
    }


def study_identity_matches(candidate: str, requested: str) -> bool:
    candidate_text = candidate.strip()
    requested_text = requested.strip()
    if not candidate_text or not requested_text:
        return False
    if candidate_text == requested_text:
        return True
    if candidate_text.lower() == requested_text.lower():
        return True
    candidate_code = _study_numeric_code(candidate_text)
    requested_code = _study_numeric_code(requested_text)
    return bool(candidate_code and requested_code and candidate_code == requested_code)


def _study_numeric_code(value: str) -> str | None:
    match = re.match(r"^(?:dm)?0*(\d+)(?:$|[-_].*)", value.strip(), flags=re.IGNORECASE)
    if match is None:
        return None
    return f"{int(match.group(1)):03d}"


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _compact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, [], {})}

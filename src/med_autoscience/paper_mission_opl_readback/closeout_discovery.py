from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_opl_readback.primitives import (
    read_json_object,
    study_relative_ref,
    text_value,
    workspace_relative_ref,
    workspace_root_for_study_root,
)


def matching_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
    closeout_relative_roots: Sequence[Path],
    workspace_closeout_relative_roots: Sequence[Path],
    matches_carrier: Callable[..., bool],
    candidate_priority: Callable[..., Any] | None = None,
) -> tuple[dict[str, Any], str] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    matches: list[tuple[tuple[Any, ...], dict[str, Any], str]] = []
    for root_ref in closeout_relative_roots:
        closeout_root = resolved_study_root / root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in closeout_root.glob("*.json"):
            closeout = read_json_object(closeout_path)
            route_back = _closeout_route_back_sidecar(closeout_path)
            if closeout is None or not matches_carrier(
                closeout=closeout,
                carrier=carrier,
                route_back=route_back,
            ):
                continue
            matches.append(
                (
                    _candidate_priority_tuple(
                        closeout=closeout,
                        carrier=carrier,
                        closeout_path=closeout_path,
                        closeout_ref=study_relative_ref(
                            study_root=resolved_study_root,
                            path=closeout_path,
                        ),
                        route_back=route_back,
                        candidate_priority=candidate_priority,
                    ),
                    closeout,
                    study_relative_ref(
                        study_root=resolved_study_root,
                        path=closeout_path,
                    ),
                )
            )
    workspace_root = workspace_root_for_study_root(resolved_study_root)
    if workspace_root is not None:
        for root_ref in workspace_closeout_relative_roots:
            closeout_root = workspace_root / root_ref
            if not closeout_root.is_dir():
                continue
            study_id = text_value(carrier.get("study_id"))
            patterns = [
                f"**/{study_id}/stage_attempt_closeout_packet.json",
                "**/stage_attempt_closeout_packet.json",
            ]
            seen_paths: set[Path] = set()
            for pattern in patterns:
                for closeout_path in closeout_root.glob(pattern):
                    resolved_path = closeout_path.resolve()
                    if resolved_path in seen_paths:
                        continue
                    seen_paths.add(resolved_path)
                    closeout = read_json_object(closeout_path)
                    route_back = _closeout_route_back_sidecar(closeout_path)
                    if closeout is None or not matches_carrier(
                        closeout=closeout,
                        carrier=carrier,
                        route_back=route_back,
                    ):
                        continue
                    matches.append(
                        (
                            _candidate_priority_tuple(
                                closeout=closeout,
                                carrier=carrier,
                                closeout_path=closeout_path,
                                closeout_ref=workspace_relative_ref(
                                    workspace_root=workspace_root,
                                    path=closeout_path,
                                ),
                                route_back=route_back,
                                candidate_priority=candidate_priority,
                            ),
                            closeout,
                            workspace_relative_ref(
                                workspace_root=workspace_root,
                                path=closeout_path,
                            ),
                        )
                    )
            route_back_patterns = [
                f"**/{study_id}/route_back_evidence_packet.json",
                "**/route_back_evidence_packet.json",
            ]
            for pattern in route_back_patterns:
                for route_back_path in closeout_root.glob(pattern):
                    resolved_path = route_back_path.resolve()
                    if resolved_path in seen_paths:
                        continue
                    seen_paths.add(resolved_path)
                    if route_back_path.with_name(
                        "stage_attempt_closeout_packet.json"
                    ).exists():
                        continue
                    route_back = read_json_object(route_back_path)
                    if route_back is None:
                        continue
                    route_back_ref = workspace_relative_ref(
                        workspace_root=workspace_root,
                        path=route_back_path,
                    )
                    closeout = _closeout_from_route_back_evidence(
                        carrier=carrier,
                        route_back=route_back,
                        route_back_path=route_back_path,
                        route_back_ref=route_back_ref,
                        workspace_root=workspace_root,
                    )
                    if not matches_carrier(
                        closeout=closeout,
                        carrier=carrier,
                        route_back=route_back,
                    ):
                        continue
                    matches.append(
                        (
                            _candidate_priority_tuple(
                                closeout=closeout,
                                carrier=carrier,
                                closeout_path=route_back_path,
                                closeout_ref=route_back_ref,
                                route_back=route_back,
                                candidate_priority=candidate_priority,
                            ),
                            closeout,
                            route_back_ref,
                        )
                    )
    if not matches:
        return None
    _priority, closeout, closeout_ref = sorted(
        matches,
        key=lambda item: item[0],
        reverse=True,
    )[0]
    return closeout, closeout_ref


def _candidate_priority_tuple(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    closeout_path: Path,
    closeout_ref: str,
    route_back: Mapping[str, Any] | None,
    candidate_priority: Callable[..., Any] | None,
) -> tuple[Any, ...]:
    if candidate_priority is None:
        return (closeout_path.stat().st_mtime,)
    priority = candidate_priority(
        closeout=closeout,
        carrier=carrier,
        closeout_path=closeout_path,
        closeout_ref=closeout_ref,
        route_back=route_back,
    )
    return priority if isinstance(priority, tuple) else (priority,)


def _closeout_route_back_sidecar(closeout_path: Path) -> dict[str, Any] | None:
    if closeout_path.name != "stage_attempt_closeout_packet.json":
        return None
    route_back_path = closeout_path.with_name("route_back_evidence_packet.json")
    if not route_back_path.exists():
        return None
    return read_json_object(route_back_path)


def _closeout_from_route_back_evidence(
    *,
    carrier: Mapping[str, Any],
    route_back: Mapping[str, Any],
    route_back_path: Path,
    route_back_ref: str,
    workspace_root: Path,
) -> dict[str, Any]:
    candidate_ref = text_value(
        route_back.get("candidate_ref")
        or route_back.get("paper_facing_delta_ref")
        or route_back.get("write_repair_candidate_ref")
    )
    candidate_manifest_ref = text_value(route_back.get("candidate_manifest_ref"))
    progress_events_ref = _sibling_workspace_ref(
        workspace_root=workspace_root,
        route_back_path=route_back_path,
        file_name="progress_events.jsonl",
    )
    closeout_refs = [
        ref
        for ref in (
            route_back_ref,
            candidate_ref,
            candidate_manifest_ref,
            progress_events_ref,
        )
        if ref is not None
    ]
    return {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "owner_answer_candidate_materialized",
        "study_id": text_value(route_back.get("study_id"))
        or text_value(carrier.get("study_id")),
        "stage_id": text_value(route_back.get("stage_id"))
        or text_value(carrier.get("route_target")),
        "stage_attempt_id": text_value(route_back.get("stage_attempt_id")),
        "stage_packet_ref": text_value(route_back.get("stage_packet_ref")),
        "paper_mission_transaction_ref": text_value(
            route_back.get("paper_mission_transaction_ref")
        ),
        "opl_route_command_ref": text_value(route_back.get("opl_route_command_ref")),
        "work_unit_id": text_value(route_back.get("work_unit_id"))
        or text_value(carrier.get("work_unit_id")),
        "work_unit_fingerprint": text_value(route_back.get("work_unit_fingerprint")),
        "route_impact": {
            "owner_answer_kind": "route_back_evidence_ref",
            "owner_answer_ref": route_back_ref,
            "route_back_evidence_ref": route_back_ref,
            "paper_facing_delta_ref": candidate_ref,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
        },
        "closeout_refs": closeout_refs,
        "candidate_manifest_ref": candidate_manifest_ref,
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_current_package": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
    }


def _sibling_workspace_ref(
    *,
    workspace_root: Path,
    route_back_path: Path,
    file_name: str,
) -> str | None:
    sibling = route_back_path.with_name(file_name)
    if not sibling.exists():
        return None
    return workspace_relative_ref(workspace_root=workspace_root, path=sibling)

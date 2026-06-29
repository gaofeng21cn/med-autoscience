from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_output_roots import (
    _assert_safe_candidate_package_output_root,
    _is_yang_ops_candidate_package_root,
)
from med_autoscience.paper_mission_candidate_materializer import (
    CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
    adopted_external_paper_delta_authority_boundary,
    materialized_paper_facing_candidate_artifact_payload,
)
from med_autoscience.paper_mission_candidate_package import (
    AI_OWNER_DECISION_SIDECAR_REFS,
    SUBMISSION_MILESTONE_KIND,
    paper_mission_submission_milestone_checklist,
)


def write_materialized_candidate_package_outputs(
    *,
    output_root: Path,
    study_id: str,
    paper_mission_readback: dict[str, Any],
    candidate_manifest: dict[str, Any],
    candidate_artifact_delta: dict[str, Any],
    owner_decision_packet: dict[str, Any],
    foreground_owner_decision_summary: dict[str, Any],
    mission_executor_handoff: dict[str, Any],
    paper_facing_candidate_delta: dict[str, Any],
    owner_consumption_request: dict[str, Any],
    owner_blocker_packet: dict[str, Any],
    candidate_package_forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
    adopted_external_paper_delta_ref: str | None = None,
) -> dict[str, Any]:
    root = output_root.expanduser().resolve()
    _assert_safe_candidate_package_output_root(root)
    study_root = root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "package_manifest": study_root / "package_manifest.json",
        "paper_mission_readback": study_root / "paper_mission_readback.json",
        "candidate_manifest": study_root / "candidate_manifest.json",
        "mission_candidate_artifact_delta": study_root
        / "mission_candidate_artifact_delta.json",
        "owner_decision_packet": study_root / "owner_decision_packet.json",
        "foreground_owner_decision_summary": study_root
        / "foreground_owner_decision_summary.json",
        "mission_executor_handoff": study_root / "mission_executor_handoff.json",
        "paper_facing_candidate_delta": study_root
        / "paper_facing_candidate_delta.json",
        "owner_consumption_request": study_root / "owner_consumption_request.json",
        "owner_blocker_packet": study_root / "owner_blocker_packet.json",
        "submission_milestone_checklist": study_root
        / "submission_milestone_checklist.json",
    }
    paper_facing_artifact_outputs = {
        kind: study_root / "paper_facing_candidate_artifacts" / f"{kind}.json"
        for kind in _paper_facing_output_kinds(paper_facing_candidate_delta)
    }
    ai_owner_decision_sidecar_outputs = {
        kind: study_root / relpath
        for kind, relpath in AI_OWNER_DECISION_SIDECAR_REFS.items()
    }
    for path in paper_facing_artifact_outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    for path in ai_owner_decision_sidecar_outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_refs = {
        "paper_mission_readback": str(outputs["paper_mission_readback"]),
        "mission_candidate_artifact_delta": str(
            outputs["mission_candidate_artifact_delta"]
        ),
        "owner_decision_packet": str(outputs["owner_decision_packet"]),
        "foreground_owner_decision_summary": str(
            outputs["foreground_owner_decision_summary"]
        ),
        "mission_executor_handoff": str(outputs["mission_executor_handoff"]),
        "paper_facing_candidate_delta": str(outputs["paper_facing_candidate_delta"]),
        "owner_consumption_request": str(outputs["owner_consumption_request"]),
        "owner_blocker_packet": str(outputs["owner_blocker_packet"]),
        "submission_milestone_checklist": str(
            outputs["submission_milestone_checklist"]
        ),
    }
    paper_facing_artifact_refs = {
        kind: str(path) for kind, path in paper_facing_artifact_outputs.items()
    }
    ai_owner_decision_sidecar_refs = {
        kind: str(path) for kind, path in ai_owner_decision_sidecar_outputs.items()
    }
    paper_facing_candidate_delta_payload = {
        **paper_facing_candidate_delta,
        "paper_facing_artifact_refs": paper_facing_artifact_refs,
        "paper_facing_outputs": [
            {
                **_mapping(item),
                **(
                    {"artifact_ref": paper_facing_artifact_refs[_mapping(item)["kind"]]}
                    if _mapping(item).get("kind") in paper_facing_artifact_refs
                    else {}
                ),
            }
            for item in paper_facing_candidate_delta.get("paper_facing_outputs", [])
            if isinstance(item, Mapping)
        ],
    }
    if adopted_external_paper_delta_ref is not None:
        paper_facing_candidate_delta_payload.update(
            {
                "adopted_external_paper_delta_ref": adopted_external_paper_delta_ref,
                "source_paper_facing_delta_ref": adopted_external_paper_delta_ref,
                "adopted_external_paper_delta_authority_boundary": (
                    adopted_external_paper_delta_authority_boundary()
                ),
            }
        )
    paper_facing_candidate_delta.clear()
    paper_facing_candidate_delta.update(paper_facing_candidate_delta_payload)
    owner_consumption_candidate_refs = {
        **sidecar_refs,
        "candidate_manifest": str(outputs["candidate_manifest"]),
        "package_manifest": str(outputs["package_manifest"]),
    }
    if adopted_external_paper_delta_ref is not None:
        owner_consumption_candidate_refs["adopted_external_paper_delta"] = (
            adopted_external_paper_delta_ref
        )
    owner_blocker_packet_payload = {
        **owner_blocker_packet,
        "candidate_refs": owner_consumption_candidate_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
    }
    _attach_candidate_manifest_to_next_command(
        owner_blocker_packet_payload,
        candidate_manifest_ref=str(outputs["package_manifest"]),
    )
    owner_blocker_packet.clear()
    owner_blocker_packet.update(owner_blocker_packet_payload)
    owner_consumption_request_payload = {
        **owner_consumption_request,
        "candidate_refs": owner_consumption_candidate_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        "consume_path": {
            **_mapping(owner_consumption_request.get("consume_path")),
            "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        },
    }
    _attach_candidate_manifest_to_next_command(
        owner_consumption_request_payload,
        candidate_manifest_ref=str(outputs["package_manifest"]),
    )
    owner_consumption_request.clear()
    owner_consumption_request.update(owner_consumption_request_payload)
    candidate_manifest_payload = {
        **candidate_manifest,
        "candidate_artifact_refs": _candidate_artifact_refs_with_paper_delta(
            candidate_manifest,
            paper_facing_candidate_delta_ref=str(
                outputs["paper_facing_candidate_delta"]
            ),
        ),
        "mission_candidate_sidecar_refs": sidecar_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
    }
    ai_owner_decision_sidecars = _mapping(
        owner_consumption_request_payload.get("ai_owner_decision_sidecars")
    ) or _mapping(owner_blocker_packet_payload.get("ai_owner_decision_sidecars"))
    payloads = {
        "paper_mission_readback": paper_mission_readback,
        "candidate_manifest": candidate_manifest_payload,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "foreground_owner_decision_summary": foreground_owner_decision_summary,
        "mission_executor_handoff": mission_executor_handoff,
        "paper_facing_candidate_delta": paper_facing_candidate_delta_payload,
        "owner_consumption_request": owner_consumption_request_payload,
        "owner_blocker_packet": owner_blocker_packet_payload,
        "submission_milestone_checklist": paper_mission_submission_milestone_checklist(
            output_kinds=list(paper_facing_artifact_outputs),
            owner_blocker_context=_optional_text(
                owner_blocker_packet_payload.get("status")
            )
            == "owner_blocker_candidate_ready",
        ),
    }
    if adopted_external_paper_delta_ref is not None:
        payloads["submission_milestone_checklist"][
            "adopted_external_paper_delta_ref"
        ] = adopted_external_paper_delta_ref
        payloads["submission_milestone_checklist"][
            "adopted_external_paper_delta_authority_boundary"
        ] = adopted_external_paper_delta_authority_boundary()
    payloads.update(
        {
            f"ai_owner_decision_sidecar::{kind}": {
                **_mapping(ai_owner_decision_sidecars.get(kind)),
                "sidecar_ref": ai_owner_decision_sidecar_refs[kind],
            }
            for kind in ai_owner_decision_sidecar_outputs
        }
    )
    payloads.update(
        {
            f"paper_facing_artifact::{kind}": materialized_paper_facing_candidate_artifact_payload(
                kind=kind,
                path=path,
                paper_facing_candidate_delta=paper_facing_candidate_delta_payload,
                mission_executor_handoff=mission_executor_handoff,
                forbidden_authority_writes=candidate_package_forbidden_authority_writes,
                forbidden_authority_claims=forbidden_authority_claims,
            )
            for kind, path in paper_facing_artifact_outputs.items()
        }
    )
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "milestone_kind": SUBMISSION_MILESTONE_KIND,
        "study_id": study_id,
        "mission_id": paper_mission_readback.get("mission_id"),
        "counts_as_paper_progress": True,
        "mission_executor_materialized": True,
        "candidate_content_kind": CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "authority_materialized_by_this_package": False,
        "source_refs": foreground_owner_decision_summary["input_refs"],
        "source_document_refs": paper_facing_candidate_delta_payload.get(
            "source_document_refs", []
        ),
        "current_terminal_decision": foreground_owner_decision_summary[
            "current_terminal_decision"
        ],
        "next_owner": foreground_owner_decision_summary["next_owner"],
        "blocked_reason": foreground_owner_decision_summary["blocked_reason"],
        "required_owner_action": foreground_owner_decision_summary[
            "required_owner_action"
        ],
        "artifact_refs": sidecar_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        **(
            {"adopted_external_paper_delta_ref": adopted_external_paper_delta_ref}
            if adopted_external_paper_delta_ref is not None
            else {}
        ),
        "mission_executor_handoff_ref": str(outputs["mission_executor_handoff"]),
        "paper_facing_candidate_delta_ref": str(
            outputs["paper_facing_candidate_delta"]
        ),
        "owner_consumption_request_ref": str(outputs["owner_consumption_request"]),
        "owner_blocker_packet_ref": str(outputs["owner_blocker_packet"]),
        "submission_milestone_checklist_ref": str(
            outputs["submission_milestone_checklist"]
        ),
        "paper_facing_artifact_refs": paper_facing_artifact_refs,
        "forbidden_authority_writes": list(candidate_package_forbidden_authority_writes),
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }
    payloads["package_manifest"] = package_manifest
    written_files: list[str] = []
    file_sha256: dict[str, str] = {}
    all_outputs = {
        **outputs,
        **{
            f"paper_facing_artifact::{kind}": path
            for kind, path in paper_facing_artifact_outputs.items()
        },
        **{
            f"ai_owner_decision_sidecar::{kind}": path
            for kind, path in ai_owner_decision_sidecar_outputs.items()
        },
    }
    for key, path in all_outputs.items():
        text = json.dumps(payloads[key], ensure_ascii=False, indent=2) + "\n"
        path.write_text(text, encoding="utf-8")
        written_files.append(str(path))
        file_sha256[str(path)] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "mode": "non_authority_candidate_package",
        "output_root": str(study_root),
        "written_files": written_files,
        "file_sha256": file_sha256,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "writes_yang_ops_candidate_package": _is_yang_ops_candidate_package_root(root),
        "package_manifest_ref": str(outputs["package_manifest"]),
        "paper_mission_readback_ref": str(outputs["paper_mission_readback"]),
        "candidate_manifest_ref": str(outputs["candidate_manifest"]),
        "mission_candidate_artifact_delta_ref": str(
            outputs["mission_candidate_artifact_delta"]
        ),
        "owner_decision_packet_ref": str(outputs["owner_decision_packet"]),
        "foreground_owner_decision_summary_ref": str(
            outputs["foreground_owner_decision_summary"]
        ),
        "mission_executor_handoff_ref": str(outputs["mission_executor_handoff"]),
        "paper_facing_candidate_delta_ref": str(
            outputs["paper_facing_candidate_delta"]
        ),
        "owner_consumption_request_ref": str(outputs["owner_consumption_request"]),
        "owner_blocker_packet_ref": str(outputs["owner_blocker_packet"]),
        "submission_milestone_checklist_ref": str(
            outputs["submission_milestone_checklist"]
        ),
        "paper_facing_artifact_refs": paper_facing_artifact_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        **(
            {"adopted_external_paper_delta_ref": adopted_external_paper_delta_ref}
            if adopted_external_paper_delta_ref is not None
            else {}
        ),
    }


def _attach_candidate_manifest_to_next_command(
    payload: dict[str, Any],
    *,
    candidate_manifest_ref: str,
) -> None:
    command = payload.get("next_legal_command")
    if not isinstance(command, dict):
        return
    argv = command.get("argv_template")
    if not isinstance(argv, list):
        return
    command["argv_template"] = [
        candidate_manifest_ref if item == "<package_manifest_ref>" else item
        for item in argv
    ]


def _paper_facing_output_kinds(
    paper_facing_candidate_delta: Mapping[str, Any],
) -> list[str]:
    kinds: list[str] = []
    for item in paper_facing_candidate_delta.get("paper_facing_outputs", []):
        if not isinstance(item, Mapping):
            continue
        kind = _optional_text(item.get("kind"))
        if kind is not None and kind not in kinds:
            kinds.append(kind)
    return kinds


def _candidate_artifact_refs_with_paper_delta(
    candidate_manifest: Mapping[str, Any],
    *,
    paper_facing_candidate_delta_ref: str,
) -> list[str]:
    refs = [
        ref
        for ref in _text_list(candidate_manifest.get("candidate_artifact_refs"))
        if ref != paper_facing_candidate_delta_ref
    ]
    refs.append(paper_facing_candidate_delta_ref)
    return refs


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]

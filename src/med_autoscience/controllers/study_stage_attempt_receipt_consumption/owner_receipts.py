from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers.body_free_evidence_packets import build_body_free_evidence_packet


_ROUTE_DECISION_OWNER_RECEIPT_VALUES = frozenset(
    {
        "proceed_to_baseline",
        "return_to_scout",
        "switch_line",
        "bounded_repair",
    }
)
_HUMAN_GATE_RESUME_ACTIONS = frozenset(
    {
        "request_opl_stage_attempt",
        "request_opl_stage_attempt_relaunch",
        "resume_runtime",
    }
)
_PUBLICATION_ROUTE_MEMORY_FAMILY = "publication_route_memory"
_MEMORY_WRITEBACK_CONSUMABLE_STATUSES = frozenset({"applied", "blocked"})
_PAPER_REPAIR_OWNER_RECEIPT_SURFACES = frozenset(
    {
        "paper_repair_owner_receipt",
        "paper_story_repair_owner_receipt",
    }
)
_PAPER_REPAIR_OWNER_RECEIPT_EXECUTION_STATUSES = {
    "paper_repair_owner_receipt": frozenset({"executed"}),
    "paper_story_repair_owner_receipt": frozenset({"executed", "progress_delta_candidate"}),
}


def mas_owner_apply_receipt_consumption(*, study_root: Path) -> dict[str, Any]:
    receipt_ref = Path("artifacts/controller/repair_execution_receipts/latest.json")
    evidence_ref = Path("artifacts/controller/repair_execution_evidence/latest.json")
    controller_decision_ref = Path("artifacts/controller_decisions/latest.json")
    receipt = _read_json_object(study_root / receipt_ref)
    evidence = _read_json_object(study_root / evidence_ref)
    if receipt is not None and evidence is not None:
        artifact_delta = _artifact_delta_owner_receipt_consumption(
            receipt=receipt,
            evidence=evidence,
            receipt_ref=receipt_ref,
            evidence_ref=evidence_ref,
        )
        if artifact_delta:
            return artifact_delta
    controller_decision = _read_json_object(study_root / controller_decision_ref)
    if controller_decision is not None:
        return _controller_decision_owner_receipt_consumption(
            controller_decision=controller_decision,
            controller_decision_ref=controller_decision_ref,
        )
    return {}


def publication_route_memory_writeback_receipt_consumption(
    *,
    state_index_refs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    refs = [
        {
            "source_ref": _text(ref.get("source_ref")),
            "payload_sha256": _text(ref.get("payload_sha256")),
        }
        for ref in state_index_refs
        if _text(ref.get("source_ref")) and _text(ref.get("payload_sha256"))
    ]
    if not refs:
        return {}
    return {
        "status": "consumed",
        "receipt_kind": "opl_state_index_publication_memory_refs",
        "state_index_refs": refs,
        "router_receipt_refs": [ref["source_ref"] for ref in refs],
        "writeback_receipt_refs": [ref["source_ref"] for ref in refs],
        "body_included": False,
        "local_persistence": "absent",
        "replacement_owner_surface": "one-person-lab StateIndexKernel",
        "quality_authorized": False,
        "submission_authorized": False,
        "can_accept_or_reject_writeback": False,
        "next_action": "inspect_domain_owned_publication_memory_receipt_ref",
    }


def human_gate_resume_receipt_consumption(
    *,
    study_root: Path,
    controller_decision: Mapping[str, Any],
    controller_decision_ref: Path,
) -> dict[str, Any]:
    if controller_decision.get("requires_human_confirmation") is not True and not controller_decision.get(
        "family_human_gates"
    ):
        return {}
    summary_ref = Path("artifacts/controller/controller_confirmation_summary.json")
    summary = _read_json_object(study_root / summary_ref)
    if summary is None:
        return {}
    decision_status = _text(summary.get("status"))
    if decision_status not in {"approved", "consumed"}:
        return {}
    controller_action_types = [
        action
        for action in (_text(item) for item in (summary.get("controller_action_types") or []))
        if action
    ]
    if not controller_action_types or not any(action in _HUMAN_GATE_RESUME_ACTIONS for action in controller_action_types):
        return {}
    decision_ref_payload = _mapping(summary.get("decision_ref"))
    summary_decision_id = _text(decision_ref_payload.get("decision_id"))
    controller_decision_id = _text(controller_decision.get("decision_id"))
    if controller_decision_id and summary_decision_id and summary_decision_id != controller_decision_id:
        return {}
    receipt_ref = str(summary_ref)
    decision_ref = str(controller_decision_ref)
    return {
        "status": "consumed",
        "receipt_kind": "human_gate_resume_receipt",
        "gate_id": _text(summary.get("gate_id")),
        "decision_id": summary_decision_id or controller_decision_id,
        "decision_status": decision_status,
        "receipt_ref": receipt_ref,
        "decision_ref": decision_ref,
        "controller_action_types": controller_action_types,
        "body_free_evidence_packet": build_body_free_evidence_packet(
            ref=f"{receipt_ref}#{summary_decision_id or controller_decision_id}",
            role="human_gate_or_resume_ref",
            owner="MedAutoScience",
            receipt_id=f"human-gate-resume:{summary_decision_id or controller_decision_id}",
        ),
        "next_action": "honor_human_gate_resume_receipt",
    }


def _artifact_delta_owner_receipt_consumption(
    *,
    receipt: Mapping[str, Any],
    evidence: Mapping[str, Any],
    receipt_ref: Path,
    evidence_ref: Path,
) -> dict[str, Any]:
    surface = _text(receipt.get("surface"))
    if surface not in _PAPER_REPAIR_OWNER_RECEIPT_SURFACES:
        return {}
    execution_status = _text(receipt.get("execution_status"))
    if receipt.get("accepted") is not True:
        return {}
    if execution_status not in _PAPER_REPAIR_OWNER_RECEIPT_EXECUTION_STATUSES[surface]:
        return {}
    if receipt.get("direct_current_package_write") is not False:
        return {}
    if receipt.get("quality_authorized") is not False:
        return {}
    if receipt.get("submission_authorized") is not False:
        return {}
    story_surface_refs = _story_surface_refs(
        [
            *_mapping_list(receipt.get("canonical_artifact_delta_refs")),
            *_mapping_list(_mapping(evidence.get("canonical_artifact_delta")).get("artifact_refs")),
            *_mapping_list(evidence.get("changed_artifact_refs")),
        ]
    )
    if surface == "paper_story_repair_owner_receipt" and not story_surface_refs:
        return {}
    progress_observed = (
        _mapping(evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is True
        or evidence.get("progress_delta_candidate") is True
        or bool(receipt.get("canonical_artifact_delta_refs"))
        or bool(story_surface_refs)
    )
    if not progress_observed:
        return {}
    next_action = (
        "honor_paper_story_repair_owner_receipt"
        if surface == "paper_story_repair_owner_receipt"
        else "allow_mas_owner_guarded_apply"
    )
    return {
        "status": "consumed",
        "receipt_kind": "mas_owner_apply_receipt",
        "apply_result": "artifact_delta",
        "receipt_surface": surface,
        "receipt_execution_status": execution_status,
        "receipt_ref": str(receipt_ref),
        "evidence_ref": str(evidence_ref),
        "story_surface_delta_ref_count": len(story_surface_refs),
        "story_surface_delta_refs": story_surface_refs,
        "quality_authorized": False,
        "submission_authorized": False,
        "current_package_write_authorized": False,
        "next_action": next_action,
    }


def _story_surface_refs(refs: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    story_refs: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for ref in refs:
        role = _text(ref.get("artifact_role"))
        path_text = _text(ref.get("path"))
        path = Path(path_text).expanduser()
        if role == "canonical_manuscript_story_surface" or path.parts[-2:] == ("paper", "draft.md") or path.parts[
            -3:
        ] == ("paper", "build", "review_manuscript.md"):
            dedupe_key = path_text or role
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            story_refs.append(ref)
    return story_refs


def _controller_decision_owner_receipt_consumption(
    *,
    controller_decision: Mapping[str, Any],
    controller_decision_ref: Path,
) -> dict[str, Any]:
    if controller_decision.get("requires_human_confirmation") is True:
        return {}
    decision_type = _text(controller_decision.get("decision_type"))
    route_decision = _text(controller_decision.get("route_decision"))
    route_target = _text(controller_decision.get("route_target"))
    runtime_decision = _text(controller_decision.get("runtime_decision"))
    if decision_type == "stop_loss" or route_decision in {"stop_loss", "terminal_stop"} or route_target == "stop":
        return {
            "status": "consumed",
            "receipt_kind": "mas_owner_stop_loss_receipt",
            "apply_result": "terminal_stop",
            "receipt_ref": str(controller_decision_ref),
            "decision_id": _text(controller_decision.get("decision_id")),
            "next_action": "honor_mas_owner_terminal_stop",
        }
    if route_decision in {"stable_blocker", "blocked"} or runtime_decision == "blocked" or _text(
        controller_decision.get("blocked_reason")
    ):
        return {
            "status": "consumed",
            "receipt_kind": "mas_owner_apply_receipt",
            "apply_result": "stable_blocker",
            "receipt_ref": str(controller_decision_ref),
            "next_action": "record_mas_owner_stable_blocker",
        }
    if route_decision in _ROUTE_DECISION_OWNER_RECEIPT_VALUES:
        return {
            "status": "consumed",
            "receipt_kind": "mas_owner_apply_receipt",
            "apply_result": "route_decision",
            "receipt_ref": str(controller_decision_ref),
            "next_action": "record_mas_owner_route_decision",
        }
    return {}


def _read_json_object(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _unique_texts(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "human_gate_resume_receipt_consumption",
    "mas_owner_apply_receipt_consumption",
    "publication_route_memory_writeback_receipt_consumption",
]

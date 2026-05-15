from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


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
        "ensure_study_runtime",
        "ensure_study_runtime_relaunch_stopped",
        "resume_runtime",
    }
)
_PUBLICATION_ROUTE_MEMORY_FAMILY = "publication_route_memory"
_MEMORY_WRITEBACK_CONSUMABLE_STATUSES = frozenset({"applied", "blocked"})


def execution_receipt_consumption(status: Mapping[str, Any]) -> dict[str, Any]:
    supersession = _mapping(status.get("blocked_turn_closeout_supersession"))
    if not supersession:
        return {}
    source_ref = relative_study_artifact_ref(_text(supersession.get("source_path")))
    return {
        "status": "superseded_stale_closeout",
        "receipt_kind": "default_executor_execution",
        "superseded_run_id": _text(supersession.get("superseded_run_id")),
        "execution_id": _text(supersession.get("execution_id")),
        "action_type": _text(supersession.get("action_type")),
        "source_ref": source_ref or _text(supersession.get("source_surface")),
        "next_action": "honor_newer_owner_execution_receipt",
    }


def ai_reviewer_publication_eval_receipt_consumption(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_ref: Path,
) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return {}
    if _text(provenance.get("source_kind")) != "publication_eval_ai_reviewer":
        return {}
    if provenance.get("ai_reviewer_required") is not False:
        return {}
    if not _mapping(publication_eval.get("reviewer_operating_system")):
        return {}
    eval_id = _text(publication_eval.get("eval_id"))
    if not eval_id:
        return {}
    return {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": str(publication_eval_ref),
        "eval_id": eval_id,
        "reviewer_trace_ref": f"{publication_eval_ref}#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }


def bundle_stage_completion_receipt_consumption(
    *,
    study_root: Path,
    publication_eval: Mapping[str, Any],
    work_unit: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
) -> dict[str, Any]:
    work_unit_id = _text(work_unit.get("unit_id"))
    if not work_unit_id:
        return {}
    work_unit_fingerprint = _text(controller_decision.get("work_unit_fingerprint")) or _text(
        work_unit.get("fingerprint")
    )
    quest_root = _publication_eval_quest_root(publication_eval)
    if quest_root is None:
        return {}
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.exists():
        return {}
    for closeout_path in sorted(closeout_root.glob("*.json")):
        closeout = _read_json_object(closeout_path)
        if closeout is None or closeout.get("status") != "completed":
            continue
        if closeout.get("meaningful_artifact_delta") is not True:
            continue
        for artifact_ref in closeout.get("artifact_refs") or []:
            artifact_ref_text = _text(artifact_ref)
            artifact_path = _resolve_runtime_artifact_ref(quest_root, artifact_ref_text)
            package_closure = _read_json_object(artifact_path) if artifact_path is not None else None
            if not _package_closure_matches_work_unit(
                package_closure,
                study_root=study_root,
                work_unit_id=work_unit_id,
                work_unit_fingerprint=work_unit_fingerprint,
            ):
                continue
            return {
                "status": "consumed",
                "receipt_kind": "runtime_turn_closeout_package_closure",
                "consumed_work_unit_id": work_unit_id,
                "consumed_work_unit_fingerprint": work_unit_fingerprint,
                "completion_ref": _quest_relative_ref(quest_root=quest_root, path=closeout_path),
                "artifact_ref": artifact_ref_text,
                "next_action": "do_not_redrive_completed_work_unit",
            }
    return {}


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


def publication_route_memory_writeback_receipt_consumption(*, study_root: Path) -> dict[str, Any]:
    receipt_root = study_root / "artifacts" / "stage_knowledge" / "memory_write_router_receipts"
    if not receipt_root.exists():
        return {}
    receipt_payloads: list[dict[str, Any]] = []
    for receipt_path in sorted(receipt_root.glob("*.json")):
        receipt = _read_json_object(receipt_path)
        if receipt is None:
            continue
        if _text(receipt.get("surface")) != "memory_write_router_receipt":
            continue
        if _text(receipt.get("memory_family")) != _PUBLICATION_ROUTE_MEMORY_FAMILY:
            continue
        receipt_status = _text(receipt.get("status"))
        if receipt_status not in _MEMORY_WRITEBACK_CONSUMABLE_STATUSES:
            continue
        accepted = _mapping_list(receipt.get("accepted_writes"))
        rejected = _mapping_list(receipt.get("rejected_writes"))
        typed_blockers = _mapping_list(receipt.get("typed_blockers"))
        writeback_refs = _writeback_receipt_refs(study_root=study_root, receipt=receipt)
        if not writeback_refs:
            continue
        if not accepted and not rejected and not typed_blockers:
            continue
        receipt_payloads.append(
            {
                "receipt": receipt,
                "receipt_ref": _study_relative_ref(study_root=study_root, path=receipt_path),
                "writeback_refs": writeback_refs,
                "receipt_status": receipt_status,
                "accepted_count": len(accepted),
                "rejected_count": len(rejected),
                "typed_blocker_count": len(typed_blockers),
                "rejected_reasons": _unique_texts(_text(item.get("reason")) for item in rejected),
                "typed_blocker_ids": _unique_texts(_text(item.get("blocker_id")) for item in typed_blockers),
                "typed_blocker_reasons": _unique_texts(_text(item.get("reason")) for item in typed_blockers),
            }
        )
    if not receipt_payloads:
        return {}

    router_receipt_refs = [item["receipt_ref"] for item in receipt_payloads]
    writeback_receipt_refs = _unique_texts(ref for item in receipt_payloads for ref in item["writeback_refs"])
    accepted_count = sum(int(item["accepted_count"]) for item in receipt_payloads)
    rejected_count = sum(int(item["rejected_count"]) for item in receipt_payloads)
    typed_blocker_count = sum(int(item["typed_blocker_count"]) for item in receipt_payloads)
    if accepted_count > 0:
        next_action = "honor_mas_memory_owner_writeback_receipt"
    elif rejected_count > 0:
        next_action = "record_rejected_memory_writeback_receipt"
    else:
        next_action = "record_blocked_memory_writeback_receipt"
    return {
        "status": "consumed",
        "receipt_kind": "publication_route_memory_writeback_receipt",
        "router_receipt_refs": router_receipt_refs,
        "writeback_receipt_refs": writeback_receipt_refs,
        "receipt_statuses": _unique_texts(item["receipt_status"] for item in receipt_payloads),
        "accepted_writeback_ref_count": accepted_count,
        "rejected_writeback_ref_count": rejected_count,
        "typed_blocker_count": typed_blocker_count,
        "rejected_reasons": _unique_texts(reason for item in receipt_payloads for reason in item["rejected_reasons"]),
        "typed_blocker_ids": _unique_texts(reason for item in receipt_payloads for reason in item["typed_blocker_ids"]),
        "typed_blocker_reasons": _unique_texts(
            reason for item in receipt_payloads for reason in item["typed_blocker_reasons"]
        ),
        "body_included": False,
        "quality_authorized": False,
        "submission_authorized": False,
        "can_accept_or_reject_writeback": False,
        "next_action": next_action,
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
    return {
        "status": "consumed",
        "receipt_kind": "human_gate_resume_receipt",
        "gate_id": _text(summary.get("gate_id")),
        "decision_id": summary_decision_id or controller_decision_id,
        "decision_status": decision_status,
        "receipt_ref": str(summary_ref),
        "decision_ref": str(controller_decision_ref),
        "controller_action_types": controller_action_types,
        "next_action": "honor_human_gate_resume_receipt",
    }


def _artifact_delta_owner_receipt_consumption(
    *,
    receipt: Mapping[str, Any],
    evidence: Mapping[str, Any],
    receipt_ref: Path,
    evidence_ref: Path,
) -> dict[str, Any]:
    if receipt.get("surface") != "paper_repair_owner_receipt":
        return {}
    if receipt.get("accepted") is not True or receipt.get("execution_status") != "executed":
        return {}
    if receipt.get("direct_current_package_write") is not False:
        return {}
    if receipt.get("quality_authorized") is not False:
        return {}
    if receipt.get("submission_authorized") is not False:
        return {}
    progress_observed = (
        _mapping(evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is True
        or evidence.get("progress_delta_candidate") is True
        or bool(receipt.get("canonical_artifact_delta_refs"))
    )
    if not progress_observed:
        return {}
    return {
        "status": "consumed",
        "receipt_kind": "mas_owner_apply_receipt",
        "apply_result": "artifact_delta",
        "receipt_ref": str(receipt_ref),
        "evidence_ref": str(evidence_ref),
        "next_action": "allow_mas_owner_guarded_apply",
    }


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


def relative_study_artifact_ref(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text).expanduser()
    parts = path.parts
    if "artifacts" not in parts:
        return path.name
    return str(Path(*parts[parts.index("artifacts") :]))


def _publication_eval_quest_root(publication_eval: Mapping[str, Any]) -> Path | None:
    runtime_context_refs = _mapping(publication_eval.get("runtime_context_refs"))
    runtime_escalation_ref = _text(runtime_context_refs.get("runtime_escalation_ref"))
    if not runtime_escalation_ref:
        return None
    path = Path(runtime_escalation_ref).expanduser()
    parts = path.parts
    if "artifacts" not in parts:
        return None
    artifacts_index = parts.index("artifacts")
    if artifacts_index <= 0:
        return None
    return Path(*parts[:artifacts_index]).resolve()


def _resolve_runtime_artifact_ref(quest_root: Path, artifact_ref: str) -> Path | None:
    if not artifact_ref:
        return None
    path = Path(artifact_ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (quest_root / path).resolve()


def _package_closure_matches_work_unit(
    payload: Mapping[str, Any] | None,
    *,
    study_root: Path,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> bool:
    if payload is None:
        return False
    if _text(payload.get("artifact_kind")) != work_unit_id:
        return False
    work_unit = _mapping(payload.get("work_unit"))
    if _text(work_unit.get("unit_id")) != work_unit_id:
        return False
    if work_unit_fingerprint and _text(work_unit.get("fingerprint")) != work_unit_fingerprint:
        return False
    authority_closure = _mapping(payload.get("authority_closure"))
    if _text(authority_closure.get("status")) != "closed_for_bundle_stage":
        return False
    if _text(authority_closure.get("publication_gate_status")) != "clear":
        return False
    if authority_closure.get("publication_gate_allow_write") is not True:
        return False
    if list(authority_closure.get("publication_gate_blockers") or []):
        return False
    submission_authority = _mapping(payload.get("submission_minimal_authority"))
    if _text(submission_authority.get("status")) != "current":
        return False
    human_facing_delivery = _mapping(payload.get("human_facing_delivery"))
    current_package_zip = _text(human_facing_delivery.get("current_package_zip"))
    if not current_package_zip:
        return False
    package_path = Path(current_package_zip).expanduser()
    if not package_path.is_absolute():
        package_path = study_root / package_path
    try:
        package_path.resolve().relative_to(study_root.resolve())
    except ValueError:
        return False
    return _text(human_facing_delivery.get("status")) == "current"


def _quest_relative_ref(*, quest_root: Path, path: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return str(resolved_path.relative_to(quest_root.expanduser().resolve()))
    except ValueError:
        return str(resolved_path)


def _study_relative_ref(*, study_root: Path, path: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return str(resolved_path.relative_to(study_root.expanduser().resolve()))
    except ValueError:
        return str(resolved_path)


def _read_json_object(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def _writeback_receipt_refs(*, study_root: Path, receipt: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    receipt_refs = _text_list(receipt.get("receipt_refs"))
    if len(receipt_refs) >= 2:
        refs.append(receipt_refs[1])
    writeback_locator = _text(receipt.get("writeback_receipt_locator_ref"))
    idempotency_key = _text(receipt.get("idempotency_key"))
    workspace_root = _workspace_root_from_study_root(study_root)
    if workspace_root is not None and writeback_locator and idempotency_key:
        refs.append(str(workspace_root / writeback_locator / f"{idempotency_key}.json"))
    return _unique_texts(refs)


def _workspace_root_from_study_root(study_root: Path) -> Path | None:
    resolved = study_root.expanduser().resolve()
    if resolved.parent.name == "studies":
        return resolved.parent.parent
    return None


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
    "ai_reviewer_publication_eval_receipt_consumption",
    "bundle_stage_completion_receipt_consumption",
    "execution_receipt_consumption",
    "mas_owner_apply_receipt_consumption",
    "publication_route_memory_writeback_receipt_consumption",
    "relative_study_artifact_ref",
]

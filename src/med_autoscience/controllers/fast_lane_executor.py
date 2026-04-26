from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from med_autoscience.controllers import gate_clearing_batch_scheduler


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _stable_idempotency_key(*, prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"{prefix}::sha256:{hashlib.sha256(encoded).hexdigest()}"


def _blocking_reasons(quality_ledger_enforcement: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if bool(quality_ledger_enforcement.get("gate_relaxation_allowed")):
        reasons.append("quality_gate_relaxation_requested")
    for item in _list(quality_ledger_enforcement.get("hard_blockers")):
        if (reason := _text(item)) is not None and reason not in reasons:
            reasons.append(reason)
    return reasons


def _manifest_state(quality_ledger_enforcement: Mapping[str, Any]) -> str:
    reasons = _blocking_reasons(quality_ledger_enforcement)
    if reasons or quality_ledger_enforcement.get("fast_lane_execution_allowed") is False:
        return "blocked_by_quality_ledger"
    return "ready"


def _checkpoint_requirements() -> dict[str, bool]:
    return {
        "write_gate_clearing_batch_record": True,
        "replay_publication_gate": True,
        "refresh_authority_surfaces": True,
        "record_controller_decision": True,
    }


def build_fast_lane_execution_manifest(
    *,
    study_id: str,
    quest_id: str | None,
    repair_units: list[Any],
    quality_ledger_enforcement: Mapping[str, Any],
    replay_case: Mapping[str, Any],
) -> dict[str, Any]:
    execution_plan = gate_clearing_batch_scheduler.build_repair_unit_execution_plan(repair_units)
    plan_manifest = _mapping(execution_plan.get("fast_lane_execution_manifest"))
    manifest_state = _manifest_state(quality_ledger_enforcement)
    blocking_reasons = _blocking_reasons(quality_ledger_enforcement)
    auto_dispatch_allowed = manifest_state == "ready" and execution_plan.get("status") == "planned"
    replay_required = bool(replay_case) or bool(
        _mapping(execution_plan.get("execution_policy")).get("requires_publication_gate_replay")
    )
    study_id_text = str(study_id or "").strip() or None
    quest_id_text = str(quest_id or "").strip() or None
    dependency_dag = _mapping(plan_manifest.get("dependency_dag"))
    action_batches = list(_list(plan_manifest.get("action_batches")))
    return {
        "surface": "fast_lane_execution_manifest",
        "manifest_type": "gate_clearing_fast_lane_execution",
        "schema_version": 1,
        "study_id": study_id_text,
        "quest_id": quest_id_text,
        "manifest_state": manifest_state,
        "blocking_reasons": blocking_reasons,
        "idempotency_key": _stable_idempotency_key(
            prefix="fast-lane",
            payload={
                "study_id": study_id_text,
                "quest_id": quest_id_text,
                "dependency_dag": dependency_dag,
                "action_batches": action_batches,
            },
        ),
        "idempotency_scope": "study_quest_work_unit_dag",
        "gate_relaxation_allowed": False,
        "paper_body_edit_allowed": False,
        "execution_permission": {
            "auto_dispatch_allowed": auto_dispatch_allowed,
            "controller_only": True,
            "gate_relaxation_allowed": False,
        },
        "execution_plan": execution_plan,
        "quality_gate_policy": dict(_mapping(plan_manifest.get("quality_gate_policy"))),
        "quality_enforcement": dict(quality_ledger_enforcement),
        "checkpoint_requirements": _checkpoint_requirements(),
        "durable_checkpoint_requirements": dict(_mapping(plan_manifest.get("checkpoint_requirements"))),
        "replay_requirements": dict(_mapping(plan_manifest.get("replay_requirements"))),
        "replay_required": replay_required,
        "replay_contract": {
            "case_id": _text(replay_case.get("case_id")),
            "case_family": _text(replay_case.get("case_family")),
            "required_truth_surfaces": [
                surface
                for item in _list(replay_case.get("required_truth_surfaces"))
                if (surface := _text(item)) is not None
            ],
            "gate_relaxation_allowed": False,
            "edits_paper_body": False,
        },
        "dependency_dag": dict(dependency_dag),
        "action_batches": action_batches,
    }

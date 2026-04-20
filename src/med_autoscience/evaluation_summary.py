from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.publication_eval_latest import read_publication_eval_latest, stable_publication_eval_latest_path
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref

__all__ = [
    "STABLE_EVALUATION_SUMMARY_RELATIVE_PATH",
    "STABLE_PROMOTION_GATE_RELATIVE_PATH",
    "materialize_evaluation_summary_artifacts",
    "read_evaluation_summary",
    "read_promotion_gate",
    "resolve_evaluation_summary_ref",
    "resolve_promotion_gate_ref",
    "stable_evaluation_summary_path",
    "stable_promotion_gate_path",
]


STABLE_EVALUATION_SUMMARY_RELATIVE_PATH = Path("artifacts/eval_hygiene/evaluation_summary/latest.json")
STABLE_PROMOTION_GATE_RELATIVE_PATH = Path("artifacts/eval_hygiene/promotion_gate/latest.json")
_GAP_SEVERITIES = ("must_fix", "important", "optional")
_ROUTE_REPAIR_ACTION_TYPES = {"continue_same_line", "route_back_same_line", "bounded_analysis"}


def stable_evaluation_summary_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_EVALUATION_SUMMARY_RELATIVE_PATH).resolve()


def stable_promotion_gate_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_PROMOTION_GATE_RELATIVE_PATH).resolve()


def _resolve_stable_ref(*, study_root: Path, stable_path: Path, ref: str | Path | None, label: str) -> Path:
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError(f"{label} only accepts the eval hygiene-owned promotion gate artifact" if "promotion gate" in label else f"{label} only accepts the eval hygiene-owned latest artifact")
    return stable_path


def resolve_evaluation_summary_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    return _resolve_stable_ref(
        study_root=study_root,
        stable_path=stable_evaluation_summary_path(study_root=study_root),
        ref=ref,
        label="evaluation summary reader",
    )


def resolve_promotion_gate_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    return _resolve_stable_ref(
        study_root=study_root,
        stable_path=stable_promotion_gate_path(study_root=study_root),
        ref=ref,
        label="promotion gate reader",
    )


def _required_text(label: str, field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _required_bool(label: str, field_name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} {field_name} must be bool")
    return value


def _required_mapping(label: str, field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    return dict(value)


def _required_string_list(label: str, field_name: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} {field_name} must be a list")
    normalized: list[str] = []
    for item in value:
        normalized.append(_required_text(label, field_name, item))
    return normalized


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{label} payload must be a JSON object: {path}")
    return payload


def _normalize_runtime_escalation_ref(
    *,
    study_root: Path,
    runtime_escalation_ref: str | Path | dict[str, Any],
) -> dict[str, str]:
    if isinstance(runtime_escalation_ref, dict):
        raw_ref = dict(runtime_escalation_ref)
        artifact_path = Path(_required_text("runtime escalation ref", "artifact_path", raw_ref.get("artifact_path"))).expanduser()
    else:
        raw_ref = {}
        artifact_path = Path(runtime_escalation_ref).expanduser()
    if not artifact_path.is_absolute():
        artifact_path = (Path(study_root).expanduser().resolve() / artifact_path).resolve()
    else:
        artifact_path = artifact_path.resolve()
    payload = _read_json_object(artifact_path, label="runtime escalation")
    record_id = _required_text("runtime escalation", "record_id", payload.get("record_id"))
    payload_artifact_path = Path(
        _required_text("runtime escalation", "artifact_path", payload.get("artifact_path"))
    ).expanduser().resolve()
    summary_ref = Path(_required_text("runtime escalation", "summary_ref", payload.get("summary_ref"))).expanduser().resolve()
    if payload_artifact_path != artifact_path:
        raise ValueError("runtime escalation artifact_path mismatch")
    if raw_ref:
        provided_record_id = _required_text("runtime escalation ref", "record_id", raw_ref.get("record_id"))
        provided_summary_ref = Path(
            _required_text("runtime escalation ref", "summary_ref", raw_ref.get("summary_ref"))
        ).expanduser().resolve()
        if provided_record_id != record_id or provided_summary_ref != summary_ref:
            raise ValueError("runtime escalation ref mismatch")
    return {
        "record_id": record_id,
        "artifact_path": str(payload_artifact_path),
        "summary_ref": str(summary_ref),
    }


def _normalize_gate_report(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path, label="promotion gate source report")
    blockers = _required_string_list("promotion gate source report", "blockers", payload.get("blockers"))
    return {
        "generated_at": _required_text("promotion gate source report", "generated_at", payload.get("generated_at")),
        "status": _required_text("promotion gate source report", "status", payload.get("status")),
        "allow_write": _required_bool("promotion gate source report", "allow_write", payload.get("allow_write")),
        "recommended_action": _required_text(
            "promotion gate source report",
            "recommended_action",
            payload.get("recommended_action"),
        ),
        "current_required_action": _required_text(
            "promotion gate source report",
            "current_required_action",
            payload.get("current_required_action"),
        ),
        "supervisor_phase": _required_text(
            "promotion gate source report",
            "supervisor_phase",
            payload.get("supervisor_phase"),
        ),
        "controller_stage_note": _required_text(
            "promotion gate source report",
            "controller_stage_note",
            payload.get("controller_stage_note"),
        ),
        "blockers": blockers,
        "source_gate_report_ref": str(path.resolve()),
    }


def _build_promotion_gate_payload(
    *,
    study_root: Path,
    publication_eval: dict[str, Any],
    runtime_escalation_ref: dict[str, str],
    gate_report: dict[str, Any],
) -> dict[str, Any]:
    quest_id = publication_eval.get("quest_id")
    quest_scope = _required_text("publication eval", "quest_id", quest_id)
    verdict = _required_mapping("publication eval", "verdict", publication_eval.get("verdict"))
    eval_id = _required_text("publication eval", "eval_id", publication_eval.get("eval_id"))
    return {
        "schema_version": 1,
        "gate_id": f"promotion-gate::{publication_eval['study_id']}::{quest_scope}::{gate_report['generated_at']}",
        "study_id": _required_text("publication eval", "study_id", publication_eval.get("study_id")),
        "quest_id": quest_scope,
        "emitted_at": gate_report["generated_at"],
        "source_gate_report_ref": gate_report["source_gate_report_ref"],
        "publication_eval_ref": {
            "eval_id": eval_id,
            "artifact_path": str(stable_publication_eval_latest_path(study_root=study_root)),
        },
        "runtime_escalation_ref": runtime_escalation_ref,
        "overall_verdict": _required_text("publication eval verdict", "overall_verdict", verdict.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "publication eval verdict",
            "primary_claim_status",
            verdict.get("primary_claim_status"),
        ),
        "stop_loss_pressure": _required_text(
            "publication eval verdict",
            "stop_loss_pressure",
            verdict.get("stop_loss_pressure"),
        ),
        "status": gate_report["status"],
        "allow_write": gate_report["allow_write"],
        "recommended_action": gate_report["recommended_action"],
        "current_required_action": gate_report["current_required_action"],
        "supervisor_phase": gate_report["supervisor_phase"],
        "controller_stage_note": gate_report["controller_stage_note"],
        "blockers": gate_report["blockers"],
    }


def _gap_counts(gaps: list[dict[str, Any]]) -> dict[str, int]:
    counts = {severity: 0 for severity in _GAP_SEVERITIES}
    for gap in gaps:
        severity = _required_text("publication eval gap", "severity", gap.get("severity"))
        if severity in counts:
            counts[severity] += 1
    counts["total"] = len(gaps)
    return counts


def _recommended_action_types(actions: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for action in actions:
        action_type = _required_text("publication eval recommended action", "action_type", action.get("action_type"))
        if action_type not in seen:
            ordered.append(action_type)
            seen.add(action_type)
    return ordered


def _route_repair_plan(actions: list[dict[str, Any]]) -> dict[str, str] | None:
    prioritized_actions = sorted(
        enumerate(actions),
        key=lambda item: (0 if item[1].get("priority") == "now" else 1, item[0]),
    )
    for _, action in prioritized_actions:
        action_type = _required_text("publication eval recommended action", "action_type", action.get("action_type"))
        if action_type not in _ROUTE_REPAIR_ACTION_TYPES:
            continue
        return {
            "action_id": _required_text("publication eval recommended action", "action_id", action.get("action_id")),
            "action_type": action_type,
            "priority": _required_text("publication eval recommended action", "priority", action.get("priority")),
            "route_target": _required_text(
                "publication eval recommended action",
                "route_target",
                action.get("route_target"),
            ),
            "route_key_question": _required_text(
                "publication eval recommended action",
                "route_key_question",
                action.get("route_key_question"),
            ),
            "route_rationale": _required_text(
                "publication eval recommended action",
                "route_rationale",
                action.get("route_rationale"),
            ),
        }
    return None


def _build_evaluation_summary_payload(
    *,
    study_root: Path,
    publication_eval: dict[str, Any],
    charter_payload: dict[str, Any],
    runtime_escalation_ref: dict[str, str],
    promotion_gate_ref: dict[str, str],
    promotion_gate_payload: dict[str, Any],
) -> dict[str, Any]:
    charter_context_ref = _required_mapping(
        "publication eval",
        "charter_context_ref",
        publication_eval.get("charter_context_ref"),
    )
    charter_id = _required_text("study charter", "charter_id", charter_payload.get("charter_id"))
    publication_objective = _required_text(
        "study charter",
        "publication_objective",
        charter_payload.get("publication_objective"),
    )
    if _required_text("publication eval charter context ref", "charter_id", charter_context_ref.get("charter_id")) != charter_id:
        raise ValueError("evaluation summary charter_id mismatch")
    if _required_text(
        "publication eval charter context ref",
        "publication_objective",
        charter_context_ref.get("publication_objective"),
    ) != publication_objective:
        raise ValueError("evaluation summary publication objective mismatch")
    verdict = _required_mapping("publication eval", "verdict", publication_eval.get("verdict"))
    gaps = list(publication_eval.get("gaps") or [])
    actions = list(publication_eval.get("recommended_actions") or [])
    quest_id = _required_text("publication eval", "quest_id", publication_eval.get("quest_id"))
    return {
        "schema_version": 1,
        "summary_id": f"evaluation-summary::{publication_eval['study_id']}::{quest_id}::{publication_eval['emitted_at']}",
        "study_id": _required_text("publication eval", "study_id", publication_eval.get("study_id")),
        "quest_id": quest_id,
        "emitted_at": _required_text("publication eval", "emitted_at", publication_eval.get("emitted_at")),
        "charter_ref": {
            "charter_id": charter_id,
            "artifact_path": str(resolve_study_charter_ref(study_root=study_root, ref=charter_context_ref.get("ref"))),
            "publication_objective": publication_objective,
        },
        "publication_eval_ref": {
            "eval_id": _required_text("publication eval", "eval_id", publication_eval.get("eval_id")),
            "artifact_path": str(stable_publication_eval_latest_path(study_root=study_root)),
        },
        "runtime_escalation_ref": runtime_escalation_ref,
        "promotion_gate_ref": dict(promotion_gate_ref),
        "evaluation_scope": _required_text(
            "publication eval",
            "evaluation_scope",
            publication_eval.get("evaluation_scope"),
        ),
        "overall_verdict": _required_text("publication eval verdict", "overall_verdict", verdict.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "publication eval verdict",
            "primary_claim_status",
            verdict.get("primary_claim_status"),
        ),
        "verdict_summary": _required_text("publication eval verdict", "summary", verdict.get("summary")),
        "stop_loss_pressure": _required_text(
            "publication eval verdict",
            "stop_loss_pressure",
            verdict.get("stop_loss_pressure"),
        ),
        "publication_objective": publication_objective,
        "gap_counts": _gap_counts(gaps),
        "recommended_action_types": _recommended_action_types(actions),
        "route_repair_plan": _route_repair_plan(actions),
        "requires_controller_decision": any(bool(action.get("requires_controller_decision")) for action in actions),
        "promotion_gate_status": {
            "status": promotion_gate_payload["status"],
            "allow_write": promotion_gate_payload["allow_write"],
            "current_required_action": promotion_gate_payload["current_required_action"],
            "blockers": list(promotion_gate_payload["blockers"]),
        },
    }


def _normalized_promotion_gate(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("promotion gate payload must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("promotion gate schema_version must be 1")
    return {
        "schema_version": 1,
        "gate_id": _required_text("promotion gate", "gate_id", payload.get("gate_id")),
        "study_id": _required_text("promotion gate", "study_id", payload.get("study_id")),
        "quest_id": _required_text("promotion gate", "quest_id", payload.get("quest_id")),
        "emitted_at": _required_text("promotion gate", "emitted_at", payload.get("emitted_at")),
        "source_gate_report_ref": _required_text(
            "promotion gate",
            "source_gate_report_ref",
            payload.get("source_gate_report_ref"),
        ),
        "publication_eval_ref": _required_mapping(
            "promotion gate",
            "publication_eval_ref",
            payload.get("publication_eval_ref"),
        ),
        "runtime_escalation_ref": _required_mapping(
            "promotion gate",
            "runtime_escalation_ref",
            payload.get("runtime_escalation_ref"),
        ),
        "overall_verdict": _required_text("promotion gate", "overall_verdict", payload.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "promotion gate",
            "primary_claim_status",
            payload.get("primary_claim_status"),
        ),
        "stop_loss_pressure": _required_text(
            "promotion gate",
            "stop_loss_pressure",
            payload.get("stop_loss_pressure"),
        ),
        "status": _required_text("promotion gate", "status", payload.get("status")),
        "allow_write": _required_bool("promotion gate", "allow_write", payload.get("allow_write")),
        "recommended_action": _required_text(
            "promotion gate",
            "recommended_action",
            payload.get("recommended_action"),
        ),
        "current_required_action": _required_text(
            "promotion gate",
            "current_required_action",
            payload.get("current_required_action"),
        ),
        "supervisor_phase": _required_text(
            "promotion gate",
            "supervisor_phase",
            payload.get("supervisor_phase"),
        ),
        "controller_stage_note": _required_text(
            "promotion gate",
            "controller_stage_note",
            payload.get("controller_stage_note"),
        ),
        "blockers": _required_string_list("promotion gate", "blockers", payload.get("blockers")),
    }


def _normalized_evaluation_summary(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("evaluation summary payload must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("evaluation summary schema_version must be 1")
    return {
        "schema_version": 1,
        "summary_id": _required_text("evaluation summary", "summary_id", payload.get("summary_id")),
        "study_id": _required_text("evaluation summary", "study_id", payload.get("study_id")),
        "quest_id": _required_text("evaluation summary", "quest_id", payload.get("quest_id")),
        "emitted_at": _required_text("evaluation summary", "emitted_at", payload.get("emitted_at")),
        "charter_ref": _required_mapping("evaluation summary", "charter_ref", payload.get("charter_ref")),
        "publication_eval_ref": _required_mapping(
            "evaluation summary",
            "publication_eval_ref",
            payload.get("publication_eval_ref"),
        ),
        "runtime_escalation_ref": _required_mapping(
            "evaluation summary",
            "runtime_escalation_ref",
            payload.get("runtime_escalation_ref"),
        ),
        "promotion_gate_ref": _required_mapping(
            "evaluation summary",
            "promotion_gate_ref",
            payload.get("promotion_gate_ref"),
        ),
        "evaluation_scope": _required_text(
            "evaluation summary",
            "evaluation_scope",
            payload.get("evaluation_scope"),
        ),
        "overall_verdict": _required_text("evaluation summary", "overall_verdict", payload.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "evaluation summary",
            "primary_claim_status",
            payload.get("primary_claim_status"),
        ),
        "verdict_summary": _required_text(
            "evaluation summary",
            "verdict_summary",
            payload.get("verdict_summary"),
        ),
        "stop_loss_pressure": _required_text(
            "evaluation summary",
            "stop_loss_pressure",
            payload.get("stop_loss_pressure"),
        ),
        "publication_objective": _required_text(
            "evaluation summary",
            "publication_objective",
            payload.get("publication_objective"),
        ),
        "gap_counts": _required_mapping("evaluation summary", "gap_counts", payload.get("gap_counts")),
        "recommended_action_types": _required_string_list(
            "evaluation summary",
            "recommended_action_types",
            payload.get("recommended_action_types"),
        ),
        "route_repair_plan": (
            None
            if payload.get("route_repair_plan") is None
            else _required_mapping("evaluation summary", "route_repair_plan", payload.get("route_repair_plan"))
        ),
        "requires_controller_decision": _required_bool(
            "evaluation summary",
            "requires_controller_decision",
            payload.get("requires_controller_decision"),
        ),
        "promotion_gate_status": _required_mapping(
            "evaluation summary",
            "promotion_gate_status",
            payload.get("promotion_gate_status"),
        ),
    }


def read_promotion_gate(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    gate_path = resolve_promotion_gate_ref(study_root=study_root, ref=ref)
    payload = _read_json_object(gate_path, label="promotion gate")
    return _normalized_promotion_gate(payload)


def read_evaluation_summary(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    summary_path = resolve_evaluation_summary_ref(study_root=study_root, ref=ref)
    payload = _read_json_object(summary_path, label="evaluation summary")
    return _normalized_evaluation_summary(payload)


def materialize_evaluation_summary_artifacts(
    *,
    study_root: Path,
    runtime_escalation_ref: str | Path | dict[str, Any],
    publishability_gate_report_ref: str | Path,
) -> dict[str, dict[str, str]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    publication_eval = read_publication_eval_latest(study_root=resolved_study_root)
    charter_context_ref = _required_mapping(
        "publication eval",
        "charter_context_ref",
        publication_eval.get("charter_context_ref"),
    )
    charter_payload = read_study_charter(
        study_root=resolved_study_root,
        ref=charter_context_ref.get("ref"),
    )
    normalized_runtime_escalation_ref = _normalize_runtime_escalation_ref(
        study_root=resolved_study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    gate_report_path = Path(publishability_gate_report_ref).expanduser()
    if gate_report_path.is_absolute():
        gate_report_path = gate_report_path.resolve()
    else:
        gate_report_path = (resolved_study_root / gate_report_path).resolve()
    gate_report = _normalize_gate_report(gate_report_path)
    promotion_gate_payload = _build_promotion_gate_payload(
        study_root=resolved_study_root,
        publication_eval=publication_eval,
        runtime_escalation_ref=normalized_runtime_escalation_ref,
        gate_report=gate_report,
    )
    promotion_gate_path = stable_promotion_gate_path(study_root=resolved_study_root)
    promotion_gate_path.parent.mkdir(parents=True, exist_ok=True)
    promotion_gate_path.write_text(
        json.dumps(_normalized_promotion_gate(promotion_gate_payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    promotion_gate_ref = {
        "gate_id": str(promotion_gate_payload["gate_id"]),
        "artifact_path": str(promotion_gate_path),
    }
    evaluation_summary_payload = _build_evaluation_summary_payload(
        study_root=resolved_study_root,
        publication_eval=publication_eval,
        charter_payload=charter_payload,
        runtime_escalation_ref=normalized_runtime_escalation_ref,
        promotion_gate_ref=promotion_gate_ref,
        promotion_gate_payload=promotion_gate_payload,
    )
    evaluation_summary_path = stable_evaluation_summary_path(study_root=resolved_study_root)
    evaluation_summary_path.parent.mkdir(parents=True, exist_ok=True)
    evaluation_summary_path.write_text(
        json.dumps(_normalized_evaluation_summary(evaluation_summary_payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "evaluation_summary_ref": {
            "summary_id": str(evaluation_summary_payload["summary_id"]),
            "artifact_path": str(evaluation_summary_path),
        },
        "promotion_gate_ref": promotion_gate_ref,
    }

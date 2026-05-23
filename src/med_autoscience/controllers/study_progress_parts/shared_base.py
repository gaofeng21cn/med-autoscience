from __future__ import annotations

import json
import re
import shlex
import sys
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Mapping

from opl_harness_shared.status_narration import (
    PROGRESS_ANSWER_CHECKLIST,
    build_status_narration_contract,
    build_status_narration_human_view,
)

from med_autoscience.controller_confirmation_summary import (
    materialize_controller_confirmation_summary,
    read_controller_confirmation_summary,
    stable_controller_confirmation_summary_path,
)
from med_autoscience.controller_summary import read_controller_summary, stable_controller_summary_path
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.controllers.study_progress_parts.macro_state_projection import (
    compact_study_macro_state_from_payload,
)
from med_autoscience.human_gate_policy import controller_human_gate_allowed
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.opl_runtime_contract import (
    CONTROLLED_RESEARCH_BACKEND_EXECUTOR_OWNER,
    OPL_RUNTIME_OWNER,
)
from med_autoscience.runtime_status_summary import (
    build_runtime_status_summary,
    materialize_runtime_status_summary,
)
from med_autoscience.study_charter import stable_study_charter_path
from med_autoscience.study_manual_finish import manual_finish_guard_only, resolve_effective_study_manual_finish_contract
from med_autoscience.study_task_intake import (
    build_task_intake_progress_override,
    read_latest_task_intake,
    summarize_task_intake,
    task_intake_requests_manuscript_fast_lane,
)


def _controller_override(name: str, default: Any) -> Any:
    controller_module = sys.modules.get("med_autoscience.controllers.study_progress")
    if controller_module is None:
        return default
    return getattr(controller_module, name, default)


def _build_same_line_route_truth(*, quality_closure_truth: Mapping[str, Any], quality_execution_lane: Mapping[str, Any]):
    evaluation_summary = import_module("med_autoscience.evaluation_summary")
    build_truth = _controller_override("build_same_line_route_truth", evaluation_summary.build_same_line_route_truth)
    return build_truth(
        quality_closure_truth=quality_closure_truth,
        quality_execution_lane=quality_execution_lane,
    )


def stable_evaluation_summary_path(*, study_root: Path) -> Path:
    return import_module("med_autoscience.evaluation_summary").stable_evaluation_summary_path(study_root=study_root)


def stable_promotion_gate_path(*, study_root: Path) -> Path:
    return import_module("med_autoscience.evaluation_summary").stable_promotion_gate_path(study_root=study_root)


def materialize_evaluation_summary_artifacts(
    *,
    study_root: Path,
    runtime_escalation_ref: str | Path | dict[str, Any],
    publishability_gate_report_ref: str | Path,
) -> dict[str, dict[str, str]]:
    materialize = _controller_override(
        "materialize_evaluation_summary_artifacts",
        import_module("med_autoscience.evaluation_summary").materialize_evaluation_summary_artifacts,
    )
    return materialize(
        study_root=study_root,
        runtime_escalation_ref=runtime_escalation_ref,
        publishability_gate_report_ref=publishability_gate_report_ref,
    )


def read_evaluation_summary(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    read_summary = _controller_override(
        "read_evaluation_summary",
        import_module("med_autoscience.evaluation_summary").read_evaluation_summary,
    )
    return read_summary(study_root=study_root, ref=ref)


SCHEMA_VERSION = 1
_DEFAULT_EVENT_LIMIT = 6
from .status_text_labels import *  # noqa: F403


def _load_controller(module_name: str):
    return import_module(f"med_autoscience.controllers.{module_name}")


class _LazyModuleProxy:
    def __init__(self, loader: Callable[[], Any]) -> None:
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_module", None)

    def _resolve(self):
        module = object.__getattribute__(self, "_module")
        if module is None:
            module = object.__getattribute__(self, "_loader")()
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        setattr(self._resolve(), name, value)


gate_clearing_batch = _LazyModuleProxy(lambda: _load_controller("gate_clearing_batch"))
quality_repair_batch = _LazyModuleProxy(lambda: _load_controller("quality_repair_batch"))
domain_status_projection = _LazyModuleProxy(lambda: _load_controller("domain_status_projection"))
_QUALITY_CLOSURE_BASIS_LABELS = {
    "clinical_significance": "临床意义",
    "evidence_strength": "证据强度",
    "novelty_positioning": "创新性定位",
    "human_review_readiness": "人工审阅准备度",
    "publication_gate": "发表门控",
}
_QUALITY_REVISION_DIMENSION_LABELS = {
    **_QUALITY_CLOSURE_BASIS_LABELS,
}
_QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS = {
    "auto_re_review_pending": "等待系统自动复评",
    "auto_re_review_blocked": "自动复评暂未继续",
    "not_in_re_review_waiting": "当前不在等待复评阶段",
}
_LATEST_EVENT_DISPLAY_TIERS = {
    "opl_runtime_owner_handoff": 0,
    "runtime_progress": 0,
    "paper_projection": 0,
    "controller_decision": 0,
    "publication_eval": 0,
    "runtime_escalation": 0,
    "domain_health_diagnostic": 1,
    "launch_report": 2,
}
_HUMAN_SURFACE_REFRESH_BLOCKER_LABELS = {
    _BLOCKER_LABELS["stale_study_delivery_mirror"],
    _BLOCKER_LABELS["missing_submission_minimal"],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _progress_freshness_now() -> datetime:
    return datetime.now(timezone.utc)


def _status_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if not isinstance(payload, dict):
            raise TypeError("study_progress status surface to_dict() must return a mapping")
        return dict(payload)
    raise TypeError("study_progress requires progress_projection to return a mapping-like payload")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _normalize_timestamp(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        return datetime.fromisoformat(raw).isoformat()
    except ValueError:
        return None


def _time_label(timestamp: str | None) -> str | None:
    normalized = _normalize_timestamp(timestamp)
    if normalized is None:
        return None
    instant = datetime.fromisoformat(normalized)
    suffix = "UTC" if instant.utcoffset() == timezone.utc.utcoffset(instant) else instant.strftime("UTC%z")
    return f"{instant.strftime('%Y-%m-%d %H:%M')} {suffix}".replace("UTC+0000", "UTC")


def _duration_hours_label(seconds: int) -> str:
    hours = max(1, round(seconds / 3600))
    return f"{hours} 小时"


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping_copy(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _runtime_control_pickup_refs(
    *,
    evaluation_summary_ref: object = None,
    refs_payload: Mapping[str, Any] | None = None,
    publication_eval_ref: object = None,
    controller_decision_ref: object = None,
    opl_runtime_owner_handoff_ref: object = None,
    domain_health_diagnostic_ref: object = None,
) -> list[str]:
    refs = dict(refs_payload or {})
    candidates = [
        _non_empty_text(evaluation_summary_ref),
        _non_empty_text(refs.get("evaluation_summary_path")),
        _non_empty_text(publication_eval_ref),
        _non_empty_text(refs.get("publication_eval_path")),
        _non_empty_text(controller_decision_ref),
        _non_empty_text(refs.get("controller_decision_path")),
        _non_empty_text(opl_runtime_owner_handoff_ref),
        _non_empty_text(refs.get("opl_runtime_owner_handoff_path")),
        _non_empty_text(domain_health_diagnostic_ref),
        _non_empty_text(refs.get("domain_health_diagnostic_report_path")),
    ]
    ordered_refs: list[str] = []
    for ref in candidates:
        if ref is None or ref in ordered_refs:
            continue
        ordered_refs.append(ref)
    return ordered_refs


def _normalized_research_runtime_control_projection_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    direct_projection = _mapping_copy(payload.get("research_runtime_control_projection"))
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    interrupt_policy = _non_empty_text(intervention_lane.get("recommended_action_id"))
    gate_lane = _non_empty_text(intervention_lane.get("lane_id"))
    if gate_lane == "human_decision_gate":
        gate_lane = "user_decision_gate"
    gate_summary = _display_text(intervention_lane.get("summary")) or _non_empty_text(
        intervention_lane.get("summary")
    )
    operator_status_card = _mapping_copy(payload.get("operator_status_card"))
    autonomy_contract = _mapping_copy(payload.get("autonomy_contract"))
    restore_point = _mapping_copy(autonomy_contract.get("restore_point"))
    refs = _mapping_copy(payload.get("refs"))
    pickup_refs = _runtime_control_pickup_refs(refs_payload=refs)
    default_projection: dict[str, Any] = {
        "surface_kind": "research_runtime_control_projection",
        "study_session_owner": {
            "runtime_owner": OPL_RUNTIME_OWNER,
            "study_owner": "med-autoscience",
            "executor_owner": CONTROLLED_RESEARCH_BACKEND_EXECUTOR_OWNER,
        },
        "session_lineage_surface": {
            "surface_kind": "study_progress",
            "field_path": "family_checkpoint_lineage",
            "resume_contract_field": "family_checkpoint_lineage.resume_contract",
            "continuation_state_field": "continuation_state",
            "active_run_id_field": "supervision.active_run_id",
        },
        "restore_point_surface": {
            "surface_kind": "study_progress",
            "field_path": "autonomy_contract.restore_point",
            "lineage_anchor_field": "family_checkpoint_lineage.resume_contract",
            "summary": _non_empty_text(restore_point.get("summary")),
        },
        "progress_cursor_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
        },
        "progress_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
            "fallback_field_path": "next_system_action",
            "current_focus": _non_empty_text(operator_status_card.get("current_focus")),
        },
        "artifact_inventory_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs",
        },
        "artifact_pickup_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs.evaluation_summary_path",
            "fallback_fields": [
                "refs.publication_eval_path",
                "refs.controller_decision_path",
                "refs.opl_runtime_owner_handoff_path",
                "refs.domain_health_diagnostic_report_path",
            ],
            "pickup_refs": pickup_refs,
        },
        "command_templates": {
            "resume": None,
            "check_progress": None,
            "check_runtime_status": None,
        },
        "research_gate_surface": {
            "surface_kind": "study_progress",
            "approval_gate_field": "needs_user_decision",
            "legacy_approval_gate_field": "needs_physician_decision",
            "approval_gate_owner": "mas_controller",
            "approval_gate_required": bool(payload.get("needs_user_decision"))
            or bool(payload.get("needs_physician_decision")),
            "interrupt_policy_field": "intervention_lane.recommended_action_id",
            "interrupt_policy": interrupt_policy,
            "gate_lane_field": "intervention_lane.lane_id",
            "gate_lane": gate_lane,
            "gate_summary_field": "intervention_lane.summary",
            "gate_summary": gate_summary,
        },
    }
    if not direct_projection:
        return default_projection

    normalized = dict(default_projection)
    normalized.update(direct_projection)

    nested_fields = (
        "study_session_owner",
        "session_lineage_surface",
        "restore_point_surface",
        "progress_cursor_surface",
        "progress_surface",
        "artifact_inventory_surface",
        "artifact_pickup_surface",
        "command_templates",
        "research_gate_surface",
    )
    for field_name in nested_fields:
        merged = _mapping_copy(default_projection.get(field_name))
        merged.update(_mapping_copy(direct_projection.get(field_name)))
        normalized[field_name] = merged

    command_templates = _mapping_copy(normalized.get("command_templates"))
    command_templates.setdefault("resume", None)
    command_templates.setdefault("check_progress", None)
    command_templates.setdefault("check_runtime_status", None)
    normalized["command_templates"] = command_templates

    artifact_pickup_surface = _mapping_copy(normalized.get("artifact_pickup_surface"))
    merged_pickup_refs: list[str] = []
    for ref in pickup_refs:
        if ref not in merged_pickup_refs:
            merged_pickup_refs.append(ref)
    for item in artifact_pickup_surface.get("pickup_refs") or []:
        text = _non_empty_text(item)
        if text is None or text in merged_pickup_refs:
            continue
        merged_pickup_refs.append(text)
    artifact_pickup_surface["pickup_refs"] = merged_pickup_refs
    normalized["artifact_pickup_surface"] = artifact_pickup_surface

    research_gate_surface = _mapping_copy(normalized.get("research_gate_surface"))
    if not isinstance(research_gate_surface.get("approval_gate_required"), bool):
        research_gate_surface["approval_gate_required"] = bool(payload.get("needs_user_decision")) or bool(
            payload.get("needs_physician_decision")
        )
    if _non_empty_text(research_gate_surface.get("interrupt_policy")) is None:
        research_gate_surface["interrupt_policy"] = interrupt_policy
    if _non_empty_text(research_gate_surface.get("gate_lane")) is None:
        research_gate_surface["gate_lane"] = gate_lane
    elif _non_empty_text(research_gate_surface.get("gate_lane")) == "human_decision_gate":
        research_gate_surface["gate_lane"] = "user_decision_gate"
    if _non_empty_text(research_gate_surface.get("gate_summary")) is None:
        research_gate_surface["gate_summary"] = gate_summary
    else:
        research_gate_surface["gate_summary"] = _display_text(
            research_gate_surface.get("gate_summary")
        ) or _non_empty_text(
            research_gate_surface.get("gate_summary")
        )
    research_gate_surface.setdefault("gate_summary_field", "intervention_lane.summary")
    normalized["research_gate_surface"] = research_gate_surface

    restore_point_surface = _mapping_copy(normalized.get("restore_point_surface"))
    if _non_empty_text(restore_point_surface.get("summary")) is None:
        restore_point_surface["summary"] = _non_empty_text(restore_point.get("summary"))
    normalized["restore_point_surface"] = restore_point_surface

    progress_surface = _mapping_copy(normalized.get("progress_surface"))
    if _non_empty_text(progress_surface.get("current_focus")) is None:
        progress_surface["current_focus"] = _non_empty_text(operator_status_card.get("current_focus"))
    normalized["progress_surface"] = progress_surface

    return normalized


def _normalized_quality_execution_lane_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    direct_lane = _mapping_copy(payload.get("quality_execution_lane"))
    if direct_lane:
        return direct_lane
    module_surfaces = _mapping_copy(payload.get("module_surfaces"))
    eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    fallback_lane = _mapping_copy(eval_hygiene_surface.get("quality_execution_lane"))
    return fallback_lane or None


def _normalized_same_line_route_surface_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    direct_surface = _mapping_copy(payload.get("same_line_route_surface"))
    if direct_surface:
        return direct_surface
    module_surfaces = _mapping_copy(payload.get("module_surfaces"))
    eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    fallback_surface = _mapping_copy(eval_hygiene_surface.get("same_line_route_surface"))
    return fallback_surface or None


def _normalized_same_line_route_truth_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if "same_line_route_truth" in payload and payload.get("same_line_route_truth") is None:
        return None
    direct_truth = _mapping_copy(payload.get("same_line_route_truth"))
    if direct_truth:
        return direct_truth
    module_surfaces = _mapping_copy(payload.get("module_surfaces"))
    eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    fallback_truth = _mapping_copy(eval_hygiene_surface.get("same_line_route_truth"))
    if fallback_truth:
        return fallback_truth
    derived_truth = _build_same_line_route_truth(
        quality_closure_truth=_mapping_copy(payload.get("quality_closure_truth")),
        quality_execution_lane=_normalized_quality_execution_lane_payload(payload) or {},
    )
    return derived_truth or None


def _normalize_study_progress_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    module_surfaces = _mapping_copy(normalized.get("module_surfaces"))
    if module_surfaces:
        eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
        if eval_hygiene_surface:
            eval_hygiene_surface["quality_execution_lane"] = _mapping_copy(
                eval_hygiene_surface.get("quality_execution_lane")
            ) or None
            eval_hygiene_surface["same_line_route_surface"] = _mapping_copy(
                eval_hygiene_surface.get("same_line_route_surface")
            ) or None
            eval_hygiene_surface["same_line_route_truth"] = _mapping_copy(
                eval_hygiene_surface.get("same_line_route_truth")
            ) or _build_same_line_route_truth(
                quality_closure_truth=_mapping_copy(eval_hygiene_surface.get("quality_closure_truth")),
                quality_execution_lane=_mapping_copy(eval_hygiene_surface.get("quality_execution_lane")),
            ) or None
            module_surfaces["eval_hygiene"] = eval_hygiene_surface
            normalized["module_surfaces"] = module_surfaces
    normalized["quality_execution_lane"] = _normalized_quality_execution_lane_payload(normalized)
    normalized["same_line_route_truth"] = _normalized_same_line_route_truth_payload(normalized)
    normalized["same_line_route_surface"] = _normalized_same_line_route_surface_payload(normalized)
    normalized["study_macro_state"] = compact_study_macro_state_from_payload(normalized)
    normalized["research_runtime_control_projection"] = _normalized_research_runtime_control_projection_payload(normalized)
    if _publication_supervisor_blocks_same_line_route(_mapping_copy(normalized.get("publication_supervisor_state"))):
        normalized["same_line_route_truth"] = None
        normalized["same_line_route_surface"] = None
        if module_surfaces:
            eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
            if eval_hygiene_surface:
                eval_hygiene_surface["same_line_route_truth"] = None
                eval_hygiene_surface["same_line_route_surface"] = None
                module_surfaces["eval_hygiene"] = eval_hygiene_surface
                normalized["module_surfaces"] = module_surfaces
    return normalized


def _timestamp_is_newer(candidate: object, baseline: object) -> bool:
    candidate_text = _normalize_timestamp(candidate)
    if candidate_text is None:
        return False
    baseline_text = _normalize_timestamp(baseline)
    if baseline_text is None:
        return True
    return datetime.fromisoformat(candidate_text) > datetime.fromisoformat(baseline_text)


def _publication_eval_semantically_stale_against_gate(
    *,
    publication_eval_payload: dict[str, Any] | None,
    publishability_gate_payload: dict[str, Any] | None,
) -> bool:
    if not isinstance(publication_eval_payload, dict) or not isinstance(publishability_gate_payload, dict):
        return False
    if _non_empty_text(publishability_gate_payload.get("status")) != "clear":
        return False
    verdict_payload = publication_eval_payload.get("verdict")
    overall_verdict = (
        _non_empty_text(verdict_payload.get("overall_verdict"))
        if isinstance(verdict_payload, dict)
        else None
    )
    if overall_verdict not in {"promising", "clear", "ready", "pass", "approved"}:
        return True
    for gap in publication_eval_payload.get("gaps") or []:
        if not isinstance(gap, dict):
            continue
        severity = _non_empty_text(gap.get("severity"))
        summary = _non_empty_text(gap.get("summary"))
        if summary == "stale_study_delivery_mirror":
            return True
        if severity and severity != "optional":
            return True
    return False


def _publication_supervisor_blocks_same_line_route(publication_supervisor_state: Mapping[str, Any] | None) -> bool:
    if not isinstance(publication_supervisor_state, Mapping):
        return False
    current_required_action = _non_empty_text(publication_supervisor_state.get("current_required_action"))
    if current_required_action == "return_to_publishability_gate":
        return True
    return bool(publication_supervisor_state.get("bundle_tasks_downstream_only"))


def _candidate_path(value: object) -> Path | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return Path(text).expanduser().resolve()


def _humanize_token(token: object) -> str | None:
    text = _non_empty_text(token)
    if text is None:
        return None
    return text.replace("_", " ")


def _quote_cli_arg(value: str | Path | None) -> str:
    text = str(value or "").strip()
    if not text:
        return "<profile>"
    return shlex.quote(text)


def _command_prefix(profile_ref: str | Path | None) -> str:
    del profile_ref
    return "uv run python -m med_autoscience.cli"


def _profile_arg(profile_ref: str | Path | None) -> str:
    return _quote_cli_arg(Path(profile_ref).expanduser().resolve() if profile_ref is not None else None)


def _study_selector(*, study_id: str) -> str:
    return f"--study-id {_quote_cli_arg(study_id)}"


def _display_text(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text in _TEXT_LABELS:
        return _TEXT_LABELS[text]
    for source, target in _TEXT_REPLACEMENTS:
        text = text.replace(source, target)
    for token, label in (
        *_CURRENT_STAGE_LABELS.items(),
        *_PAPER_STAGE_LABELS.items(),
        *_BLOCKER_LABELS.items(),
    ):
        text = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])",
            label,
            text,
        )
    return text


def _status_narration_human_view(payload: Mapping[str, Any]) -> dict[str, Any]:
    return build_status_narration_human_view(
        payload,
        fallback_current_stage=_non_empty_text(payload.get("current_stage")),
        fallback_latest_update=_display_text(payload.get("current_stage_summary"))
        or _non_empty_text(payload.get("current_stage_summary")),
        fallback_next_step=_display_text(payload.get("next_system_action"))
        or _non_empty_text(payload.get("next_system_action")),
        fallback_blockers=payload.get("current_blockers") or [],
    )


def _current_stage_label(stage: object) -> str | None:
    text = _non_empty_text(stage)
    if text is None:
        return None
    return _CURRENT_STAGE_LABELS.get(text, _humanize_token(text))


def _paper_stage_label(stage: object) -> str | None:
    text = _non_empty_text(stage)
    if text is None:
        return None
    return _PAPER_STAGE_LABELS.get(text, _humanize_token(text))


def _route_repair_mode(action_type: str) -> str:
    if action_type == "bounded_analysis":
        return "bounded_analysis"
    return "same_line_route_back"


def _route_repair_summary(route_repair: dict[str, Any] | None, *, include_rationale: bool = False) -> str | None:
    if not isinstance(route_repair, dict):
        return None
    route_label = _non_empty_text(route_repair.get("route_target_label"))
    key_question = _non_empty_text(route_repair.get("route_key_question"))
    if route_label is None or key_question is None:
        return None
    repair_mode = _non_empty_text(route_repair.get("repair_mode"))
    if repair_mode == "bounded_analysis":
        summary = f"进入“{route_label}”有限补充分析，先回答“{key_question}”。"
    else:
        summary = f"回到“{route_label}”，回答“{key_question}”。"
    rationale = _non_empty_text(route_repair.get("route_rationale"))
    if include_rationale and rationale is not None:
        summary = f"{summary} 理由：{rationale}"
    return summary

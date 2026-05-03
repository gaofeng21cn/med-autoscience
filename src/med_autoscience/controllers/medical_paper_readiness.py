from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.controllers import literature_provider_runtime
from med_autoscience.controllers import real_paper_ai_first_soak
from med_autoscience.controllers import real_workspace_soak_monitor
from med_autoscience.controllers import revision_rebuttal_loop
from med_autoscience.controllers import route_decision_orchestrator
from med_autoscience.controllers import literature_intelligence_os
from med_autoscience.controllers import multistudy_soak_proof
from med_autoscience.controllers import statistical_discipline_runtime
from med_autoscience.controllers import study_line_decision_engine
from med_autoscience.policies import publication_critique


SCHEMA_VERSION = 1
SURFACE = "medical_paper_readiness"
READINESS_ROOT = Path("artifacts/medical_paper")


CapabilityValidator = Callable[[Mapping[str, Any]], tuple[str, str]]


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _has_text(value: object) -> bool:
    return bool(_text(value))


def _has_any_text(value: object) -> bool:
    return any(_text(item) for item in _list(value))


def _status_from_missing(missing_reason: str) -> str:
    return "present" if not missing_reason else "blocked"


def _first_blocker(payload: Mapping[str, Any], default: str) -> str:
    blockers = payload.get("blockers")
    if isinstance(blockers, list) and blockers:
        first = blockers[0]
        if isinstance(first, Mapping):
            return _text(first.get("reason_code")) or _text(first.get("code")) or default
        return _text(first) or default
    return default


def _blocks_quality_authority(payload: Mapping[str, Any]) -> str:
    if payload.get("quality_claim_authorized") not in {False, None}:
        return "quality_claim_authorized_by_projection"
    if payload.get("mechanical_projection_can_authorize_quality") not in {False, None}:
        return "mechanical_projection_quality_authority_enabled"
    authority = _mapping(payload.get("authority"))
    if authority.get("mechanical_projection_can_authorize_quality") not in {False, None}:
        return "mechanical_projection_quality_authority_enabled"
    contract = _mapping(payload.get("authority_contract"))
    if contract.get("can_authorize_quality") is not False and "can_authorize_quality" in contract:
        return "quality_authority_enabled_by_read_model"
    if contract.get("can_authorize_submission") is not False and "can_authorize_submission" in contract:
        return "submission_authority_enabled_by_read_model"
    if contract.get("can_authorize_finalize") is not False and "can_authorize_finalize" in contract:
        return "finalize_authority_enabled_by_read_model"
    return ""


def _validate_literature_scout(payload: Mapping[str, Any]) -> tuple[str, str]:
    if payload.get("surface") == literature_intelligence_os.SURFACE:
        if _text(payload.get("status")) == "ready":
            return "present", ""
        return "blocked", _text(payload.get("missing_reason")) or "literature_intelligence_not_ready"
    if not _mapping(payload.get("search_strategy")):
        return "blocked", "missing_search_strategy"
    if not _has_text(payload.get("search_date")):
        return "blocked", "missing_search_date"
    if not _has_any_text(payload.get("anchor_papers")):
        return "blocked", "missing_anchor_papers"
    if not _has_any_text(payload.get("guidelines")):
        return "blocked", "missing_guidelines"
    if not _has_any_text(payload.get("journal_neighbor_refs")):
        return "blocked", "missing_journal_neighbor_refs"
    return "present", ""


def _validate_line_selection(payload: Mapping[str, Any]) -> tuple[str, str]:
    if payload.get("surface") == study_line_decision_engine.SURFACE:
        if _text(payload.get("status")) == "selected":
            return "present", ""
        blockers = payload.get("blockers")
        if isinstance(blockers, list) and blockers:
            first = blockers[0]
            if isinstance(first, Mapping):
                return "blocked", _text(first.get("code")) or "study_line_decision_blocked"
        return "blocked", "study_line_decision_blocked"
    if not _has_text(payload.get("selected_line_id")):
        return "blocked", "missing_selected_line_id"
    dimensions = _mapping(payload.get("dimensions"))
    required = (
        "novelty",
        "clinical_relevance",
        "data_fit",
        "analysis_plasticity",
        "external_validation",
        "journal_fit",
        "cost_risk",
        "stop_threshold",
    )
    for key in required:
        if not _has_text(dimensions.get(key)):
            return "blocked", f"missing_{key}"
    return "present", ""


def _validate_analysis_contract(payload: Mapping[str, Any]) -> tuple[str, str]:
    if any(field in payload for field in statistical_discipline_runtime.REQUIRED_STATISTICAL_DISCIPLINE_FIELDS):
        statistical_status = statistical_discipline_runtime.validate_statistical_discipline_contract(payload)
        if _text(statistical_status.get("status")) == "present":
            return "present", ""
        return "blocked", _text(statistical_status.get("reason_code")) or "statistical_contract_not_resolved"
    status = _text(payload.get("status"))
    if status != "resolved":
        return "blocked", _text(payload.get("reason_code")) or "analysis_contract_not_resolved"
    if not _has_text(payload.get("study_archetype")):
        return "blocked", "missing_study_archetype"
    if not _has_text(payload.get("endpoint_type")):
        return "blocked", "missing_endpoint_type"
    return "present", ""


def _validate_bounded_board(payload: Mapping[str, Any]) -> tuple[str, str]:
    candidates = [item for item in _list(payload.get("candidates")) if isinstance(item, Mapping)]
    if any("statistical_risk" in candidate for candidate in candidates):
        statistical_status = statistical_discipline_runtime.validate_bounded_analysis_candidate_board(payload)
        if _text(statistical_status.get("status")) == "present":
            return "present", ""
        return "blocked", _text(statistical_status.get("reason_code")) or "bounded_board_not_resolved"
    if not candidates:
        return "blocked", "missing_candidates"
    for candidate in candidates:
        for key in (
            "target_claim",
            "expected_evidence_gain",
            "cost_risk",
            "clinical_interpretability",
            "decision",
            "decision_reason",
        ):
            if not _has_text(candidate.get(key)):
                return "blocked", f"candidate_missing_{key}"
    return "present", ""


def _validate_stop_loss_memo(payload: Mapping[str, Any]) -> tuple[str, str]:
    if payload.get("surface") in {"route_control_stoploss", "stop_loss_memo"}:
        return _validate_route_control_stop_loss_payload(payload)
    return _validate_legacy_stop_loss_payload(payload)


def _validate_route_control_stop_loss_payload(payload: Mapping[str, Any]) -> tuple[str, str]:
    if payload.get("quality_claim_authorized") is not False:
        return "blocked", "quality_claim_authorized_by_projection"
    if payload.get("decision_allowed") is False:
        return "blocked", _route_control_decision_blocker(payload)
    return _validate_stop_loss_required_inputs(
        payload=payload,
        route_inputs=_mapping(payload.get("route_control_inputs")) or payload,
    )


def _route_control_decision_blocker(payload: Mapping[str, Any]) -> str:
    blockers = payload.get("blockers")
    if isinstance(blockers, list) and blockers:
        return _text(blockers[0]) or "route_control_decision_blocked"
    return "route_control_decision_blocked"


def _validate_legacy_stop_loss_payload(payload: Mapping[str, Any]) -> tuple[str, str]:
    return _validate_stop_loss_required_inputs(payload=payload, route_inputs=payload)


def _validate_stop_loss_required_inputs(
    *,
    payload: Mapping[str, Any],
    route_inputs: Mapping[str, Any],
) -> tuple[str, str]:
    if not _has_any_text(route_inputs.get("attempted_paths")):
        return "blocked", "missing_attempted_paths"
    if not _has_text(route_inputs.get("evidence_gain_ceiling")):
        return "blocked", "missing_evidence_gain_ceiling"
    if not _has_text(payload.get("decision")):
        return "blocked", "missing_decision"
    return "present", ""


def _validate_target_journal_layer(payload: Mapping[str, Any]) -> tuple[str, str]:
    if payload.get("mechanical_projection_can_authorize_quality") is not False:
        return "blocked", "mechanical_projection_quality_authority_enabled"
    if payload.get("quality_claim_authorized") is not False:
        return "blocked", "quality_claim_authorized_by_projection"
    return "present", ""


def _validate_soak_matrix(payload: Mapping[str, Any]) -> tuple[str, str]:
    if payload.get("mechanical_projection_can_authorize_quality") is not False:
        return "blocked", "mechanical_projection_quality_authority_enabled"
    if payload.get("quality_claim_authorized") is not False:
        return "blocked", "quality_claim_authorized_by_projection"
    status = _text(payload.get("overall_status"))
    if status == "complete":
        return "present", ""
    if status == "partial":
        return "partial", "missing_required_soak_stage"
    return "blocked", "missing_real_study_soak_evidence"


def _validate_literature_provider_runtime(payload: Mapping[str, Any]) -> tuple[str, str]:
    authority_blocker = _blocks_quality_authority(payload)
    if authority_blocker:
        return "blocked", authority_blocker
    if _text(payload.get("surface")) != literature_provider_runtime.SURFACE:
        return "blocked", "unexpected_literature_provider_runtime_surface"
    if _text(payload.get("status")) == "ready":
        return "present", ""
    return "blocked", _text(payload.get("missing_reason")) or "literature_provider_runtime_not_ready"


def _validate_route_decision_orchestrator(payload: Mapping[str, Any]) -> tuple[str, str]:
    authority_blocker = _blocks_quality_authority(payload)
    if authority_blocker:
        return "blocked", authority_blocker
    if _text(payload.get("surface")) != route_decision_orchestrator.SURFACE:
        return "blocked", "unexpected_route_decision_orchestrator_surface"
    if _text(payload.get("status")) != "ready":
        return "blocked", _first_blocker(payload, "route_decision_orchestrator_not_ready")
    if _text(payload.get("route_decision")) not in {"proceed_to_baseline", "return_to_scout", "switch_line"}:
        return "blocked", "unsupported_route_decision"
    if not _has_text(payload.get("controller_decision_ref")):
        return "blocked", "missing_controller_decision_ref"
    controller_decision = _mapping(payload.get("controller_decision"))
    if controller_decision and controller_decision.get("quality_claim_authorized") is not False:
        return "blocked", "controller_decision_quality_authority_enabled"
    return "present", ""


def _validate_statistical_discipline_operations(payload: Mapping[str, Any]) -> tuple[str, str]:
    authority_blocker = _blocks_quality_authority(payload)
    if authority_blocker:
        return "blocked", authority_blocker
    if _text(payload.get("surface")) != "statistical_discipline_operations":
        return "blocked", "unexpected_statistical_discipline_operations_surface"
    status = _text(payload.get("status"))
    if status == "ready":
        return "present", ""
    if status == "partial":
        return "partial", _first_blocker(payload, "statistical_discipline_operations_partial")
    return "blocked", _first_blocker(payload, "statistical_discipline_operations_blocked")


def _validate_revision_rebuttal_loop(payload: Mapping[str, Any]) -> tuple[str, str]:
    authority_blocker = _blocks_quality_authority(payload)
    if authority_blocker:
        return "blocked", authority_blocker
    if _text(payload.get("surface")) != revision_rebuttal_loop.SURFACE:
        return "blocked", "unexpected_revision_rebuttal_loop_surface"
    if _text(payload.get("status")) == "ready":
        return "present", ""
    return "blocked", _first_blocker(payload, "revision_rebuttal_loop_blocked")


def _validate_authoring_runtime_authorization(payload: Mapping[str, Any]) -> tuple[str, str]:
    if payload.get("mechanical_projection_can_authorize_quality") not in {False, None}:
        return "blocked", "mechanical_projection_quality_authority_enabled"
    authority = _mapping(payload.get("authority"))
    if authority.get("mechanical_projection_can_authorize_quality") is not False:
        return "blocked", "mechanical_projection_quality_authority_enabled"
    if _text(payload.get("surface")) != "ai_reviewer_journal_writing_authorization":
        return "blocked", "unexpected_authoring_runtime_authorization_surface"
    if payload.get("full_drafting_authorized") is True:
        return "present", ""
    return "blocked", _first_blocker(payload, "full_drafting_not_authorized")


def _validate_real_workspace_soak_monitor(payload: Mapping[str, Any]) -> tuple[str, str]:
    authority_blocker = _blocks_quality_authority(payload)
    if authority_blocker:
        return "blocked", authority_blocker
    if _text(payload.get("surface")) != real_workspace_soak_monitor.SURFACE:
        return "blocked", "unexpected_real_workspace_soak_monitor_surface"
    contract = _mapping(payload.get("authority_contract"))
    if contract.get("can_mutate_runtime") is not False and "can_mutate_runtime" in contract:
        return "blocked", "runtime_mutation_authority_enabled_by_read_model"
    status = _text(payload.get("overall_status"))
    if status == "ready":
        return "present", ""
    if status == "partial":
        return "partial", _text(payload.get("next_action")) or "real_workspace_soak_monitor_partial"
    return "blocked", _text(payload.get("next_action")) or "real_workspace_soak_monitor_blocked"


def _literature_scout_payload(*, study_root: Path) -> Mapping[str, Any]:
    payload = literature_intelligence_os.read_literature_intelligence_os(study_root=study_root)
    if payload:
        return payload
    return _read_json(stable_capability_surface_path(study_root=study_root, surface_key="literature_scout"))


def _study_line_payload(*, study_root: Path) -> Mapping[str, Any]:
    payload = _read_json(study_line_decision_engine.stable_study_line_decision_path(study_root=study_root))
    if payload:
        return payload
    return _read_json(stable_capability_surface_path(study_root=study_root, surface_key="study_line_selection"))


def _soak_matrix_payload(*, study_root: Path) -> Mapping[str, Any]:
    fixture_payload = _read_json(stable_capability_surface_path(study_root=study_root, surface_key="real_study_soak_matrix_evidence"))
    matrix_input = fixture_payload.get("multistudy_soak_matrix")
    if isinstance(matrix_input, list):
        projection = multistudy_soak_proof.build_multistudy_soak_matrix_projection(matrix_input)
        if projection.get("overall_status") == "ready":
            return {
                "surface": "real_study_soak_matrix_evidence",
                "overall_status": "complete",
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
                "multistudy_soak_projection": projection,
            }
        return {
            "surface": "real_study_soak_matrix_evidence",
            "overall_status": "partial" if projection.get("overall_status") == "partial" else "missing",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
            "missing_stage_gaps": [
                {"stage": str(gap), "missing_reason": "multistudy_soak_gap"}
                for study in projection.get("studies", [])
                if isinstance(study, Mapping)
                for gap in study.get("missing_gaps", [])
            ],
            "multistudy_soak_projection": projection,
        }
    evidence_path = stable_capability_surface_path(study_root=study_root, surface_key="real_study_soak_matrix_evidence")
    if not evidence_path.is_file():
        return {}
    return real_paper_ai_first_soak.build_real_study_soak_matrix_evidence(
        study_roots=[Path(study_root)]
    )


CAPABILITY_SPECS: tuple[dict[str, Any], ...] = (
    {
        "surface_key": "literature_scout",
        "surface": "literature_scout",
        "label": "Literature Scout OS",
        "path": READINESS_ROOT / "literature_scout.json",
        "required_for_ready": True,
        "next_action_summary": "补齐 Literature Scout OS 后再继续自动论文链路。",
        "validator": _validate_literature_scout,
    },
    {
        "surface_key": "study_line_selection",
        "surface": "study_line_selection_scorecard",
        "label": "Study Line Selection Scorecard",
        "path": READINESS_ROOT / "study_line_selection.json",
        "required_for_ready": True,
        "next_action_summary": "补齐 Study Line Selection Scorecard 后再继续自动论文链路。",
        "validator": _validate_line_selection,
    },
    {
        "surface_key": "archetype_analysis_contract",
        "surface": "archetype_specific_analysis_contract",
        "label": "Archetype-specific Analysis Contract",
        "path": Path("paper/medical_analysis_contract.json"),
        "required_for_ready": True,
        "next_action_summary": "补齐 archetype-specific analysis contract 后再继续自动论文链路。",
        "validator": _validate_analysis_contract,
    },
    {
        "surface_key": "bounded_analysis_candidate_board",
        "surface": "bounded_analysis_candidate_board",
        "label": "Bounded Analysis Candidate Board",
        "path": READINESS_ROOT / "bounded_analysis_candidate_board.json",
        "required_for_ready": True,
        "next_action_summary": "补齐 Bounded Analysis Candidate Board 后再继续自动论文链路。",
        "validator": _validate_bounded_board,
    },
    {
        "surface_key": "stop_loss_memo",
        "surface": "stop_loss_memo",
        "label": "Stop-loss Memo",
        "path": READINESS_ROOT / "stop_loss_memo.json",
        "required_for_ready": True,
        "next_action_summary": "补齐 Stop-loss Memo 后再继续自动论文链路。",
        "validator": _validate_stop_loss_memo,
    },
    {
        "surface_key": "target_journal_writing_layer",
        "surface": "target_journal_writing_layer",
        "label": "Target Journal Writing Layer",
        "path": publication_critique.TARGET_JOURNAL_WRITING_LAYER_RELATIVE_PATH,
        "required_for_ready": True,
        "next_action_summary": "冻结 target journal writing layer 后再授权完整写作链路。",
        "validator": _validate_target_journal_layer,
    },
    {
        "surface_key": "real_study_soak_matrix_evidence",
        "surface": "real_study_soak_matrix_evidence",
        "label": "Real-study Soak Matrix Evidence",
        "path": Path("artifacts/real_study_soak_matrix/evidence.json"),
        "required_for_ready": True,
        "next_action_summary": "补齐真实 study soak evidence 后再声明自动论文链路可用。",
        "validator": _validate_soak_matrix,
    },
    {
        "surface_key": "literature_provider_runtime",
        "surface": "literature_provider_runtime",
        "label": "Literature Provider Runtime",
        "path": literature_provider_runtime.ARTIFACT_RELATIVE_PATH,
        "required_for_ready": True,
        "next_action_summary": "运行联网 literature provider runtime 并写入可审计来源后再继续。",
        "validator": _validate_literature_provider_runtime,
    },
    {
        "surface_key": "route_decision_orchestrator",
        "surface": "route_decision_orchestrator",
        "label": "Route Decision Orchestrator",
        "path": READINESS_ROOT / "route_decision_orchestrator.json",
        "required_for_ready": True,
        "next_action_summary": "写入路线裁决和 controller decision durable ref 后再进入执行。",
        "validator": _validate_route_decision_orchestrator,
    },
    {
        "surface_key": "statistical_discipline_operations",
        "surface": "statistical_discipline_operations",
        "label": "Statistical Discipline Operations",
        "path": READINESS_ROOT / "statistical_discipline_operations.json",
        "required_for_ready": True,
        "next_action_summary": "处理统计纪律 blocker 或记录 waiver 后再继续分析。",
        "validator": _validate_statistical_discipline_operations,
    },
    {
        "surface_key": "revision_rebuttal_loop",
        "surface": "revision_rebuttal_loop",
        "label": "Revision Rebuttal Loop",
        "path": revision_rebuttal_loop.ARTIFACT_RELATIVE_PATH,
        "required_for_ready": True,
        "next_action_summary": "启动返修 rebuttal loop 并绑定证据账本和 review ledger。",
        "validator": _validate_revision_rebuttal_loop,
    },
    {
        "surface_key": "authoring_runtime_authorization",
        "surface": "authoring_runtime_authorization",
        "label": "Authoring Runtime Authorization",
        "path": READINESS_ROOT / "authoring_runtime_authorization.json",
        "required_for_ready": True,
        "next_action_summary": "补齐目标期刊写作层、claim/display map、AI reviewer provenance 后再授权完整写作。",
        "validator": _validate_authoring_runtime_authorization,
    },
    {
        "surface_key": "real_workspace_soak_monitor",
        "surface": "real_workspace_soak_monitor",
        "label": "Real Workspace Soak Monitor",
        "path": real_workspace_soak_monitor.MONITOR_REF,
        "required_for_ready": True,
        "next_action_summary": "运行只读真实 workspace soak monitor 并补齐 blocked/partial 缺口。",
        "validator": _validate_real_workspace_soak_monitor,
    },
)


def _spec_by_key(surface_key: str) -> dict[str, Any]:
    for spec in CAPABILITY_SPECS:
        if spec["surface_key"] == surface_key:
            return spec
    raise ValueError(f"unsupported medical paper readiness surface: {surface_key}")


def stable_medical_paper_readiness_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / READINESS_ROOT / "readiness.json").resolve()


def stable_capability_surface_path(*, study_root: Path, surface_key: str) -> Path:
    spec = _spec_by_key(surface_key)
    return (Path(study_root).expanduser().resolve() / spec["path"]).resolve()


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_materialized_payload(
    *,
    surface_key: str,
    payload: Mapping[str, Any],
    status: str,
    missing_reason: str,
) -> dict[str, Any]:
    spec = _spec_by_key(surface_key)
    return {
        "surface": spec["surface"],
        "schema_version": SCHEMA_VERSION,
        "surface_key": surface_key,
        "status": status,
        "missing_reason": missing_reason,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        **dict(payload),
    }


def materialize_medical_paper_readiness_surface(
    *,
    study_root: Path,
    surface_key: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    spec = _spec_by_key(surface_key)
    validator: CapabilityValidator = spec["validator"]
    status, missing_reason = validator(payload)
    normalized = _normalize_materialized_payload(
        surface_key=surface_key,
        payload=payload,
        status=status,
        missing_reason=missing_reason,
    )
    path = stable_capability_surface_path(study_root=study_root, surface_key=surface_key)
    _write_json(path, normalized)
    return {
        "surface": spec["surface"],
        "surface_key": surface_key,
        "status": status,
        "missing_reason": missing_reason,
        "artifact_path": str(path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _surface_payload(*, study_root: Path, surface_key: str) -> Mapping[str, Any]:
    if surface_key == "literature_scout":
        return _literature_scout_payload(study_root=study_root)
    if surface_key == "study_line_selection":
        return _study_line_payload(study_root=study_root)
    if surface_key == "real_study_soak_matrix_evidence":
        return _soak_matrix_payload(study_root=study_root)
    return _read_json(stable_capability_surface_path(study_root=study_root, surface_key=surface_key))


def _surface_evidence_refs(*, study_root: Path, surface_key: str, fallback_path: Path) -> list[str]:
    if surface_key == "literature_scout":
        path = literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root)
        if path.is_file():
            return [str(path)]
    if surface_key == "study_line_selection":
        path = study_line_decision_engine.stable_study_line_decision_path(study_root=study_root)
        if path.is_file():
            return [str(path)]
    return [str(fallback_path)]


def _capability_status(*, study_root: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    surface_key = str(spec["surface_key"])
    path = stable_capability_surface_path(study_root=study_root, surface_key=surface_key)
    payload = _surface_payload(study_root=study_root, surface_key=surface_key)
    if not payload:
        return {
            "surface_key": surface_key,
            "surface": spec["surface"],
            "label": spec["label"],
            "status": "missing",
            "artifact_path": str(path),
            "evidence_refs": [],
            "missing_reason": "missing_canonical_artifact",
            "required_for_ready": bool(spec["required_for_ready"]),
        }

    validator: CapabilityValidator = spec["validator"]
    status, missing_reason = validator(payload)
    result = {
        "surface_key": surface_key,
        "surface": spec["surface"],
        "label": spec["label"],
        "status": status,
        "artifact_path": str(path),
        "evidence_refs": _surface_evidence_refs(study_root=study_root, surface_key=surface_key, fallback_path=path),
        "missing_reason": missing_reason,
        "required_for_ready": bool(spec["required_for_ready"]),
    }
    missing_stage_gaps = payload.get("missing_stage_gaps")
    if isinstance(missing_stage_gaps, list):
        result["missing_stage_gaps"] = [
            dict(item)
            for item in missing_stage_gaps
            if isinstance(item, Mapping)
        ]
    return result


def _overall_status(capability_surfaces: list[Mapping[str, Any]]) -> str:
    required = [item for item in capability_surfaces if item.get("required_for_ready")]
    if required and all(item.get("status") == "present" for item in required):
        return "ready"
    if any(item.get("status") == "present" for item in required):
        return "blocked"
    return "missing"


def _next_action(capability_surfaces: list[Mapping[str, Any]]) -> dict[str, Any]:
    for item in capability_surfaces:
        if not item.get("required_for_ready") or item.get("status") == "present":
            continue
        spec = _spec_by_key(str(item.get("surface_key")))
        return {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": item["surface_key"],
            "summary": spec["next_action_summary"],
        }
    return {
        "action_id": "continue_managed_execution",
        "surface_key": None,
        "summary": "自动医学论文能力闭环已具备可见 readiness surface，可继续托管执行。",
    }


def build_medical_paper_readiness_surface(*, study_root: Path) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    capability_surfaces = [
        _capability_status(study_root=root, spec=spec)
        for spec in CAPABILITY_SPECS
    ]
    ready_count = sum(1 for item in capability_surfaces if item["status"] == "present")
    payload = {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_root": str(root),
        "overall_status": _overall_status(capability_surfaces),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": ready_count,
        "required_count": len(capability_surfaces),
        "capability_surfaces": capability_surfaces,
        "next_action": _next_action(capability_surfaces),
    }
    _write_json(stable_medical_paper_readiness_path(study_root=root), payload)
    return payload


def read_medical_paper_readiness_surface(*, study_root: Path) -> dict[str, Any]:
    return dict(_read_json(stable_medical_paper_readiness_path(study_root=study_root)))

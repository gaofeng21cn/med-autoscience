from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.controllers import literature_provider_runtime
from med_autoscience.controllers import medical_paper_readiness
from med_autoscience.controllers import real_workspace_soak_monitor
from med_autoscience.controllers import revision_rebuttal_loop
from med_autoscience.controllers import route_control_stoploss
from med_autoscience.controllers import route_decision_orchestrator
from med_autoscience.controllers import statistical_discipline_runtime
from med_autoscience.controllers import study_line_decision_engine
from med_autoscience.controllers.ai_reviewer_journal_loop import build_authoring_runtime_authorization


SCHEMA_VERSION = 1
SURFACE = "medical_paper_v2_materializers"
MEDICAL_PAPER_ROOT = Path("artifacts/medical_paper")


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _surface_path(*, study_root: Path, surface_key: str) -> Path:
    return (Path(study_root).expanduser().resolve() / MEDICAL_PAPER_ROOT / f"{surface_key}.json").resolve()


def _result(
    *,
    surface_key: str,
    status: str,
    artifact_path: Path | str,
    missing_reason: str = "",
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "surface_key": surface_key,
        "status": status,
        "missing_reason": missing_reason,
        "artifact_path": str(artifact_path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "payload": dict(payload or {}),
    }


def _materialize_literature_provider_runtime(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        return _result(
            surface_key="literature_provider_runtime",
            status="present" if _text(payload.get("status")) == "ready" else "blocked",
            missing_reason="" if _text(payload.get("status")) == "ready" else "literature_provider_runtime_not_ready",
            artifact_path=Path(study_root).expanduser().resolve() / literature_provider_runtime.ARTIFACT_RELATIVE_PATH,
            payload=payload,
        )
    result = literature_provider_runtime.materialize_literature_provider_runtime(
        study_root=study_root,
        payload=payload,
    )
    return _result(
        surface_key="literature_provider_runtime",
        status=_text(result.get("status")) or "blocked",
        missing_reason=_text(result.get("missing_reason")),
        artifact_path=_text(result.get("artifact_path")),
        payload=result,
    )


def _materialize_study_line_selection(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    path = study_line_decision_engine.stable_study_line_decision_path(study_root=study_root)
    if apply:
        _write_json(path, payload)
    blockers = payload.get("blockers") if isinstance(payload.get("blockers"), list) else []
    first = blockers[0] if blockers else {}
    missing_reason = _text(first.get("code")) if isinstance(first, Mapping) else _text(first)
    return _result(
        surface_key="study_line_selection",
        status="present" if _text(payload.get("status")) == "selected" else "blocked",
        missing_reason=missing_reason,
        artifact_path=path,
        payload=payload,
    )


def _materialize_archetype_analysis_contract(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        path = medical_paper_readiness.stable_capability_surface_path(
            study_root=study_root,
            surface_key="archetype_analysis_contract",
        )
        status, missing_reason = medical_paper_readiness._validate_analysis_contract(payload)
        return _result(
            surface_key="archetype_analysis_contract",
            status=status,
            missing_reason=missing_reason,
            artifact_path=path,
            payload=payload,
        )
    result = medical_paper_readiness.materialize_medical_paper_readiness_surface(
        study_root=study_root,
        surface_key="archetype_analysis_contract",
        payload=payload,
    )
    return _result(
        surface_key="archetype_analysis_contract",
        status=_text(result.get("status")) or "blocked",
        missing_reason=_text(result.get("missing_reason")),
        artifact_path=_text(result.get("artifact_path")),
        payload=payload,
    )


def _materialize_bounded_analysis_candidate_board(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    path = medical_paper_readiness.stable_capability_surface_path(
        study_root=study_root,
        surface_key="bounded_analysis_candidate_board",
    )
    if not apply:
        status, missing_reason = medical_paper_readiness._validate_bounded_board(payload)
        return _result(
            surface_key="bounded_analysis_candidate_board",
            status=status,
            missing_reason=missing_reason,
            artifact_path=path,
            payload=payload,
        )
    result = medical_paper_readiness.materialize_medical_paper_readiness_surface(
        study_root=study_root,
        surface_key="bounded_analysis_candidate_board",
        payload=payload,
    )
    return _result(
        surface_key="bounded_analysis_candidate_board",
        status=_text(result.get("status")) or "blocked",
        missing_reason=_text(result.get("missing_reason")),
        artifact_path=_text(result.get("artifact_path")) or path,
        payload=payload,
    )


def _materialize_stop_loss_memo(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    path = Path(study_root).expanduser().resolve() / route_control_stoploss.STOP_LOSS_MEMO_PATH
    route_payload = {
        key: value
        for key, value in dict(payload).items()
        if key
        not in {
            "payload_source",
            "source_basis",
            "source_refs",
            "quality_claim_authorized",
            "mechanical_projection_can_authorize_quality",
        }
    }
    if not apply:
        memo = route_control_stoploss.build_route_control_stoploss_memo(**route_payload)
        status, missing_reason = medical_paper_readiness._validate_stop_loss_memo(memo)
        return _result(
            surface_key="stop_loss_memo",
            status=status,
            missing_reason=missing_reason,
            artifact_path=path,
            payload=memo,
        )
    result = route_control_stoploss.materialize_route_control_stoploss_memo(
        root=study_root,
        **route_payload,
    )
    memo_payload = _mapping(result.get("stop_loss_memo")) or result
    status, missing_reason = medical_paper_readiness._validate_stop_loss_memo(memo_payload)
    return _result(
        surface_key="stop_loss_memo",
        status=status,
        missing_reason=missing_reason,
        artifact_path=path,
        payload=memo_payload,
    )


def _materialize_route_decision_orchestrator(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    projection = route_decision_orchestrator.materialize_route_decision_orchestration(
        study_root=study_root,
        candidates=[
            item for item in payload.get("candidates") or []
            if isinstance(item, Mapping)
        ],
        requested_action=_text(payload.get("requested_action")) or "select_line",
        readiness=_mapping(payload.get("readiness")),
        alternative_line_id=_text(payload.get("alternative_line_id")) or None,
    )
    path = _surface_path(study_root=study_root, surface_key="route_decision_orchestrator")
    if apply:
        _write_json(path, projection)
    blockers = projection.get("blockers") if isinstance(projection.get("blockers"), list) else []
    missing_reason = _text(blockers[0]) if blockers else ""
    return _result(
        surface_key="route_decision_orchestrator",
        status=_text(projection.get("status")) or "blocked",
        missing_reason=missing_reason,
        artifact_path=path,
        payload=projection,
    )


def _materialize_statistical_discipline_operations(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    projection = statistical_discipline_runtime.build_statistical_discipline_operations_projection(
        _mapping(payload.get("contract")) or payload,
        bounded_board=_mapping(payload.get("bounded_board")),
    )
    path = _surface_path(study_root=study_root, surface_key="statistical_discipline_operations")
    if apply:
        _write_json(path, projection)
    blockers = projection.get("blockers") if isinstance(projection.get("blockers"), list) else []
    first = blockers[0] if blockers else {}
    missing_reason = _text(first.get("reason_code")) if isinstance(first, Mapping) else _text(first)
    return _result(
        surface_key="statistical_discipline_operations",
        status=_text(projection.get("status")) or "blocked",
        missing_reason=missing_reason,
        artifact_path=path,
        payload=projection,
    )


def _materialize_revision_rebuttal_loop(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        return _result(
            surface_key="revision_rebuttal_loop",
            status="ready" if _text(payload.get("status")) == "ready" else "blocked",
            missing_reason="" if _text(payload.get("status")) == "ready" else "revision_rebuttal_loop_not_ready",
            artifact_path=Path(study_root).expanduser().resolve() / revision_rebuttal_loop.ARTIFACT_RELATIVE_PATH,
            payload=payload,
        )
    result = revision_rebuttal_loop.materialize_revision_rebuttal_loop(study_root, payload)
    path = _text(result.get("artifact_path"))
    persisted = _read_json(Path(path)) if path else {}
    blockers = persisted.get("blockers") if isinstance(persisted.get("blockers"), list) else []
    return _result(
        surface_key="revision_rebuttal_loop",
        status=_text(result.get("status")) or "blocked",
        missing_reason=_text(blockers[0]) if blockers else "",
        artifact_path=path,
        payload=persisted or result,
    )


def _materialize_authoring_runtime_authorization(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    projection = build_authoring_runtime_authorization(**dict(payload))
    path = _surface_path(study_root=study_root, surface_key="authoring_runtime_authorization")
    if apply:
        _write_json(path, projection)
    blockers = projection.get("blockers") if isinstance(projection.get("blockers"), list) else []
    status = "ready" if projection.get("full_drafting_authorized") is True else "blocked"
    return _result(
        surface_key="authoring_runtime_authorization",
        status=status,
        missing_reason=_text(blockers[0]) if blockers else "",
        artifact_path=path,
        payload=projection,
    )


def _materialize_real_workspace_soak_monitor(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        return _result(
            surface_key="real_workspace_soak_monitor",
            status="ready" if _text(payload.get("overall_status")) == "ready" else _text(payload.get("overall_status")) or "blocked",
            missing_reason="" if _text(payload.get("overall_status")) == "ready" else _text(payload.get("next_action")),
            artifact_path=Path(study_root).expanduser().resolve() / real_workspace_soak_monitor.MONITOR_REF,
            payload=payload,
        )
    study_roots = payload.get("study_roots")
    roots = [Path(item) for item in study_roots] if isinstance(study_roots, list) and study_roots else [study_root]
    result = real_workspace_soak_monitor.materialize_real_workspace_soak_monitor(study_roots=roots)
    return _result(
        surface_key="real_workspace_soak_monitor",
        status="ready" if _text(result.get("overall_status")) == "ready" else _text(result.get("overall_status")) or "blocked",
        missing_reason="" if _text(result.get("overall_status")) == "ready" else _text(result.get("next_action")),
        artifact_path=_text(result.get("artifact_path")),
        payload=result,
    )


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


MATERIALIZERS: dict[str, Callable[..., dict[str, Any]]] = {
    "literature_provider_runtime": _materialize_literature_provider_runtime,
    "study_line_selection": _materialize_study_line_selection,
    "archetype_analysis_contract": _materialize_archetype_analysis_contract,
    "bounded_analysis_candidate_board": _materialize_bounded_analysis_candidate_board,
    "stop_loss_memo": _materialize_stop_loss_memo,
    "route_decision_orchestrator": _materialize_route_decision_orchestrator,
    "statistical_discipline_operations": _materialize_statistical_discipline_operations,
    "revision_rebuttal_loop": _materialize_revision_rebuttal_loop,
    "authoring_runtime_authorization": _materialize_authoring_runtime_authorization,
    "real_workspace_soak_monitor": _materialize_real_workspace_soak_monitor,
}


def materialize_medical_paper_v2_surface(
    *,
    study_root: Path,
    surface_key: str,
    payload: Mapping[str, Any],
    apply: bool = True,
) -> dict[str, Any]:
    materializer = MATERIALIZERS.get(surface_key)
    if materializer is None:
        return _result(
            surface_key=surface_key,
            status="blocked",
            missing_reason=f"unsupported_surface_{surface_key}",
            artifact_path="",
        )
    result = materializer(
        study_root=Path(study_root).expanduser().resolve(),
        payload=payload,
        apply=apply,
    )
    result["dry_run"] = not apply
    result["quality_claim_authorized"] = False
    result["mechanical_projection_can_authorize_quality"] = False
    return result

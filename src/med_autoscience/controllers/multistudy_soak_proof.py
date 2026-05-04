from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "multistudy_soak_proof_projection"
READ_MODEL = "multistudy_soak_matrix_read_model"

REQUIRED_ARCHETYPES = (
    "prediction_model/external_validation",
    "observational_real_world",
    "subtype_or_triage",
)
REQUIRED_STAGES = (
    "literature_scout",
    "line_selection",
    "baseline",
    "primary_analysis",
    "bounded_analysis",
    "route_back",
    "stop_loss",
    "revision_reopen",
    "runtime_recovery",
    "finalize_rebuild",
    "final_pre_submission_audit",
)
BLOCKING_GAPS = {"literature_contract", "statistical_contract", "external_validation_fixture"}
WEAK_RESULT_ALLOWED_ACTIONS = {"stop_loss", "switch_line"}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _text(value: object, default: str = "unknown") -> str:
    text = str(value or "").strip()
    return text or default


def _bool(value: object) -> bool:
    return value is True


def _optional_bool(value: object) -> bool | None:
    if value is True:
        return True
    if value is False:
        return False
    return None


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_read_model_only",
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "can_mutate_runtime": False,
        "read_model_is_quality_authority": False,
    }


def _read_only_monitor_contract() -> dict[str, Any]:
    return {
        "read_model": READ_MODEL,
        "writes_runtime_owned_surfaces": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def _stage_set(study: Mapping[str, Any]) -> set[str]:
    stages = study.get("stages")
    if isinstance(stages, Mapping):
        return {str(stage) for stage, state in stages.items() if state not in {False, None, "missing"}}
    return {str(stage) for stage in _sequence(stages)}


def _contract_present(study: Mapping[str, Any], key: str) -> bool:
    contracts = _mapping(study.get("contracts"))
    fixtures = _mapping(study.get("fixtures"))
    if key in study:
        return _bool(study.get(key))
    if key in contracts:
        return _bool(contracts.get(key))
    return _bool(fixtures.get(key))


def _required_contracts(study_archetype: str) -> tuple[str, ...]:
    contracts = ["literature_contract", "statistical_contract"]
    if study_archetype == "prediction_model/external_validation":
        contracts.append("external_validation_fixture")
    return tuple(contracts)


def _result_strength(study: Mapping[str, Any]) -> str:
    result = _mapping(study.get("result"))
    return _text(study.get("result_strength") or result.get("strength"), "adequate")


def _route_mapping(study: Mapping[str, Any]) -> Mapping[str, Any]:
    route_decision = _mapping(study.get("route_decision"))
    if route_decision:
        return route_decision
    return _mapping(study.get("route"))


def _route_action(study: Mapping[str, Any]) -> str:
    route = _route_mapping(study)
    return _text(route.get("action") or study.get("route_action"), "continue")


def _route_reason(study: Mapping[str, Any]) -> str:
    route = _route_mapping(study)
    return _text(
        study.get("route_reason")
        or study.get("route_decision_reason")
        or route.get("reason")
        or route.get("decision_reason"),
        "",
    )


def _readiness_mapping(study: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(study.get("readiness"))


def _previous_readiness_status(study: Mapping[str, Any]) -> str:
    readiness = _readiness_mapping(study)
    return _text(
        study.get("previous_readiness_status")
        or study.get("last_readiness_status")
        or readiness.get("previous_overall_status"),
        "",
    )


def _readiness_status(study: Mapping[str, Any]) -> str:
    readiness = _readiness_mapping(study)
    return _text(
        study.get("readiness_status")
        or study.get("current_readiness_status")
        or readiness.get("overall_status"),
        "",
    )


def _blocked_reason(study: Mapping[str, Any]) -> str:
    readiness = _readiness_mapping(study)
    reasons = study.get("blocked_reasons") or readiness.get("blocked_reasons")
    if isinstance(reasons, list | tuple) and reasons:
        return "; ".join(_text(reason, "") for reason in reasons if _text(reason, ""))
    return _text(
        study.get("blocked_reason")
        or study.get("blocked_reason_summary")
        or readiness.get("blocked_reason")
        or readiness.get("missing_reason"),
        "",
    )


def _observed_bool(study: Mapping[str, Any], key: str) -> bool:
    explicit = _optional_bool(study.get(key))
    if explicit is not None:
        return explicit
    if key == "stop_loss_triggered":
        return _route_action(study) == "stop_loss"
    stage_by_key = {
        "revision_reopen_seen": "revision_reopen",
        "runtime_recovery_seen": "runtime_recovery",
        "finalize_rebuild_seen": "finalize_rebuild",
    }
    stage = stage_by_key.get(key, "")
    return bool(stage and stage in _stage_set(study))


def _readiness_observation(study: Mapping[str, Any]) -> dict[str, Any]:
    previous = _previous_readiness_status(study)
    current = _readiness_status(study)
    return {
        "previous_status": previous,
        "current_status": current,
        "drift": f"{previous}->{current}" if previous and current and previous != current else "",
        "last_green_at": _text(study.get("last_green_at"), ""),
        "last_green_scan_id": _text(study.get("last_green_scan_id"), ""),
        "blocked_reason": _blocked_reason(study),
    }


def _route_decision_observation(study: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "action": _route_action(study),
        "reason": _route_reason(study),
        "result_strength": _result_strength(study),
        "stop_loss_triggered": _observed_bool(study, "stop_loss_triggered"),
    }


def _proof_observation(study: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "revision_reopen_seen": _observed_bool(study, "revision_reopen_seen"),
        "runtime_recovery_seen": _observed_bool(study, "runtime_recovery_seen"),
        "finalize_rebuild_seen": _observed_bool(study, "finalize_rebuild_seen"),
    }


def _missing_gaps(study: Mapping[str, Any]) -> list[str]:
    study_archetype = _text(study.get("study_archetype"))
    present_stages = _stage_set(study)
    gaps = [f"stage:{stage}" for stage in REQUIRED_STAGES if stage not in present_stages]
    gaps.extend(
        f"contract:{contract}"
        for contract in _required_contracts(study_archetype)
        if not _contract_present(study, contract)
    )
    if study_archetype not in REQUIRED_ARCHETYPES:
        gaps.append("archetype:unsupported")
    if _result_strength(study) == "weak" and _route_action(study) not in WEAK_RESULT_ALLOWED_ACTIONS:
        gaps.append("route:weak_result_requires_stop_loss_or_switch_line")
    return gaps


def _blocking_gaps(gaps: Iterable[str]) -> list[str]:
    blocked: list[str] = []
    for gap in gaps:
        kind, _, name = gap.partition(":")
        if kind == "contract" and name in BLOCKING_GAPS:
            blocked.append(gap)
        elif gap == "archetype:unsupported":
            blocked.append(gap)
        elif gap == "route:weak_result_requires_stop_loss_or_switch_line":
            blocked.append(gap)
    return blocked


def _study_status(*, gaps: Sequence[str], blocking_gaps: Sequence[str]) -> str:
    if blocking_gaps:
        return "blocked"
    if gaps:
        return "partial"
    return "ready"


def _study_next_action(
    *,
    study: Mapping[str, Any],
    status: str,
    gaps: Sequence[str],
    blocking_gaps: Sequence[str],
) -> str:
    if _result_strength(study) == "weak" and _route_action(study) in WEAK_RESULT_ALLOWED_ACTIONS:
        return _route_action(study)
    if blocking_gaps:
        first = blocking_gaps[0].removeprefix("contract:").replace(":", "_")
        return f"materialize_{first}"
    if gaps:
        first = gaps[0].replace(":", "_")
        return f"complete_{first}"
    if status == "ready":
        return "continue_multistudy_soak"
    return "review_multistudy_soak_gaps"


def _build_study_projection(study: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _text(study.get("study_id"))
    study_archetype = _text(study.get("study_archetype"))
    present_stages = sorted(_stage_set(study))
    gaps = _missing_gaps(study)
    blocked = _blocking_gaps(gaps)
    status = _study_status(gaps=gaps, blocking_gaps=blocked)
    next_action = _study_next_action(
        study=study,
        status=status,
        gaps=gaps,
        blocking_gaps=blocked,
    )
    return {
        "study_id": study_id,
        "study_archetype": study_archetype,
        "status": status,
        "present_stages": present_stages,
        "required_stages": list(REQUIRED_STAGES),
        "missing_gaps": gaps,
        "blocking_gaps": blocked,
        "result_strength": _result_strength(study),
        "route_action": _route_action(study),
        "readiness_observation": _readiness_observation(study),
        "route_decision": _route_decision_observation(study),
        "proof_observation": _proof_observation(study),
        "next_action": next_action,
        "authority_contract": _authority_contract(),
    }


def _coverage_manifest(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "required_archetypes": list(REQUIRED_ARCHETYPES),
        "covered_archetypes": sorted(
            {
                _text(study.get("study_archetype"))
                for study in studies
                if _text(study.get("study_id")) != "multistudy_matrix"
            }
        ),
        "required_stages": list(REQUIRED_STAGES),
        "covered_stage_matrix": {
            _text(study.get("study_id")): [
                stage
                for stage in REQUIRED_STAGES
                if stage in set(str(item) for item in _sequence(study.get("present_stages")))
            ]
            for study in studies
            if _text(study.get("study_id")) != "multistudy_matrix"
        },
    }


def _overall_status(studies: Sequence[Mapping[str, Any]]) -> str:
    statuses = {_text(study.get("status")) for study in studies}
    if "blocked" in statuses:
        return "blocked"
    if statuses == {"ready"}:
        return "ready"
    return "partial"


def _overall_next_action(*, status: str, studies: Sequence[Mapping[str, Any]]) -> str:
    if status == "ready":
        return "continue_multistudy_soak"
    for study in studies:
        if study.get("status") == "blocked":
            return _text(study.get("next_action"), "resolve_blocking_gap")
    for study in studies:
        if study.get("status") == "partial":
            return _text(study.get("next_action"), "complete_missing_gap")
    return "review_multistudy_soak_gaps"


def build_multistudy_soak_matrix_projection(
    studies: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    study_items = [_build_study_projection(study) for study in studies]
    covered_archetypes = sorted({study["study_archetype"] for study in study_items})
    missing_archetypes = [
        archetype for archetype in REQUIRED_ARCHETYPES if archetype not in covered_archetypes
    ]
    if missing_archetypes:
        synthetic_gap_item = {
            "study_id": "multistudy_matrix",
            "study_archetype": "matrix_coverage",
            "status": "partial",
            "present_stages": [],
            "required_stages": list(REQUIRED_STAGES),
            "missing_gaps": [f"archetype:{archetype}" for archetype in missing_archetypes],
            "blocking_gaps": [],
            "result_strength": "unknown",
            "route_action": "continue",
            "next_action": "add_missing_study_archetype_fixture",
            "authority_contract": _authority_contract(),
        }
        study_items.append(synthetic_gap_item)
    status = _overall_status(study_items)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "overall_status": status,
        "next_action": _overall_next_action(status=status, studies=study_items),
        "required_archetypes": list(REQUIRED_ARCHETYPES),
        "covered_archetypes": covered_archetypes,
        "missing_archetypes": missing_archetypes,
        "required_stages": list(REQUIRED_STAGES),
        "coverage_manifest": _coverage_manifest(study_items),
        "studies": study_items,
        "authority_contract": _authority_contract(),
        "read_only_monitor_contract": _read_only_monitor_contract(),
    }

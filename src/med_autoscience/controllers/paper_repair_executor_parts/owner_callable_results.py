from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    has_opl_transition_readback,
)
from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    first_trusted_opl_execution_authorization,
)


def owner_result_executed(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> bool:
    if owner_result_handoff_ready(
        owner_result,
        opl_execution_authorization=opl_execution_authorization,
    ):
        return True
    if owner_result_contains_unproven_handoff(
        owner_result,
        opl_execution_authorization=opl_execution_authorization,
    ):
        return False
    if _owner_result_has_blocker(owner_result):
        return False
    if owner_result.get("ok") is False:
        return False
    if owner_result.get("ok") is True:
        return True
    if _text(owner_result.get("status")) in {"executed", "skipped_duplicate_eval"}:
        return True
    if int(owner_result.get("executed_count") or 0) > 0 and int(owner_result.get("blocked_count") or 0) == 0:
        return True
    return False


def owner_result_handoff_ready(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> bool:
    if _text(owner_result.get("status")) != "handoff_ready":
        executions = _executions(owner_result)
        return any(
            _text(execution.get("execution_status")) == "handoff_ready"
            and ai_reviewer_record_worker_handoff_ready(
                execution,
                opl_execution_authorization=opl_execution_authorization,
            )
            for execution in executions
        )
    return writer_worker_handoff_ready(
        owner_result,
        opl_execution_authorization=opl_execution_authorization,
    ) or ai_reviewer_record_worker_handoff_ready(
        owner_result,
        opl_execution_authorization=opl_execution_authorization,
    )


def writer_worker_handoff_ready(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> bool:
    handoff = _mapping(owner_result.get("writer_worker_handoff"))
    return (
        _text(handoff.get("surface")) == "default_executor_dispatch_request"
        and _text(handoff.get("dispatch_status")) == "ready"
        and _text(handoff.get("next_executable_owner")) == "write"
        and _handoff_has_opl_proof(handoff, owner_result, opl_execution_authorization=opl_execution_authorization)
    )


def ai_reviewer_record_worker_handoff_ready(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> bool:
    handoff = _mapping(owner_result.get("ai_reviewer_record_worker_handoff"))
    return (
        _text(handoff.get("surface")) == "default_executor_dispatch_request"
        and _text(handoff.get("dispatch_status")) == "ready"
        and _text(handoff.get("dispatch_authority")) == "ai_reviewer_record_production_handoff"
        and _text(handoff.get("next_executable_owner")) == "ai_reviewer"
        and _handoff_has_opl_proof(handoff, owner_result, opl_execution_authorization=opl_execution_authorization)
    )


def owner_result_blocker(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> str:
    if owner_result_contains_unproven_handoff(
        owner_result,
        opl_execution_authorization=opl_execution_authorization,
    ):
        return OPL_EXECUTION_AUTHORIZATION_BLOCKER
    for execution in owner_result.get("executions") or ():
        if not isinstance(execution, Mapping):
            continue
        if reason := _text(execution.get("blocked_reason")):
            return reason
        if _text(execution.get("execution_status")) == "repeat_suppressed":
            return "repeat_suppressed"
        if why_not_applied := _text(execution.get("why_not_applied")):
            return why_not_applied
    if int(owner_result.get("repeat_suppressed_count") or 0) > 0:
        return "repeat_suppressed"
    if blocker := _first_blocker(owner_result):
        return blocker
    evidence = _mapping(owner_result.get("repair_execution_evidence"))
    if blocker := _first_blocker(evidence):
        return blocker
    manuscript_hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    if blocker := _first_blocker(manuscript_hygiene):
        return blocker
    artifact_delta = _mapping(evidence.get("canonical_artifact_delta"))
    if _text(artifact_delta.get("status")) == "blocked":
        return "canonical_artifact_delta_blocked"
    if (
        artifact_delta.get("meaningful_artifact_delta") is False
        and manuscript_hygiene.get("story_surface_delta_required") is True
        and manuscript_hygiene.get("story_surface_delta_present") is False
    ):
        return "manuscript_story_surface_delta_missing"
    return (
        _text(owner_result.get("blocked_reason"))
        or _text(owner_result.get("reason"))
        or "owner_callable_surface_blocked"
    )


def ai_reviewer_record_worker_handoff(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    if ai_reviewer_record_worker_handoff_ready(
        owner_result,
        opl_execution_authorization=opl_execution_authorization,
    ):
        return _mapping(owner_result.get("ai_reviewer_record_worker_handoff"))
    for execution in _executions(owner_result):
        if (
            _text(execution.get("execution_status")) == "handoff_ready"
            and ai_reviewer_record_worker_handoff_ready(
                execution,
                opl_execution_authorization=opl_execution_authorization,
            )
        ):
            return _mapping(execution.get("ai_reviewer_record_worker_handoff"))
    return {}


def writer_worker_handoff(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    if writer_worker_handoff_ready(
        owner_result,
        opl_execution_authorization=opl_execution_authorization,
    ):
        return _mapping(owner_result.get("writer_worker_handoff"))
    return {}


def owner_result_contains_unproven_handoff(
    owner_result: Mapping[str, Any],
    *,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> bool:
    if _text(owner_result.get("status")) == "handoff_ready" and _raw_writer_worker_handoff_ready(owner_result):
        handoff = _mapping(owner_result.get("writer_worker_handoff"))
        return not _handoff_has_opl_proof(
            handoff,
            owner_result,
            opl_execution_authorization=opl_execution_authorization,
        )
    if _text(owner_result.get("status")) == "handoff_ready" and _raw_ai_reviewer_record_worker_handoff_ready(owner_result):
        handoff = _mapping(owner_result.get("ai_reviewer_record_worker_handoff"))
        return not _handoff_has_opl_proof(
            handoff,
            owner_result,
            opl_execution_authorization=opl_execution_authorization,
        )
    for execution in _executions(owner_result):
        if (
            _text(execution.get("execution_status")) == "handoff_ready"
            and _raw_ai_reviewer_record_worker_handoff_ready(execution)
        ):
            handoff = _mapping(execution.get("ai_reviewer_record_worker_handoff"))
            if not _handoff_has_opl_proof(
                handoff,
                execution,
                owner_result,
                opl_execution_authorization=opl_execution_authorization,
            ):
                return True
    return False


def evidence_path(*, study_root: Path, owner_result: Mapping[str, Any]) -> Path:
    if evidence_path_text := _text(owner_result.get("repair_execution_evidence_path")):
        return Path(evidence_path_text).expanduser().resolve()
    return study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"


def changed_refs(owner_result: Mapping[str, Any]) -> list[dict[str, str]]:
    refs = _mapping(owner_result.get("repair_execution_evidence")).get("changed_artifact_refs")
    if not isinstance(refs, list):
        return []
    changed: list[dict[str, str]] = []
    for ref in refs:
        path = _text(_mapping(ref).get("path")) or _text(ref)
        if path:
            changed.append({"path": path, "artifact_role": _text(_mapping(ref).get("artifact_role")) or "canonical_paper_artifact"})
    return changed


def _executions(owner_result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    value = owner_result.get("executions")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _raw_writer_worker_handoff_ready(owner_result: Mapping[str, Any]) -> bool:
    handoff = _mapping(owner_result.get("writer_worker_handoff"))
    return (
        _text(handoff.get("surface")) == "default_executor_dispatch_request"
        and _text(handoff.get("dispatch_status")) == "ready"
        and _text(handoff.get("next_executable_owner")) == "write"
    )


def _raw_ai_reviewer_record_worker_handoff_ready(owner_result: Mapping[str, Any]) -> bool:
    handoff = _mapping(owner_result.get("ai_reviewer_record_worker_handoff"))
    return (
        _text(handoff.get("surface")) == "default_executor_dispatch_request"
        and _text(handoff.get("dispatch_status")) == "ready"
        and _text(handoff.get("dispatch_authority")) == "ai_reviewer_record_production_handoff"
        and _text(handoff.get("next_executable_owner")) == "ai_reviewer"
    )


def _handoff_has_opl_proof(
    *payloads: Mapping[str, Any],
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> bool:
    if has_opl_transition_readback({"opl_runtime_result": opl_execution_authorization or {}}):
        return True
    if first_trusted_opl_execution_authorization(opl_execution_authorization) is not None:
        return True
    for payload in payloads:
        if has_opl_transition_readback(payload):
            return True
        prompt_contract = _mapping(payload.get("prompt_contract"))
        owner_route = _mapping(payload.get("owner_route"))
        if first_trusted_opl_execution_authorization(
            payload.get("opl_execution_authorization"),
            payload.get("opl_provider_attempt"),
            prompt_contract.get("opl_execution_authorization"),
            prompt_contract.get("opl_provider_attempt"),
            owner_route.get("opl_execution_authorization"),
            owner_route.get("opl_provider_attempt"),
        ) is not None:
            return True
    return False


def _owner_result_has_blocker(owner_result: Mapping[str, Any]) -> bool:
    if _text(owner_result.get("status")) == "blocked":
        return True
    if _blockers(owner_result):
        return True
    evidence = _mapping(owner_result.get("repair_execution_evidence"))
    if not evidence:
        return False
    if _text(evidence.get("status")) == "blocked":
        return True
    if _blockers(evidence):
        return True
    artifact_delta = _mapping(evidence.get("canonical_artifact_delta"))
    if _text(artifact_delta.get("status")) == "blocked":
        return True
    manuscript_hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    if _text(manuscript_hygiene.get("status")) == "blocked":
        return True
    if _blockers(manuscript_hygiene):
        return True
    return (
        artifact_delta.get("meaningful_artifact_delta") is False
        and manuscript_hygiene.get("story_surface_delta_required") is True
        and manuscript_hygiene.get("story_surface_delta_present") is False
    )


def _first_blocker(value: Mapping[str, Any]) -> str | None:
    if blocker := _blockers(value):
        return blocker[0]
    return _text(value.get("blocked_reason")) or _text(value.get("reason"))


def _blockers(value: Mapping[str, Any]) -> list[str]:
    blockers = value.get("blockers")
    if not isinstance(blockers, list):
        return []
    return [blocker for blocker in (_text(item) for item in blockers) if blocker]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ai_reviewer_record_worker_handoff",
    "ai_reviewer_record_worker_handoff_ready",
    "changed_refs",
    "evidence_path",
    "owner_result_contains_unproven_handoff",
    "owner_result_blocker",
    "owner_result_executed",
    "owner_result_handoff_ready",
    "writer_worker_handoff",
    "writer_worker_handoff_ready",
]

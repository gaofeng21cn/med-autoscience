from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    first_trusted_opl_execution_authorization,
)


BlockedResultFactory = Callable[..., dict[str, Any]]


def authorized_or_blocked_result(
    *,
    explicit: Mapping[str, Any] | None,
    work_unit: Mapping[str, Any],
    authority_route_context: Mapping[str, Any] | None,
    route_context: Mapping[str, Any] | None,
    blocked_result: BlockedResultFactory,
    generated_at: str,
    study_id: str,
    quest_id: str,
    study_root: Path,
    surface: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    authorization = first_trusted_opl_execution_authorization(
        explicit,
        _mapping(work_unit.get("opl_execution_authorization")),
        _mapping(work_unit.get("opl_provider_attempt")),
        _mapping(_mapping(authority_route_context or {}).get("opl_execution_authorization")),
        _mapping(_mapping(authority_route_context or {}).get("opl_provider_attempt")),
        _mapping(_mapping(route_context or {}).get("opl_execution_authorization")),
        _mapping(_mapping(route_context or {}).get("opl_provider_attempt")),
    )
    if authorization is not None:
        return authorization, None
    return None, blocked_result(
        generated_at=generated_at,
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        work_unit=work_unit,
        review_finding={
            "surface": surface,
            "blocked_reason": OPL_EXECUTION_AUTHORIZATION_BLOCKER,
            "message": (
                "paper repair apply requires an OPL provider attempt, lease, "
                "or receipt binding; MAS only signs owner receipts or typed blockers"
            ),
        },
        typed_blocker=OPL_EXECUTION_AUTHORIZATION_BLOCKER,
        retryable=False,
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}

from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import mas_runtime_core as domain_adapter

BACKEND_ID = "opl_provider_backed_stage_runtime"
ENGINE_ID = "opl-provider-backed-stage-runtime"
DEFAULT_DAEMON_TIMEOUT_SECONDS = domain_adapter.DEFAULT_DAEMON_TIMEOUT_SECONDS
CONTROLLED_RESEARCH_BACKEND_ID = "mas_runtime_core"
CONTROLLED_RESEARCH_ENGINE_ID = "mas-runtime-core"
DELEGATED_DOMAIN_ADAPTER_ID = domain_adapter.BACKEND_ID
DELEGATED_DOMAIN_ADAPTER_ENGINE_ID = domain_adapter.ENGINE_ID


def _with_delegation_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["runtime_backend_id"] = BACKEND_ID
    result["runtime_engine_id"] = ENGINE_ID
    result["delegated_domain_adapter_id"] = DELEGATED_DOMAIN_ADAPTER_ID
    result["delegated_domain_adapter_engine_id"] = DELEGATED_DOMAIN_ADAPTER_ENGINE_ID
    result["generic_runtime_owner"] = "one-person-lab"
    result["domain_adapter_owner"] = "med-autoscience"
    result["runtime_backend_is_generic_owner"] = False
    return result


def resolve_daemon_url(*, runtime_root: Path) -> str:
    return domain_adapter.resolve_daemon_url(runtime_root=runtime_root)


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = domain_adapter.create_quest(runtime_root=runtime_root, payload=payload)
    return _with_delegation_metadata(result)


def resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return _with_delegation_metadata(domain_adapter.resume_quest(runtime_root=runtime_root, quest_id=quest_id, source=source))


def relaunch_stopped_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.relaunch_stopped_quest(runtime_root=runtime_root, quest_id=quest_id, source=source)
    )


def pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return _with_delegation_metadata(domain_adapter.pause_quest(runtime_root=runtime_root, quest_id=quest_id, source=source))


def stop_quest(
    *,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    quest_id: str,
    source: str,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.stop_quest(
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            quest_id=quest_id,
            source=source,
        )
    )


def get_quest_session(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.get_quest_session(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        )
    )


def inspect_quest_live_runtime(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.inspect_quest_live_runtime(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        )
    )


def inspect_quest_live_bash_sessions(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.inspect_quest_live_bash_sessions(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        )
    )


def inspect_quest_live_execution(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.inspect_quest_live_execution(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        )
    )


def update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any] | None = None,
    requested_baseline_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.update_quest_startup_context(
            runtime_root=runtime_root,
            quest_id=quest_id,
            startup_contract=startup_contract,
            requested_baseline_ref=requested_baseline_ref,
        )
    )


def chat_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    text: str,
    source: str,
    reply_to_interaction_id: str | None = None,
    decision_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.chat_quest(
            runtime_root=runtime_root,
            quest_id=quest_id,
            text=text,
            source=source,
            reply_to_interaction_id=reply_to_interaction_id,
            decision_response=decision_response,
        )
    )


def schedule_turn(*, runtime_root: Path, quest_id: str, reason: str, source: str) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.schedule_turn(runtime_root=runtime_root, quest_id=quest_id, reason=reason, source=source)
    )


def complete_turn_and_normalize(
    *,
    runtime_root: Path,
    quest_id: str,
    run_id: str,
    runner_status: str,
    source: str,
    blocking_decision_request: dict[str, Any] | None = None,
    same_fingerprint: bool = False,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.complete_turn_and_normalize(
            runtime_root=runtime_root,
            quest_id=quest_id,
            run_id=run_id,
            runner_status=runner_status,
            source=source,
            blocking_decision_request=blocking_decision_request,
            same_fingerprint=same_fingerprint,
        )
    )


def inspect_turn_lifecycle(*, runtime_root: Path, quest_id: str) -> dict[str, Any]:
    return _with_delegation_metadata(domain_adapter.inspect_turn_lifecycle(runtime_root=runtime_root, quest_id=quest_id))


def artifact_complete_quest(*, runtime_root: Path, quest_id: str, summary: str) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.artifact_complete_quest(runtime_root=runtime_root, quest_id=quest_id, summary=summary)
    )


def artifact_interact(*, runtime_root: Path, quest_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.artifact_interact(runtime_root=runtime_root, quest_id=quest_id, payload=payload)
    )


def inspect_terminal_attach(
    *,
    runtime_root: Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str | None = None,
    source: str,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.inspect_terminal_attach(
            runtime_root=runtime_root,
            quest_id=quest_id,
            run_id=run_id,
            study_id=study_id,
            token=token,
            source=source,
        )
    )


def attach_terminal(
    *,
    runtime_root: Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    idempotency_key: str,
    source: str,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.attach_terminal(
            runtime_root=runtime_root,
            quest_id=quest_id,
            run_id=run_id,
            study_id=study_id,
            idempotency_key=idempotency_key,
            source=source,
        )
    )


def terminal_input(
    *,
    runtime_root: Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str,
    lease_id: str,
    text: str,
    idempotency_key: str,
    source: str,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.terminal_input(
            runtime_root=runtime_root,
            quest_id=quest_id,
            run_id=run_id,
            study_id=study_id,
            token=token,
            lease_id=lease_id,
            text=text,
            idempotency_key=idempotency_key,
            source=source,
        )
    )


def resize_terminal(
    *,
    runtime_root: Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str,
    lease_id: str,
    rows: int,
    cols: int,
    idempotency_key: str,
    source: str,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.resize_terminal(
            runtime_root=runtime_root,
            quest_id=quest_id,
            run_id=run_id,
            study_id=study_id,
            token=token,
            lease_id=lease_id,
            rows=rows,
            cols=cols,
            idempotency_key=idempotency_key,
            source=source,
        )
    )


def detach_terminal(
    *,
    runtime_root: Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str,
    lease_id: str,
    idempotency_key: str,
    source: str,
) -> dict[str, Any]:
    return _with_delegation_metadata(
        domain_adapter.detach_terminal(
            runtime_root=runtime_root,
            quest_id=quest_id,
            run_id=run_id,
            study_id=study_id,
            token=token,
            lease_id=lease_id,
            idempotency_key=idempotency_key,
            source=source,
        )
    )

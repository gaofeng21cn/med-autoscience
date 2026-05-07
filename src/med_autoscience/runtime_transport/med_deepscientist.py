from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import subprocess
from typing import Any
from urllib import error, request
from urllib.parse import quote

from med_autoscience.native_runtime_event import NativeRuntimeEventRecord
from med_autoscience.runtime_event_record import RuntimeEventRecordRef
from med_autoscience.runtime_transport.med_deepscientist_parts.daemon_launcher import (
    _companion_js_launcher_path,
    _launcher_command,
    _launcher_looks_like_python_console_script,
    _launcher_requires_node,
    _read_config_env_value,
    _read_launcher_text,
    _read_optional_config_env_value,
    _repo_root_from_repo_local_venv_path,
    _resolve_launcher_node_binary,
    _resolve_launcher_path,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.daemon_lifecycle import (
    release_idle_workspace_daemon as _release_idle_workspace_daemon,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.daemon_status import (
    _daemon_state_path,
    _health_matches_runtime_state,
    _normalize_health_home,
    _parse_launcher_status,
    _recover_launcher_status_from_runtime_state as _recover_launcher_status_from_runtime_state_impl,
    ensure_managed_daemon as _ensure_managed_daemon_impl,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.http_client import (
    _daemon_url_matches_runtime_home as _daemon_url_matches_runtime_home_impl,
    _get_json as _get_json_impl,
    _normalize_local_host,
    _patch_json as _patch_json_impl,
    _post_json as _post_json_impl,
    _request_json as _request_json_impl,
    resolve_daemon_url as _resolve_daemon_url_impl,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.quest_contracts import (
    _normalize_stable_artifact_completion_result,
    _normalize_stable_bash_session_entry,
    _normalize_stable_quest_control_result,
    _normalize_stable_quest_create_result,
    _normalize_stable_quest_session,
    _normalize_stable_startup_context_result,
    _normalize_startup_contract_for_stable_transport as _normalize_startup_contract_for_stable_transport_impl,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.quest_liveness import (
    ACTIVE_BASH_SESSION_STATUSES,
    STALE_PROGRESS_SILENCE_SECONDS as _STALE_PROGRESS_SILENCE_SECONDS,
    _infer_local_runtime_liveness as _infer_local_runtime_liveness_impl,
    _interaction_watchdog_payload,
    _missing_first_progress_watchdog,
    _nonnegative_int,
    _seconds_since_iso_timestamp,
    _stale_progress_watchdog,
    get_quest_session as _get_quest_session_impl,
    inspect_quest_live_bash_sessions as _inspect_quest_live_bash_sessions_impl,
    inspect_quest_live_execution as _inspect_quest_live_execution_impl,
    inspect_quest_live_runtime as _inspect_quest_live_runtime_impl,
    list_quest_bash_sessions as _list_quest_bash_sessions_impl,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.quest_operations import (
    artifact_complete_quest as _artifact_complete_quest_impl,
    artifact_interact as _artifact_interact_impl,
    chat_quest as _chat_quest_impl,
    create_quest as _create_quest_impl,
    pause_quest as _pause_quest_impl,
    post_quest_control as _post_quest_control_impl,
    resume_quest as _resume_quest_impl,
    stop_quest as _stop_quest_impl,
    update_quest_startup_context as _update_quest_startup_context_impl,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.storage import _load_json_dict, _load_yaml_dict


BACKEND_ID = "med_deepscientist"
ENGINE_ID = "med-deepscientist"
DEFAULT_DAEMON_TIMEOUT_SECONDS = 10
DAEMON_CONTROL_TIMEOUT_SECONDS = 60
_UNSET = object()


def _run_launcher(
    *,
    runtime_root: Path,
    args: tuple[str, ...],
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _launcher_command(runtime_root=runtime_root, args=args),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _recover_launcher_status_from_runtime_state(*, runtime_root: Path) -> dict[str, Any] | None:
    return _recover_launcher_status_from_runtime_state_impl(runtime_root=runtime_root, get_json=_get_json)


def ensure_managed_daemon(*, runtime_root: Path) -> dict[str, Any]:
    return _ensure_managed_daemon_impl(
        runtime_root=runtime_root,
        run_launcher=_run_launcher,
        parse_launcher_status=_parse_launcher_status,
        get_json=_get_json,
    )


def release_idle_workspace_daemon(
    *,
    runtime_root: Path,
    idle_ttl_seconds: int = 300,
    pending_lease_seconds: int = 3600,
) -> dict[str, Any]:
    return _release_idle_workspace_daemon(
        runtime_root=runtime_root,
        run_launcher=_run_launcher,
        parse_launcher_status=_parse_launcher_status,
        idle_ttl_seconds=idle_ttl_seconds,
        pending_lease_seconds=pending_lease_seconds,
    )


def _ensure_managed_daemon_url(*, runtime_root: Path) -> str:
    daemon_status = ensure_managed_daemon(runtime_root=runtime_root)
    daemon_url = str(daemon_status.get("url") or "").strip().rstrip("/")
    if not daemon_url:
        raise RuntimeError("med-deepscientist launcher status is missing daemon url")
    return daemon_url


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _get_json(*, url: str, timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS) -> Any:
    return _get_json_impl(url=url, timeout=timeout)


def _daemon_url_matches_runtime_home(
    *,
    daemon_url: str,
    expected_home: Path,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> bool:
    return _daemon_url_matches_runtime_home_impl(
        daemon_url=daemon_url,
        expected_home=expected_home,
        timeout=timeout,
    )


def resolve_daemon_url(*, runtime_root: Path) -> str:
    return _resolve_daemon_url_impl(
        runtime_root=runtime_root,
        timeout=DEFAULT_DAEMON_TIMEOUT_SECONDS,
    )


def _request_json(
    *,
    url: str,
    payload: dict[str, Any],
    method: str,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return _request_json_impl(url=url, payload=payload, method=method, timeout=timeout)


def _post_json(*, url: str, payload: dict[str, Any], timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS) -> dict[str, Any]:
    return _post_json_impl(url=url, payload=payload, timeout=timeout)


def _patch_json(*, url: str, payload: dict[str, Any], timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS) -> dict[str, Any]:
    return _patch_json_impl(url=url, payload=payload, timeout=timeout)


def list_quest_bash_sessions(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    return _list_quest_bash_sessions_impl(
        quest_id=quest_id,
        get_json=_get_json,
        resolve_daemon_url=resolve_daemon_url,
        normalize_bash_session_entry=_normalize_stable_bash_session_entry,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )


def get_quest_session(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return _get_quest_session_impl(
        quest_id=quest_id,
        get_json=_get_json,
        resolve_daemon_url=resolve_daemon_url,
        normalize_quest_session=_normalize_stable_quest_session,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )


def inspect_quest_live_bash_sessions(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return _inspect_quest_live_bash_sessions_impl(
        quest_id=quest_id,
        list_quest_bash_sessions_fn=list_quest_bash_sessions,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )


def inspect_quest_live_runtime(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return _inspect_quest_live_runtime_impl(
        quest_id=quest_id,
        get_quest_session_fn=get_quest_session,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )


def inspect_quest_live_execution(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return _inspect_quest_live_execution_impl(
        quest_id=quest_id,
        inspect_quest_live_runtime_fn=inspect_quest_live_runtime,
        inspect_quest_live_bash_sessions_fn=inspect_quest_live_bash_sessions,
        infer_local_runtime_liveness_fn=_infer_local_runtime_liveness,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )


def _infer_local_runtime_liveness(*, runtime_root: Path, quest_id: str) -> dict[str, Any] | None:
    return _infer_local_runtime_liveness_impl(runtime_root=runtime_root, quest_id=quest_id)


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return _create_quest_impl(
        runtime_root=runtime_root,
        payload=payload,
        ensure_managed_daemon_url=_ensure_managed_daemon_url,
        post_json=_post_json,
        normalize_quest_create_result=_normalize_stable_quest_create_result,
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
    return _chat_quest_impl(
        runtime_root=runtime_root,
        quest_id=quest_id,
        text=text,
        source=source,
        resolve_daemon_url=resolve_daemon_url,
        post_json=_post_json,
        reply_to_interaction_id=reply_to_interaction_id,
        decision_response=decision_response,
    )


def artifact_interact(
    *,
    runtime_root: Path,
    quest_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return _artifact_interact_impl(
        runtime_root=runtime_root,
        quest_id=quest_id,
        payload=payload,
        resolve_daemon_url=resolve_daemon_url,
        post_json=_post_json,
    )


def artifact_complete_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    summary: str,
) -> dict[str, Any]:
    return _artifact_complete_quest_impl(
        runtime_root=runtime_root,
        quest_id=quest_id,
        summary=summary,
        resolve_daemon_url=resolve_daemon_url,
        post_json=_post_json,
    )


def post_quest_control(
    *,
    quest_id: str,
    action: str,
    source: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    return _post_quest_control_impl(
        quest_id=quest_id,
        action=action,
        source=source,
        resolve_daemon_url=resolve_daemon_url,
        ensure_managed_daemon_url=_ensure_managed_daemon_url,
        post_json=_post_json,
        normalize_quest_control_result=_normalize_stable_quest_control_result,
        daemon_control_timeout_seconds=DAEMON_CONTROL_TIMEOUT_SECONDS,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
    )


def resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return _resume_quest_impl(
        runtime_root=runtime_root,
        quest_id=quest_id,
        source=source,
        post_quest_control_fn=post_quest_control,
    )


def _normalize_startup_contract_for_stable_transport(
    *,
    startup_contract: dict[str, Any] | None | object,
) -> dict[str, Any] | None | object:
    return _normalize_startup_contract_for_stable_transport_impl(
        startup_contract=startup_contract,
        unset=_UNSET,
    )


def update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any] | None | object = _UNSET,
    requested_baseline_ref: dict[str, Any] | None | object = _UNSET,
) -> dict[str, Any]:
    return _update_quest_startup_context_impl(
        runtime_root=runtime_root,
        quest_id=quest_id,
        normalize_startup_contract=_normalize_startup_contract_for_stable_transport,
        ensure_managed_daemon_url=_ensure_managed_daemon_url,
        patch_json=_patch_json,
        normalize_startup_context_result=_normalize_stable_startup_context_result,
        daemon_control_timeout_seconds=DAEMON_CONTROL_TIMEOUT_SECONDS,
        unset=_UNSET,
        startup_contract=startup_contract,
        requested_baseline_ref=requested_baseline_ref,
    )


def pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return _pause_quest_impl(
        runtime_root=runtime_root,
        quest_id=quest_id,
        source=source,
        post_quest_control_fn=post_quest_control,
    )


def stop_quest(
    *,
    quest_id: str,
    source: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    return _stop_quest_impl(
        quest_id=quest_id,
        source=source,
        post_quest_control_fn=post_quest_control,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
    )

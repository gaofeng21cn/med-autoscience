from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from med_autoscience.hermes_runtime_contract import inspect_hermes_runtime_contract
from med_autoscience.runtime_transport import med_deepscientist as stable_transport

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


# Hermes 接入当前是“真实 outer-runtime adapter + controlled backend delegation”：
# adapter 自身必须先拿到 external Hermes runtime binding 并做 ready 校验，
# 然后才允许把 quest 控制动作委托给受控的 MedDeepScientist backend。
BACKEND_ID = "hermes"
ENGINE_ID = "hermes"
CONTROLLED_RESEARCH_BACKEND_ID = stable_transport.BACKEND_ID
CONTROLLED_RESEARCH_ENGINE_ID = stable_transport.ENGINE_ID
DEFAULT_DAEMON_TIMEOUT_SECONDS = stable_transport.DEFAULT_DAEMON_TIMEOUT_SECONDS
RUNTIME_BINDING_FILENAME = "hermes_runtime_binding.yaml"


def _resolved_runtime_root(runtime_root: Path) -> Path:
    return Path(runtime_root).expanduser().resolve()


def _runtime_home(runtime_root: Path) -> Path:
    return _resolved_runtime_root(runtime_root).parent


def _binding_path(runtime_root: Path) -> Path:
    return _runtime_home(runtime_root) / RUNTIME_BINDING_FILENAME


def _write_yaml_dict(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing hermes runtime adapter binding: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid hermes runtime adapter binding payload: {path}")
    return payload


def bind_runtime_root(
    *,
    runtime_root: Path,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None,
    source: str,
) -> dict[str, Any]:
    if hermes_agent_repo_root is None:
        raise ValueError("hermes adapter binding requires hermes_agent_repo_root")
    resolved_runtime_root = _resolved_runtime_root(runtime_root)
    resolved_repo_root = Path(hermes_agent_repo_root).expanduser().resolve()
    resolved_home_root = (
        Path(hermes_home_root).expanduser().resolve()
        if hermes_home_root is not None
        else (Path.home() / ".hermes").resolve()
    )
    payload = {
        "schema_version": 1,
        "runtime_root": str(resolved_runtime_root),
        "runtime_home": str(_runtime_home(resolved_runtime_root)),
        "hermes_agent_repo_root": str(resolved_repo_root),
        "hermes_home_root": str(resolved_home_root),
        "source": str(source or "").strip() or "managed_runtime_profile",
    }
    _write_yaml_dict(_binding_path(resolved_runtime_root), payload)
    return payload


def bind_runtime_root_from_profile(
    *,
    runtime_root: Path,
    profile: WorkspaceProfile,
    source: str = "managed_runtime_profile",
) -> dict[str, Any]:
    return bind_runtime_root(
        runtime_root=runtime_root,
        hermes_agent_repo_root=profile.hermes_agent_repo_root,
        hermes_home_root=profile.hermes_home_root,
        source=f"{source}:{profile.name}",
    )


def _load_runtime_binding(runtime_root: Path) -> dict[str, Any]:
    return _load_yaml_dict(_binding_path(runtime_root))


def _required_runtime_root(
    *,
    runtime_root: Path | None,
    operation_name: str,
) -> Path:
    if runtime_root is None:
        raise RuntimeError(
            f"hermes adapter requires runtime_root for `{operation_name}` so it can verify external Hermes runtime readiness"
        )
    return _resolved_runtime_root(runtime_root)


def _require_ready_external_runtime(*, runtime_root: Path) -> dict[str, Any]:
    binding = _load_runtime_binding(runtime_root)
    contract = inspect_hermes_runtime_contract(
        hermes_agent_repo_root=Path(str(binding.get("hermes_agent_repo_root") or "")).expanduser().resolve(),
        hermes_home_root=Path(str(binding.get("hermes_home_root") or "")).expanduser().resolve(),
    )
    if contract.get("ready"):
        return contract
    issues = contract.get("issues") or []
    rendered_issues = ", ".join(str(item) for item in issues) if issues else "external_runtime.not_ready"
    raise RuntimeError(
        f"external Hermes runtime is not ready for managed adapter delegation at {runtime_root}: {rendered_issues}"
    )


def _load_runtime_local_state(*, runtime_root: Path, quest_id: str) -> dict[str, Any] | None:
    quest_root = _resolved_runtime_root(runtime_root) / "quests" / quest_id
    quest_yaml_path = quest_root / "quest.yaml"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    if not quest_yaml_path.exists() and not runtime_state_path.exists():
        return None
    quest_payload = _load_yaml_dict(quest_yaml_path) if quest_yaml_path.exists() else {}
    try:
        runtime_payload = json.loads(runtime_state_path.read_text(encoding="utf-8")) if runtime_state_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        runtime_payload = {}
    if not isinstance(quest_payload, dict):
        quest_payload = {}
    if not isinstance(runtime_payload, dict):
        runtime_payload = {}
    status = str(runtime_payload.get("status") or quest_payload.get("status") or "").strip() or None
    active_run_id = str(runtime_payload.get("active_run_id") or quest_payload.get("active_run_id") or "").strip() or None
    payload = {
        "status": status,
        "active_run_id": active_run_id,
        "continuation_policy": str(runtime_payload.get("continuation_policy") or "").strip() or None,
        "continuation_anchor": str(runtime_payload.get("continuation_anchor") or "").strip() or None,
        "continuation_reason": str(runtime_payload.get("continuation_reason") or "").strip() or None,
    }
    return payload


def _external_runtime_unavailable_live_execution(
    *,
    runtime_root: Path,
    quest_id: str,
    error_text: str,
) -> dict[str, Any]:
    local_runtime_state = _load_runtime_local_state(runtime_root=runtime_root, quest_id=quest_id)
    active_run_id = None
    if isinstance(local_runtime_state, dict):
        active_run_id = str(local_runtime_state.get("active_run_id") or "").strip() or None
    payload = {
        "ok": False,
        "status": "unknown",
        "source": "external_runtime_contract",
        "active_run_id": active_run_id,
        "runner_live": False,
        "bash_live": False,
        "runtime_audit": {
            "ok": False,
            "status": "unknown",
            "source": "external_runtime_contract",
            "active_run_id": active_run_id,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": error_text,
        },
        "bash_session_audit": {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": error_text,
        },
        "error": error_text,
    }
    if isinstance(local_runtime_state, dict):
        payload["local_runtime_state"] = local_runtime_state
    return payload


def resolve_daemon_url(*, runtime_root: Path) -> str:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="resolve_daemon_url")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.resolve_daemon_url(runtime_root=resolved_runtime_root)


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="create_quest")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.create_quest(runtime_root=resolved_runtime_root, payload=payload)


def resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="resume_quest")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.resume_quest(runtime_root=resolved_runtime_root, quest_id=quest_id, source=source)


def pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="pause_quest")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.pause_quest(runtime_root=resolved_runtime_root, quest_id=quest_id, source=source)


def stop_quest(
    *,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    quest_id: str,
    source: str,
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="stop_quest")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.stop_quest(
        daemon_url=daemon_url,
        runtime_root=resolved_runtime_root,
        quest_id=quest_id,
        source=source,
    )


def get_quest_session(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="get_quest_session")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.get_quest_session(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=resolved_runtime_root,
        timeout=timeout,
    )


def inspect_quest_live_runtime(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="inspect_quest_live_runtime")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.inspect_quest_live_runtime(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=resolved_runtime_root,
        timeout=timeout,
    )


def inspect_quest_live_bash_sessions(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="inspect_quest_live_bash_sessions")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.inspect_quest_live_bash_sessions(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=resolved_runtime_root,
        timeout=timeout,
    )


def inspect_quest_live_execution(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="inspect_quest_live_execution")
    try:
        _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    except RuntimeError as exc:
        return _external_runtime_unavailable_live_execution(
            runtime_root=resolved_runtime_root,
            quest_id=quest_id,
            error_text=str(exc),
        )
    return stable_transport.inspect_quest_live_execution(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=resolved_runtime_root,
        timeout=timeout,
    )


def update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any] | None = None,
    requested_baseline_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="update_quest_startup_context")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.update_quest_startup_context(
        runtime_root=resolved_runtime_root,
        quest_id=quest_id,
        startup_contract=startup_contract,
        requested_baseline_ref=requested_baseline_ref,
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
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="chat_quest")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.chat_quest(
        runtime_root=resolved_runtime_root,
        quest_id=quest_id,
        text=text,
        source=source,
        reply_to_interaction_id=reply_to_interaction_id,
        decision_response=decision_response,
    )


def artifact_complete_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    summary: str,
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="artifact_complete_quest")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.artifact_complete_quest(
        runtime_root=resolved_runtime_root,
        quest_id=quest_id,
        summary=summary,
    )


def artifact_interact(
    *,
    runtime_root: Path,
    quest_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    resolved_runtime_root = _required_runtime_root(runtime_root=runtime_root, operation_name="artifact_interact")
    _require_ready_external_runtime(runtime_root=resolved_runtime_root)
    return stable_transport.artifact_interact(
        runtime_root=resolved_runtime_root,
        quest_id=quest_id,
        payload=payload,
    )

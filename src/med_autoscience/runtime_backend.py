from __future__ import annotations

from collections.abc import Mapping
import inspect
from pathlib import Path
from typing import Any, Protocol

DEFAULT_MANAGED_RUNTIME_BACKEND_ID = "med_deepscientist"


class ManagedRuntimeBackend(Protocol):
    BACKEND_ID: str
    ENGINE_ID: str

    def resolve_daemon_url(self, *, runtime_root: Path) -> str: ...

    def create_quest(self, *, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]: ...

    def resume_quest(self, *, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]: ...

    def pause_quest(self, *, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]: ...

    def stop_quest(
        self,
        *,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        quest_id: str,
        source: str,
    ) -> dict[str, Any]: ...

    def get_quest_session(
        self,
        *,
        quest_id: str,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]: ...

    def inspect_quest_live_runtime(
        self,
        *,
        quest_id: str,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]: ...

    def inspect_quest_live_execution(
        self,
        *,
        quest_id: str,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]: ...

    def update_quest_startup_context(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        startup_contract: dict[str, Any] | None = None,
        requested_baseline_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def artifact_complete_quest(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        summary: str,
    ) -> dict[str, Any]: ...

    def artifact_interact(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]: ...


_REGISTERED_MANAGED_RUNTIME_BACKENDS: dict[str, ManagedRuntimeBackend] = {}
_ENGINE_TO_BACKEND_ID: dict[str, str] = {}
_BACKEND_CALLABLE_CONTRACT: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "resolve_daemon_url": (("runtime_root",), ()),
    "create_quest": (("runtime_root", "payload"), ()),
    "resume_quest": (("runtime_root", "quest_id", "source"), ()),
    "pause_quest": (("runtime_root", "quest_id", "source"), ()),
    "stop_quest": (("quest_id", "source"), ("daemon_url", "runtime_root")),
    "get_quest_session": (("quest_id",), ("daemon_url", "runtime_root", "timeout")),
    "inspect_quest_live_runtime": (("quest_id",), ("daemon_url", "runtime_root", "timeout")),
    "inspect_quest_live_execution": (("quest_id",), ("daemon_url", "runtime_root", "timeout")),
    "update_quest_startup_context": (
        ("runtime_root", "quest_id"),
        ("startup_contract", "requested_baseline_ref"),
    ),
    "artifact_complete_quest": (("runtime_root", "quest_id", "summary"), ()),
    "artifact_interact": (("runtime_root", "quest_id", "payload"), ()),
}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _validate_backend_callable_contract(*, backend_id: str, backend: ManagedRuntimeBackend) -> None:
    for operation_name, (required_parameters, optional_parameters) in _BACKEND_CALLABLE_CONTRACT.items():
        candidate = getattr(backend, operation_name, None)
        if not callable(candidate):
            raise ValueError(f"managed runtime backend `{backend_id}` is missing callable `{operation_name}`")
        signature = inspect.signature(candidate)
        parameters = signature.parameters
        missing_parameters = [
            parameter_name
            for parameter_name in (*required_parameters, *optional_parameters)
            if parameter_name not in parameters
        ]
        if missing_parameters:
            raise ValueError(
                f"managed runtime backend `{backend_id}` callable `{operation_name}` is missing parameters: "
                + ", ".join(missing_parameters)
            )
        for parameter_name in required_parameters:
            parameter = parameters[parameter_name]
            if parameter.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                raise ValueError(
                    f"managed runtime backend `{backend_id}` callable `{operation_name}` has unsupported parameter kind "
                    f"for `{parameter_name}`"
                )
            if parameter.default is not inspect.Signature.empty:
                raise ValueError(
                    f"managed runtime backend `{backend_id}` callable `{operation_name}` must require `{parameter_name}`"
                )
        for parameter_name in optional_parameters:
            parameter = parameters[parameter_name]
            if parameter.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                raise ValueError(
                    f"managed runtime backend `{backend_id}` callable `{operation_name}` has unsupported parameter kind "
                    f"for `{parameter_name}`"
                )
        allowed_parameters = set(required_parameters) | set(optional_parameters)
        for parameter_name, parameter in parameters.items():
            if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if parameter_name not in allowed_parameters:
                raise ValueError(
                    f"managed runtime backend `{backend_id}` callable `{operation_name}` has unexpected parameter "
                    f"`{parameter_name}`"
                )
        for parameter_name in optional_parameters:
            parameter = parameters[parameter_name]
            if parameter.default is inspect.Signature.empty:
                raise ValueError(
                    f"managed runtime backend `{backend_id}` callable `{operation_name}` must make `{parameter_name}` optional"
                )


def register_managed_runtime_backend(backend: ManagedRuntimeBackend) -> None:
    backend_id = _non_empty_text(getattr(backend, "BACKEND_ID", None))
    engine_id = _non_empty_text(getattr(backend, "ENGINE_ID", None))
    if backend_id is None:
        raise ValueError("managed runtime backend must expose non-empty BACKEND_ID")
    if engine_id is None:
        raise ValueError("managed runtime backend must expose non-empty ENGINE_ID")
    _validate_backend_callable_contract(backend_id=backend_id, backend=backend)
    _REGISTERED_MANAGED_RUNTIME_BACKENDS[backend_id] = backend
    _ENGINE_TO_BACKEND_ID[engine_id] = backend_id


def registered_managed_runtime_backend_ids() -> tuple[str, ...]:
    return tuple(sorted(_REGISTERED_MANAGED_RUNTIME_BACKENDS))


def get_managed_runtime_backend(backend_id: str) -> ManagedRuntimeBackend:
    normalized_backend_id = _non_empty_text(backend_id)
    if normalized_backend_id is None:
        raise ValueError("managed runtime backend_id must be non-empty")
    try:
        return _REGISTERED_MANAGED_RUNTIME_BACKENDS[normalized_backend_id]
    except KeyError as exc:
        raise ValueError(f"unknown managed runtime backend: {normalized_backend_id}") from exc


def try_get_managed_runtime_backend(backend_id: str | None) -> ManagedRuntimeBackend | None:
    normalized_backend_id = _non_empty_text(backend_id)
    if normalized_backend_id is None:
        return None
    return _REGISTERED_MANAGED_RUNTIME_BACKENDS.get(normalized_backend_id)


def explicit_runtime_backend_id(execution: Mapping[str, Any] | None) -> str | None:
    if not isinstance(execution, Mapping):
        return None
    return _non_empty_text(execution.get("runtime_backend_id")) or _non_empty_text(execution.get("runtime_backend"))


def runtime_backend_id_from_execution(execution: Mapping[str, Any] | None) -> str | None:
    explicit_backend_id = explicit_runtime_backend_id(execution)
    if explicit_backend_id is not None:
        return explicit_backend_id
    if not isinstance(execution, Mapping):
        return None
    engine_id = _non_empty_text(execution.get("engine"))
    if engine_id is None:
        return None
    return _ENGINE_TO_BACKEND_ID.get(engine_id)


def resolve_managed_runtime_backend(execution: Mapping[str, Any] | None) -> ManagedRuntimeBackend | None:
    return try_get_managed_runtime_backend(runtime_backend_id_from_execution(execution))


def is_managed_runtime_execution(execution: Mapping[str, Any] | None) -> bool:
    return resolve_managed_runtime_backend(execution) is not None


def is_managed_research_execution(execution: Mapping[str, Any] | None) -> bool:
    if not is_managed_runtime_execution(execution):
        return False
    if not isinstance(execution, Mapping):
        return False
    return _non_empty_text(execution.get("auto_entry")) == "on_managed_research_intent"


def engine_id_for_backend_id(backend_id: str) -> str:
    backend = get_managed_runtime_backend(backend_id)
    engine_id = _non_empty_text(getattr(backend, "ENGINE_ID", None))
    if engine_id is None:
        raise ValueError(f"managed runtime backend `{backend_id}` is missing ENGINE_ID")
    return engine_id


from med_autoscience.runtime_transport import med_deepscientist as _med_deepscientist_backend
from med_autoscience.runtime_transport import hermes as _hermes_backend


register_managed_runtime_backend(_med_deepscientist_backend)
register_managed_runtime_backend(_hermes_backend)

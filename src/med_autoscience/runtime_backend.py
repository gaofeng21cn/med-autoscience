from __future__ import annotations

from collections.abc import Callable, Mapping
import inspect
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol

DEFAULT_MANAGED_RUNTIME_BACKEND_ID = "mas_runtime_core"
MAS_RUNTIME_OWNER = "one-person-lab"
MAS_RUNTIME_SUBSTRATE = "opl_provider_backed_stage_runtime"
MAS_DOMAIN_RUNTIME_ADAPTER_ROLE = "mas_domain_owner_receipt_adapter"
CONTROLLED_RESEARCH_BACKEND_EXECUTOR_OWNER = "controlled_research_backend"
EXTERNAL_MDS_ALLOWED_USES = (
    "source_provenance_ref",
    "historical_fixture_ref",
)


class ManagedRuntimeBackend(Protocol):
    BACKEND_ID: str
    ENGINE_ID: str

    def resolve_daemon_url(self, *, runtime_root: Path) -> str: ...

    def create_quest(self, *, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]: ...

    def resume_quest(self, *, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]: ...

    def relaunch_stopped_quest(self, *, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]: ...

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

    def chat_quest(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        text: str,
        source: str,
        reply_to_interaction_id: str | None = None,
        decision_response: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def schedule_turn(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        reason: str,
        source: str,
    ) -> dict[str, Any]: ...

    def complete_turn_and_normalize(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        run_id: str,
        runner_status: str,
        source: str,
        blocking_decision_request: dict[str, Any] | None = None,
        same_fingerprint: bool = False,
    ) -> dict[str, Any]: ...

    def inspect_turn_lifecycle(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
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

    def inspect_terminal_attach(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        run_id: str,
        study_id: str,
        token: str | None = None,
        source: str,
    ) -> dict[str, Any]: ...

    def attach_terminal(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        run_id: str,
        study_id: str,
        idempotency_key: str,
        source: str,
    ) -> dict[str, Any]: ...

    def terminal_input(
        self,
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
    ) -> dict[str, Any]: ...

    def resize_terminal(
        self,
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
    ) -> dict[str, Any]: ...

    def detach_terminal(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        run_id: str,
        study_id: str,
        token: str,
        lease_id: str,
        idempotency_key: str,
        source: str,
    ) -> dict[str, Any]: ...


_REGISTERED_MANAGED_RUNTIME_BACKENDS: dict[str, ManagedRuntimeBackend] = {}
_ENGINE_TO_BACKEND_ID: dict[str, str] = {}
_LAZY_MANAGED_RUNTIME_BACKENDS: dict[str, Callable[[], ManagedRuntimeBackend]] = {}
_LAZY_ENGINE_TO_BACKEND_ID: dict[str, str] = {}
_BACKEND_CALLABLE_CONTRACT: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "resolve_daemon_url": (("runtime_root",), ()),
    "create_quest": (("runtime_root", "payload"), ()),
    "resume_quest": (("runtime_root", "quest_id", "source"), ()),
    "relaunch_stopped_quest": (("runtime_root", "quest_id", "source"), ()),
    "pause_quest": (("runtime_root", "quest_id", "source"), ()),
    "stop_quest": (("quest_id", "source"), ("daemon_url", "runtime_root")),
    "get_quest_session": (("quest_id",), ("daemon_url", "runtime_root", "timeout")),
    "inspect_quest_live_runtime": (("quest_id",), ("daemon_url", "runtime_root", "timeout")),
    "inspect_quest_live_execution": (("quest_id",), ("daemon_url", "runtime_root", "timeout")),
    "update_quest_startup_context": (
        ("runtime_root", "quest_id"),
        ("startup_contract", "requested_baseline_ref"),
    ),
    "chat_quest": (
        ("runtime_root", "quest_id", "text", "source"),
        ("reply_to_interaction_id", "decision_response"),
    ),
    "schedule_turn": (("runtime_root", "quest_id", "reason", "source"), ()),
    "complete_turn_and_normalize": (
        ("runtime_root", "quest_id", "run_id", "runner_status", "source"),
        ("blocking_decision_request", "same_fingerprint"),
    ),
    "inspect_turn_lifecycle": (("runtime_root", "quest_id"), ()),
    "artifact_complete_quest": (("runtime_root", "quest_id", "summary"), ()),
    "artifact_interact": (("runtime_root", "quest_id", "payload"), ()),
    "inspect_terminal_attach": (
        ("runtime_root", "quest_id", "run_id", "study_id", "source"),
        ("token",),
    ),
    "attach_terminal": (
        ("runtime_root", "quest_id", "run_id", "study_id", "idempotency_key", "source"),
        (),
    ),
    "terminal_input": (
        ("runtime_root", "quest_id", "run_id", "study_id", "token", "lease_id", "text", "idempotency_key", "source"),
        (),
    ),
    "resize_terminal": (
        ("runtime_root", "quest_id", "run_id", "study_id", "token", "lease_id", "rows", "cols", "idempotency_key", "source"),
        (),
    ),
    "detach_terminal": (
        ("runtime_root", "quest_id", "run_id", "study_id", "token", "lease_id", "idempotency_key", "source"),
        (),
    ),
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
        _validate_backend_callable_declared_parameters(
            backend_id=backend_id,
            operation_name=operation_name,
            parameters=parameters,
            required_parameters=required_parameters,
            optional_parameters=optional_parameters,
        )
        _validate_backend_callable_extra_parameters(
            backend_id=backend_id,
            operation_name=operation_name,
            parameters=parameters,
            required_parameters=required_parameters,
            optional_parameters=optional_parameters,
        )


def _validate_backend_callable_declared_parameters(
    *,
    backend_id: str,
    operation_name: str,
    parameters: Mapping[str, inspect.Parameter],
    required_parameters: tuple[str, ...],
    optional_parameters: tuple[str, ...],
) -> None:
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
        if parameter.default is inspect.Signature.empty:
            raise ValueError(
                f"managed runtime backend `{backend_id}` callable `{operation_name}` must make `{parameter_name}` optional"
            )


def _validate_backend_callable_extra_parameters(
    *,
    backend_id: str,
    operation_name: str,
    parameters: Mapping[str, inspect.Parameter],
    required_parameters: tuple[str, ...],
    optional_parameters: tuple[str, ...],
) -> None:
    allowed_parameters = set(required_parameters) | set(optional_parameters)
    for parameter_name, parameter in parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if parameter_name not in allowed_parameters:
            raise ValueError(
                f"managed runtime backend `{backend_id}` callable `{operation_name}` has unexpected parameter "
                f"`{parameter_name}`"
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


def register_lazy_managed_runtime_backend(
    *,
    backend_id: str,
    engine_id: str,
    loader: Callable[[], ManagedRuntimeBackend],
) -> None:
    normalized_backend_id = _non_empty_text(backend_id)
    normalized_engine_id = _non_empty_text(engine_id)
    if normalized_backend_id is None or normalized_engine_id is None:
        raise ValueError("lazy managed runtime backend metadata must be non-empty")
    _LAZY_MANAGED_RUNTIME_BACKENDS[normalized_backend_id] = loader
    _LAZY_ENGINE_TO_BACKEND_ID[normalized_engine_id] = normalized_backend_id


def _load_lazy_backend(backend_id: str) -> ManagedRuntimeBackend | None:
    loader = _LAZY_MANAGED_RUNTIME_BACKENDS.get(backend_id)
    if loader is None:
        return None
    backend = loader()
    register_managed_runtime_backend(backend)
    _LAZY_MANAGED_RUNTIME_BACKENDS.pop(backend_id, None)
    _LAZY_ENGINE_TO_BACKEND_ID.pop(str(getattr(backend, "ENGINE_ID", "")).strip(), None)
    return _REGISTERED_MANAGED_RUNTIME_BACKENDS[backend_id]


def registered_managed_runtime_backend_ids() -> tuple[str, ...]:
    return tuple(sorted(set(_REGISTERED_MANAGED_RUNTIME_BACKENDS) | set(_LAZY_MANAGED_RUNTIME_BACKENDS)))


def get_managed_runtime_backend(backend_id: str) -> ManagedRuntimeBackend:
    normalized_backend_id = _non_empty_text(backend_id)
    if normalized_backend_id is None:
        raise ValueError("managed runtime backend_id must be non-empty")
    try:
        return _REGISTERED_MANAGED_RUNTIME_BACKENDS[normalized_backend_id]
    except KeyError as exc:
        backend = _load_lazy_backend(normalized_backend_id)
        if backend is not None:
            return backend
        raise ValueError(f"unknown managed runtime backend: {normalized_backend_id}") from exc


def try_get_managed_runtime_backend(backend_id: str | None) -> ManagedRuntimeBackend | None:
    normalized_backend_id = _non_empty_text(backend_id)
    if normalized_backend_id is None:
        return None
    return _REGISTERED_MANAGED_RUNTIME_BACKENDS.get(normalized_backend_id) or _load_lazy_backend(normalized_backend_id)


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
    return _ENGINE_TO_BACKEND_ID.get(engine_id) or _LAZY_ENGINE_TO_BACKEND_ID.get(engine_id)


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


def controlled_research_backend_metadata_for_backend_id(backend_id: str) -> tuple[str, str]:
    backend = get_managed_runtime_backend(backend_id)
    research_backend_id = (
        _non_empty_text(getattr(backend, "CONTROLLED_RESEARCH_BACKEND_ID", None))
        or _non_empty_text(getattr(backend, "BACKEND_ID", None))
    )
    research_engine_id = (
        _non_empty_text(getattr(backend, "CONTROLLED_RESEARCH_ENGINE_ID", None))
        or _non_empty_text(getattr(backend, "ENGINE_ID", None))
    )
    if research_backend_id is None or research_engine_id is None:
        raise ValueError(f"managed runtime backend `{backend_id}` is missing controlled research backend metadata")
    return research_backend_id, research_engine_id


def runtime_backend_default_operation_contract(backend_id: str) -> dict[str, object]:
    backend = get_managed_runtime_backend(backend_id)
    runtime_backend_id = _non_empty_text(getattr(backend, "BACKEND_ID", None))
    runtime_engine_id = _non_empty_text(getattr(backend, "ENGINE_ID", None))
    if runtime_backend_id is None or runtime_engine_id is None:
        raise ValueError(f"managed runtime backend `{backend_id}` is missing runtime backend metadata")
    research_backend_id, research_engine_id = controlled_research_backend_metadata_for_backend_id(backend_id)
    return {
        "runtime_owner": MAS_RUNTIME_OWNER,
        "runtime_substrate": MAS_RUNTIME_SUBSTRATE,
        "runtime_backend_id": runtime_backend_id,
        "runtime_engine_id": runtime_engine_id,
        "runtime_backend_role": MAS_DOMAIN_RUNTIME_ADAPTER_ROLE,
        "runtime_backend_is_generic_owner": False,
        "domain_runtime_adapter_id": runtime_backend_id,
        "domain_runtime_adapter_role": MAS_DOMAIN_RUNTIME_ADAPTER_ROLE,
        "generic_runtime_owner": MAS_RUNTIME_OWNER,
        "generic_runtime_substrate": MAS_RUNTIME_SUBSTRATE,
        "domain_truth_owner": "med-autoscience",
        "domain_authority_retained": [
            "study_truth",
            "publication_quality_verdict",
            "artifact_authority",
            "memory_accept_reject_receipt",
            "owner_receipt",
            "typed_blocker",
        ],
        "runtime_backend_retirement_gate": {
            "no_active_default_caller_required": True,
            "opl_replacement_parity_required": True,
            "domain_receipt_parity_required": True,
            "history_tombstone_required": True,
        },
        "research_backend_id": research_backend_id,
        "research_engine_id": research_engine_id,
        "external_mds_required_for_default_operation": False,
        "external_mds_runnable_dependency": False,
        "external_mds_retained_role": "frozen_source_archive_or_historical_fixture",
        "external_mds_allowed_uses": list(EXTERNAL_MDS_ALLOWED_USES),
    }


register_lazy_managed_runtime_backend(
    backend_id="mas_runtime_core",
    engine_id="mas-runtime-core",
    loader=lambda: import_module("med_autoscience.runtime_transport.mas_runtime_core"),
)

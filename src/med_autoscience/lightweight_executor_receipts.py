from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_lightweight_executor_receipt"
CONTRACT_SURFACE_KIND = "mas_lightweight_executor_receipt_contract"
DEFAULT_ISOLATION_LEVELS = (
    "L0_host_clean_runner",
    "L1_process_workspace",
)
DEFAULT_ISOLATION_LEVEL = "L1_process_workspace"
L3_ISOLATION_LEVEL = "L3_containerized_sandbox"
ALLOWED_WRITES = ("artifacts/executor_receipts/**/*.json",)
FORBIDDEN_WRITES = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/**",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
    "submission_package/**",
    "current_package/**",
    "memory/**/body",
)
EXECUTION_REF_FIELDS = (
    "status",
    "exit_code",
    "stdout_ref",
    "stderr_ref",
    "output_refs",
    "artifact_refs",
    "changed_file_refs",
    "duration_ms",
    "resource_usage_ref",
    "working_dir_ref",
    "env_fingerprint",
    "failure_class",
)
FORBIDDEN_AUTHORITY = (
    "domain_truth",
    "publication_eval",
    "controller_decisions",
    "paper_body",
    "current_package",
    "owner_receipt",
    "typed_blocker",
    "quality_verdict",
    "publication_readiness",
    "submission_readiness",
    "artifact_authority",
    "stage_closeout",
)


def build_lightweight_executor_receipt(
    *,
    executor_backend: str,
    command_ref: str,
    work_unit: Mapping[str, Any] | None = None,
    execution: Mapping[str, Any] | None = None,
    requested_isolation_level: str | None = None,
    host_context: Mapping[str, Any] | None = None,
    explicit_sandbox_request: bool = False,
) -> dict[str, Any]:
    context = _mapping(host_context)
    requested_level = _text(requested_isolation_level) or DEFAULT_ISOLATION_LEVEL
    diagnostics = _diagnostics(
        requested_level=requested_level,
        host_context=context,
        explicit_sandbox_request=explicit_sandbox_request,
    )
    effective_level = _effective_isolation_level(
        requested_level=requested_level,
        host_context=context,
        explicit_sandbox_request=explicit_sandbox_request,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "sandbox_not_authorized" if diagnostics else "executor_receipt_recorded",
        "execution_model": "receipt_only_no_command_execution",
        "executor_backend": _text(executor_backend) or "unknown_executor",
        "command_ref": _text(command_ref) or "missing_command_ref",
        "work_unit": _work_unit_payload(work_unit),
        "execution": _execution_payload(execution),
        "evidence_source": _evidence_source_payload(None),
        "isolation": _isolation_payload(
            effective_level=effective_level,
            requested_level=requested_level,
            host_context=context,
            explicit_sandbox_request=explicit_sandbox_request,
        ),
        "diagnostics": diagnostics,
        "allowed_writes": list(ALLOWED_WRITES),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "refs_only": True,
        "body_included": False,
        "can_block_current_owner_action": False,
        "mainline_waits_for_executor_receipt": False,
        "receipt_counts_as_owner_receipt": False,
        "authority_boundary": _authority_boundary(),
        "readiness_authorization": _readiness_authorization(),
    }


def build_lightweight_executor_receipt_from_evidence(
    evidence: Mapping[str, Any],
    *,
    work_unit: Mapping[str, Any] | None = None,
    executor_backend: str | None = None,
    command_ref: str | None = None,
    requested_isolation_level: str | None = None,
    host_context: Mapping[str, Any] | None = None,
    explicit_sandbox_request: bool | None = None,
) -> dict[str, Any]:
    payload = _mapping(evidence)
    source_payload = _source_payload(payload)
    audit_trail = _mapping(payload.get("audit_trail"))
    explicit_work_unit = _mapping(work_unit)
    inferred_work_unit = _work_unit_from_evidence(payload=payload, source_payload=source_payload)
    inferred_work_unit.update({key: value for key, value in explicit_work_unit.items() if _text(value)})
    backend = (
        _text(executor_backend)
        or _text(payload.get("executor_backend"))
        or ("tool_result_envelope" if _is_tool_result_envelope(payload) else "executor_evidence_dict")
    )
    sandbox_request = (
        bool(payload.get("explicit_sandbox_request"))
        if explicit_sandbox_request is None
        else explicit_sandbox_request
    )
    receipt = build_lightweight_executor_receipt(
        executor_backend=backend,
        command_ref=(
            _text(command_ref)
            or _text(payload.get("command_ref"))
            or _command_ref_from_evidence(payload)
        ),
        work_unit=inferred_work_unit,
        execution=_execution_from_evidence(
            payload=payload,
            source_payload=source_payload,
            audit_trail=audit_trail,
        ),
        requested_isolation_level=(
            _text(requested_isolation_level) or _text(payload.get("requested_isolation_level"))
        ),
        host_context=host_context if host_context is not None else _mapping(payload.get("host_context")),
        explicit_sandbox_request=sandbox_request,
    )
    receipt["evidence_source"] = _evidence_source_payload(payload)
    return receipt


def build_lightweight_executor_receipt_contract() -> dict[str, Any]:
    return {
        "surface_kind": CONTRACT_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "runtime_owner": "one-person-lab",
        "purpose": (
            "Describe lightweight executor receipts for current OPL/Codex execution without "
            "introducing a default container runtime."
        ),
        "execution_model": "receipt_only_no_command_execution",
        "default_isolation_levels": list(DEFAULT_ISOLATION_LEVELS),
        "default_isolation_level": DEFAULT_ISOLATION_LEVEL,
        "containerized_sandbox_default": False,
        "docker_in_docker_default": False,
        "docker_socket_mount_default": False,
        "openhands_runtime_default": False,
        "explicit_l3_proof_lane_only": True,
        "mainline_waits_for_executor_receipt": False,
        "receipt_counts_as_owner_receipt": False,
        "receipt_counts_as_stage_closeout": False,
        "receipt_counts_as_quality_verdict": False,
        "allowed_writes": list(ALLOWED_WRITES),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "execution_ref_fields": list(EXECUTION_REF_FIELDS),
        "forbidden_authority": list(FORBIDDEN_AUTHORITY),
        "authority_boundary": _authority_boundary(),
        "readiness_authorization": _readiness_authorization(),
        "friction_policy": {
            "can_block_current_owner_action": False,
            "missing_receipt_blocks_dispatch": False,
            "docker_unavailable_blocks_dispatch": False,
            "inside_container_disables_default_docker": True,
            "owner_policy_wins": True,
        },
    }


def _effective_isolation_level(
    *,
    requested_level: str,
    host_context: Mapping[str, Any],
    explicit_sandbox_request: bool,
) -> str:
    if requested_level != L3_ISOLATION_LEVEL:
        return requested_level if requested_level in DEFAULT_ISOLATION_LEVELS else DEFAULT_ISOLATION_LEVEL
    if _bool(host_context.get("inside_container")):
        return DEFAULT_ISOLATION_LEVEL
    return L3_ISOLATION_LEVEL if explicit_sandbox_request else DEFAULT_ISOLATION_LEVEL


def _diagnostics(
    *,
    requested_level: str,
    host_context: Mapping[str, Any],
    explicit_sandbox_request: bool,
) -> list[str]:
    diagnostics: list[str] = []
    if requested_level == L3_ISOLATION_LEVEL and not explicit_sandbox_request:
        diagnostics.append("containerized sandbox requires explicit proof-lane authorization")
    if requested_level == L3_ISOLATION_LEVEL and _bool(host_context.get("inside_container")):
        diagnostics.append("inside-container context disables default Docker sandbox")
    if _bool(host_context.get("docker_socket_mounted")):
        diagnostics.append("Docker socket mount is not accepted as implicit sandbox authorization")
    return diagnostics


def _isolation_payload(
    *,
    effective_level: str,
    requested_level: str,
    host_context: Mapping[str, Any],
    explicit_sandbox_request: bool,
) -> dict[str, Any]:
    inside_container = _bool(host_context.get("inside_container"))
    docker_socket_mounted = _bool(host_context.get("docker_socket_mounted"))
    l3_available = (
        effective_level == L3_ISOLATION_LEVEL
        and explicit_sandbox_request
        and not inside_container
        and not docker_socket_mounted
    )
    return {
        "level": effective_level,
        "requested_level": requested_level,
        "default_levels": list(DEFAULT_ISOLATION_LEVELS),
        "explicit_sandbox_request": explicit_sandbox_request,
        "inside_container": inside_container,
        "docker_sandbox_available": l3_available,
        "docker_in_docker_allowed": False,
        "docker_socket_mounted": docker_socket_mounted,
        "docker_socket_mount_allowed": False,
        "openhands_runtime_default": False,
    }


def _work_unit_payload(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(value)
    return {
        "owner": _text(payload.get("owner")),
        "action_type": _text(payload.get("action_type")),
        "action_id": _text(payload.get("action_id")),
        "work_unit_id": _text(payload.get("work_unit_id")) or _text(payload.get("unit_id")),
        "work_unit_fingerprint": _text(payload.get("work_unit_fingerprint")),
        "source_fingerprint": _text(payload.get("source_fingerprint")),
        "idempotency_key": _text(payload.get("idempotency_key")),
    }


def _execution_payload(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(value)
    return {
        "status": _text(payload.get("status")),
        "exit_code": _int_or_none(payload.get("exit_code")),
        "stdout_ref": _text(payload.get("stdout_ref")),
        "stderr_ref": _text(payload.get("stderr_ref")),
        "output_refs": _text_list(payload.get("output_refs")),
        "artifact_refs": _text_list(payload.get("artifact_refs")),
        "changed_file_refs": _text_list(payload.get("changed_file_refs")),
        "duration_ms": _int_or_none(payload.get("duration_ms")),
        "resource_usage_ref": _text(payload.get("resource_usage_ref")),
        "working_dir_ref": _text(payload.get("working_dir_ref")),
        "env_fingerprint": _text(payload.get("env_fingerprint")),
        "failure_class": _text(payload.get("failure_class")),
    }


def _execution_from_evidence(
    *,
    payload: Mapping[str, Any],
    source_payload: Mapping[str, Any],
    audit_trail: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": _first_text(source_payload, payload, "status"),
        "exit_code": source_payload.get("exit_code", payload.get("exit_code")),
        "stdout_ref": _first_text(source_payload, payload, "stdout_ref"),
        "stderr_ref": _first_text(source_payload, payload, "stderr_ref"),
        "output_refs": _output_refs_from_evidence(
            payload=payload,
            source_payload=source_payload,
            audit_trail=audit_trail,
        ),
        "artifact_refs": _first_text_list(source_payload, payload, "artifact_refs"),
        "changed_file_refs": _first_text_list(source_payload, payload, "changed_file_refs"),
        "duration_ms": source_payload.get("duration_ms", payload.get("duration_ms")),
        "resource_usage_ref": _first_text(source_payload, payload, "resource_usage_ref"),
        "working_dir_ref": _first_text(source_payload, payload, "working_dir_ref"),
        "env_fingerprint": _first_text(source_payload, payload, "env_fingerprint"),
        "failure_class": _first_text(source_payload, payload, "failure_class"),
    }


def _source_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    structured = payload.get("structured_payload")
    return structured if isinstance(structured, Mapping) else payload


def _is_tool_result_envelope(payload: Mapping[str, Any]) -> bool:
    return _text(payload.get("surface_kind")) == "mas_tool_result_envelope"


def _command_ref_from_evidence(payload: Mapping[str, Any]) -> str:
    if _is_tool_result_envelope(payload):
        tool_id = _text(payload.get("tool_id")) or "unknown_tool"
        tool_mode = _text(payload.get("tool_mode"))
        return f"tool_result_envelope:{tool_id}:{tool_mode}" if tool_mode else f"tool_result_envelope:{tool_id}"
    action_type = _text(payload.get("action_type")) or _text(payload.get("action_id")) or "unknown_action"
    return f"executor_evidence:{action_type}"


def _work_unit_from_evidence(
    *,
    payload: Mapping[str, Any],
    source_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "owner": _first_text(source_payload, payload, "owner"),
        "action_type": (
            _first_text(source_payload, payload, "action_type")
            or _first_text(source_payload, payload, "action_id")
            or _first_text(source_payload, payload, "tool_id")
        ),
        "action_id": _first_text(source_payload, payload, "action_id"),
        "work_unit_id": _first_text(source_payload, payload, "work_unit_id")
        or _first_text(source_payload, payload, "unit_id"),
        "work_unit_fingerprint": _first_text(source_payload, payload, "work_unit_fingerprint"),
        "source_fingerprint": _first_text(source_payload, payload, "source_fingerprint"),
        "idempotency_key": _first_text(source_payload, payload, "idempotency_key"),
    }


def _evidence_source_payload(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(value)
    source_payload = _source_payload(payload)
    return {
        "surface_kind": _text(payload.get("surface_kind")),
        "tool_id": _text(payload.get("tool_id")) or _text(source_payload.get("tool_id")),
        "tool_mode": _text(payload.get("tool_mode")) or _text(source_payload.get("tool_mode")),
        "action_type": _text(payload.get("action_type")) or _text(source_payload.get("action_type")),
        "status": _text(payload.get("status")) or _text(source_payload.get("status")),
        "content_ref": _text(payload.get("content_ref")),
        "structured_content_ref": _text(payload.get("structured_content_ref")),
        "executor_receipt_ref": _text(payload.get("executor_receipt_ref")),
        "lightweight_executor_receipt_contract_ref": _text(
            payload.get("lightweight_executor_receipt_contract_ref")
        ),
    }


def _output_refs_from_evidence(
    *,
    payload: Mapping[str, Any],
    source_payload: Mapping[str, Any],
    audit_trail: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    refs.extend(_text_list(payload.get("content_ref")))
    refs.extend(_text_list(payload.get("structured_content_ref")))
    refs.extend(_text_list(source_payload.get("output_refs")))
    refs.extend(_text_list(payload.get("output_refs")))
    refs.extend(_text_list(source_payload.get("artifact_refs")))
    refs.extend(_text_list(payload.get("artifact_refs")))
    refs.extend(_text_list(source_payload.get("changed_file_refs")))
    refs.extend(_text_list(payload.get("changed_file_refs")))
    refs.extend(_text_list(audit_trail.get("allowed_write_refs")))
    refs.extend(_text_list(audit_trail.get("receipt_refs")))
    refs.extend(_text_list(payload.get("executor_receipt_ref")))
    return _dedupe_text(refs)


def _first_text(primary: Mapping[str, Any], secondary: Mapping[str, Any], key: str) -> str | None:
    return _text(primary.get(key)) or _text(secondary.get(key))


def _first_text_list(
    primary: Mapping[str, Any],
    secondary: Mapping[str, Any],
    key: str,
) -> list[str]:
    values = _text_list(primary.get(key))
    return values if values else _text_list(secondary.get(key))


def _dedupe_text(values: Sequence[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _authority_boundary() -> dict[str, bool | str]:
    return {
        "surface_role": "executor_receipt_not_runtime_authority",
        "can_execute_command": False,
        "can_start_docker": False,
        "can_mount_docker_socket": False,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_authorize_owner_action": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_quality": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_stage": False,
    }


def _readiness_authorization() -> dict[str, bool]:
    return {
        "may_authorize_publication_readiness": False,
        "may_authorize_submission_readiness": False,
        "may_authorize_quality_verdict": False,
        "may_authorize_artifact_readiness": False,
        "may_authorize_artifact_mutation": False,
        "may_authorize_stage_closeout": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        items: Sequence[object] = [value]
    elif isinstance(value, Sequence):
        items = value
    else:
        items = []
    result: list[str] = []
    for item in items:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool(value: object) -> bool:
    return bool(value)


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        text = _text(value)
        return int(text) if text is not None else None
    except (TypeError, ValueError):
        return None


__all__ = [
    "ALLOWED_WRITES",
    "CONTRACT_SURFACE_KIND",
    "DEFAULT_ISOLATION_LEVELS",
    "FORBIDDEN_AUTHORITY",
    "FORBIDDEN_WRITES",
    "L3_ISOLATION_LEVEL",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_lightweight_executor_receipt",
    "build_lightweight_executor_receipt_from_evidence",
    "build_lightweight_executor_receipt_contract",
]

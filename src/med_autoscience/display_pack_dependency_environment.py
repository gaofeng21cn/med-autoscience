from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_loader import LoadedDisplayTemplate


DEPENDENCY_REQUIREMENT_PROFILE_REF = (
    "display-packs/fenggaolab.org.medical-display-core/renderer_dependency_profile.json"
)
DEPENDENCY_LOCK_REF = "paper/build/dependency_environment_lock.json"
DEPENDENCY_RECEIPT_REF = "paper/build/dependency_environment_receipt.json"
DEPENDENCY_RUN_CONTEXT_REF = "paper/build/dependency_run_context.json"
DEPENDENCY_SUBSTRATE_CONTRACT_REF = (
    "opl-framework:contracts/opl-framework/runtime-environment-substrate-contract.json"
)
DEPENDENCY_SUBSTRATE_TARGET_DOC_REF = "docs/runtime/designs/opl_dependency_environment_substrate_target.md"


FORBIDDEN_DEPENDENCY_ENVIRONMENT_CLAIMS = {
    "dependency_environment_receipt_means_publication_ready": False,
    "dependency_environment_lock_means_visual_audit_clear": False,
    "dependency_environment_prepared_means_scientific_correctness": False,
    "renderer_dependency_profile_can_write_study_truth": False,
}


class DependencyEnvironmentNotPrepared(RuntimeError):
    def __init__(self, status: Mapping[str, Any]):
        self.status = dict(status)
        super().__init__(str(self.status.get("blocker_reason") or "dependency environment is not prepared"))


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else None


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def load_renderer_dependency_profile(*, repo_root: Path) -> dict[str, Any]:
    payload = _read_json_object(repo_root / DEPENDENCY_REQUIREMENT_PROFILE_REF)
    return payload or {}


def _profile_template_ids(profile_entry: Mapping[str, Any]) -> set[str]:
    ids = {
        _text(value)
        for value in [
            *_list(profile_entry.get("template_ids")),
            *_list(profile_entry.get("template_requirement_refs")),
        ]
        if _text(value)
    }
    scoped_templates = _mapping(profile_entry.get("scoped_templates"))
    ids.update(_text(value) for value in _list(scoped_templates.get("template_ids")) if _text(value))
    ids.update(_text(value) for value in _list(scoped_templates.get("template_requirement_refs")) if _text(value))
    return ids


def _record_template_ids(record: LoadedDisplayTemplate) -> set[str]:
    manifest = record.template_manifest
    return {manifest.template_id, manifest.full_template_id}


def _profile_entry_matches_record(profile_entry: Mapping[str, Any], record: LoadedDisplayTemplate) -> bool:
    template_ids = _profile_template_ids(profile_entry)
    if template_ids:
        return bool(template_ids & _record_template_ids(record))
    return (
        _text(profile_entry.get("renderer_family")) == record.template_manifest.renderer_family
        and _text(profile_entry.get("execution_mode")) == record.template_manifest.execution_mode
    )


def dependency_profile_entries_for_template_ids(
    *,
    repo_root: Path,
    template_ids: set[str],
) -> list[dict[str, Any]]:
    profile = load_renderer_dependency_profile(repo_root=repo_root)
    entries: list[dict[str, Any]] = []
    seen_profile_ids: set[str] = set()
    for profile_entry in _list(profile.get("profiles")):
        entry = _mapping(profile_entry)
        profile_id = _text(entry.get("profile_id"))
        if not profile_id or profile_id in seen_profile_ids:
            continue
        scoped_ids = _profile_template_ids(entry)
        if scoped_ids and scoped_ids & template_ids:
            entries.append(entry)
            seen_profile_ids.add(profile_id)
    return entries


def dependency_profile_entries_for_records(
    *,
    repo_root: Path,
    records: list[LoadedDisplayTemplate],
) -> list[dict[str, Any]]:
    profile = load_renderer_dependency_profile(repo_root=repo_root)
    scoped_entries: list[dict[str, Any]] = []
    generic_entries: list[dict[str, Any]] = []
    seen_profile_ids: set[str] = set()
    for profile_entry in _list(profile.get("profiles")):
        entry = _mapping(profile_entry)
        profile_id = _text(entry.get("profile_id"))
        if not profile_id or profile_id in seen_profile_ids:
            continue
        matching_records = [
            record
            for record in records
            if _profile_entry_matches_record(entry, record)
        ]
        if not matching_records:
            continue
        if _profile_template_ids(entry):
            scoped_entries.append(entry)
            seen_profile_ids.add(profile_id)
            continue
        generic_entries.append(entry)
        seen_profile_ids.add(profile_id)
    scoped_template_ids = set().union(
        *(_profile_template_ids(entry) for entry in scoped_entries),
    ) if scoped_entries else set()
    unscoped_records = [
        record
        for record in records
        if not (_record_template_ids(record) & scoped_template_ids)
    ]
    entries = list(scoped_entries)
    seen_entry_ids = {_text(entry.get("profile_id")) for entry in entries}
    for entry in generic_entries:
        profile_id = _text(entry.get("profile_id"))
        if profile_id in seen_entry_ids:
            continue
        if any(_profile_entry_matches_record(entry, record) for record in unscoped_records):
            entries.append(entry)
            seen_entry_ids.add(profile_id)
    return entries


def dependency_requirements_for_profile_entries(entries: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for entry in entries:
        package_requirements: list[dict[str, Any]] = []
        language_packages = _mapping(entry.get("language_packages"))
        for language, packages in language_packages.items():
            for package in _list(packages):
                package_map = _mapping(package)
                name = _text(package_map.get("name"))
                if not name:
                    continue
                package_requirements.append(
                    {
                        "language": _text(language),
                        "name": name,
                        "required": package_map.get("required") is True,
                        "role": _text(package_map.get("role")),
                        "template_ids": [
                            _text(value) for value in _list(package_map.get("template_ids")) if _text(value)
                        ],
                    }
                )
        requirements.append(
            {
                "profile_id": _text(entry.get("profile_id")),
                "renderer_family": _text(entry.get("renderer_family")),
                "execution_mode": _text(entry.get("execution_mode")),
                "surface_role": _text(entry.get("surface_role")),
                "template_ids": sorted(_profile_template_ids(entry)),
                "mature_dependency_intent": _mapping(entry.get("mature_dependency_intent")),
                "language_package_requirements": package_requirements,
                "run_context_requirements": _mapping(entry.get("run_context_requirements")),
                "render_contract": _mapping(entry.get("render_contract")),
            }
        )
    return requirements


def dependency_requirements_for_records(
    *,
    repo_root: Path,
    records: list[LoadedDisplayTemplate],
) -> list[dict[str, Any]]:
    return dependency_requirements_for_profile_entries(
        dependency_profile_entries_for_records(repo_root=repo_root, records=records)
    )


def dependency_requirements_for_template_ids(
    *,
    repo_root: Path,
    template_ids: set[str],
) -> list[dict[str, Any]]:
    return dependency_requirements_for_profile_entries(
        dependency_profile_entries_for_template_ids(repo_root=repo_root, template_ids=template_ids)
    )


def _workspace_ref_path(ref: str, *, paper_root: Path) -> Path:
    normalized = str(ref or "").strip()
    if not normalized:
        raise ValueError("dependency environment ref must be non-empty")
    path = Path(normalized).expanduser()
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] == paper_root.name:
        return (paper_root.parent / path).resolve()
    if path.parts and path.parts[0] == "paper":
        return (paper_root.parent / path).resolve()
    return (paper_root / path).resolve()


def _status_route(status: str, failure_class: str) -> str:
    if status == "lock_stale" or failure_class == "lock_stale":
        return "opl_runtime_env_lock_refresh_required"
    if status == "permission_required" or failure_class == "permission_required":
        return "human_or_admin_gate_required"
    return "opl_runtime_env_doctor"


def dependency_environment_finding(status: Mapping[str, Any]) -> dict[str, Any] | None:
    if status.get("required") is not True or status.get("status") == "prepared":
        return None
    route_hint = str(status.get("route_hint") or "opl_runtime_env_doctor")
    return {
        "code": "dependency_environment_not_prepared",
        "layer": "dependency_environment",
        "repair_owner": "OPL Framework",
        "route_hint": route_hint,
        "failure_class": str(status.get("failure_class") or "missing_prepared_receipt"),
        "doctor_status": str(status.get("doctor_status") or "planned_missing"),
        "blocks_render": True,
        "dependency_environment": {
            "requirement_profile_ref": str(status.get("requirement_profile_ref") or ""),
            "lock_ref": str(status.get("lock_ref") or ""),
            "receipt_ref": str(status.get("receipt_ref") or ""),
            "run_context_ref": str(status.get("run_context_ref") or ""),
            "status": str(status.get("status") or ""),
        },
        "authority_boundary": {
            "dependency_environment_issue_owner": "OPL Framework",
            "mas_may_consume_refs_only": True,
            "can_authorize_publication_readiness": False,
            "can_replace_visual_audit": False,
            "can_mutate_data_or_statistics": False,
        },
    }


def dependency_environment_status(
    *,
    repo_root: Path,
    paper_root: Path | None,
    records: list[LoadedDisplayTemplate],
) -> dict[str, Any]:
    requirement_path = repo_root / DEPENDENCY_REQUIREMENT_PROFILE_REF
    dependency_requirements = dependency_requirements_for_records(repo_root=repo_root, records=records)
    required = bool(dependency_requirements)
    base: dict[str, Any] = {
        "surface_kind": "display_pack_dependency_environment_status",
        "required": required,
        "owner": "OPL Framework",
        "consumer": "MedAutoScience display pack",
        "requirement_profile_ref": DEPENDENCY_REQUIREMENT_PROFILE_REF,
        "requirement_profile_status": "present" if requirement_path.is_file() else "missing",
        "dependency_requirements": dependency_requirements,
        "lock_ref": DEPENDENCY_LOCK_REF,
        "receipt_ref": DEPENDENCY_RECEIPT_REF,
        "run_context_ref": DEPENDENCY_RUN_CONTEXT_REF,
        "contract_ref": DEPENDENCY_SUBSTRATE_CONTRACT_REF,
        "target_doc_ref": DEPENDENCY_SUBSTRATE_TARGET_DOC_REF,
        "doctor_status": "not_required" if not required else "not_checked",
        "authority_boundary": dependency_environment_authority_boundary(),
        "forbidden_claims": dict(FORBIDDEN_DEPENDENCY_ENVIRONMENT_CLAIMS),
    }
    if not required:
        return {**base, "status": "not_required", "failure_class": ""}
    if paper_root is None:
        return {
            **base,
            "status": "missing_paper_root",
            "failure_class": "missing_paper_root",
            "doctor_status": "planned_missing",
            "route_hint": "provide_paper_root_then_opl_runtime_env_readback",
            "blocker_reason": "dependency environment receipt cannot be read without paper_root",
        }
    normalized_paper_root = Path(paper_root).expanduser().resolve()
    lock_path = _workspace_ref_path(DEPENDENCY_LOCK_REF, paper_root=normalized_paper_root)
    receipt_path = _workspace_ref_path(DEPENDENCY_RECEIPT_REF, paper_root=normalized_paper_root)
    run_context_path = _workspace_ref_path(DEPENDENCY_RUN_CONTEXT_REF, paper_root=normalized_paper_root)
    lock_payload = _read_json_object(lock_path)
    receipt_payload = _read_json_object(receipt_path)
    run_context_payload = _read_json_object(run_context_path)
    base.update(
        {
            "lock_status": "present" if lock_payload is not None else "missing",
            "receipt_status": "present" if receipt_payload is not None else "missing",
            "run_context_status": "present" if run_context_payload is not None else "missing",
        }
    )
    if receipt_payload is None:
        return {
            **base,
            "status": "missing_prepared_receipt",
            "failure_class": "missing_prepared_receipt",
            "doctor_status": "planned_missing",
            "route_hint": "opl_runtime_env_doctor",
            "blocker_reason": "OPL dependency environment prepared receipt is missing",
        }
    receipt_status = str(receipt_payload.get("status") or "").strip() or "unknown"
    failure_class = str(receipt_payload.get("failure_class") or "").strip()
    run_context_ref = str(receipt_payload.get("run_context_ref") or DEPENDENCY_RUN_CONTEXT_REF).strip()
    if receipt_status != "prepared":
        route_hint = _status_route(receipt_status, failure_class)
        return {
            **base,
            "status": receipt_status,
            "failure_class": failure_class or receipt_status,
            "doctor_status": "finding",
            "route_hint": route_hint,
            "receipt_payload_status": receipt_status,
            "receipt_failure_route": route_hint,
            "blocker_reason": "OPL dependency environment receipt is not prepared",
        }
    if not run_context_ref:
        return {
            **base,
            "status": "missing_run_context_ref",
            "failure_class": "missing_run_context_ref",
            "doctor_status": "finding",
            "route_hint": "opl_runtime_env_run_context",
            "blocker_reason": "OPL dependency environment receipt is prepared but run_context_ref is missing",
        }
    run_context_path = _workspace_ref_path(run_context_ref, paper_root=normalized_paper_root)
    run_context_payload = _read_json_object(run_context_path)
    if run_context_payload is None:
        return {
            **base,
            "status": "missing_run_context",
            "failure_class": "missing_run_context",
            "doctor_status": "finding",
            "run_context_ref": run_context_ref,
            "run_context_status": "missing",
            "route_hint": "opl_runtime_env_run_context",
            "blocker_reason": "OPL dependency environment run context is missing",
        }
    return {
        **base,
        "status": "prepared",
        "failure_class": "",
        "doctor_status": "pass",
        "receipt_payload_status": receipt_status,
        "run_context_ref": run_context_ref,
        "run_context_status": "present",
        "run_context_fingerprint": str(
            run_context_payload.get("execution_fingerprint")
            or run_context_payload.get("run_context_fingerprint")
            or ""
        ),
        "prepared_receipt": {
            "lock_ref": str(receipt_payload.get("lock_ref") or DEPENDENCY_LOCK_REF),
            "environment_ref": str(receipt_payload.get("environment_ref") or ""),
            "cache_key": str(receipt_payload.get("cache_key") or ""),
            "target_platform": str(receipt_payload.get("target_platform") or ""),
        },
    }


def load_dependency_run_context(*, paper_root: Path, status: Mapping[str, Any]) -> dict[str, Any]:
    if status.get("status") != "prepared":
        raise DependencyEnvironmentNotPrepared(status)
    run_context_ref = str(status.get("run_context_ref") or DEPENDENCY_RUN_CONTEXT_REF)
    run_context = _read_json_object(_workspace_ref_path(run_context_ref, paper_root=paper_root))
    if run_context is None:
        raise DependencyEnvironmentNotPrepared(
            {
                **dict(status),
                "status": "missing_run_context",
                "failure_class": "missing_run_context",
                "route_hint": "opl_runtime_env_run_context",
            }
        )
    return run_context


def apply_dependency_run_context(
    *,
    argv: list[str],
    env: Mapping[str, str],
    run_context: Mapping[str, Any],
) -> tuple[list[str], dict[str, str]]:
    prefix = [str(item) for item in list(run_context.get("argv_prefix") or []) if str(item).strip()]
    binary_paths = dict(run_context.get("binary_paths") or {})
    resolved_argv = list(argv)
    if resolved_argv and str(resolved_argv[0]) in binary_paths:
        resolved_argv[0] = str(binary_paths[str(resolved_argv[0])])
    if prefix:
        resolved_argv = [*prefix, *resolved_argv]
    env_updates = dict(run_context.get("env_vars") or run_context.get("environment_variables") or {})
    return resolved_argv, {**dict(env), **{str(key): str(value) for key, value in env_updates.items()}}


def require_prepared_dependency_environment(status: Mapping[str, Any]) -> None:
    if status.get("required") is True and status.get("status") != "prepared":
        raise DependencyEnvironmentNotPrepared(status)


def dependency_environment_authority_boundary() -> dict[str, Any]:
    return {
        "canonical_substrate_owner": "OPL Framework",
        "mas_consumes_dependency_environment_refs_only": True,
        "renderer_code_must_not_install_packages": True,
        "can_authorize_publication_readiness": False,
        "can_replace_visual_audit": False,
        "can_replace_owner_receipt": False,
        "can_mutate_data_or_statistics": False,
    }

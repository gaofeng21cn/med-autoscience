from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import json
import os
import subprocess

from med_autoscience.display_pack_dependency_environment import (
    load_renderer_dependency_profile,
)
from med_autoscience.display_pack_gallery_catalog import TemplateRecord
from med_autoscience.display_pack_gallery_parts import paths

_PACKAGE_CHECK_CACHE: dict[tuple[str, str, tuple[str, ...]], list[str]] = {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def load_gallery_dependency_run_context(path_text: str) -> dict[str, Any]:
    if not path_text:
        return {}
    path = Path(path_text).expanduser()
    if not path.is_file():
        raise FileNotFoundError(
            f"gallery dependency run-context not found: {path}; run OPL prepare/doctor for the MAS display profile"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"gallery dependency run-context must be a JSON object: {path}")
    return dict(payload)


def required_profile_entries_for_record(record: TemplateRecord) -> list[dict[str, Any]]:
    profile = load_renderer_dependency_profile(repo_root=paths.REPO_ROOT)
    template_ids = {record.template_id, record.full_template_id}
    scoped_entries: list[dict[str, Any]] = []
    generic_entries: list[dict[str, Any]] = []
    for raw_entry in _list(profile.get("profiles")):
        entry = _mapping(raw_entry)
        profile_id = _text(entry.get("profile_id"))
        if not profile_id:
            continue
        entry_template_ids = _entry_template_ids(entry)
        if entry_template_ids:
            if entry_template_ids & template_ids:
                scoped_entries.append(entry)
            continue
        if _entry_package_template_ids(entry) & template_ids:
            generic_entries.append(entry)
            continue
        if (
            _text(entry.get("renderer_family")) == record.renderer_family
            and _text(entry.get("execution_mode")) == record.execution_mode
            and _text(entry.get("entrypoint_pattern")) == record.entrypoint
        ):
            generic_entries.append(entry)
    return _dedupe_profile_entries([*scoped_entries, *generic_entries])


def required_profile_ids_for_record(record: TemplateRecord) -> list[str]:
    return [
        profile_id
        for profile_id in (_text(entry.get("profile_id")) for entry in required_profile_entries_for_record(record))
        if profile_id
    ]


def required_r_packages_for_profile_entries(entries: list[Mapping[str, Any]]) -> list[str]:
    packages: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        r_packages = _list(_mapping(entry.get("language_packages")).get("r"))
        for package in r_packages:
            package_name = _text(_mapping(package).get("name"))
            if package_name and package_name not in seen:
                packages.append(package_name)
                seen.add(package_name)
    return packages


def _entry_template_ids(entry: Mapping[str, Any]) -> set[str]:
    ids = {
        _text(value)
        for value in [
            *_list(entry.get("template_ids")),
            *_list(entry.get("template_requirement_refs")),
        ]
        if _text(value)
    }
    scoped_templates = _mapping(entry.get("scoped_templates"))
    ids.update(_text(value) for value in _list(scoped_templates.get("template_ids")) if _text(value))
    ids.update(_text(value) for value in _list(scoped_templates.get("template_requirement_refs")) if _text(value))
    return ids


def _entry_package_template_ids(entry: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for packages in _mapping(entry.get("language_packages")).values():
        for package in _list(packages):
            package_ids = _list(_mapping(package).get("template_ids"))
            ids.update(_text(value) for value in package_ids if _text(value))
    return ids


def _dedupe_profile_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        profile_id = _text(entry.get("profile_id"))
        if not profile_id or profile_id in seen:
            continue
        deduped.append(entry)
        seen.add(profile_id)
    return deduped


def _run_context_fingerprint(run_context: Mapping[str, Any]) -> str:
    return _text(
        run_context.get("execution_fingerprint")
        or run_context.get("run_context_fingerprint")
    )


def _run_context_r_library(run_context: Mapping[str, Any]) -> str:
    env_vars = _mapping(run_context.get("env_vars") or run_context.get("environment_variables"))
    return _text(env_vars.get("R_LIBS_USER") or run_context.get("managed_r_library_path"))


def _run_context_rscript(run_context: Mapping[str, Any]) -> str:
    return _text(_mapping(run_context.get("binary_paths")).get("Rscript"))


def _selected_profile_ids(run_context: Mapping[str, Any]) -> set[str]:
    return {_text(value) for value in _list(run_context.get("selected_requirement_profile_ids")) if _text(value)}


def validate_gallery_dependency_run_context(
    *,
    record: TemplateRecord,
    run_context: Mapping[str, Any],
    expected_fingerprint: str,
) -> dict[str, str]:
    entries = required_profile_entries_for_record(record)
    profile_ids = [
        profile_id
        for profile_id in (_text(entry.get("profile_id")) for entry in entries)
        if profile_id
    ]
    if not profile_ids:
        return {}
    if _text(run_context.get("status")) != "prepared":
        raise RuntimeError(
            f"{record.template_id} requires OPL-prepared dependency run-context; "
            "run `opl runtime env prepare --domain mas --profile display --apply` or OPL doctor"
        )
    actual_fingerprint = _run_context_fingerprint(run_context)
    if not actual_fingerprint:
        raise RuntimeError(
            f"{record.template_id} dependency run-context is missing execution fingerprint; "
            "rerun OPL prepare/doctor for the MAS display profile"
        )
    if expected_fingerprint and actual_fingerprint != expected_fingerprint:
        raise RuntimeError(
            f"{record.template_id} dependency run-context fingerprint mismatch: "
            f"expected {expected_fingerprint}, got {actual_fingerprint}; rerun OPL prepare/doctor"
        )
    missing_profiles = sorted(set(profile_ids) - _selected_profile_ids(run_context))
    if missing_profiles:
        raise RuntimeError(
            f"{record.template_id} dependency run-context profile mismatch; missing "
            f"{', '.join(missing_profiles)}. Run OPL prepare with the MAS display requirement profile."
        )
    rscript_path = _run_context_rscript(run_context)
    r_lib_path = _run_context_r_library(run_context)
    if not rscript_path:
        raise RuntimeError(
            f"{record.template_id} dependency run-context is missing binary_paths.Rscript; run OPL prepare/doctor"
        )
    if not r_lib_path:
        raise RuntimeError(
            f"{record.template_id} dependency run-context is missing R_LIBS_USER/managed R library; run OPL prepare/doctor"
        )
    missing_packages = _missing_required_r_packages(
        rscript_path=Path(rscript_path).expanduser(),
        r_lib_path=r_lib_path,
        package_names=required_r_packages_for_profile_entries(entries),
    )
    if missing_packages:
        raise RuntimeError(
            f"{record.template_id} dependency run-context managed R library is missing packages "
            f"{', '.join(missing_packages)}; run OPL prepare/doctor for the MAS display profile"
        )
    return {
        "status": "prepared",
        "required_profile_ids": ",".join(profile_ids),
        "run_context_fingerprint": actual_fingerprint,
        "rscript_path": rscript_path,
        "r_libs_user": r_lib_path,
    }


def _missing_required_r_packages(
    *,
    rscript_path: Path,
    r_lib_path: str,
    package_names: list[str],
) -> list[str]:
    checked_packages = [package for package in package_names if package != "grid"]
    if not checked_packages:
        return []
    cache_key = (str(rscript_path), r_lib_path, tuple(checked_packages))
    if cache_key in _PACKAGE_CHECK_CACHE:
        return list(_PACKAGE_CHECK_CACHE[cache_key])
    r_expr = "\n".join(
        [
            "packages <- commandArgs(trailingOnly = TRUE)",
            "missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]",
            "if (length(missing)) { cat(paste(missing, collapse = ',')); quit(status = 2) }",
        ]
    )
    result = subprocess.run(
        [str(rscript_path), "-e", r_expr, *checked_packages],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env={**dict(os.environ), "R_LIBS_USER": r_lib_path},
    )
    if result.returncode == 0:
        _PACKAGE_CHECK_CACHE[cache_key] = []
        return []
    if result.returncode == 2:
        missing = [item for item in result.stdout.strip().split(",") if item]
        _PACKAGE_CHECK_CACHE[cache_key] = missing
        return missing
    raise RuntimeError(
        "failed to validate OPL managed R library packages with Rscript; "
        f"exit={result.returncode}; stderr={result.stderr.strip()}"
    )

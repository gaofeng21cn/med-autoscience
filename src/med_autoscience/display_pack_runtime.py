from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from functools import lru_cache
import importlib
from pathlib import Path
import sys

from med_autoscience.display_pack_loader import (
    LoadedDisplayTemplate,
    load_enabled_local_display_template_records,
)


UNIFIED_HOST_MATERIALIZATION_ENTRYPOINT = (
    "med_autoscience.controllers.display_surface_materialization:materialize_display_surface"
)


@lru_cache(maxsize=None)
def _template_runtime_index(repo_root: Path) -> dict[str, LoadedDisplayTemplate]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    records = load_enabled_local_display_template_records(normalized_repo_root)
    return {
        record.template_manifest.full_template_id: record
        for record in records
    }


def resolve_display_template_runtime(*, repo_root: Path, template_id: str) -> LoadedDisplayTemplate:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_template_id = str(template_id).strip()
    if "::" not in normalized_template_id:
        matches = [
            full_template_id
            for full_template_id, record in _template_runtime_index(normalized_repo_root).items()
            if record.template_manifest.template_id == normalized_template_id
        ]
        if len(matches) == 1:
            normalized_template_id = matches[0]
    try:
        return _template_runtime_index(normalized_repo_root)[normalized_template_id]
    except KeyError as exc:
        raise ValueError(f"unknown display template runtime `{template_id}`") from exc


@contextmanager
def _pack_src_on_sys_path(pack_root: Path):
    src_root = pack_root / "src"
    if not src_root.is_dir():
        yield
        return

    src_root_str = str(src_root)
    already_present = src_root_str in sys.path
    if not already_present:
        sys.path.insert(0, src_root_str)
        importlib.invalidate_caches()
    try:
        yield
    finally:
        if not already_present:
            try:
                sys.path.remove(src_root_str)
            except ValueError:
                pass


def load_python_plugin_callable(
    *,
    repo_root: Path,
    template_id: str,
) -> Callable[..., object]:
    runtime = resolve_display_template_runtime(repo_root=repo_root, template_id=template_id)
    if runtime.template_manifest.execution_mode != "python_plugin":
        raise ValueError(
            f"template `{template_id}` does not use python_plugin execution mode"
        )

    module_name, function_name = runtime.template_manifest.entrypoint.split(":", 1)
    with _pack_src_on_sys_path(runtime.pack_root):
        module = importlib.import_module(module_name)
    target = getattr(module, function_name)
    if not callable(target):
        raise TypeError(f"entrypoint `{runtime.template_manifest.entrypoint}` is not callable")
    return target


def resolve_python_plugin_callable(
    *,
    repo_root: Path,
    template_id: str,
) -> Callable[..., object] | None:
    runtime = resolve_display_template_runtime(repo_root=repo_root, template_id=template_id)
    if runtime.template_manifest.entrypoint == UNIFIED_HOST_MATERIALIZATION_ENTRYPOINT:
        return None
    return load_python_plugin_callable(repo_root=repo_root, template_id=template_id)

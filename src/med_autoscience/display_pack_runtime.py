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
from med_autoscience.display_pack_canonical_catalog import load_canonical_template_catalog


UNIFIED_HOST_MATERIALIZATION_ENTRYPOINT = (
    "med_autoscience.controllers.display_surface_materialization:materialize_display_surface"
)


@lru_cache(maxsize=None)
def _template_runtime_index(
    repo_root: str,
    paper_root: str | None,
    inventory_scope: str,
) -> dict[str, LoadedDisplayTemplate]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve() if paper_root is not None else None
    records = load_enabled_local_display_template_records(
        normalized_repo_root,
        paper_root=normalized_paper_root,
        inventory_scope=inventory_scope,
    )
    return {
        record.template_manifest.full_template_id: record
        for record in records
    }


def resolve_display_template_runtime(
    *,
    repo_root: Path,
    template_id: str,
    paper_root: Path | None = None,
    inventory_scope: str = "canonical",
) -> LoadedDisplayTemplate:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve() if paper_root is not None else None
    normalized_template_id = str(template_id).strip()
    runtime_index = _template_runtime_index(
        str(normalized_repo_root),
        str(normalized_paper_root) if normalized_paper_root is not None else None,
        inventory_scope,
    )
    if "::" not in normalized_template_id:
        matches = [
            full_template_id
            for full_template_id, record in runtime_index.items()
            if record.template_manifest.template_id == normalized_template_id
        ]
        if len(matches) == 1:
            normalized_template_id = matches[0]
    if normalized_template_id not in runtime_index:
        normalized_template_id = _canonicalized_runtime_template_id(
            runtime_index,
            requested_template_id=normalized_template_id,
        )
    try:
        return runtime_index[normalized_template_id]
    except KeyError as exc:
        raise ValueError(f"unknown display template runtime `{template_id}`") from exc


def _canonicalized_runtime_template_id(
    runtime_index: dict[str, LoadedDisplayTemplate],
    *,
    requested_template_id: str,
) -> str:
    requested_short_id = requested_template_id.split("::")[-1]
    for record in runtime_index.values():
        catalog = load_canonical_template_catalog(record.pack_root)
        if catalog is None:
            continue
        entry = catalog.entries_by_template_id.get(requested_short_id)
        if entry is None or entry.migration_status != "migrated_alias":
            continue
        canonical_full_id = f"{record.pack_manifest.pack_id}::{entry.canonical_template_id}"
        if canonical_full_id in runtime_index:
            return canonical_full_id
    return requested_template_id


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
    paper_root: Path | None = None,
) -> Callable[..., object]:
    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        template_id=template_id,
        paper_root=paper_root,
        inventory_scope="canonical",
    )
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
    paper_root: Path | None = None,
) -> Callable[..., object] | None:
    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        template_id=template_id,
        paper_root=paper_root,
        inventory_scope="canonical",
    )
    if runtime.template_manifest.entrypoint == UNIFIED_HOST_MATERIALIZATION_ENTRYPOINT:
        return None
    return load_python_plugin_callable(
        repo_root=repo_root,
        template_id=template_id,
        paper_root=paper_root,
    )

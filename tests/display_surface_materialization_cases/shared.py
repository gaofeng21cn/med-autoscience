from __future__ import annotations

from pathlib import Path

from med_autoscience import display_pack_loader, display_registry

from . import shared_base as _shared_base
from . import registry_id_helpers as _registry_id_helpers
from . import workspace_surface_fixtures as _workspace_surface_fixtures
from . import layout_sidecar_fixtures as _layout_sidecar_fixtures


def current_scholarskills_core_pack_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    workspace_root = repo_root.parent.parent if repo_root.parent.name in {".worktrees", "_worktrees"} else repo_root.parent
    return workspace_root / "mas-scholar-skills" / "packs" / "medical-display-core"


def use_current_scholarskills_display_pack(monkeypatch) -> Path:
    pack_root = current_scholarskills_core_pack_root().resolve()
    source_root = pack_root.parents[1]
    if not (source_root / ".git").exists() or not (pack_root / "display_pack.toml").is_file():
        raise AssertionError(f"current ScholarSkills display pack is unavailable: {pack_root}")

    original_resolver = display_pack_loader._resolve_git_repo_source_root

    def resolve_git_repo_source_root(anchor_root: Path, raw_path: str) -> Path:
        if raw_path == "../mas-scholar-skills":
            return source_root
        return original_resolver(anchor_root, raw_path)

    monkeypatch.setattr(display_pack_loader, "_resolve_git_repo_source_root", resolve_git_repo_source_root)
    display_registry._active_template_manifests.cache_clear()
    display_registry._active_registry_state.cache_clear()
    return pack_root

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_registry_id_helpers)
_module_reexport(_workspace_surface_fixtures)
_module_reexport(_layout_sidecar_fixtures)

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]

from __future__ import annotations

from pathlib import Path

from med_autoscience import display_registry
from med_autoscience.display_pack_paths import core_medical_display_pack_root

from . import shared_base as _shared_base
from . import registry_id_helpers as _registry_id_helpers
from . import workspace_surface_fixtures as _workspace_surface_fixtures
from . import layout_sidecar_fixtures as _layout_sidecar_fixtures


def current_scholarskills_core_pack_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return core_medical_display_pack_root(repo_root)


def use_current_scholarskills_display_pack() -> Path:
    pack_root = current_scholarskills_core_pack_root().resolve()
    source_root = pack_root.parents[1]
    if not (source_root / ".git").exists() or not (pack_root / "display_pack.toml").is_file():
        raise AssertionError(f"current ScholarSkills display pack is unavailable: {pack_root}")
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

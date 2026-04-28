from __future__ import annotations

from . import shared_base as _shared_base
from . import registry_id_helpers as _registry_id_helpers
from . import workspace_surface_fixtures as _workspace_surface_fixtures
from . import layout_sidecar_fixtures as _layout_sidecar_fixtures
from . import illustration_payload_fixtures as _illustration_payload_fixtures
from . import atlas_payload_fixtures as _atlas_payload_fixtures
from . import genomic_payload_fixtures as _genomic_payload_fixtures
from . import response_payload_fixtures as _response_payload_fixtures
from . import transportability_payload_fixtures as _transportability_payload_fixtures

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_registry_id_helpers)
_module_reexport(_workspace_surface_fixtures)
_module_reexport(_layout_sidecar_fixtures)
_module_reexport(_illustration_payload_fixtures)
_module_reexport(_atlas_payload_fixtures)
_module_reexport(_genomic_payload_fixtures)
_module_reexport(_response_payload_fixtures)
_module_reexport(_transportability_payload_fixtures)

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]

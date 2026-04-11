from __future__ import annotations

import importlib
from types import SimpleNamespace


def test_default_managed_runtime_backend_registry_exposes_med_deepscientist() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")

    backend = module.get_managed_runtime_backend(module.DEFAULT_MANAGED_RUNTIME_BACKEND_ID)

    assert backend.BACKEND_ID == "med_deepscientist"
    assert backend.ENGINE_ID == "med-deepscientist"
    assert "med_deepscientist" in module.registered_managed_runtime_backend_ids()


def test_runtime_backend_resolves_registered_backend_from_engine_and_explicit_backend_id() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")
    fake_backend = SimpleNamespace(BACKEND_ID="hermes", ENGINE_ID="hermes")
    module.register_managed_runtime_backend(fake_backend)

    assert module.runtime_backend_id_from_execution({"engine": "hermes"}) == "hermes"
    assert module.runtime_backend_id_from_execution({"runtime_backend_id": "hermes"}) == "hermes"
    assert module.resolve_managed_runtime_backend({"runtime_backend": "hermes"}) is fake_backend
    assert module.is_managed_research_execution(
        {"runtime_backend_id": "hermes", "auto_entry": "on_managed_research_intent"}
    )


def test_runtime_backend_reports_unknown_explicit_backend_id_without_downgrading_to_engine_guess() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")

    assert module.explicit_runtime_backend_id({"runtime_backend_id": "unknown-backend"}) == "unknown-backend"
    assert module.resolve_managed_runtime_backend({"runtime_backend_id": "unknown-backend"}) is None
    assert module.runtime_backend_id_from_execution({"runtime_backend_id": "unknown-backend"}) == "unknown-backend"

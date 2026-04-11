from __future__ import annotations

import importlib
from pathlib import Path

import pytest


class _BackendStub:
    def __init__(self, *, backend_id: str, engine_id: str) -> None:
        self.BACKEND_ID = backend_id
        self.ENGINE_ID = engine_id

    def resolve_daemon_url(self, *, runtime_root: Path) -> str:
        return f"file://{runtime_root}"

    def create_quest(self, *, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        return {"runtime_root": str(runtime_root), "payload": payload}

    def resume_quest(self, *, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        return {"runtime_root": str(runtime_root), "quest_id": quest_id, "source": source}

    def pause_quest(self, *, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        return {"runtime_root": str(runtime_root), "quest_id": quest_id, "source": source}

    def stop_quest(
        self,
        *,
        quest_id: str,
        source: str,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
    ) -> dict[str, object]:
        return {"quest_id": quest_id, "source": source, "daemon_url": daemon_url, "runtime_root": str(runtime_root or "")}

    def get_quest_session(
        self,
        *,
        quest_id: str,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        timeout: int | None = None,
    ) -> dict[str, object]:
        return {"quest_id": quest_id, "daemon_url": daemon_url, "runtime_root": str(runtime_root or ""), "timeout": timeout}

    def inspect_quest_live_runtime(
        self,
        *,
        quest_id: str,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        timeout: int | None = None,
    ) -> dict[str, object]:
        return {"quest_id": quest_id, "daemon_url": daemon_url, "runtime_root": str(runtime_root or ""), "timeout": timeout}

    def inspect_quest_live_execution(
        self,
        *,
        quest_id: str,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        timeout: int | None = None,
    ) -> dict[str, object]:
        return {"quest_id": quest_id, "daemon_url": daemon_url, "runtime_root": str(runtime_root or ""), "timeout": timeout}

    def update_quest_startup_context(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        startup_contract: dict[str, object] | None = None,
        requested_baseline_ref: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return {
            "runtime_root": str(runtime_root),
            "quest_id": quest_id,
            "startup_contract": startup_contract,
            "requested_baseline_ref": requested_baseline_ref,
        }

    def artifact_complete_quest(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        summary: str,
    ) -> dict[str, object]:
        return {"runtime_root": str(runtime_root), "quest_id": quest_id, "summary": summary}

    def artifact_interact(
        self,
        *,
        runtime_root: Path,
        quest_id: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        return {"runtime_root": str(runtime_root), "quest_id": quest_id, "payload": payload}


def test_default_managed_runtime_backend_registry_exposes_med_deepscientist_and_hermes() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")

    backend = module.get_managed_runtime_backend(module.DEFAULT_MANAGED_RUNTIME_BACKEND_ID)
    hermes_backend = module.get_managed_runtime_backend("hermes")

    assert backend.BACKEND_ID == "hermes"
    assert backend.ENGINE_ID == "hermes"
    assert "med_deepscientist" in module.registered_managed_runtime_backend_ids()
    assert hermes_backend.BACKEND_ID == "hermes"
    assert hermes_backend.ENGINE_ID == "hermes"
    assert "hermes" in module.registered_managed_runtime_backend_ids()
    assert module.controlled_research_backend_metadata_for_backend_id("hermes") == (
        "med_deepscientist",
        "med-deepscientist",
    )


def test_runtime_backend_resolves_registered_backend_from_engine_and_explicit_backend_id() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")
    fake_backend = _BackendStub(backend_id="demo_backend", engine_id="demo-engine")
    module.register_managed_runtime_backend(fake_backend)

    assert module.runtime_backend_id_from_execution({"engine": "demo-engine"}) == "demo_backend"
    assert module.runtime_backend_id_from_execution({"runtime_backend_id": "demo_backend"}) == "demo_backend"
    assert module.resolve_managed_runtime_backend({"runtime_backend": "demo_backend"}) is fake_backend
    assert module.is_managed_research_execution(
        {"runtime_backend_id": "demo_backend", "auto_entry": "on_managed_research_intent"}
    )


def test_runtime_backend_reports_unknown_explicit_backend_id_without_downgrading_to_engine_guess() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")

    assert module.explicit_runtime_backend_id({"runtime_backend_id": "unknown-backend"}) == "unknown-backend"
    assert module.resolve_managed_runtime_backend({"runtime_backend_id": "unknown-backend"}) is None
    assert module.runtime_backend_id_from_execution({"runtime_backend_id": "unknown-backend"}) == "unknown-backend"


def test_runtime_backend_rejects_backend_missing_required_callable() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")

    class IncompleteBackend:
        BACKEND_ID = "broken"
        ENGINE_ID = "broken-engine"

    with pytest.raises(ValueError, match="missing callable `resolve_daemon_url`"):
        module.register_managed_runtime_backend(IncompleteBackend())


def test_runtime_backend_rejects_backend_with_signature_drift() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")

    class SignatureDriftBackend(_BackendStub):
        def artifact_interact(  # type: ignore[override]
            self,
            *,
            runtime_root: Path,
            quest_id: str,
            message: str,
        ) -> dict[str, object]:
            return {"runtime_root": str(runtime_root), "quest_id": quest_id, "message": message}

    with pytest.raises(ValueError, match="missing parameters: payload"):
        module.register_managed_runtime_backend(
            SignatureDriftBackend(backend_id="broken_signature", engine_id="broken-signature")
        )

from __future__ import annotations

import importlib
from pathlib import Path


def test_study_runtime_transport_create_quest_uses_router_transport_binding(monkeypatch, tmp_path: Path) -> None:
    transport = importlib.import_module("med_autoscience.controllers.study_runtime_transport")
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        router.med_deepscientist_transport,
        "create_quest",
        lambda **kwargs: (seen.__setitem__("create_kwargs", kwargs) or {"ok": True}),
    )

    payload = {"quest_id": "quest-001"}
    result = transport._create_quest(runtime_root=tmp_path / "runtime", payload=payload)

    assert seen["create_kwargs"]["payload"] == payload
    assert result == {"ok": True}


def test_study_runtime_transport_update_startup_context_uses_router_transport_binding(
    monkeypatch,
    tmp_path: Path,
) -> None:
    transport = importlib.import_module("med_autoscience.controllers.study_runtime_transport")
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        router.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda **kwargs: (
            seen.__setitem__("update_kwargs", kwargs)
            or {
                "ok": True,
                "snapshot": {
                    "quest_id": kwargs["quest_id"],
                    "startup_contract": kwargs["startup_contract"],
                    "requested_baseline_ref": kwargs["requested_baseline_ref"],
                },
            }
        ),
    )

    startup_contract = {"schema_version": 4}
    requested_baseline_ref = {"baseline_id": "demo-baseline"}
    result = transport._update_quest_startup_context(
        runtime_root=tmp_path / "runtime",
        quest_id="quest-001",
        startup_contract=startup_contract,
        requested_baseline_ref=requested_baseline_ref,
    )

    assert seen["update_kwargs"]["quest_id"] == "quest-001"
    assert seen["update_kwargs"]["startup_contract"] == startup_contract
    assert seen["update_kwargs"]["requested_baseline_ref"] == requested_baseline_ref
    assert result.ok is True
    assert result.to_dict()["quest_id"] == "quest-001"
    assert result.to_dict()["snapshot"]["startup_contract"] == startup_contract
    assert result.to_dict()["snapshot"]["requested_baseline_ref"] == requested_baseline_ref


def test_study_runtime_transport_update_startup_context_omits_requested_baseline_ref_when_absent(
    monkeypatch,
    tmp_path: Path,
) -> None:
    transport = importlib.import_module("med_autoscience.controllers.study_runtime_transport")
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        router.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda **kwargs: (
            seen.__setitem__("update_kwargs", kwargs)
            or {
                "ok": True,
                "snapshot": {
                    "quest_id": kwargs["quest_id"],
                    "startup_contract": kwargs["startup_contract"],
                },
            }
        ),
    )

    result = transport._update_quest_startup_context(
        runtime_root=tmp_path / "runtime",
        quest_id="quest-001",
        startup_contract={"schema_version": 4},
    )

    assert "requested_baseline_ref" not in seen["update_kwargs"]
    assert "requested_baseline_ref" not in result.to_dict()["snapshot"]

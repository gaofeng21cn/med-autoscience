from __future__ import annotations

import importlib
from pathlib import Path


def test_runtime_transport_package_defaults_to_opl_provider_backed_stage_runtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport")
    runtime_root = tmp_path / "workspace" / "runtime"

    result = module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})

    assert result["source"] == "mas_runtime_core"
    assert result["runtime_backend_id"] == "opl_provider_backed_stage_runtime"
    assert result["runtime_engine_id"] == "opl-provider-backed-stage-runtime"
    assert result["delegated_domain_adapter_id"] == "mas_runtime_core"
    assert result["delegated_domain_adapter_engine_id"] == "mas-runtime-core"
    assert result["generic_runtime_owner"] == "one-person-lab"
    assert result["domain_adapter_owner"] == "med-autoscience"
    assert result["snapshot"]["runtime_backend_id"] == "mas_runtime_core"

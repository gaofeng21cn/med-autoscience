from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_quality_repair_route_context_remains_canary_regression_ref() -> None:
    registry = json.loads(
        (REPO_ROOT / "contracts" / "unique_control_plane_canary_registry.json").read_text(
            encoding="utf-8"
        )
    )
    registry_text = json.dumps(registry)

    assert "tests/test_gate_clearing_batch_cases/quality_repair_route_context.py" in registry_text
    assert "regression-suite:mas/owner-route/owner-precedence" in registry_text
    assert "no-forbidden-write:mas/dm003/owner-precedence" in registry_text

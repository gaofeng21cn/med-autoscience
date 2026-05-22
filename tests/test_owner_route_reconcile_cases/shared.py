from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.owner_route_reconcile_cases.owner_route_test_helpers import project_owner_route_runtime_state
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_owner_route_required(
    *,
    apply_result: dict,
    runtime_state: dict,
    ensure_calls: list[dict[str, object]] | None = None,
    expected_reason: str | None = None,
) -> dict:
    if ensure_calls is not None:
        assert ensure_calls == []
    assert "resume_result" not in apply_result
    assert apply_result["dispatch_status"] == "owner_route_required"
    if expected_reason is not None:
        assert apply_result["reason"] == expected_reason
    assert apply_result["queue_owner"] == "one-person-lab"
    assert apply_result["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert "quest_root/.ds/runtime_state.json" not in apply_result["allowed_write_surfaces"]
    assert "quest_root/.ds/events.jsonl" not in apply_result["allowed_write_surfaces"]
    assert "last_opl_runtime_owner_route_handoff" not in runtime_state
    assert apply_result["opl_runtime_owner_route_mark"]["runtime_state_mutated"] is False
    return project_owner_route_runtime_state(runtime_state, apply_result)


__all__ = [
    "Path",
    "importlib",
    "json",
    "make_profile",
    "write_study",
    "_write_json",
    "_assert_owner_route_required",
    "project_owner_route_runtime_state",
]

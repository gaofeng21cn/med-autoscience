from __future__ import annotations

import importlib
from pathlib import Path


def test_external_lane_registry_protects_default_external_lane_patterns(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_external_lane_registry")

    registry = module.build_external_lane_registry(
        entries=[
            {
                "session_id": "session-paper",
                "worktree_path": str(tmp_path / "paper-orchestra-authoring"),
                "branch": "paper-orchestra/authoring",
                "study_id": "001-risk",
                "study_line": "001-risk::paper",
            },
            {
                "session_id": "session-gate",
                "worktree_path": str(tmp_path / "mas-gate-publication-redrive"),
                "branch": "codex/mas-gate-publication-redrive",
                "study_id": "002-risk",
                "study_line": "002-risk::publication-gate",
            },
            {
                "session_id": "session-progress",
                "worktree_path": str(tmp_path / "mas-progress-runtime-projection"),
                "branch": "codex/mas-progress-runtime-projection",
                "study_id": "003-risk",
                "study_line": "003-risk::progress",
            },
            {
                "session_id": "session-runtime",
                "worktree_path": str(tmp_path / "mas-runtime-live-supervision"),
                "branch": "codex/mas-runtime-live-supervision",
                "study_id": "004-risk",
                "study_line": "004-risk::runtime",
            },
        ]
    )

    assert registry["surface"] == "ai_first_external_lane_registry"
    assert registry["authority_contract"]["authority"] == "governance_cleanup_protection_only"
    assert registry["authority_contract"]["can_authorize_quality"] is False
    assert registry["authority_contract"]["can_authorize_submission"] is False
    assert registry["authority_contract"]["can_mutate_runtime"] is False
    assert registry["counts"]["protected_lane_count"] == 4
    assert {item["protection_reason"] for item in registry["lanes"]} == {
        "matches_default_external_lane_pattern"
    }
    for pattern in ("paper-orchestra-*", "mas-gate-*", "mas-progress-*", "mas-runtime-*"):
        assert pattern in registry["default_protected_patterns"]


def test_external_lane_protection_check_matches_registry_and_default_patterns(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_external_lane_registry")
    registered_path = tmp_path / "external-session-owned"
    registry = module.build_external_lane_registry(
        entries=[
            {
                "session_id": "session-external",
                "worktree_path": str(registered_path),
                "branch": "codex/external-session-owned",
                "study_id": "004-risk",
                "study_line": "004-risk::revision",
                "active": True,
            }
        ]
    )

    registered = module.assess_external_lane_cleanup_protection(
        worktree_path=registered_path,
        branch="codex/external-session-owned",
        registry=registry,
    )
    default_pattern = module.assess_external_lane_cleanup_protection(
        worktree_path=tmp_path / "paper-orchestra-reviewer-loop",
        branch="codex/paper-orchestra-reviewer-loop",
        registry=registry,
    )

    assert registered["protected"] is True
    assert registered["reason"] == "registered_external_active_lane"
    assert registered["matched_lane"]["session_id"] == "session-external"
    assert default_pattern["protected"] is True
    assert default_pattern["reason"] == "matches_default_external_lane_pattern"
    assert default_pattern["authority_contract"]["can_authorize_quality"] is False
    assert default_pattern["authority_contract"]["can_authorize_submission"] is False


def test_unknown_ai_first_lane_is_not_misclassified_as_external_active(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_external_lane_registry")
    registry = module.build_external_lane_registry(entries=[])

    assessment = module.assess_external_lane_cleanup_protection(
        worktree_path=tmp_path / "codex-ai-first-external-lane-registry",
        branch="codex/ai-first-external-lane-registry",
        registry=registry,
    )

    assert assessment["protected"] is False
    assert assessment["reason"] == "not_registered_or_default_protected"
    assert assessment["matched_lane"] is None
    assert registry["counts"]["protected_lane_count"] == 0


def test_closeout_cleanup_safety_check_preserves_mas_runtime_default_pattern(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_external_lane_registry")

    safety = module.build_closeout_cleanup_safety_check(
        worktree_path=tmp_path / "mas-runtime-authoring-worker",
        branch="codex/mas-runtime-authoring-worker",
        registry=module.build_external_lane_registry(entries=[]),
    )

    assert safety["surface"] == "ai_first_closeout_cleanup_safety_check"
    assert safety["allowed_to_cleanup"] is False
    assert safety["must_preserve"] is True
    assert safety["decision_reason"] == "matches_default_external_lane_pattern"
    assert safety["external_lane_protection"]["protected"] is True


def test_closeout_cleanup_safety_check_allows_unregistered_ai_first_lane(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_external_lane_registry")

    safety = module.build_closeout_cleanup_safety_check(
        worktree_path=tmp_path / "codex-ai-first-external-lane-safety-gate",
        branch="codex/ai-first-external-lane-safety-gate",
        registry=module.build_external_lane_registry(entries=[]),
    )

    assert safety["allowed_to_cleanup"] is True
    assert safety["must_preserve"] is False
    assert safety["decision_reason"] == "not_registered_or_default_protected"


def test_external_lane_registry_payload_redacts_raw_logs_prompts_and_tokens(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_external_lane_registry")

    registry = module.build_external_lane_registry(
        entries=[
            {
                "session_id": "session-secret",
                "worktree_path": str(tmp_path / "mas-gate-secret"),
                "branch": "codex/mas-gate-secret",
                "study_id": "005-risk",
                "study_line": "005-risk::gate",
                "raw_terminal_log": "raw log must not be exposed",
                "full_prompt": "prompt must not be exposed",
                "token_count": 999999,
                "token_stream": "token stream must not be exposed",
                "refs": {
                    "runtime_status": "artifacts/runtime/status/latest.json",
                    "log_path": "/tmp/internal.log",
                },
            }
        ]
    )

    serialized = str(registry)
    assert "raw log must not be exposed" not in serialized
    assert "prompt must not be exposed" not in serialized
    assert "999999" not in serialized
    assert "token stream must not be exposed" not in serialized
    assert "/tmp/internal.log" not in serialized
    assert registry["lanes"][0]["redacted_fields"] == [
        "full_prompt",
        "raw_terminal_log",
        "refs.log_path",
        "token_count",
        "token_stream",
    ]
    assert registry["lanes"][0]["refs"] == {
        "runtime_status": "artifacts/runtime/status/latest.json"
    }


def test_closeout_cleanup_safety_payload_does_not_expose_raw_logs_prompts_or_tokens(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_external_lane_registry")
    registry = module.build_external_lane_registry(
        entries=[
            {
                "session_id": "session-secret",
                "worktree_path": str(tmp_path / "external-session-owned"),
                "branch": "codex/external-session-owned",
                "study_id": "006-risk",
                "study_line": "006-risk::runtime",
                "raw_log": "raw log must not leak",
                "prompt_body": "prompt must not leak",
                "token_usage": 123456,
                "refs": {
                    "status": "artifacts/status.json",
                    "prompt_path": "/tmp/internal-prompt.md",
                    "token_report": "/tmp/tokens.json",
                },
            }
        ]
    )

    safety = module.build_closeout_cleanup_safety_check(
        worktree_path=tmp_path / "external-session-owned",
        branch="codex/external-session-owned",
        registry=registry,
    )

    serialized = str(safety)
    assert "raw log must not leak" not in serialized
    assert "prompt must not leak" not in serialized
    assert "123456" not in serialized
    assert "/tmp/internal-prompt.md" not in serialized
    assert "/tmp/tokens.json" not in serialized
    assert safety["external_lane_protection"]["matched_lane"]["refs"] == {
        "status": "artifacts/status.json"
    }
    assert safety["external_lane_protection"]["matched_lane"]["redacted_fields"] == [
        "prompt_body",
        "raw_log",
        "refs.prompt_path",
        "refs.token_report",
        "token_usage",
    ]

from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_deepscientist_learning_policy_survives_mds_absorption() -> None:
    policy = _read("docs/program/deepscientist_continuous_learning_policy.md")

    assert "即使 `MedDeepScientist` 未来被 `MAS` 完全吸收" in policy
    for learned_surface in ("behavior", "contract", "packet"):
        assert learned_surface in policy
    assert "durable continuity spine" in policy
    assert "takeover / resume control surface" in policy
    assert "inspectable workspace" in policy
    assert "stage operational packets" in policy
    assert "failed-path learning" in policy
    assert "不把 provider / UI / marketing 变化升级成 MAS behavior、contract 或 packet" in policy
    assert "MDS 被进一步吸收后，本政策仍继续生效" in policy


def test_current_learning_plan_points_to_policy_entry() -> None:
    plan = _read("docs/program/med_deepscientist_continuous_learning_plan.md")

    assert "DeepScientist Continuous Learning Policy" in plan
    assert "DeepScientist Latest-Update Learning Protocol" in plan
    assert "学习主线如何继续" in plan


def test_latest_update_learning_protocol_defines_trigger_and_landing_workflow() -> None:
    protocol = _read("docs/program/deepscientist_latest_update_learning_protocol.md")
    policy = _read("docs/program/deepscientist_continuous_learning_policy.md")
    status = _read("docs/status.md")

    assert "学习一下 `DeepScientist` 的最新更新" in protocol
    assert "learning-and-landing intake" in protocol
    for required_step in (
        "fresh upstream audit",
        "decision matrix",
        "Parallel worktrees",
        "Verification gate",
        "Audit record",
        "吸收回 `main`",
        "清理 worktree",
    ):
        assert required_step in protocol
    for decision in ("adopt_code_slice", "adopt_contract", "adopt_template", "watch_only", "reject"):
        assert decision in protocol
    for owner_surface in ("MDS runtime/backend lane", "MAS contract/template lane", "MAS runtime-consumer lane"):
        assert owner_surface in protocol
    assert "provider / UI / marketing" in protocol
    assert "DeepScientist Latest-Update Learning Protocol" in policy
    assert "DeepScientist Latest-Update Learning Protocol" in status


def test_2026_04_25_intake_records_decisions_and_owner_surfaces() -> None:
    intake = _read("docs/program/deepscientist_learning_intake_2026_04_25.md")

    assert "e539e2e..710792e" in intake
    for decision in ("adopt_code_slice", "adopt_contract", "adopt_template", "watch_only", "reject"):
        assert decision in intake
    for upstream_lesson in (
        "MDS retry priority",
        "baseline refresh",
        "stage operational packets / SOP",
        "provider / connector surface",
    ):
        assert upstream_lesson in intake
    for owner in ("runtime", "workspace projection", "controller_charter", "eval_hygiene"):
        assert owner in intake
    assert "preempt retry/backoff" in intake
    assert "idea objective contract / candidate board" in intake
    assert "analysis bounded campaign" in intake
    assert "write evidence-bound repair" in intake
    assert "finalize submission truth" in intake
    assert "decision route outcome" in intake
    assert "本轮不追随 upstream UI 大包" in intake

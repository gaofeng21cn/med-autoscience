from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_unified_enhancement_program_maps_all_recommendations_to_five_lanes() -> None:
    doc = _read("docs/program/mas_mds_unified_enhancement_program.md")

    expected_lanes = {
        "L1_real_workspace_longitudinal_soak",
        "L2_pi_action_projection",
        "L3_outcome_calibration_and_provider_ops",
        "L4_delivery_and_legacy_upgrade_visibility",
        "L5_natural_boundary_and_audit_compaction",
    }
    for lane_id in expected_lanes:
        assert lane_id in doc

    original_recommendation_markers = (
        "自动科研 1",
        "自动科研 2",
        "自动科研 3",
        "自动科研 4",
        "自动科研 5",
        "自动科研 6",
        "文件管理 1",
        "文件管理 2",
        "文件管理 3",
        "文件管理 4",
        "文件管理 5",
        "控制面 1",
        "控制面 2",
        "控制面 3",
        "控制面 4",
    )
    for marker in original_recommendation_markers:
        assert marker in doc

    assert doc.count("| 自动科研 ") == 6
    assert doc.count("| 文件管理 ") == 5
    assert doc.count("| 控制面 ") == 4
    assert "这 15 条继续增强建议大多必要" in doc
    assert "不应继续按三组清单各自推进" in doc


def test_unified_enhancement_program_preserves_authority_boundaries() -> None:
    doc = _read("docs/program/mas_mds_unified_enhancement_program.md")

    required_authority_terms = (
        "StudyTruthKernel",
        "RuntimeHealthKernel",
        "AI reviewer-backed `publication_eval/latest.json`",
        "controller_decisions/latest.json",
        "canonical artifact proof",
    )
    for term in required_authority_terms:
        assert term in doc

    forbidden_projection_patterns = (
        "不得独立声明 publication readiness",
        "不得根据文件状态、provider 状态或 MDS oracle 另算下一步",
        "不能绕过 AI reviewer 或 publication gate",
        "只有 controller-authorized sync/apply 能写 delivery truth",
        "结构治理不改变 study truth、publication truth、delivery truth 或 runtime action",
    )
    for pattern in forbidden_projection_patterns:
        assert pattern in doc


def test_unified_enhancement_program_records_external_engineering_basis_and_parallel_landing() -> None:
    doc = _read("docs/program/mas_mds_unified_enhancement_program.md")

    for basis_id in (
        "strangler_fig",
        "architecture_fitness_functions",
        "team_topologies_cognitive_load",
        "sre_toil_elimination_and_observability",
        "owner_private_truth_surfaces",
    ):
        assert basis_id in doc

    for branch in (
        "codex/mas-soak-matrix-read-model",
        "codex/mas-pi-action-projection",
        "codex/mas-calibration-provider-ops",
        "codex/mas-delivery-legacy-visibility",
        "codex/mas-structure-audit-compaction",
    ):
        assert branch in doc

    assert "吸收顺序固定为 `L1 -> L2 -> L3 -> L4 -> L5`" in doc
    assert "projection_pending_authority" in doc


def test_unified_enhancement_program_is_linked_from_core_architecture_and_program_board() -> None:
    architecture = _read("docs/architecture.md")
    program = _read("docs/program/mas_mds_autonomy_operating_system_program.md")
    docs_readme = _read("docs/README.md")
    docs_readme_zh = _read("docs/README.zh-CN.md")
    ledger = _read("docs/program/plan_completion_ledger.md")

    assert "MAS/MDS Unified Enhancement Program" in architecture
    assert "./program/mas_mds_unified_enhancement_program.md" in architecture
    assert "mas_mds_unified_enhancement_program.md" in program
    assert "automatic research, file management, and control-plane consistency" in program
    assert "audit compaction remains blocked until restore/index/provenance contracts exist" in program
    assert "MAS/MDS unified enhancement program" in docs_readme
    assert "MAS/MDS 统一增强 program" in docs_readme_zh
    assert "2026-05-04-mas-mds-unified-enhancement-program" in ledger
    assert "no live study workspace" in ledger

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ai_first_research_os_freezes_owner_boundaries_and_os_layers() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_research_os")

    contract = module.build_ai_first_research_os_contract()

    assert contract["surface"] == "ai_first_research_os_architecture_contract"
    assert contract["target_state"] == {
        "research_owner": "MedAutoScience",
        "quality_owner": "MedAutoScience AI reviewer artifacts",
        "mds_role": "replaceable_backend_oracle",
        "mechanical_system_role": "evidence_status_completeness_replay",
        "quality_gate_relaxation_allowed": False,
    }
    assert [layer["layer_id"] for layer in contract["operating_layers"]] == [
        "mas_core",
        "quality_os",
        "runtime_os",
        "artifact_os",
        "evaluation_os",
        "observability_os",
        "mds_deconstruction",
    ]
    assert contract["authority_rules"]["submission_readiness_requires_ai_reviewer_provenance"] is True
    assert contract["authority_rules"]["mechanical_projection_can_authorize_quality"] is False
    assert contract["migration_strategy"]["physical_monorepo_absorb"] == "post_parity_gate_only"
    assert {item["basis_id"] for item in contract["external_engineering_basis"]} == {
        "iso_42010_architecture_description",
        "nist_ai_rmf",
        "equator_reporting_guidelines",
        "fair_data_principles",
        "durable_execution",
        "opentelemetry_observability",
        "g_eval_structured_reviewer",
        "sre_toil_elimination",
    }


def test_ai_first_research_os_docs_are_visible_from_core_architecture_surfaces() -> None:
    architecture = (REPO_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    decisions = (REPO_ROOT / "docs" / "decisions.md").read_text(encoding="utf-8")
    status = (REPO_ROOT / "docs" / "status.md").read_text(encoding="utf-8")
    program_doc = (REPO_ROOT / "docs" / "program" / "ai_first_research_os_architecture.md").read_text(
        encoding="utf-8"
    )

    assert "MAS AI-first Research OS" in architecture
    assert "ai_first_research_os_architecture_contract" in architecture
    assert "AI reviewer artifacts 持有科学质量" in decisions
    assert "机械系统只负责 evidence、status、completeness、blocker、projection 与 replay" in decisions
    assert "2026-05-02 长线目标架构已固定为 `MAS AI-first Research OS`" in status
    assert "只有由 AI reviewer 读取 manuscript、evidence ledger、review ledger 与 study charter" in status
    assert "MDS Deconstruction" in program_doc


def test_ai_first_research_os_validation_fails_closed_on_owner_or_quality_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_research_os")
    contract = module.build_ai_first_research_os_contract()
    contract["target_state"]["research_owner"] = "MedDeepScientist"
    contract["target_state"]["quality_owner"] = "mechanical_gate"
    contract["target_state"]["mechanical_system_role"] = "quality_authority"
    contract["target_state"]["quality_gate_relaxation_allowed"] = True
    contract["authority_rules"]["mechanical_projection_can_authorize_quality"] = True
    contract["authority_rules"]["subjective_medical_quality_requires_ai_reviewer"] = False
    contract["operating_layers"][0]["authority_surfaces"] = []

    validation = module.validate_ai_first_research_os_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "wrong_research_owner",
        "quality_owner_not_ai_reviewer_artifacts",
        "mechanical_system_role_not_projection_replay",
        "quality_gate_relaxation_allowed",
        "mechanical_projection_authorizes_quality",
        "subjective_quality_not_ai_reviewer_backed",
        "layer_missing_authority_surfaces",
    }

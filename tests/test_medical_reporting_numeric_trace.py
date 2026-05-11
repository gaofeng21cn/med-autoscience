from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_medical_reporting_audit import _write_keyed_medical_story_contracts


def test_medical_reporting_audit_blocks_missing_numeric_trace(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "002-dm-china-us-mortality-attribution"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "STROBE",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
                "quality_gate_expectation": {"gate_relaxation_allowed": True},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_keyed_medical_story_contracts(paper_root)
    (paper_root / "numeric_trace.json").unlink()

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert "missing_medical_story_contract" in report["blockers"]
    assert "missing_numeric_trace" in report["medical_story_contract_blockers"]


def test_numeric_trace_contract_requires_verified_rounding_and_sources() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    assert policy.validate_numeric_trace(
        {
            "traces": [
                {
                    "trace_id": "trace-1",
                    "claim_id": "primary-result",
                    "reported_value": "HR 1.42",
                    "statistic_kind": "hazard_ratio",
                    "source_paths": ["analysis/results/model.json"],
                    "source_field": "cox.primary.hazard_ratio",
                    "rounding_rule": "two_decimals_half_even",
                    "manuscript_refs": ["results:primary-model"],
                    "verification_status": "verified",
                    "evidence_refs": ["primary-model"],
                }
            ]
        }
    ) == []
    assert policy.validate_numeric_trace(
        {
            "traces": [
                {
                    "trace_id": "trace-1",
                    "claim_id": "primary-result",
                    "reported_value": "HR 1.42",
                    "statistic_kind": "hazard_ratio",
                    "source_paths": [],
                    "source_field": "cox.primary.hazard_ratio",
                    "rounding_rule": "two_decimals_half_even",
                    "manuscript_refs": ["results:primary-model"],
                    "verification_status": "verified",
                    "evidence_refs": ["primary-model"],
                }
            ]
        }
    ) == ["missing traces[0] fields: source_paths"]
    assert policy.validate_numeric_trace(
        {
            "traces": [
                {
                    "trace_id": "trace-1",
                    "claim_id": "primary-result",
                    "reported_value": "HR 1.42",
                    "statistic_kind": "hazard_ratio",
                    "source_paths": ["analysis/results/model.json"],
                    "source_field": "cox.primary.hazard_ratio",
                    "rounding_rule": "",
                    "manuscript_refs": ["results:primary-model"],
                    "verification_status": "verified",
                    "evidence_refs": ["primary-model"],
                }
            ]
        }
    ) == ["missing traces[0] fields: rounding_rule"]
    assert policy.validate_numeric_trace(
        {
            "traces": [
                {
                    "trace_id": "trace-1",
                    "claim_id": "primary-result",
                    "reported_value": "HR 1.42",
                    "statistic_kind": "hazard_ratio",
                    "source_paths": ["analysis/results/model.json"],
                    "source_field": "cox.primary.hazard_ratio",
                    "rounding_rule": "two_decimals_half_even",
                    "manuscript_refs": ["results:primary-model"],
                    "verification_status": "needs_review",
                    "evidence_refs": ["primary-model"],
                }
            ]
        }
    ) == ["traces[0].verification_status must be verified"]


def test_claim_evidence_map_accepts_optional_numeric_trace_refs() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    valid_claim_map = {
        "claims": [
            {
                "claim_id": "primary-result",
                "statement": "The primary model reports a bounded association.",
                "status": "supported",
                "paper_role": "main_text",
                "display_bindings": ["T2"],
                "sections": ["primary-results"],
                "evidence_items": [
                    {
                        "item_id": "primary-model",
                        "support_level": "direct",
                        "source_paths": ["analysis/results/model.json"],
                        "numeric_trace_refs": ["trace-1"],
                    }
                ],
            }
        ]
    }
    invalid_claim_map = json.loads(json.dumps(valid_claim_map))
    invalid_claim_map["claims"][0]["evidence_items"][0]["numeric_trace_refs"] = []

    assert policy.validate_claim_evidence_map(valid_claim_map) == []
    assert policy.validate_claim_evidence_map(invalid_claim_map) == [
        "claims[0].evidence_items[0].numeric_trace_refs must contain at least one non-empty string"
    ]

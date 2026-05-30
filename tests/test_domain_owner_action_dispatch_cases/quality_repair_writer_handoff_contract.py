from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_quality_repair_writer_handoff_carries_structured_reporting_checklist(tmp_path: Path) -> None:
    writer_handoff = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.writer_handoff"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"

    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=f"quest-{study_id}",
        schema_version=1,
        source_eval_id="publication-eval::dm003",
        source_eval_artifact_path="artifacts/publication_eval/latest.json",
        source_summary_artifact_path="artifacts/eval_hygiene/evaluation_summary/latest.json",
        repair_execution_evidence_path=(
            profile.studies_root
            / study_id
            / "artifacts/controller/repair_execution_evidence/latest.json"
        ),
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "controller_route_context": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::dm003-structured-reporting",
            },
        },
    )

    prompt_contract = handoff["prompt_contract"]
    assert prompt_contract["next_work_unit"]["unit_id"] == "medical_prose_write_repair"
    assert prompt_contract["structured_reporting_checklist"] == [
        "phenotype_derivation_reporting_incomplete",
        "treatment_gap_reporting_incomplete",
        "baseline_characteristics_reporting_incomplete",
        "data_quality_reporting_incomplete",
        "manuscript_voice_reporting_incomplete",
    ]
    assert prompt_contract["medical_journal_quality_floor"] == {
        "phenotype_derivation": (
            "Explain whether assignment is deterministic rules or clustering; name domains, thresholds, "
            "six-class rationale, and how a new patient is assigned."
        ),
        "treatment_gap": (
            "Use recorded medication-coverage or recorded treatment-review gap language, with explicit "
            "numerators, eligible denominators, medication data source limits, and non-causal guardrails."
        ),
        "data_quality": (
            "Add BP semantic-field and variable-quality assessment with missingness, plausibility filters, "
            "and claim-impact downgrades."
        ),
        "baseline_table": (
            "Render a true phenotype-level baseline characteristics table and keep the cohort/QC table "
            "separate from Table 1 semantics when needed."
        ),
        "manuscript_voice": (
            "Remove runtime/meta-review language and avoid repetitive defensive boundary statements outside "
            "Methods and Limitations."
        ),
    }
    assert prompt_contract["forbidden_manuscript_terms"] == [
        "MAS",
        "AI reviewer",
        "verified outputs",
        "accepted records",
        "source gaps",
        "submission readiness",
        "repair note",
        "manuscript repair",
        "quality repair",
        "publication gate",
        "controller",
    ]
    assert prompt_contract["search_boundaries"]["surface"] == "default_executor_search_discipline.v1"
    assert "grep -R" in prompt_contract["search_boundaries"]["forbidden_command_patterns"]
    assert "runtime/.ds/**" in prompt_contract["search_boundaries"]["forbidden_path_globs"]
    assert "runtime/**/codex_homes/**" in prompt_contract["tool_discipline"]["forbidden_path_globs"]
    assert any(
        command.startswith("rg --hidden")
        for command in prompt_contract["search_boundaries"]["recommended_search_commands"]
    )

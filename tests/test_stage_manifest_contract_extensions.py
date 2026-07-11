from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_IDS = [
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
]
COMMON_DOMAIN_EXTENSION_FIELDS = {
    "cohort_query_refs",
    "dashboard_metric_refs",
    "human_gate_progress_evidence",
    "hypothesis_portfolio_evidence_pack",
    "minimum_forward_delta",
    "monitor_refs",
    "route_obligation_lens",
    "runtime_event_refs",
    "source_scope_refs",
    "trigger_refs",
}
LATE_STAGE_EXTENSION_FIELDS = {
    "manuscript_authoring": {
        "late_stage_progress_sprint_contract",
        "typed_cognitive_subpacket_gate",
    },
    "review_and_quality_gate": {
        "late_stage_progress_sprint_contract",
        "typed_cognitive_subpacket_gate",
        "mandatory_pre_gate_checks",
    },
    "finalize_and_publication_handoff": {
        "late_stage_progress_sprint_contract",
        "typed_cognitive_subpacket_gate",
        "mandatory_pre_gate_checks",
    },
}
FORBIDDEN_FRAMEWORK_FIELDS = {
    "requires",
    "ensures",
    "boundary_assumptions",
    "properties",
    "expected_receipt_refs",
    "receipt_schema_refs",
    "authority_function_refs",
    "l4_entry_gate",
    "l5_entry_gate",
    "stage_completion_policy",
    "user_stage_log_contract",
    "progress_delta_policy",
    "typed_blocker_lineage_policy",
}


def _stage_manifest() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )


def test_stage_manifest_declares_domain_extensions_for_opl_generated_plane() -> None:
    manifest = _stage_manifest()
    stages = manifest["stages"]
    assert isinstance(stages, list)
    assert [stage["stage_id"] for stage in stages] == STAGE_IDS

    for stage in stages:
        extension = stage.get("stage_contract_extension")
        assert isinstance(extension, dict)
        assert COMMON_DOMAIN_EXTENSION_FIELDS <= set(extension)
        assert not (FORBIDDEN_FRAMEWORK_FIELDS & set(extension))
        assert extension["runtime_event_refs"]
        assert extension["monitor_refs"]
        assert extension["source_scope_refs"]

        minimum_delta = extension["minimum_forward_delta"]
        assert minimum_delta["owner_action"]["allowed_action_refs"] == stage[
            "allowed_action_refs"
        ]
        action_trigger = next(
            trigger
            for trigger in extension["trigger_refs"]
            if trigger["role"] == "mas_guarded_action_trigger_candidates"
        )
        assert action_trigger["ref"] == stage["allowed_action_refs"]

        expected_late_fields = LATE_STAGE_EXTENSION_FIELDS.get(stage["stage_id"], set())
        assert expected_late_fields <= set(extension)

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts/kdense_byok_external_intake.json"
AUTHORITY_FALSE_FIELDS = {
    "body_included",
    "can_write_study_truth",
    "can_write_source_truth",
    "can_write_paper_body",
    "can_write_artifact_body",
    "can_write_publication_eval",
    "can_write_controller_decisions",
    "can_write_current_package",
    "can_sign_owner_receipt",
    "can_create_typed_blocker",
    "can_create_human_gate",
    "can_authorize_source_readiness",
    "can_authorize_quality_verdict",
    "can_authorize_publication_readiness",
    "can_authorize_submission_readiness",
    "can_authorize_provider_admission",
    "can_close_stage",
}


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_kdense_byok_intake_contract_pins_sources_and_counts() -> None:
    contract = _contract()
    kdense = contract["source_evidence"]["kdense_byok"]
    skills = contract["source_evidence"]["scientific_agent_skills"]

    assert contract["surface_kind"] == "mas_kdense_byok_external_intake"
    assert kdense["repo"] == "https://github.com/K-Dense-AI/k-dense-byok"
    assert kdense["inspected_head_commit"] == (
        "dccc7ec4d034a00d7662eaabb3f5916bc3d00602"
    )
    assert kdense["latest_release_tag"] == "v0.6.0"
    assert kdense["release_tag_commit"] == (
        "b5b6b832ad6eaa266ca27924331041435b834bd4"
    )
    assert kdense["workflow_template_count"] == 326
    assert kdense["database_ref_count"] == 229
    assert kdense["scientific_specialist_count"] == 21
    assert skills["inspected_head_commit"] == (
        "1e024ea8547ada12039edbe8197aaa959d97763f"
    )
    assert skills["skill_dir_count"] == 149


def test_kdense_intake_is_selective_refs_only_and_has_closed_authority() -> None:
    contract = _contract()
    authority = contract["authority_boundary"]
    runtime = contract["runtime_boundary"]
    policy = contract["external_skill_library_policy"]
    items = contract["planned_learning_items"]

    assert set(authority) == {"refs_only", *AUTHORITY_FALSE_FIELDS}
    assert authority["refs_only"] is True
    assert not any(authority[field] for field in AUTHORITY_FALSE_FIELDS)
    assert runtime["opl_base"] == "Codex CLI harness"
    assert runtime["codex_cli_as_opl_harness"] is True
    assert runtime["pi_runtime_dependency"] is False
    assert runtime["external_library_bulk_load_allowed"] is False
    assert runtime["no_second_catalog"] is True
    assert runtime["no_second_selector"] is True
    assert policy["bulk_load_allowed"] is False
    assert policy["sequence"] == ["search", "inspect", "sync"]
    assert len(policy["selected_allowlist"]) >= 16
    assert [item["plan_order"] for item in items] == list(range(1, 15))
    assert {item["landing_status"] for item in items} <= {
        "contract_projection_landed",
        "read_model_landed",
        "sidecar_or_worker_landed",
        "watch_only",
    }

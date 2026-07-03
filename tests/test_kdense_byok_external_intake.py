from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "kdense_byok_external_intake.json"
CAPABILITY_MAP_PATH = ROOT / "contracts" / "capability_map.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_kdense_byok_intake_contract_pins_sources_and_counts() -> None:
    contract = _contract()
    kdense = contract["source_evidence"]["kdense_byok"]
    skills = contract["source_evidence"]["scientific_agent_skills"]

    assert contract["surface_kind"] == "mas_kdense_byok_external_intake"
    assert kdense["repo"] == "https://github.com/K-Dense-AI/k-dense-byok"
    assert kdense["inspected_head_commit"] == "dccc7ec4d034a00d7662eaabb3f5916bc3d00602"
    assert kdense["latest_release_tag"] == "v0.6.0"
    assert kdense["release_tag_commit"] == "b5b6b832ad6eaa266ca27924331041435b834bd4"
    assert kdense["license"] == "MIT"
    assert kdense["workflow_template_count"] == 326
    assert kdense["database_ref_count"] == 229
    assert kdense["scientific_specialist_count"] == 21
    assert skills["inspected_head_commit"] == "1e024ea8547ada12039edbe8197aaa959d97763f"
    assert skills["license"] == "MIT"
    assert skills["skill_dir_count"] == 149


def test_kdense_byok_intake_keeps_codex_cli_harness_and_blocks_pi_runtime() -> None:
    contract = _contract()
    runtime = contract["runtime_boundary"]
    authority = contract["authority_boundary"]

    assert runtime["opl_base"] == "Codex CLI harness"
    assert runtime["codex_cli_as_opl_harness"] is True
    assert runtime["pi_runtime_dependency"] is False
    assert runtime["pi_subagent_engine_dependency"] is False
    assert runtime["kdense_runtime_dependency"] is False
    assert runtime["external_library_bulk_load_allowed"] is False
    assert runtime["no_second_catalog"] is True
    assert runtime["no_second_selector"] is True

    forbidden_truthy = [
        key
        for key, value in authority.items()
        if key != "refs_only" and isinstance(value, bool) and value
    ]
    assert forbidden_truthy == []
    assert authority["refs_only"] is True
    assert authority["can_write_publication_eval"] is False
    assert authority["can_sign_owner_receipt"] is False
    assert authority["can_create_typed_blocker"] is False
    assert authority["can_create_human_gate"] is False


def test_kdense_external_skill_policy_is_selective_search_inspect_sync() -> None:
    contract = _contract()
    policy = contract["external_skill_library_policy"]
    allowlist = policy["selected_allowlist"]
    allowlist_by_id = {item["skill_id"]: item for item in allowlist}

    assert policy["surface"] == "opl_connect_external_skills"
    assert policy["bulk_load_allowed"] is False
    assert policy["sequence"] == ["search", "inspect", "sync"]
    assert policy["outputs_are_refs_only_candidates"] is True
    assert len(allowlist) >= 16
    assert {
        "scanpy",
        "anndata",
        "bulk-rnaseq",
        "pydeseq2",
        "pathway-enrichment",
        "rdkit",
        "deepchem",
        "pyhealth",
        "pydicom",
        "imaging-data-commons",
        "nextflow",
        "dask",
        "paper-lookup",
        "citation-management",
        "pyzotero",
        "database-lookup",
    } <= set(allowlist_by_id)

    for item in allowlist:
        assert item["source_ref"].startswith(
            "external_repo:K-Dense-AI/scientific-agent-skills@"
        )
        assert item["module_id"].startswith("mas-scholar-skills.")
        assert item["owner_surface"]
        assert item["use_when"]
        assert item["completion_gate"]


def test_kdense_planned_learning_items_have_owner_surface_and_gates() -> None:
    contract = _contract()
    items = contract["planned_learning_items"]
    by_id = {item["item_id"]: item for item in items}

    assert len(items) == 14
    assert [item["plan_order"] for item in items] == list(range(1, 15))
    required = {
        "source_pin_license_authority_boundary",
        "scientific_agent_skills_subset_allowlist",
        "skill_to_module_mapping",
        "workflow_templates_to_stagecraft",
        "database_catalog_to_atlas",
        "codex_specialist_roster",
        "artifact_workspace_preview_file_tree",
        "session_replay_lab_notebook",
        "cost_ledger_budget_cap",
        "mcp_connector_test_surface",
        "remote_compute_adapter",
        "human_gate_form_schema",
        "workbench_ux_selector_tool_activity",
        "openrouter_fusion_watch_only",
    }
    assert set(by_id) == required

    for item in items:
        assert item["classification"] in {"adopt_contract", "adapt", "watch_only"}
        assert item["local_owner_surface"]
        assert item["target_landing"]
        assert item["landing_status"] in {
            "contract_projection_landed",
            "read_model_landed",
            "sidecar_or_worker_landed",
            "watch_only",
        }
        assert item["completion_gate"]
        assert item["why_worth_learning"]

    fusion = by_id["openrouter_fusion_watch_only"]
    assert fusion["classification"] == "watch_only"
    assert fusion["landing_status"] == "watch_only"
    assert "cannot close independent reviewer gate" in fusion["completion_gate"]


def test_capability_map_routes_kdense_external_library_as_non_authority_gap_fill() -> None:
    capability_map = json.loads(CAPABILITY_MAP_PATH.read_text(encoding="utf-8"))
    policy = capability_map["consumer_policy"]["external_specialist_library_policy"]

    assert "contracts/kdense_byok_external_intake.json" in capability_map["source_of_truth"]
    assert policy["external_learning_intake_ref"] == (
        "contracts/kdense_byok_external_intake.json#/external_skill_library_policy"
    )
    assert policy["bulk_load_allowed"] is False
    assert policy["sync_sequence"] == ["search", "inspect", "sync"]
    assert policy["selected_allowlist_ref"] == (
        "contracts/kdense_byok_external_intake.json#/external_skill_library_policy/selected_allowlist"
    )
    assert policy["kdense_authority"] is False
    assert policy["external_skill_outputs_are_refs_only_candidates"] is True
    assert "scanpy" in policy["example_specialist_gaps"]
    assert "database-lookup" in policy["example_specialist_gaps"]

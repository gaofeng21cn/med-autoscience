from __future__ import annotations

import fnmatch
from pathlib import Path

import pytest

from tests.control_plane_route_helpers import writable_route_context


REPO_ROOT = Path(__file__).resolve().parents[1]

NESTED_CASE_COLLECTION_IGNORE_GLOBS = (
    "product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_*.py",
    "test_cli_cases/ai_reviewer_publication_eval_command_cases/test_*.py",
    "test_adapter_retirement_boundary_cases/runtime_surface_no_authority_violation_guards_cases/test_*.py",
)

collect_ignore_glob = list(NESTED_CASE_COLLECTION_IGNORE_GLOBS)

META_FILES = {
    "tests/controller_charter/test_controller_charter_module_contract.py",
    "tests/eval_hygiene/test_eval_hygiene_module_contract.py",
    "tests/integration/test_monorepo_scaffold_boundaries.py",
    "tests/runtime/test_runtime_module_contract.py",
    "tests/test_stage_route_assets.py",
    "tests/test_codex_plugin.py",
    "tests/test_codex_plugin_installer.py",
    "tests/test_codex_plugin_installer_script.py",
    "tests/test_codex_plugin_scaffold.py",
    "tests/test_med_deepscientist_repo_manifest.py",
    "tests/test_python_environment_contract.py",
    "tests/test_release_installer.py",
    "tests/test_release_metadata.py",
    "tests/test_release_workflow.py",
    "tests/test_workspace_contracts.py",
}

DISPLAY_HEAVY_FILES = {
    "tests/test_display_ab_golden_regression.py",
    "tests/test_display_abh_golden_regression.py",
    "tests/test_display_ch_golden_regression.py",
    "tests/test_display_deg_golden_regression.py",
    "tests/test_display_f_golden_regression.py",
    "tests/test_display_layout_qc.py",
    "tests/test_display_surface_materialization.py",
    "tests/test_display_surface_materialization_cli.py",
    "tests/test_medical_startup_contract_support.py",
    "tests/test_submission_minimal_display_surface.py",
}

FAMILY_FILES = {
    "tests/test_dev_preflight.py",
    "tests/test_dev_preflight_contract.py",
    "tests/test_editable_shared_bootstrap.py",
    "tests/test_family_shared_release.py",
    "tests/test_opl_agent_lab_longline_migration.py",
}

MATERIALIZATION_HEAVY_FILES = {
    "tests/test_fast_lane_executor.py",
    "tests/test_gate_clearing_batch.py",
    "tests/test_journal_package_controller.py",
    "tests/test_publication_gate.py",
    "tests/test_quality_repair_batch.py",
    "tests/test_study_delivery_sync.py",
}

SOAK_OR_GOLDEN_FILES = {
    "tests/test_control_plane_generalization_cases/test_study_soak_replay_cases.py",
    "tests/test_mas_mds_longitudinal_soak.py",
    "tests/test_medical_paper_v2_final_soak_proof.py",
    "tests/test_multistudy_soak_proof.py",
    "tests/test_open_auto_research_soak.py",
    "tests/test_real_paper_ai_first_soak.py",
    "tests/test_real_paper_autonomy_soak_inventory.py",
    "tests/test_real_workspace_soak_monitor.py",
    "tests/test_storage_governance_read_only_soak.py",
    "tests/test_study_truth_kernel_golden_fixtures.py",
}


def _relative_test_path(item: pytest.Item) -> str:
    path = Path(str(item.fspath)).resolve()
    return path.relative_to(REPO_ROOT).as_posix()


def _is_nested_case_collection_path(relative_test_path: str) -> bool:
    relative_to_tests = relative_test_path.removeprefix("tests/")
    return any(fnmatch.fnmatch(relative_to_tests, pattern) for pattern in NESTED_CASE_COLLECTION_IGNORE_GLOBS)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    nested_case_items = [item for item in items if _is_nested_case_collection_path(_relative_test_path(item))]
    if nested_case_items:
        items[:] = [item for item in items if item not in nested_case_items]
    for item in items:
        relative_path = _relative_test_path(item)
        if relative_path in META_FILES:
            item.add_marker(pytest.mark.meta)
        if relative_path in DISPLAY_HEAVY_FILES:
            item.add_marker(pytest.mark.display_heavy)
        if relative_path in FAMILY_FILES:
            item.add_marker(pytest.mark.family)
        if relative_path in MATERIALIZATION_HEAVY_FILES:
            item.add_marker(pytest.mark.materialization_heavy)
        if relative_path in SOAK_OR_GOLDEN_FILES:
            item.add_marker(pytest.mark.soak_or_golden)


@pytest.fixture
def writable_authority_route_context() -> dict[str, object]:
    return writable_route_context()


@pytest.fixture(scope="session")
def mas_scholar_skills_external_owner_skill_repo_path(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    repo_root = tmp_path_factory.mktemp("mas-scholar-skills")
    skill_bodies = {
        "medical-research-write": """---
name: write
description: MAS medical manuscript writing owner skill. Use for medical paper section drafting, rewrite, claim tightening, journal voice, figure-to-text integration, and response-ready manuscript repair.
---

# Medical Research Write

Use this AI-first skill for MAS medical manuscript writing. Preserve MAS owner gates: every claim needs evidence refs, every number needs source trace, and publication readiness still requires MAS owner acceptance.

Open `figure/SKILL.md` first for figures that enter the draft. Use `figure-polish/SKILL.md` only after figure intent, claim, evidence refs, panel plan, backend selection, draft render, and visual QA are scoped.

Use `opl connect pubmed search --query <query> --limit <n> --json` or `medical-research-lit` when the draft needs literature candidates. Treat the returned literature as candidate refs until MAS accepts them.

Key blockers: numeric_trace_blocker, claim_evidence_blocker, display_to_claim_blocker, reporting_guideline_gate.
""",
        "medical-research-review": """---
name: review
description: MAS medical manuscript review owner skill. Use for adversarial medical paper review, claim/evidence/display consistency checks, citation repair, route-back, and publishability critique.
---

# Medical Research Review

Run an independent AI reviewer pass. Check citation support, numeric consistency, table and figure alignment, reporting guideline coverage, and whether the manuscript should route back to analysis, writing, figure, or submission work.

Use `opl connect pubmed search --query <query> --limit <n> --json` or `medical-research-lit` for citation repair candidates. Keep reviewer output as review_signal_only until MAS owner evidence accepts it.

Return concrete route-back items, claim downgrade candidates, reusable critique lessons, and closeout evidence.
""",
        "medical-research-figure": """---
name: figure
description: MAS medical research figure owner skill. Use for zero-to-one medical paper figure planning, evidence refs, panel design, rendering, visual QA, polish, reviewer handoff, and publication-facing figure repair.
---

# Medical Research Figure

Use this AI-first figure skill for new or materially reworked paper-facing figures.

## Figure Intent And Claim
State the manuscript claim the figure supports and the owner gate that must accept it.

## Evidence Refs
Bind all inputs to paper-local or MAS refs. Use `opl connect pubmed search --query <query> --limit <n> --json` or `medical-research-lit` for literature context when needed.

## Panel Plan
Design panel order, comparison groups, labels, statistical annotations, and caption obligations before rendering.

## Template And Backend Selection
Choose a renderer or template from the available MAS/ScholarSkills Display refs. Nature Figure-style planning and K-Dense-style manifest/QA ideas are references inside this owner path.
Do not introduce a parallel `opl-scholar-display` main entry.

## Draft Render
Scripts are render and check tools. Tool/Fabric execution may create candidate outputs, but MAS owner gate decides paper truth.

## Visual QA
Check typography, scale, color, legends, sample sizes, figure manifest, and claim/evidence consistency.

## Polish
Polish after the draft supports the claim. `figure-polish` remains the bounded review phase entry.

## Reviewer Handoff
Return figure refs, QA notes, and route-back items. Domain Owner Gate remains MAS-owned.
""",
    }
    for skill_id, body in skill_bodies.items():
        skill_path = repo_root / "skills" / skill_id / "SKILL.md"
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(body, encoding="utf-8")
    return repo_root


@pytest.fixture(autouse=True)
def mas_scholar_skills_external_owner_skill_repo(
    mas_scholar_skills_external_owner_skill_repo_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAS_SCHOLAR_SKILLS_REPO", str(mas_scholar_skills_external_owner_skill_repo_path))

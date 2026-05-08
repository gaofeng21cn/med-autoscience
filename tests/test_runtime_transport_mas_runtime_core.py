from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


def test_mas_runtime_core_creates_and_resumes_quest_without_external_daemon(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    create_result = module.create_quest(
        runtime_root=runtime_root,
        payload={"quest_id": "quest-001", "study_id": "study-001", "auto_start": False},
    )
    resume_result = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    quest_root = runtime_root / "quests" / "quest-001"
    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert create_result["source"] == "mas_runtime_core"
    assert create_result["snapshot"]["status"] == "created"
    assert resume_result["source"] == "mas_runtime_core"
    assert resume_result["snapshot"]["status"] == "running"
    assert resume_result["snapshot"]["active_run_id"].startswith("mas-run-")
    assert state["runtime_backend_id"] == "mas_runtime_core"
    assert state["external_mds_required"] is False


def test_mas_runtime_core_live_execution_reads_local_runtime_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    result = module.inspect_quest_live_execution(runtime_root=runtime_root, quest_id="quest-001")

    assert result["ok"] is True
    assert result["status"] == "live"
    assert result["source"] == "mas_runtime_core_local_state"
    assert result["runner_live"] is True
    assert result["bash_live"] is False
    assert result["runtime_audit"]["worker_running"] is True


def test_mas_runtime_core_monitoring_url_points_to_progress_portal(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    workspace_root = tmp_path / "workspace"
    runtime_root = workspace_root / "runtime"
    portal_path = workspace_root / "ops" / "mas" / "progress" / "index.html"
    portal_path.parent.mkdir(parents=True)
    portal_path.write_text("<!doctype html><title>MAS Progress Portal</title>", encoding="utf-8")

    result = module.resolve_daemon_url(runtime_root=runtime_root)

    assert result == portal_path.resolve().as_uri()
    assert result != runtime_root.resolve().as_uri()


def test_mas_runtime_core_monitoring_url_requires_materialized_progress_portal(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    try:
        module.resolve_daemon_url(runtime_root=runtime_root)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("resolve_daemon_url should require a materialized MAS Progress Portal")

    assert "MAS Progress Portal is not materialized" in message
    assert "workspace progress-portal" in message
    assert str(runtime_root.parent / "ops" / "mas" / "progress" / "index.html") in message


def test_mas_runtime_core_update_startup_context_echoes_typed_receipt_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    result = module.update_quest_startup_context(
        runtime_root=runtime_root,
        quest_id="quest-001",
        startup_contract={"scope": "full_research"},
        requested_baseline_ref={"baseline_id": "demo"},
    )

    startup_context = json.loads(
        (runtime_root / "quests" / "quest-001" / "artifacts" / "runtime" / "startup_context.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["ok"] is True
    assert result["quest_id"] == "quest-001"
    assert result["snapshot"]["quest_id"] == "quest-001"
    assert result["snapshot"]["startup_contract"] == {"scope": "full_research"}
    assert result["snapshot"]["requested_baseline_ref"] == {"baseline_id": "demo"}
    assert startup_context["quest_id"] == "quest-001"


def test_runtime_transport_package_defaults_to_mas_runtime_core(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport")
    runtime_root = tmp_path / "workspace" / "runtime"

    result = module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})

    assert result["source"] == "mas_runtime_core"
    assert result["snapshot"]["runtime_backend_id"] == "mas_runtime_core"


def test_mas_runtime_core_repair_paper_live_paths_rewrites_without_external_launcher(
    tmp_path: Path,
) -> None:
    helpers = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_parts.execution_helpers")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    legacy_root = tmp_path / "legacy-workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "legacy" / "mds-runtime",
        med_deepscientist_repo_root=None,
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    paper_workspace = profile.managed_runtime_quests_root / "quest-001" / ".ds" / "worktrees" / "paper-run-001"
    paper_root = paper_workspace / "paper"
    source_csv = workspace_root / "studies" / "001-risk" / "artifacts" / "score.csv"
    source_csv.parent.mkdir(parents=True, exist_ok=True)
    source_csv.write_text("score\n1\n", encoding="utf-8")
    legacy_score_path = str(legacy_root / source_csv.relative_to(workspace_root))
    catalog_path = paper_root / "figures" / "figure_catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "figures": [
                    {
                        "figure_id": "F1",
                        "export_paths": [
                            str(paper_root / "paper" / "figures" / "generated" / "F1.png"),
                        ],
                        "source_paths": [legacy_score_path],
                        "qc_result": {
                            "layout_sidecar_path": str(
                                paper_root / "paper" / "figures" / "generated" / "F1.layout.json"
                            )
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = helpers.repair_paper_live_paths(
        profile=profile,
        quest_id="quest-001",
        workspace_root=paper_workspace,
        current_workspace_root=workspace_root,
    )

    repaired_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["source"] == "mas_runtime_core"
    assert result["external_mds_required"] is False
    assert str(catalog_path) in result["repaired_files"]
    assert repaired_catalog["figures"][0]["source_paths"] == [
        os.path.relpath(source_csv, paper_workspace).replace(os.sep, "/")
    ]
    assert repaired_catalog["figures"][0]["export_paths"] == ["paper/figures/generated/F1.png"]
    assert repaired_catalog["figures"][0]["qc_result"]["layout_sidecar_path"] == (
        "paper/figures/generated/F1.layout.json"
    )

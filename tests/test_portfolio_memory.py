from __future__ import annotations

import importlib
from pathlib import Path


def test_init_portfolio_memory_creates_scaffold_and_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portfolio_memory")
    workspace_root = tmp_path / "workspace"

    result = module.init_portfolio_memory(workspace_root=workspace_root)

    root = workspace_root / "portfolio" / "research_memory"
    assert result["workspace_root"] == str(workspace_root.resolve())
    assert root.is_dir()
    assert (root / "README.md").is_file()
    assert (root / "registry.yaml").is_file()
    assert (root / "topic_landscape.md").is_file()
    assert (root / "dataset_question_map.md").is_file()
    assert (root / "venue_intelligence.md").is_file()

    status = module.portfolio_memory_status(workspace_root=workspace_root)

    assert status["portfolio_memory_exists"] is True
    assert status["registry_exists"] is True
    assert status["asset_count"] == 3
    assert status["existing_asset_count"] == 3
    assert status["seeded_asset_count"] == 0


def test_init_portfolio_memory_is_idempotent_and_preserves_existing_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portfolio_memory")
    workspace_root = tmp_path / "workspace"

    module.init_portfolio_memory(workspace_root=workspace_root)
    topic_landscape = workspace_root / "portfolio" / "research_memory" / "topic_landscape.md"
    topic_landscape.write_text("# custom\n", encoding="utf-8")

    result = module.init_portfolio_memory(workspace_root=workspace_root)

    assert str(topic_landscape) in result["skipped_files"]
    assert topic_landscape.read_text(encoding="utf-8") == "# custom\n"


def test_portfolio_memory_status_counts_seeded_assets_from_registry(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portfolio_memory")
    workspace_root = tmp_path / "workspace"
    module.init_portfolio_memory(workspace_root=workspace_root)

    registry_path = workspace_root / "portfolio" / "research_memory" / "registry.yaml"
    registry_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "memory_layer: portfolio_research_memory",
                "workspace_scope: disease_workspace",
                "assets:",
                "  - asset_id: topic_landscape",
                "    title: Disease Topic Landscape",
                "    path: topic_landscape.md",
                "    status: seeded",
                "    purpose: topics",
                "  - asset_id: dataset_question_map",
                "    title: Dataset Question Map",
                "    path: dataset_question_map.md",
                "    status: mature",
                "    purpose: questions",
                "  - asset_id: venue_intelligence",
                "    title: Venue Intelligence",
                "    path: venue_intelligence.md",
                "    status: stub",
                "    purpose: venues",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    status = module.portfolio_memory_status(workspace_root=workspace_root)

    assert status["seeded_asset_count"] == 2
    assert status["existing_asset_count"] == 3

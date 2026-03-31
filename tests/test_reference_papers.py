from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolve_reference_papers_reads_startup_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.reference_papers")
    quest_root = tmp_path / "workspace" / "ops" / "deepscientist" / "runtime" / "quests" / "002-early-risk"
    write_text(
        quest_root / "quest.yaml",
        """quest_id: 002-early-risk
startup_contract:
  reference_papers:
    - id: yamashita2024-jama
      title: Risk stratification for endocrine surgery
      url: https://example.org/jama-risk-paper
      role: anchor_paper
      borrow_contract:
        - cohort framing
        - evaluation package
      do_not_borrow:
        - disease-specific thresholds
    - id: li2023-bmj
      title: Gray-zone triage workflow
      pdf_path: references/li2023-bmj.pdf
      role: adjacent_inspiration
      borrow_contract:
        - workflow framing
        - figure package
""",
    )

    contract = module.resolve_reference_paper_contract(quest_root=quest_root)

    assert contract is not None
    assert contract.paper_count == 2
    assert contract.stage_requirements == {
        "scout": "required",
        "idea": "required",
        "write": "advisory",
    }
    assert contract.papers[0].paper_id == "yamashita2024-jama"
    assert contract.papers[0].source_kind == "url"
    assert contract.papers[0].role == "anchor_paper"
    assert contract.papers[0].borrow_contract == ("cohort framing", "evaluation package")
    assert contract.papers[0].do_not_borrow == ("disease-specific thresholds",)
    assert contract.papers[1].source_kind == "pdf_path"
    assert contract.papers[1].pdf_path == quest_root / "references" / "li2023-bmj.pdf"


def test_resolve_reference_papers_accepts_top_level_fallback(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.reference_papers")
    quest_root = tmp_path / "quest"
    write_text(
        quest_root / "quest.yaml",
        """quest_id: q001
reference_papers:
  - doi: 10.1001/example.2024.12345
    title: Example paper
    role: closest_competitor
    notes: keep the comparison package, not the endpoint definition
""",
    )

    contract = module.resolve_reference_paper_contract(quest_root=quest_root)

    assert contract is not None
    assert contract.paper_count == 1
    assert contract.papers[0].source_kind == "doi"
    assert contract.papers[0].role == "closest_competitor"
    assert contract.papers[0].notes == "keep the comparison package, not the endpoint definition"


def test_resolve_reference_papers_requires_at_least_one_locator(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.reference_papers")
    quest_root = tmp_path / "quest"
    write_text(
        quest_root / "quest.yaml",
        """quest_id: q001
startup_contract:
  reference_papers:
    - title: Broken reference paper
      role: anchor_paper
""",
    )

    with pytest.raises(ValueError, match="locator"):
        module.resolve_reference_paper_contract(quest_root=quest_root)


def test_reference_papers_export_hydration_ready_literature_records(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.reference_papers")
    quest_root = tmp_path / "quest"
    write_text(
        quest_root / "quest.yaml",
        """quest_id: q001
startup_contract:
  reference_papers:
    - id: yamashita2024-jama
      title: Risk stratification for endocrine surgery
      doi: 10.1001/example.2024.12345
      role: anchor_paper
    - id: li2023-bmj
      title: Gray-zone triage workflow
      pdf_path: references/li2023-bmj.pdf
      role: adjacent_inspiration
""",
    )

    contract = module.resolve_reference_paper_contract(quest_root=quest_root)

    assert contract is not None

    records = module.export_reference_papers_to_literature_records(contract=contract)

    assert len(records) == 2
    assert records[0]["record_id"] == "yamashita2024-jama"
    assert records[0]["doi"] == "10.1001/example.2024.12345"
    assert records[0]["source_priority"] == 3
    assert records[0]["full_text_availability"] == "metadata_only"
    assert records[0]["relevance_role"] == "anchor_paper"
    assert records[1]["record_id"] == "li2023-bmj"
    assert records[1]["local_asset_paths"] == (str(quest_root / "references" / "li2023-bmj.pdf"),)
    assert records[1]["source_priority"] == 6
    assert records[1]["full_text_availability"] == "full_text"


def test_startup_brief_template_mentions_reference_papers() -> None:
    template = Path("templates/startup_brief.template.md").read_text(encoding="utf-8")
    assert "## Reference papers" in template

from .shared import *


def test_build_report_blocks_when_manuscript_under_cites_reference_database(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = _paper_root_from_quest(quest_root)
    manuscript_path = paper_root / "draft.md"
    manuscript_path.write_text(
        manuscript_path.read_text(encoding="utf-8")
        + "\nThe model was interpreted against prior cardiovascular risk literature [@ref_1; @ref_2; @ref_3; @ref_4; @ref_5; @ref_6; @ref_7; @ref_8].\n",
        encoding="utf-8",
    )
    reference_items = [
        f"@article{{ref_{index},\n  title = {{Reference {index}}},\n  journal = {{Medical Journal}},\n  year = {{2024}}\n}}\n"
        for index in range(1, 24)
    ]
    (paper_root / "references.bib").write_text("\n".join(reference_items), encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "reference_citation_coverage_incomplete" in report["blockers"]
    assert report["reference_citation_coverage"]["bib_entry_count"] == 23
    assert report["reference_citation_coverage"]["cited_key_count"] == 8
    assert any(hit["pattern_id"] == "reference_citation_coverage_low" for hit in report["top_hits"])

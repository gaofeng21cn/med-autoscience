from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_build_gate_report_resolves_v2_submission_manifest_source_markdown_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        include_submission_authority_inputs=False,
        figure_catalog={
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "manuscript_status": "main_text",
                }
            ],
        },
    )
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    paper_root = worktree_root / "paper"
    legacy_manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    v2_manifest_path = paper_root / "submission_minimal" / "audit" / "submission_manifest.json"
    payload = json.loads(legacy_manifest_path.read_text(encoding="utf-8"))
    payload["manuscript"]["source_markdown_path"] = "paper/submission_minimal/manuscript_submission.md"
    v2_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(v2_manifest_path, payload)
    legacy_manifest_path.unlink()
    write_text(paper_root / "submission_minimal" / "manuscript_submission.md", "# authoritative\n")

    captured: dict[str, Path] = {}

    def fake_build_submission_manuscript_surface_qc(
        *,
        publication_profile: str,
        source_markdown_path: Path,
        docx_path: Path,
        pdf_path: Path,
        expected_main_figure_count: int,
    ) -> dict[str, object]:
        captured["source_markdown_path"] = source_markdown_path
        captured["docx_path"] = docx_path
        captured["pdf_path"] = pdf_path
        return {
            "qc_profile": "submission_manuscript_surface",
            "status": "pass",
            "failures": [],
        }

    monkeypatch.setattr(
        module.submission_minimal,
        "build_submission_manuscript_surface_qc",
        fake_build_submission_manuscript_surface_qc,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["submission_minimal_manifest_path"] == str(v2_manifest_path)
    assert captured["source_markdown_path"] == paper_root / "submission_minimal" / "manuscript_submission.md"
    assert captured["docx_path"] == paper_root / "submission_minimal" / "manuscript.docx"
    assert captured["pdf_path"] == paper_root / "submission_minimal" / "paper.pdf"
    assert "submission_surface_qc_failure_present" not in report["blockers"]

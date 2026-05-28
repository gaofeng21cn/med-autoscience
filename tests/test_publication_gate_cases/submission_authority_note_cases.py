from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_build_gate_report_excludes_submission_authority_note_from_manuscript_terminology_scan(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    submission_root = paper_root / "submission_minimal"
    submission_manifest_path = submission_root / "submission_manifest.json"
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload["manuscript"].update(
        {
            "source_markdown_path": "paper/submission_minimal/manuscript_submission.md",
            "source_markdown_alias_path": "paper/submission_minimal/manuscript_source.md",
            "source_markdown_alias_role": "authority_note",
        }
    )
    dump_json(submission_manifest_path, payload)
    write_text(
        submission_root / "manuscript_source.md",
        (
            "Package authority note for the minimal submission bundle; not the full manuscript surface.\n\n"
            "Scientific quality closure and submission readiness still require an AI reviewer-backed "
            "quality record, a clear publication gate, and a fresh package projection.\n\n"
            "Paper content revisions belong in controller-authorized canonical paper sources followed by MAS export/sync/QC.\n"
        ),
    )
    write_text(
        submission_root / "manuscript_submission.md",
        "# Abstract\n\nThis clean manuscript projection contains no internal runtime terminology.\n",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert "forbidden_manuscript_terminology" not in report["blockers"]
    assert not any(
        item["path"].endswith("submission_minimal/manuscript_source.md")
        for item in report["manuscript_terminology_violations"]
    )

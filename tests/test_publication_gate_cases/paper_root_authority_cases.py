from __future__ import annotations

from .shared import *


def test_build_gate_state_prefers_complete_bound_study_canonical_paper_when_branch_differs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        include_submission_authority_inputs=False,
    )
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    study_paper_root = study_root / "paper"
    dump_json(worktree_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/old"})
    dump_json(study_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "main"})
    write_text(study_paper_root / "draft.md", "# Draft\n\nJournal-style manuscript.\n")
    dump_json(study_paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    dump_json(study_paper_root / "medical_prose_review.json", {"schema_version": 1})
    dump_json(study_paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(study_paper_root / "results_narrative_map.json", {"schema_version": 1})
    dump_json(study_paper_root / "figure_semantics_manifest.json", {"schema_version": 1})
    dump_json(study_paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(study_paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})

    state = module.build_gate_state(quest_root)

    assert state.paper_bundle_manifest_path == study_paper_root.resolve() / "paper_bundle_manifest.json"
    assert state.paper_root == study_paper_root.resolve()
    assert state.study_root == study_root.resolve()

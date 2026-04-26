from .shared import *

def test_build_report_blocks_when_non_formal_question_sentence_appears(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_question_mark_prose=True,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "non_formal_question_sentence_present" in report["blockers"]
    assert any(hit["pattern_id"] == "non_formal_question_sentence" for hit in report["top_hits"])


def test_scan_non_formal_question_sentences_does_not_use_backtracking_question_regex(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    manuscript_path = tmp_path / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True)
    manuscript_path.write_text(
        "## Discussion\n"
        + ("This clause keeps extending the same manuscript sentence " * 200)
        + "does the supervisor tick remain bounded?\n",
        encoding="utf-8",
    )

    class ExplodingQuestionRegex:
        def finditer(self, text: str):
            raise AssertionError("question sentence scanning must not depend on the backtracking regex")

    monkeypatch.setattr(module, "QUESTION_SENTENCE_RE", ExplodingQuestionRegex(), raising=False)

    hits = module.scan_non_formal_question_sentences(manuscript_path)

    assert len(hits) == 1
    assert hits[0]["pattern_id"] == "non_formal_question_sentence"
    assert hits[0]["location"] == "line 2"
    assert hits[0]["phrase"].endswith("does the supervisor tick remain bounded?")


def test_build_report_blocks_generic_tool_disclosure_labels_in_caption(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        figure_caption_override=(
            "This figure summarizes operating characteristics. "
            "Publication-grade refinement remains external "
            "(open-source: https://example.com/repo; online service: https://figure-service.example.com)."
        ),
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(hit["phrase"] == "open-source:" for hit in report["top_hits"])
    assert any(hit["phrase"] == "online service:" for hit in report["top_hits"])


def test_build_report_blocks_prediction_model_engineering_terms_in_manuscript_text(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    draft_path = _paper_root_from_quest(quest_root) / "draft.md"
    draft_path.write_text(
        "# Draft\n\n"
        "## Abstract\n\n"
        "The horizon contract and predictor surface were evaluated in the validation surface.\n\n"
        "## Results\n\n"
        "Endpoint-alignment evidence and the control endpoint supported a limitation-aware conclusion.\n",
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    phrases = {hit["phrase"] for hit in report["top_hits"]}
    assert "contract" in phrases
    assert "predictor surface" in phrases
    assert "validation surface" in phrases
    assert "endpoint-alignment evidence" in phrases
    assert "control endpoint" in phrases
    assert "limitation-aware" in phrases


def test_build_report_blocks_poster_style_figure_export_annotations(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        generated_figure_text_override=(
            "<svg><text>Sources: grouped-center summary.md</text>"
            "<text>Why this matters</text></svg>\n"
        ),
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(hit["phrase"] == "Sources:" for hit in report["top_hits"])
    assert any(hit["phrase"] == "Why this matters" for hit in report["top_hits"])


def test_build_report_blocks_internal_project_writing_terms_from_manuscript(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    draft_path = paper_root / "draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8")
        + "\n## Conclusion\n\n"
        "This manuscript should be read as a limitation-aware report using frozen analysis outputs. "
        "All-cause mortality remained a supportive endpoint in the paper-facing narrative.\n",
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    pattern_ids = {hit["pattern_id"] for hit in report["top_hits"]}
    assert "this manuscript should be read as" in pattern_ids
    assert "limitation-aware" in pattern_ids
    assert "frozen analysis outputs" in pattern_ids
    assert "supportive endpoint" in pattern_ids
    assert "paper-facing" in pattern_ids


def test_build_report_blocks_when_secondary_model_entry_is_incomplete(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_complete_model_registry=False,
    )

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]


def test_build_report_blocks_when_model_entry_omits_input_scope_and_construction_details(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_model_method_details=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"])
    assert "input_scope" in excerpts
    assert "feature_construction" in excerpts
    assert "predictor_selection_strategy" in excerpts


def test_build_report_blocks_when_model_entry_omits_comparison_rationale(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    manifest_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "methods_implementation_manifest.json"
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["model_registry"][1].pop("comparison_rationale", None)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"])
    assert "comparison_rationale" in excerpts


def test_build_report_blocks_when_case_mix_and_applicability_boundary_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_case_mix_boundary_fields=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"])
    assert "case_mix_summary" in excerpts
    assert "applicability_boundary" in excerpts


def test_build_report_blocks_when_missing_data_policy_ids_are_inconsistent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        align_missing_data_policy_ids=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "missing_data_policy_inconsistent" in report["blockers"]
    assert any(hit["pattern_id"] == "missing_data_policy_inconsistent" for hit in report["top_hits"])


def test_build_report_blocks_when_review_ledger_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_review_ledger=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "review_ledger_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "review_ledger" for hit in report["top_hits"])


def test_build_report_blocks_when_review_ledger_shape_is_invalid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    review_ledger_path = _paper_root_from_quest(quest_root) / "review" / "review_ledger.json"
    dump_json(
        review_ledger_path,
        {
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer_1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "open",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [],
                }
            ],
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "review_ledger_missing_or_incomplete" in report["blockers"]
    assert any(
        hit["pattern_id"] == "review_ledger" and "revision_links" in hit["excerpt"]
        for hit in report["top_hits"]
    )


def test_build_report_accepts_valid_review_ledger(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "review_ledger_missing_or_incomplete" not in report["blockers"]
    assert report["review_ledger_present"] is True
    assert report["review_ledger_valid"] is True


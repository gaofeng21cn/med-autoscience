from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

__all__ = [
    "STABLE_MEDICAL_JOURNAL_STYLE_CORPUS_RELATIVE_PATH",
    "build_medical_journal_style_corpus",
    "materialize_medical_journal_style_corpus",
    "read_medical_journal_style_corpus",
    "resolve_medical_journal_style_corpus_ref",
    "stable_medical_journal_style_corpus_path",
    "validate_medical_journal_style_corpus",
]


STABLE_MEDICAL_JOURNAL_STYLE_CORPUS_RELATIVE_PATH = Path("paper/medical_journal_style_corpus.json")

_REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "surface",
    "corpus_id",
    "style_profile",
    "source_refs",
    "principles",
    "rhetorical_moves",
    "reviewer_questions",
    "copyright_boundary",
)


def stable_medical_journal_style_corpus_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_MEDICAL_JOURNAL_STYLE_CORPUS_RELATIVE_PATH).resolve()


def resolve_medical_journal_style_corpus_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_medical_journal_style_corpus_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("medical journal style corpus reader only accepts the study paper corpus artifact")
    return stable_path


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _non_empty_sequence(value: object) -> bool:
    return isinstance(value, list) and any(_text(item) or isinstance(item, Mapping) for item in value)


def build_medical_journal_style_corpus() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "medical_journal_style_corpus",
        "corpus_id": "general_medical_journal_style_corpus_v1",
        "style_profile": {
            "target_voice": "neutral_clinical_original_research",
            "target_reader": ["clinician_researcher", "statistical_reviewer", "journal_editor"],
            "journal_voice_target": "JAMA/NEJM/BMJ/Lancet-style restrained original research prose",
        },
        "source_refs": [
            {
                "source_id": "zeiger_biomedical_papers",
                "label": "Mimi Zeiger, Essentials of Writing Biomedical Research Papers",
                "url": "https://accesspharmacy.mhmedical.com/book.aspx?bookID=2123",
                "style_takeaway": "Treat the biomedical paper as a section-by-section argument; make each section perform its rhetorical job with clear, concrete prose.",
            },
            {
                "source_id": "gopen_swan_reader_expectations",
                "label": "Gopen and Swan, The Science of Scientific Writing",
                "url": "https://www.cs.tufts.edu/comp/105-2016s/readings/sci.html",
                "style_takeaway": "Use topic and stress positions deliberately so readers meet familiar context before the new finding or boundary.",
            },
            {
                "source_id": "jama_author_instructions",
                "label": "JAMA Instructions for Authors",
                "url": "https://jamanetwork.com/journals/jama/pages/instructions-for-authors",
                "style_takeaway": "Prefer concise, specific, informative wording; quantify results with uncertainty and avoid overgeneralized relevance claims.",
            },
            {
                "source_id": "elsevier_medicine_writing",
                "label": "Elsevier Author Services medical manuscript writing guidance",
                "url": "https://scientific-publishing.webshop.elsevier.com/manuscript-preparation/the-essentials-of-writing-to-communicate-research-in-medicine/",
                "style_takeaway": "Write for the medical audience, show relevance, and keep conclusions inside the evidence.",
            },
            {
                "source_id": "jama_network_open_original_investigations",
                "label": "JAMA Network Open original investigations",
                "url": "https://jamanetwork.com/journals/jamanetworkopen",
                "style_takeaway": "Use a clinically motivated opening, findings-first Results paragraphs, and restrained Discussion interpretation.",
            },
        ],
        "principles": {
            "introduction": [
                "Open with the clinical problem and why the reader should care.",
                "Narrow quickly to the specific evidence gap the study can answer.",
                "End the setup with a precise objective, not a project-status statement.",
            ],
            "sentence_information_flow": [
                "Put known context near the beginning of a sentence.",
                "Put the important new finding or limitation near the sentence close.",
                "Keep controller artifacts, files, and displays out of the topic position of manuscript sentences.",
            ],
            "results": [
                "Make the clinical finding the grammatical subject.",
                "Give the quantitative result and uncertainty before the display citation.",
                "Order paragraphs by clinical importance rather than pipeline chronology.",
            ],
            "discussion": [
                "Start with the principal finding in restrained language.",
                "Relate the finding to prior work before extending interpretation.",
                "State limitations as claim boundaries, not as a defensive checklist.",
                "Close with what the data support, not what the system completed.",
            ],
            "claim_restraint": [
                "Avoid best, first, novel, practice-changing, and no-difference claims unless the evidence map supports the exact wording.",
                "When findings are imprecise, report estimates and uncertainty instead of converting imprecision into absence.",
            ],
        },
        "rhetorical_moves": [
            {
                "move_id": "clinical_problem_to_gap",
                "use_for": "Introduction opening",
                "bad_pattern": "This project completed a pipeline for the cohort.",
                "journal_style_move": "Patients with the condition face a clinical decision problem; prior evidence has not resolved the specific decision boundary.",
            },
            {
                "move_id": "finding_first_results",
                "use_for": "Results paragraph lead",
                "bad_pattern": "Figure 1 shows the model worked well.",
                "journal_style_move": "The prespecified model separated clinically relevant risk groups, with the display cited after the quantitative finding.",
            },
            {
                "move_id": "restrained_discussion",
                "use_for": "Discussion interpretation",
                "bad_pattern": "The manuscript proves the model is ready for clinical use.",
                "journal_style_move": "The findings support a bounded interpretation and require external confirmation before clinical adoption claims.",
            },
        ],
        "reviewer_questions": [
            "Does the opening move from clinical problem to evidence gap to objective?",
            "Do Results sentences make findings, patients, exposures, outcomes, or estimates the subjects rather than figures, tables, files, or controller artifacts?",
            "Does the Discussion interpret the main finding before listing limitations?",
            "Are claims restrained to the evidence map and uncertainty?",
            "Would a medical journal editor read the manuscript as original research rather than a work report?",
        ],
        "copyright_boundary": {
            "mode": "principle_and_short_paraphrase_only",
            "long_excerpts_allowed": False,
            "writer_instruction": "Use the corpus to learn voice, rhythm, and reviewer questions; do not copy source text.",
        },
    }


def validate_medical_journal_style_corpus(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["payload must be a JSON object"]
    missing = [field for field in _REQUIRED_TOP_LEVEL_FIELDS if field not in payload]
    if missing:
        return [f"missing top-level keys: {', '.join(missing)}"]
    if payload.get("schema_version") != 1:
        return ["schema_version must be 1"]
    if payload.get("surface") != "medical_journal_style_corpus":
        return ["surface must be medical_journal_style_corpus"]
    if _text(payload.get("corpus_id")) != "general_medical_journal_style_corpus_v1":
        return ["corpus_id must be general_medical_journal_style_corpus_v1"]
    style_profile = payload.get("style_profile")
    if not isinstance(style_profile, Mapping) or not _text(style_profile.get("target_voice")):
        return ["style_profile.target_voice must be non-empty"]
    source_refs = payload.get("source_refs")
    if not isinstance(source_refs, list) or len(source_refs) < 5:
        return ["source_refs must include the style source set"]
    principles = payload.get("principles")
    if not isinstance(principles, Mapping):
        return ["principles must be an object"]
    for key in ("introduction", "sentence_information_flow", "results", "discussion", "claim_restraint"):
        if not _non_empty_sequence(principles.get(key)):
            return [f"principles.{key} must be a non-empty list"]
    if not _non_empty_sequence(payload.get("rhetorical_moves")):
        return ["rhetorical_moves must be a non-empty list"]
    if not _non_empty_sequence(payload.get("reviewer_questions")):
        return ["reviewer_questions must be a non-empty list"]
    boundary = payload.get("copyright_boundary")
    if not isinstance(boundary, Mapping) or boundary.get("long_excerpts_allowed") is not False:
        return ["copyright_boundary.long_excerpts_allowed must be false"]
    return []


def read_medical_journal_style_corpus(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    path = resolve_medical_journal_style_corpus_ref(study_root=study_root, ref=ref)
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    errors = validate_medical_journal_style_corpus(payload)
    if errors:
        raise ValueError(f"medical journal style corpus is invalid: {'; '.join(errors)}")
    return dict(payload)


def materialize_medical_journal_style_corpus(
    *,
    study_root: Path,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    resolved_payload = dict(payload) if isinstance(payload, Mapping) else build_medical_journal_style_corpus()
    errors = validate_medical_journal_style_corpus(resolved_payload)
    if errors:
        raise ValueError(f"medical journal style corpus is invalid: {'; '.join(errors)}")
    path = stable_medical_journal_style_corpus_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resolved_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": "medical_journal_style_corpus",
        "artifact_path": str(path),
    }

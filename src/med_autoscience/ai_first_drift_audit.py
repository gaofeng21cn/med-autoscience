from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "ai_first_drift_audit"


@dataclass(frozen=True)
class DriftRule:
    check_id: str
    category: str
    root_key: str
    relative_path: str
    summary: str
    required_markers: tuple[str, ...]
    forbidden_markers: tuple[str, ...] = ()


MAS_AI_FIRST_RULES: tuple[DriftRule, ...] = (
    DriftRule(
        check_id="quality_ready_requires_ai_reviewer_provenance",
        category="ready_wording_without_ai_provenance",
        root_key="mas_repo_root",
        relative_path="src/med_autoscience/quality/study_quality.py",
        summary="Study quality cannot close quality readiness without AI reviewer provenance.",
        required_markers=(
            'provenance["owner"] == "ai_reviewer"',
            'not bool(provenance["ai_reviewer_required"])',
            '"source": "publication_eval_projection"',
            '"status": "review_required"',
            '"contract_closed": contract_state in {"write_line_ready", "bundle_only_remaining"}',
        ),
    ),
    DriftRule(
        check_id="quality_closure_reducer_fails_closed_without_ai_reviewer",
        category="ready_wording_without_ai_provenance",
        root_key="mas_repo_root",
        relative_path="src/med_autoscience/evaluation_summary_parts/quality_closure_truth.py",
        summary="Quality closure truth must fail closed to review_required for projection-only evals.",
        required_markers=(
            "publication_eval_ai_reviewer_backed(publication_eval)",
            "if not publication_eval_ai_reviewer_backed(publication_eval):",
            '"state": "review_required"',
            '"current_required_action": "return_to_ai_reviewer"',
            '"ai_reviewer_required": True',
        ),
    ),
    DriftRule(
        check_id="runtime_materialized_eval_marks_mechanical_projection",
        category="mechanical_projection_as_quality",
        root_key="mas_repo_root",
        relative_path="src/med_autoscience/controllers/study_runtime_decision_parts/publication_and_submission.py",
        summary="Runtime-derived publication eval records must be mechanical projections.",
        required_markers=(
            'owner="mechanical_projection"',
            'source_kind="publication_gate_report"',
            'policy_id="publication_gate_projection_v1"',
            "ai_reviewer_required=True",
        ),
        forbidden_markers=(
            'owner="ai_reviewer"',
            'source_kind="publication_eval_ai_reviewer"',
        ),
    ),
    DriftRule(
        check_id="mechanical_stop_loss_flags_do_not_authorize_stop_loss",
        category="mechanical_stop_loss",
        root_key="mas_repo_root",
        relative_path="src/med_autoscience/quality/publication_gate.py",
        summary="Stop-loss decisions need AI reviewer-backed publishability authority.",
        required_markers=(
            "def _ai_reviewer_backed",
            "def _mechanical_stop_loss_flags",
            "if not _ai_reviewer_backed(promotion_gate_payload):",
            '"current_required_action": "return_to_ai_reviewer"',
            '"mechanical_stop_loss_flags"',
            "def _publishability_stop_loss_recommended",
        ),
    ),
    DriftRule(
        check_id="pattern_hits_are_evidence_not_subjective_prose_authority",
        category="pattern_only_subjective_blockers",
        root_key="mas_repo_root",
        relative_path="src/med_autoscience/controllers/medical_publication_surface_parts/reporting.py",
        summary="Pattern scans may provide evidence snippets, but subjective prose blockers need AI review.",
        required_markers=(
            'medical_journal_prose_ai_verdict in {"block", "revise"}',
            '"medical_prose_review_mechanical_safety_flags"',
            '"AI-first medical prose review"',
        ),
        forbidden_markers=(
            'blockers.append("figure_table_led_results_narration_present")',
            'blockers.append("non_formal_question_sentence_present")',
        ),
    ),
    DriftRule(
        check_id="canonical_blueprint_requires_ai_authorization",
        category="mechanical_blueprint_as_canonical",
        root_key="mas_repo_root",
        relative_path="src/med_autoscience/medical_manuscript_blueprint.py",
        summary="Mechanical blueprint materialization must not become the canonical manuscript blueprint.",
        required_markers=(
            'Path("paper/medical_manuscript_blueprint_source.json")',
            '"source_kind"] = "mechanical_draft"',
            '"canonical_ready"] = False',
            "requires AI authorization provenance",
            'owner not in {"ai_author", "ai_reviewer"}',
            "validate_medical_manuscript_blueprint(resolved_payload)",
        ),
    ),
    DriftRule(
        check_id="quality_os_forbids_prompt_only_quality_gates",
        category="prompt_only_gates",
        root_key="mas_repo_root",
        relative_path="src/med_autoscience/controllers/medical_quality_operating_system.py",
        summary="The quality OS must encode evidence-over-claims and AI reviewer authority as data.",
        required_markers=(
            '"claim_only_ready_allowed": False',
            '"ready_verbs_require_authority_refs": True',
            '"mechanical_projection_can_authorize_quality": False',
            '"ai_first_subjective_quality"',
            '"mechanical_pattern_role": "evidence_snippets_only"',
        ),
    ),
    DriftRule(
        check_id="policy_records_external_engineering_basis_and_audit_scope",
        category="doctor_meta_test_surface",
        root_key="mas_repo_root",
        relative_path="docs/policies/ai_first_quality_boundary.md",
        summary="The stable policy must document the audit scope and external engineering basis.",
        required_markers=(
            "AI-first drift audit",
            "NIST AI RMF",
            "EQUATOR",
            "G-Eval",
            "Google SRE",
            "coverage-as-quality",
        ),
    ),
)


MDS_AI_FIRST_RULES: tuple[DriftRule, ...] = (
    DriftRule(
        check_id="mds_existing_draft_still_requires_mas_ai_preflight",
        category="stale_or_bypassed_ai_preflight",
        root_key="med_deepscientist_repo_root",
        relative_path="src/deepscientist/quest/service.py",
        summary="MDS paper contract health must not let an existing draft bypass MAS AI medical preflight.",
        required_markers=(
            '_MAS_MEDICAL_BLUEPRINT_AUTHORING_PROVENANCE_FIELD = "authoring_provenance"',
            "mas_required_trigger_relpaths = (",
            "mas_medical_preflight_required = bool(managed_study_root) or any",
            "MAS medical manuscript blueprint lacks AI authorization/provenance",
        ),
    ),
    DriftRule(
        check_id="mds_ai_surface_cache_fingerprint",
        category="stale_ai_cache",
        root_key="med_deepscientist_repo_root",
        relative_path="src/deepscientist/artifact/service.py",
        summary="MDS paper contract health cache must include MAS AI-first surfaces.",
        required_markers=(
            "mas_ai_first_surface_summaries",
            '"mas_ai_first_surfaces": mas_ai_first_surface_summaries',
            '"artifacts/publication_eval/medical_prose_review.json"',
            '"paper/review/review_ledger.json"',
            "sha256_text(path.read_text",
        ),
    ),
    DriftRule(
        check_id="mds_coverage_is_mechanical_only",
        category="coverage_as_quality",
        root_key="med_deepscientist_repo_root",
        relative_path="src/deepscientist/artifact/service.py",
        summary="MDS manuscript coverage may only claim mechanical coverage, not quality readiness.",
        required_markers=(
            '"mechanical_coverage_only": True',
            '"quality_authority": "ai_reviewer_required"',
        ),
    ),
    DriftRule(
        check_id="mds_finalize_skill_cannot_use_coverage_as_quality_gate",
        category="prompt_only_gates",
        root_key="med_deepscientist_repo_root",
        relative_path="src/skills/finalize/SKILL.md",
        summary="MDS finalize guidance must route through contract health and MAS AI preflight.",
        required_markers=(
            "mechanical coverage",
            "paper contract health",
            "MAS AI preflight/prose review",
        ),
    ),
    DriftRule(
        check_id="mds_decision_skill_cannot_finalize_from_coverage_alone",
        category="coverage_as_quality",
        root_key="med_deepscientist_repo_root",
        relative_path="src/skills/decision/SKILL.md",
        summary="MDS decision guidance must not choose finalize from coverage alone.",
        required_markers=(
            "mechanical coverage check",
            "paper_contract_health",
            "MAS AI preflight",
        ),
    ),
)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_text(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def evaluate_drift_rule(*, roots: dict[str, Path | None], rule: DriftRule) -> dict[str, Any]:
    root = roots.get(rule.root_key)
    path = (root / rule.relative_path) if root is not None else None
    if path is None or root is None or not root.exists():
        return {
            "check_id": rule.check_id,
            "category": rule.category,
            "status": "skipped",
            "root_key": rule.root_key,
            "relative_path": rule.relative_path,
            "summary": rule.summary,
            "reason": f"{rule.root_key} is not configured or does not exist",
        }
    source = _read_text(path)
    if source is None:
        return {
            "check_id": rule.check_id,
            "category": rule.category,
            "status": "fail",
            "root_key": rule.root_key,
            "path": str(path),
            "relative_path": rule.relative_path,
            "summary": rule.summary,
            "missing_file": True,
            "missing_required_markers": list(rule.required_markers),
            "forbidden_markers_present": [],
        }
    missing = [marker for marker in rule.required_markers if marker not in source]
    forbidden = [marker for marker in rule.forbidden_markers if marker in source]
    status = "pass" if not missing and not forbidden else "fail"
    return {
        "check_id": rule.check_id,
        "category": rule.category,
        "status": status,
        "root_key": rule.root_key,
        "path": str(path),
        "relative_path": rule.relative_path,
        "summary": rule.summary,
        "missing_required_markers": missing,
        "forbidden_markers_present": forbidden,
    }


def run_ai_first_drift_audit(
    *,
    repo_root: Path | str | None = None,
    med_deepscientist_repo_root: Path | str | None = None,
) -> dict[str, Any]:
    mas_root = Path(repo_root).expanduser().resolve() if repo_root is not None else default_repo_root()
    mds_root = (
        Path(med_deepscientist_repo_root).expanduser().resolve()
        if med_deepscientist_repo_root is not None and str(med_deepscientist_repo_root).strip()
        else None
    )
    roots = {
        "mas_repo_root": mas_root,
        "med_deepscientist_repo_root": mds_root,
    }
    checks = [evaluate_drift_rule(roots=roots, rule=rule) for rule in MAS_AI_FIRST_RULES]
    checks.extend(evaluate_drift_rule(roots=roots, rule=rule) for rule in MDS_AI_FIRST_RULES)
    failed = [check for check in checks if check["status"] == "fail"]
    skipped = [check for check in checks if check["status"] == "skipped"]
    categories = sorted({check["category"] for check in checks})
    return {
        "schema_version": SCHEMA_VERSION,
        "surface": SURFACE,
        "status": "fail" if failed else "pass",
        "ready": not failed,
        "checked_roots": {
            "mas_repo_root": str(mas_root),
            "med_deepscientist_repo_root": str(mds_root) if mds_root is not None else None,
        },
        "categories": categories,
        "summary": {
            "check_count": len(checks),
            "pass_count": len([check for check in checks if check["status"] == "pass"]),
            "fail_count": len(failed),
            "skipped_count": len(skipped),
            "failed_check_ids": [str(check["check_id"]) for check in failed],
            "skipped_check_ids": [str(check["check_id"]) for check in skipped],
        },
        "checks": checks,
        "policy_refs": [
            "docs/policies/ai_first_quality_boundary.md",
            "tests/test_ai_first_quality_boundary.py",
            "tests/test_ai_first_drift_audit.py",
        ],
    }

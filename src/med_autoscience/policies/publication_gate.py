from __future__ import annotations


WRITE_DRIFT_STRUCTURED_PATTERNS = (
    r'"action"\s*:\s*"write"',
    r'"next_anchor"\s*:\s*"write"',
    r'"active_anchor"\s*:\s*"write"',
)

WRITE_DRIFT_PATTERNS = (
    r"(?m)^\s*(?:[-*]\s*)?route\s*(?:->|to|:)\s*`?write`?\b",
    r"(?m)^\s*(?:[-*]\s*)?next anchor\s*:\s*`?write`?\b",
    r"(?m)^\s*(?:[-*]\s*)?进入\s*`write`",
    r"(?m)^\s*(?:[-*]\s*)?切到了\s*`write`",
)

MANUSCRIPT_SURFACE_GLOBS = (
    "draft.md",
    "build/review_manuscript.md",
    "tables/*.md",
    "supplementary_tables.md",
)

MANAGED_SUBMISSION_SURFACE_GLOBS = (
    "**/*.md",
    "**/*.tex",
    "**/*.txt",
)

MANUSCRIPT_TERMINOLOGY_REDLINE_PATTERNS = (
    {
        "label": "locked_dataset_version_label",
        "pattern": r"\blocked\s+v\d{4}-\d{2}-\d{2}\b",
    },
    {
        "label": "workspace_cohort_label",
        "pattern": r"\bworkspace cohort\b",
    },
    {
        "label": "followup_freeze_label",
        "pattern": r"\bfollow-up freeze\b",
    },
    {
        "label": "data_freeze_label",
        "pattern": r"\b(?:data|dataset)\s+freeze\b",
    },
    {
        "label": "locked_followup_surface_label",
        "pattern": r"\blocked\s+\d+-month\s+follow-up surface\b",
    },
    {
        "label": "internal_editorial_label",
        "pattern": (
            r"\bpaper-facing\b|"
            r"\bmainline\b|"
            r"\bsidecar\b|"
            r"\banalysis surface\b|"
            r"\bstudy surface\b|"
            r"\bbounded complexity audit\b"
        ),
    },
)

BLOCKED_RECOMMENDED_ACTION = "return_to_publishability_gate"
CLEAR_RECOMMENDED_ACTION = "continue_per_gate"
CONTROLLER_NOTE = (
    "The controller does not decide scientific publishability by itself. "
    "It only blocks uncontrolled transitions into write when the post-main gate "
    "is missing, the contract-level clinical-utility deliverables are absent, "
    "or manuscript-facing text still carries internal runtime terminology."
)


def _format_metric(metrics: dict[str, object], key: str) -> str:
    value = metrics.get(key)
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return "n/a"


def build_intervention_message(report: dict[str, object]) -> str:
    missing = ", ".join(report.get("missing_non_scalar_deliverables") or []) or "none"
    metrics = report.get("headline_metrics") or {}
    blockers = {str(item).strip() for item in (report.get("blockers") or []) if str(item).strip()}
    route_back = str(report.get("medical_publication_surface_route_back_recommendation") or "").strip()
    bundle_stage_blockers = {
        "medical_publication_surface_blocked",
        "submission_hardening_incomplete",
        "stale_submission_minimal_authority",
        "submission_surface_qc_failure_present",
        "missing_submission_minimal",
        "missing_paper_compile_report",
        "missing_journal_package",
        "stale_study_delivery_mirror",
        "unmanaged_submission_surface_present",
    }
    if blockers and blockers.issubset(bundle_stage_blockers) and "submission_hardening_incomplete" in blockers and route_back == "return_to_finalize":
        return (
            "Hard control message from Codex orchestration layer: stop uncontrolled expansion now. "
            "The latest publication gate blockers are limited to same-line submission hardening and package synchronization. "
            "Do not launch new model search, new broad literature expansion, or new analysis campaigns. "
            "Resume the same paper line through a bounded `finalize` / submission-hardening pass: "
            "repair manuscript Methods, statistical reporting, claim-to-table/figure mapping, and clinical actionability, "
            "then rebuild submission_minimal and rerun the publication gate."
        )
    return (
        "Hard control message from Codex orchestration layer: immediately stop the current "
        "transition into `write` / outline generation. Outline creation counts as `write` and "
        "cannot be used to bypass the post-main-result publishability gate. "
        f"The latest recorded main run (`{report['run_id']}`) currently has controller blockers: "
        f"{', '.join(report.get('blockers') or ['none'])}. "
        f"Required contract deliverables still missing from the recorded output bundle: {missing}. "
        f"Headline metrics are A1 roc_auc={_format_metric(metrics, 'roc_auc')}, "
        f"average_precision={_format_metric(metrics, 'average_precision')}, "
        f"brier_score={_format_metric(metrics, 'brier_score')}. "
        "Do not launch new model search. Do not continue write. "
        "Return to `decision` and record an explicit publishability gate memo that compares: "
        "(1) A1 calibration-first interpretable package, "
        "(2) tree-ceiling package, and "
        "(3) stop/branch. "
        "The next route may only be a bounded evidence-building campaign or stop/branch."
    )

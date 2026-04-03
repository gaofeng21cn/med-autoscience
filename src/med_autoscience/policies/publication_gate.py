from __future__ import annotations


WRITE_DRIFT_PATTERNS = [
    r'"action":"write"',
    r"`write`",
    r"进入 `write`",
    r"切到了 `write`",
    r"route.*write",
]

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

def build_intervention_message(report: dict[str, object]) -> str:
    missing = ", ".join(report.get("missing_non_scalar_deliverables") or []) or "none"
    metrics = report.get("headline_metrics") or {}
    return (
        "Hard control message from Codex orchestration layer: immediately stop the current "
        "transition into `write` / outline generation. Outline creation counts as `write` and "
        "cannot be used to bypass the post-main-result publishability gate. "
        f"The latest recorded main run (`{report['run_id']}`) currently has controller blockers: "
        f"{', '.join(report.get('blockers') or ['none'])}. "
        f"Required contract deliverables still missing from the recorded output bundle: {missing}. "
        f"Headline metrics are A1 roc_auc={metrics.get('roc_auc'):.4f}, "
        f"average_precision={metrics.get('average_precision'):.4f}, "
        f"brier_score={metrics.get('brier_score'):.4f}. "
        "Do not launch new model search. Do not continue write. "
        "Return to `decision` and record an explicit publishability gate memo that compares: "
        "(1) A1 calibration-first interpretable package, "
        "(2) tree-ceiling package, and "
        "(3) stop/branch. "
        "The next route may only be a bounded evidence-building campaign or stop/branch."
    )

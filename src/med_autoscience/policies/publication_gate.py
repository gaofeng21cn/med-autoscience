from __future__ import annotations


WRITE_DRIFT_PATTERNS = [
    r'"action":"write"',
    r"`write`",
    r"进入 `write`",
    r"切到了 `write`",
    r"route.*write",
]

BLOCKED_RECOMMENDED_ACTION = "return_to_publishability_gate"
CLEAR_RECOMMENDED_ACTION = "continue_per_gate"
CONTROLLER_NOTE = (
    "The controller does not decide scientific publishability by itself. "
    "It only blocks uncontrolled transitions into write when the post-main gate "
    "is missing or the contract-level clinical-utility deliverables are absent."
)

FORBIDDEN_MANUSCRIPT_TERMINOLOGY_PATTERNS = (
    {
        "rule_id": "dataset_version_label",
        "description": "dataset version labels do not belong in manuscript-facing text",
        "pattern": r"\blocked\s+v\d{4}-\d{2}-\d{2}\b",
    },
    {
        "rule_id": "freeze_label",
        "description": "freeze labels do not belong in manuscript-facing text",
        "pattern": r"\b(?:follow-up|data|dataset)\s+freeze\b",
    },
    {
        "rule_id": "workspace_cohort_label",
        "description": "workspace cohort labels do not belong in manuscript-facing text",
        "pattern": r"\bworkspace cohort\b",
    },
    {
        "rule_id": "internal_editorial_term",
        "description": "internal editorial labels do not belong in manuscript-facing text",
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

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


def _format_metric(metrics: dict[str, object], key: str) -> str:
    value = metrics.get(key)
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return "n/a"


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

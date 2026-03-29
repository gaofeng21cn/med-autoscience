from __future__ import annotations


BLOCKED_RECOMMENDED_ACTION = "reassess_data_state_before_continuing"
CLEAR_RECOMMENDED_ACTION = "continue_with_current_data_contract"
CONTROLLER_NOTE = (
    "The controller does not judge paper quality directly. "
    "It blocks or flags quest progression when the underlying study is using an outdated private release "
    "or when a newly registered public-data extension opportunity appears and has not yet been triaged."
)


def build_intervention_message(report: dict[str, object]) -> str:
    outdated = ", ".join(report.get("outdated_dataset_ids") or []) or "none"
    public_candidates = ", ".join(report.get("public_support_dataset_ids") or []) or "none"
    return (
        "Hard control message from Codex orchestration layer: stop launching new experiments until the data-asset "
        "state is explicitly reviewed. "
        f"Current data blockers for study `{report['study_id']}`: {', '.join(report.get('blockers') or ['none'])}. "
        f"Datasets bound to outdated private releases: {outdated}. "
        f"Registered public-data extension opportunities: {public_candidates}. "
        "Return to `decision` or the study control surface and record one explicit choice: "
        "(1) keep the current freeze and justify why, "
        "(2) upgrade the private dataset release and rerun the affected package, or "
        "(3) branch into an external-validation / mechanistic-extension route. "
        "Do not continue model search or manuscript expansion by inertia."
    )

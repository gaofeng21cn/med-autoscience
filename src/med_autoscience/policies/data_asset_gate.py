from __future__ import annotations


BLOCKED_RECOMMENDED_ACTION = "reassess_data_state_before_continuing"
ADVISORY_RECOMMENDED_ACTION = "triage_and_materialize_public_data_extension_without_interrupting_current_run"
CLEAR_RECOMMENDED_ACTION = "continue_with_current_data_contract"
CONTROLLER_NOTE = (
    "The controller does not judge paper quality directly. "
    "It blocks or flags quest progression when the underlying study is using an outdated private release "
    "and flags newly registered public-data extension opportunities as advisory items whose default follow-through "
    "is durable triage plus immediate download or materialization for retained datasets."
)


def build_intervention_message(report: dict[str, object]) -> str:
    outdated = ", ".join(report.get("outdated_dataset_ids") or []) or "none"
    unresolved = ", ".join(report.get("unresolved_dataset_ids") or []) or "none"
    public_candidates = ", ".join(report.get("public_support_dataset_ids") or []) or "none"
    status = report.get("status")
    if status == "advisory":
        return (
            "Advisory control message from Codex orchestration layer: a newly registered public-data extension "
            "opportunity has appeared and should be explicitly triaged. "
            f"Current advisory items for study `{report['study_id']}`: {', '.join(report.get('advisories') or ['none'])}. "
            f"Registered public-data extension opportunities: {public_candidates}. "
            "You do not need to stop the current run for this reason alone, but the default action is to triage it "
            "durably, record retain / reject decisions through `apply-data-asset-update`, and start immediate "
            "download or materialization follow-through for any retained public dataset. Return to `decision` or the "
            "study control surface before the next major experiment branch or manuscript expansion and record one "
            "explicit choice: (1) keep the current freeze and justify why, or (2) branch into an external-validation / "
            "mechanistic-extension route."
        )
    return (
        "Hard control message from Codex orchestration layer: stop launching new experiments until the data-asset "
        "state is explicitly reviewed. "
        f"Current data blockers for study `{report['study_id']}`: {', '.join(report.get('blockers') or ['none'])}. "
        f"Datasets bound to outdated private releases: {outdated}. "
        f"Datasets with unresolved private-data contract: {unresolved}. "
        f"Registered public-data extension opportunities: {public_candidates}. "
        "Return to `decision` or the study control surface and record one explicit choice: "
        "(1) keep the current freeze and justify why, "
        "(2) upgrade the private dataset release and rerun the affected package, or "
        "(3) branch into an external-validation / mechanistic-extension route. "
        "Do not continue model search or manuscript expansion by inertia."
    )

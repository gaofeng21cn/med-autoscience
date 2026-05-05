from __future__ import annotations


def _derive_manual_finish_dominance_state(
    *,
    quest_exists: bool,
    quest_status: StudyRuntimeQuestStatus,
    study_root: Path,
    quest_root: Path,
    publication_gate_report: dict[str, object] | None,
) -> dict[str, bool]:
    task_intake_payload = read_latest_task_intake(study_root=study_root)
    manual_hold_task_intake = task_intake_requests_manual_hold(task_intake_payload)
    task_intake_overrides_auto_manual_finish = _task_intake_overrides_auto_manual_finish_active(
        study_root=study_root,
    )
    task_intake_releases_manual_finish_parking = task_intake_overrides_auto_manual_finish
    submission_metadata_only_manual_finish = (
        quest_exists
        and not task_intake_releases_manual_finish_parking
        and _submission_metadata_only_manual_finish_active(
            study_root=study_root,
            quest_root=quest_root,
        )
    )
    task_intake_yields_to_submission_closeout = False
    bundle_only_manual_finish = (
        quest_exists
        and _bundle_only_submission_ready_manual_finish_active(
            study_root=study_root,
            quest_root=quest_root,
        )
    )
    delivered_package_manual_finish = quest_exists and _delivered_submission_package_manual_finish_active(
        study_root=study_root,
    )
    if task_intake_overrides_auto_manual_finish and bundle_only_manual_finish:
        summary_payload = _load_json_dict(
            study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
        )
        task_intake_yields_to_submission_closeout = task_intake_yields_to_deterministic_submission_closeout(
            task_intake_payload,
            publishability_gate_report=None,
            evaluation_summary=summary_payload,
        )
        if task_intake_releases_manual_finish_parking and not task_intake_yields_to_submission_closeout:
            bundle_only_manual_finish = False
    task_intake_yields_to_submission_closeout = (
        task_intake_yields_to_submission_closeout
        or _task_intake_yields_to_submission_closeout_active(
            study_root=study_root,
            publication_gate_report=publication_gate_report,
        )
    )
    if task_intake_releases_manual_finish_parking and _task_intake_release_blocked_by_current_closeout(
        study_root=study_root,
        publication_gate_report=publication_gate_report,
    ):
        task_intake_releases_manual_finish_parking = False
        task_intake_yields_to_submission_closeout = True
        submission_metadata_only_manual_finish = quest_exists and _submission_metadata_only_manual_finish_active(
            study_root=study_root,
            quest_root=quest_root,
        )
        bundle_only_manual_finish = quest_exists and _bundle_only_submission_ready_manual_finish_active(
            study_root=study_root,
            quest_root=quest_root,
        )
        delivered_package_manual_finish = quest_exists and _delivered_submission_package_manual_finish_active(
            study_root=study_root,
        )
    explicit_manual_finish_compatibility_guard = _explicit_manual_finish_compatibility_guard_active(
        study_root=study_root,
    )
    manual_finish_compatibility_guard = (
        explicit_manual_finish_compatibility_guard
        or submission_metadata_only_manual_finish
        or bundle_only_manual_finish
        or delivered_package_manual_finish
    )
    submission_metadata_only_wait = (
        quest_exists
        and quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not task_intake_releases_manual_finish_parking
        and _waiting_submission_metadata_only(quest_root)
    )
    return {
        "task_intake_overrides_auto_manual_finish": task_intake_overrides_auto_manual_finish,
        "task_intake_releases_manual_finish_parking": task_intake_releases_manual_finish_parking,
        "submission_metadata_only_manual_finish": submission_metadata_only_manual_finish,
        "task_intake_yields_to_submission_closeout": task_intake_yields_to_submission_closeout,
        "manual_hold_task_intake": manual_hold_task_intake,
        "bundle_only_manual_finish": bundle_only_manual_finish,
        "delivered_package_manual_finish": delivered_package_manual_finish,
        "explicit_manual_finish_compatibility_guard": explicit_manual_finish_compatibility_guard,
        "manual_finish_compatibility_guard": manual_finish_compatibility_guard,
        "submission_metadata_only_wait": submission_metadata_only_wait,
    }

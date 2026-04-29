from __future__ import annotations

from pathlib import Path as _Path

_PARTS = (
    "fixtures_and_launch_cases.py",
    "creation_and_profile_cases.py",
    "overlay_and_resume_cases.py",
    "completion_and_package_cases.py",
    "controller_parking_cases.py",
    "interaction_arbitration_cases.py",
    "finalize_and_recovery_cases.py",
    "startup_boundary_cases.py",
    "runtime_event_surface_cases.py",
    "overlay_audit_and_progress_cases.py",
    "publication_eval_cases.py",
    "stop_loss_status_cases.py",
    "publication_eval_ai_reviewer_cases.py",
    "submission_metadata_waiting_cases.py",
    "submission_metadata_resume_signal_cases.py",
    "submission_metadata_drift_cases.py",
    "submission_metadata_cases.py",
    "submission_metadata_revision_intake_cases.py",
    "live_write_drift_cases.py",
    "live_reviewer_closeout_cases.py",
    "restart_and_submission_cases.py",
)
for _part in _PARTS:
    _chunk_path = _Path(__file__).with_name("test_study_runtime_router_cases") / _part
    exec(compile(_chunk_path.read_text(encoding="utf-8"), str(_chunk_path), "exec"), globals())

del _Path, _PARTS, _part, _chunk_path

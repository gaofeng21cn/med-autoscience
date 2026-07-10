from med_autoscience.controllers import work_unit_runtime_registry as registry


def test_work_unit_registry_fails_closed_and_stays_observability_only(tmp_path):
    root = tmp_path / "workspace"
    cwd = root / "attempt"
    cwd.mkdir(parents=True)
    payload = dict(
        program_id="p", study_id="s", quest_id="q", active_run_id="r", work_unit_id="w", route_id="analysis",
        attempt_state="running", attempt_count=1, run_attempt_phase="analysis", failure_reason="",
        workspace_root=str(root), cwd=str(cwd),
    )
    valid = registry.build_work_unit_attempt_record(payload)
    identities = tuple(valid[key] for key in ("program_id", "study_id", "quest_id", "active_run_id", "work_unit_id"))
    assert registry.validate_work_unit_attempt_record(valid)["ok"] and identities == ("p", "s", "q", "r", "w")
    assert valid["workspace_boundary"]["inside_root"] is True
    assert valid["authority_boundary"] == {
        "orchestration_record_only": True,
        "can_create_study_truth": False,
        "can_override_publication_eval": False,
        "requires_controller_decision_for_release": False,
    }
    escaped = registry.build_work_unit_attempt_record({**payload, "cwd": str(tmp_path / "outside")})
    validation = registry.validate_work_unit_attempt_record(escaped)
    assert escaped["workspace_boundary"]["fail_closed"] and not validation["ok"]
    assert {"code": "workspace_boundary_violation"} in validation["issues"]
    summary = registry.summarize_work_unit_attempts([valid, escaped])
    assert tuple(summary[key] for key in (
        "observability_only", "study_truth_authority", "publication_authority", "boundary_violation_count"
    )) == (True, False, False, 1)

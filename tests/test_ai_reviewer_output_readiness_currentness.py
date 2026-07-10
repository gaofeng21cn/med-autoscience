from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from med_autoscience.controllers.stage_outcome_authority import output_readiness
from med_autoscience.controllers.paper_mission_owner_surface import (
    SUPERVISION_LATEST_RELATIVE_PATH,
)

from tests.stage_outcome_authority_helpers import (
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_current_manuscript_after_publication_eval(study_root: Path) -> Path:
    draft = study_root / "paper" / "draft.md"
    review_manuscript = study_root / "paper" / "build" / "review_manuscript.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("# Current draft\n\nCurrent evidence-backed story.\n", encoding="utf-8")
    review_manuscript.write_text(
        "# Current review manuscript\n\nCurrent evidence-backed story.\n",
        encoding="utf-8",
    )
    latest_eval = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        latest_eval,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::stale-current-manuscript",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
            "reviewer_operating_system": {
                "currentness_checks": {
                    "medical_prose_review": {
                        "status": "current",
                        "request_digest": "sha256:" + "a" * 64,
                        "manuscript_ref": str(draft),
                        "manuscript_digest": "sha256:" + "b" * 64,
                    }
                }
            },
        },
    )
    os.utime(latest_eval, (100.0, 100.0))
    os.utime(draft, (200.0, 200.0))
    os.utime(review_manuscript, (200.0, 200.0))
    return latest_eval


def test_ai_reviewer_output_pending_when_current_manuscript_is_newer_than_latest_eval(tmp_path: Path) -> None:
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_current_manuscript_after_publication_eval(study_root)

    assert output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        current_study={},
    ) is True


def test_materializer_does_not_revive_legacy_scan_action_for_pending_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_current_manuscript_after_publication_eval(study_root)
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route["work_unit_fingerprint"] = "publication-blockers::current-manuscript-pending-eval"
    action = {
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_paper_mission_owner_surface",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                }
            ],
            "action_queue": [action],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json",
        {
            "surface": "owner_callable_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "owner_callable_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_request_missing",
                    "owner_route": route,
                    "prompt_contract": {
                        "do_not_repeat": True,
                        "repeat_suppression_key": route["work_unit_fingerprint"],
                        "owner_route": route,
                    },
                    "repeat_suppression_key": route["work_unit_fingerprint"],
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["repeat_suppressed_count"] == 0
    assert result["domain_progress_transition_requests"] == []
    assert result["written_files"] == []
    assert result["ignored_actions"] == [
        {
            "action_id": None,
            "action_type": "return_to_ai_reviewer_workflow",
            "reason": "legacy_next_action_authority_retired_use_next_action_envelope",
            "study_id": study_id,
        }
    ]
    assert result["authority_boundary"]["durable_carrier_owner"] == "one-person-lab"

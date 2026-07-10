from __future__ import annotations

import os
from pathlib import Path

from med_autoscience.controllers.stage_outcome_authority import output_readiness
from tests.stage_outcome_authority_helpers import write_json as _write_json
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

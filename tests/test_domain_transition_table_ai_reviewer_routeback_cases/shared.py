from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _current_ai_reviewer_route_back_eval(study_root: Path) -> dict:
    return {
        "eval_id": "publication-eval::dm002::current-route-back",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "ai_reviewer_required": False,
        },
        "verdict": {"overall_verdict": "blocked"},
        "quality_assessment": {
            "medical_journal_prose_quality": {
                "status": "blocked",
                "summary": "The manuscript needs same-line story repair.",
            }
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request",
                    "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
                    "manuscript_digest": "sha256:manuscript",
                    "route_back_required": True,
                    "route_target": "write",
                }
            }
        },
        "recommended_actions": [
            {
                "action_id": "ai-reviewer-action::return-to-write",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
                "next_work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Rewrite the manuscript as a clean external-validation paper.",
                },
            }
        ],
    }

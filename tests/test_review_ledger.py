from __future__ import annotations

import importlib


MODULE_NAME = "med_autoscience.quality.study_quality"


def _load_module() -> object:
    return importlib.import_module(MODULE_NAME)


def test_review_ledger_readiness_blocks_on_open_major_concern() -> None:
    module = _load_module()

    readiness = module.build_reviewer_first_readiness(
        review_ledger_payload={
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer-1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "open",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                }
            ],
        },
        review_ledger_path="/tmp/workspace/studies/001-risk/paper/review/review_ledger.json",
        fallback_basis_item={
            "status": "partial",
            "summary": "Fallback reviewer-first summary.",
            "evidence_refs": ["/tmp/fallback.json"],
        },
    )

    assert readiness == {
        "required": True,
        "status": "blocked",
        "ready": False,
        "source": "review_ledger",
        "summary": "review ledger 仍有 1 个未关闭 concern，reviewer-first readiness 不能视为已闭环。",
        "open_concern_count": 1,
        "resolved_concern_count": 0,
        "evidence_refs": ["/tmp/workspace/studies/001-risk/paper/review/review_ledger.json"],
    }


def test_review_ledger_readiness_uses_resolved_ledger_as_ready_signal() -> None:
    module = _load_module()

    readiness = module.build_reviewer_first_readiness(
        review_ledger_payload={
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer-1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "resolved",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                },
                {
                    "concern_id": "RC2",
                    "reviewer_id": "reviewer-2",
                    "summary": "Tighten novelty framing in the Discussion.",
                    "severity": "minor",
                    "status": "resolved",
                    "owner_action": "tighten_discussion_boundary",
                    "revision_links": [
                        {
                            "revision_id": "rev-002",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                },
            ],
        },
        review_ledger_path="/tmp/workspace/studies/001-risk/paper/review/review_ledger.json",
        fallback_basis_item={
            "status": "partial",
            "summary": "Fallback reviewer-first summary.",
            "evidence_refs": ["/tmp/fallback.json"],
        },
    )

    assert readiness == {
        "required": True,
        "status": "ready",
        "ready": True,
        "source": "review_ledger",
        "summary": "review ledger 已把 2 个 concern 全部收口，reviewer-first readiness 已具备常规放行条件。",
        "open_concern_count": 0,
        "resolved_concern_count": 2,
        "evidence_refs": ["/tmp/workspace/studies/001-risk/paper/review/review_ledger.json"],
    }

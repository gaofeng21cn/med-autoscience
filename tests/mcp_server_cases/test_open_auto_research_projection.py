from __future__ import annotations

import importlib
from pathlib import Path


def _write_profile(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'med_deepscientist_repo_root = "/tmp/med-deepscientist"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _delivery_journal_usability_guard() -> dict[str, object]:
    return {
        "real_study_soak_role": "evidence_status_projection_only",
        "delivery_journal_usability": "not_authorized_by_soak",
        "submission_ready_authorized": False,
        "can_authorize_publication_quality": False,
        "next_required_action": {
            "action_id": "return_to_ai_reviewer_workflow",
            "target_surface": "artifacts/publication_eval/latest.json",
            "authority_owner": "ai_reviewer",
        },
        "authority_surfaces": {
            "publication_quality": "artifacts/publication_eval/latest.json",
            "controller_decision": "artifacts/controller_decisions/latest.json",
            "study_truth": "progress_projection",
        },
    }


def test_mcp_compacts_and_renders_open_auto_research_projection() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "current_stage": "publication_supervision",
        "paper_stage": "write",
        "open_auto_research_projection": {
            "surface": "open_auto_research_projection",
            "status": "needs_review",
            "summary": "3 ready, 1 needs review.",
            "counts": {"ready": 3, "blocked": 0, "needs_review": 1, "total": 4},
            "capabilities": {
                "literature_evidence_graph": {"status": "ready", "large": ["omit"]},
            },
            "actions": [
                {
                    "action_id": "run_literature_evidence_graph",
                    "status": "ready",
                    "surface": "literature_intelligence_os",
                    "large": {"omit": True},
                },
                {
                    "action_id": "review_rubric_gaps",
                    "status": "needs_review",
                    "surface": "paperbench_style_hierarchical_rubric_tree",
                },
                {
                    "action_id": "inspect_trajectory",
                    "status": "ready",
                    "surface": "action_observation_trajectory",
                },
                {
                    "action_id": "refine_candidate_path",
                    "status": "ready",
                    "surface": "candidate_path_graph",
                },
            ],
            "delivery_journal_usability_guard": _delivery_journal_usability_guard(),
            "authority": {"read_only": True, "can_authorize_publication_quality": False},
            "refs": {"projection_path": "/tmp/projection.json"},
        },
    }

    compact = module.compact_study_progress_projection(payload)
    markdown = module.render_mcp_study_progress_markdown(payload)

    projection = compact["open_auto_research_projection"]
    assert projection["status"] == "needs_review"
    assert projection["counts"]["needs_review"] == 1
    assert "capabilities" not in projection
    assert "summary" not in projection
    assert "surface" not in projection
    assert projection["actions"][0] == {
        "action_id": "run_literature_evidence_graph",
        "status": "ready",
        "surface": "literature_intelligence_os",
    }
    assert projection["authority"]["read_only"] is True
    assert projection["refs"] == {"projection_path": "/tmp/projection.json"}
    assert projection["delivery_journal_usability_guard"]["delivery_journal_usability"] == (
        "not_authorized_by_soak"
    )
    assert projection["delivery_journal_usability_guard"]["submission_ready_authorized"] is False
    assert projection["delivery_journal_usability_guard"]["next_required_action"] == {
        "action_id": "return_to_ai_reviewer_workflow",
        "target_surface": "artifacts/publication_eval/latest.json",
        "authority_owner": "ai_reviewer",
    }
    assert "Open Auto Research" in markdown
    assert "run_literature_evidence_graph" in markdown
    assert "review_rubric_gaps" in markdown
    assert "inspect_trajectory" in markdown
    assert "refine_candidate_path" in markdown


def test_mcp_server_exposes_open_auto_research_soak_contract() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}

    tool = tools["open_auto_research_soak"]
    properties = tool["inputSchema"]["properties"]

    assert "read-only" in tool["description"]
    assert "allow_controller_writes" in tool["description"]
    assert properties == {
        "profile_path": {"type": "string"},
        "study_id": {"type": "string"},
        "study_root": {"type": "string"},
        "entry_mode": {"type": "string"},
        "allow_controller_writes": {"type": "boolean"},
    }
    assert tool["inputSchema"]["required"] == ["profile_path"]
    assert tool["inputSchema"]["additionalProperties"] is False


def test_mcp_server_can_call_open_auto_research_soak_compact_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path)
    captured: dict[str, object] = {}

    def fake_run_open_auto_research_soak(**kwargs):
        captured.update(kwargs)
        return {
            "surface": "open_auto_research_soak",
            "study_id": "DM002",
            "capability_results": {
                "open_auto_research_projection": {
                    "surface": "open_auto_research_projection",
                    "schema_version": 1,
                    "study_root": "/tmp/dm002",
                    "status": "needs_review",
                    "summary": "3 ready; 1 needs review; 0 blocked.",
                    "counts": {"ready": 3, "needs_review": 1, "blocked": 0, "total": 4},
                    "capabilities": {"large": {"omitted": True}},
                    "actions": [
                        {
                            "action_id": "run_literature_evidence_graph",
                            "status": "ready",
                            "surface": "literature_intelligence_os",
                            "large": "omit",
                        },
                        {
                            "action_id": "review_rubric_gaps",
                            "status": "needs_review",
                            "surface": "paperbench_style_hierarchical_rubric_tree",
                        },
                    ],
                    "delivery_journal_usability_guard": _delivery_journal_usability_guard(),
                    "authority": {
                        "read_only": True,
                        "can_mutate_runtime": False,
                        "can_materialize_artifacts": False,
                        "can_authorize_publication_quality": False,
                    },
                    "refs": {
                        "projection_path": "/tmp/dm002/artifacts/runtime/open_auto_research_projection/latest.json",
                        "runtime_trajectory_proof_path": (
                            "/tmp/dm002/artifacts/runtime/action_observation_trajectory/latest.json"
                        ),
                    },
                },
            },
            "verdict": {"status": "blocked", "mode": "controller_authorized_soak"},
            "remaining_gaps": ["cover_missing_archetypes"],
            "authority_guard_results": {
                "forbidden_surface_unchanged": True,
                "authorized_writes_only": True,
            },
            "input_refs": {
                "publication_eval_path": "/tmp/dm002/artifacts/publication_eval/latest.json",
                "domain_health_diagnostic_report_path": "/tmp/dm002/artifacts/runtime/watch/latest.json",
                "ignored_large_ref": "/tmp/dm002/large.json",
            },
        }

    monkeypatch.setattr(
        module.open_auto_research_soak,
        "run_open_auto_research_soak",
        fake_run_open_auto_research_soak,
    )

    result = module.call_tool(
        "open_auto_research_soak",
        {
            "profile_path": str(profile_path),
            "study_id": "DM002",
            "allow_controller_writes": True,
        },
    )

    assert result["isError"] is False
    assert captured["allow_controller_writes"] is True
    envelope = result["structuredContent"]
    assert envelope["surface_kind"] == "mas_tool_result_envelope"
    assert envelope["tool_id"] == "open_auto_research_soak"
    assert envelope["status"] == "succeeded"
    assert envelope["authority_boundary"]["tool_result_envelope_is_authority_outcome"] is False
    assert envelope["authority_boundary"]["can_authorize_publication_quality"] is False
    assert envelope["structured_payload"] == {
        "status": "needs_review",
        "counts": {"ready": 3, "needs_review": 1, "blocked": 0, "total": 4},
        "actions": [
            {
                "action_id": "run_literature_evidence_graph",
                "status": "ready",
                "surface": "literature_intelligence_os",
            },
            {
                "action_id": "review_rubric_gaps",
                "status": "needs_review",
                "surface": "paperbench_style_hierarchical_rubric_tree",
            },
        ],
        "delivery_journal_usability_guard": {
            "real_study_soak_role": "evidence_status_projection_only",
            "delivery_journal_usability": "not_authorized_by_soak",
            "submission_ready_authorized": False,
            "can_authorize_publication_quality": False,
            "next_required_action": {
                "action_id": "return_to_ai_reviewer_workflow",
                "target_surface": "artifacts/publication_eval/latest.json",
                "authority_owner": "ai_reviewer",
            },
            "authority_surfaces": {
                "publication_quality": "artifacts/publication_eval/latest.json",
                "controller_decision": "artifacts/controller_decisions/latest.json",
                "study_truth": "progress_projection",
            },
        },
        "authority": {
            "read_only": True,
            "can_mutate_runtime": False,
            "can_materialize_artifacts": False,
            "can_authorize_publication_quality": False,
            "allow_controller_writes": True,
            "write_scope": "controller-authorized surfaces only",
        },
        "refs": {
            "projection_path": "/tmp/dm002/artifacts/runtime/open_auto_research_projection/latest.json",
            "runtime_trajectory_proof_path": "/tmp/dm002/artifacts/runtime/action_observation_trajectory/latest.json",
            "publication_eval_path": "/tmp/dm002/artifacts/publication_eval/latest.json",
            "domain_health_diagnostic_report_path": "/tmp/dm002/artifacts/runtime/watch/latest.json",
        },
        "soak_report_summary": {
            "status": "blocked",
            "mode": "controller_authorized_soak",
            "remaining_gaps": ["cover_missing_archetypes"],
            "forbidden_surface_unchanged": True,
            "authorized_writes_only": True,
        },
        "mcp_projection": {
            "surface_kind": "mcp_open_auto_research_soak",
            "source_surface_kind": "open_auto_research_projection",
            "compacted": True,
        },
    }
    assert "Open Auto Research Soak" in result["content"][0]["text"]
    assert "needs_review" in result["content"][0]["text"]
    assert "cover_missing_archetypes" in result["content"][0]["text"]
    assert "not_authorized_by_soak" in result["content"][0]["text"]
    assert "return_to_ai_reviewer_workflow" in result["content"][0]["text"]

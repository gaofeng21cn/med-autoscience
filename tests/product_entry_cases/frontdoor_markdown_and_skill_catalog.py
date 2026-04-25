from __future__ import annotations

from .frontdoor_preflight_and_task_submission import *  # noqa: F403,F401

def test_render_product_frontdesk_markdown_shows_auto_re_review_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前处在等待系统自动复评",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "operator_status_card": {
                        "handling_state": "monitor_only",
                        "user_visible_verdict": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
                        "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
                    },
                    "quality_review_loop": {
                        "current_phase_label": "等待复评",
                        "recommended_next_phase_label": "发起复评",
                        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert "当前处理结论: 当前在等系统自动复评；你现在不用介入，先等待复评回写。" in markdown
    assert "下一确认信号: 看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。" in markdown
    assert "质量评审闭环: 等待复评 -> 发起复评；当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。" in markdown


def test_build_skill_catalog_projects_recommended_shell_and_direct_activation_hints(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_text(
        profile.workspace_root / "contracts" / "runtime-program" / "current-program.json",
        json.dumps(
            {
                "schema_version": 1,
                "program_id": "research-foundry-medical-mainline",
                "title": "Medical Research Mainline",
                "current_phase_id": "phase_2_user_product_loop",
                "phases": [
                    {
                        "phase_id": "phase_2_user_product_loop",
                        "label": "Phase 2",
                        "status": "active",
                        "summary": "继续收口 blocker 并把用户入口壳压实。",
                        "exit_criteria": ["todo"],
                    }
                ],
                "active_tranche_id": "f4_blocker_closeout",
            },
            ensure_ascii=False,
        ),
    )
    write_study(profile.workspace_root, "001-risk")

    payload = module.build_skill_catalog(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "skill_catalog"
    assert payload["recommended_shell"] == "workspace_cockpit"
    assert payload["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["manifest_command"].endswith(
        "product-entry-manifest --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["skills"][0]["domain_projection"]["skill_entry"] == "mas"
    assert payload["skills"][0]["domain_projection"]["recommended_shell"] == "workspace_cockpit"
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]

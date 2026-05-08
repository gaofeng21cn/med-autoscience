from __future__ import annotations

def _assert_phase3_clearance_lane(*, module, payload, profile, profile_ref) -> None:
    assert payload["phase3_clearance_lane"] == {
        "surface_kind": "phase3_host_clearance_lane",
        "summary": "Phase 3 只做可选 hosted runtime / 多宿主 proof；MAS 默认运行和诊断已经由 MAS Runtime OS 承接。",
        "recommended_step_id": "mas_runtime_contract",
        "recommended_command": (
            "uv run python -m med_autoscience.cli doctor --profile "
            + str(profile_ref.resolve())
        ),
        "clearance_targets": [
            {
                "target_id": "external_runtime_contract",
                "title": "Check optional hosted runtime contract",
                "commands": [
                    "uv run python -m med_autoscience.cli doctor --profile " + str(profile_ref.resolve()),
                    "uv run python -m med_autoscience.cli hermes-runtime-check --profile " + str(profile_ref.resolve()),
                ],
            },
            {
                "target_id": "supervisor_service",
                "title": "Keep MAS workspace supervision online",
                "commands": [
                    (
                        "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                        + str(profile_ref.resolve())
                    ),
                    (
                        "uv run python -m med_autoscience.cli watch --runtime-root "
                        + str(profile.runtime_root)
                        + " --profile "
                        + str(profile_ref.resolve())
                        + " --ensure-study-runtimes --apply-supervisor-platform-repair --apply"
                    ),
                ],
            },
            {
                "target_id": "study_recovery_proof",
                "title": "Prove live study recovery and supervision",
                "commands": [
                    (
                        "uv run python -m med_autoscience.cli launch-study --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                    (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                ],
            },
        ],
        "clearance_loop": [
            {
                "step_id": "external_runtime_contract",
                "title": "确认 optional hosted runtime contract 或 MAS runtime contract ready",
                "surface_kind": "doctor_runtime_contract",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "hermes_runtime_check",
                "title": "显式检查 optional Hermes runtime 绑定证据",
                "surface_kind": "hermes_runtime_check",
                "command": (
                    "uv run python -m med_autoscience.cli hermes-runtime-check --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "supervisor_service",
                "title": "确认 workspace 定时监管在线",
                "surface_kind": "workspace_supervisor_service",
                "command": (
                    "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "refresh_supervision",
                "title": "刷新 MAS runtime supervision tick",
                "surface_kind": "runtime_watch_refresh",
                "command": (
                    "uv run python -m med_autoscience.cli watch --runtime-root "
                    + str(profile.runtime_root)
                    + " --profile "
                    + str(profile_ref.resolve())
                    + " --ensure-study-runtimes --apply-supervisor-platform-repair --apply"
                ),
            },
            {
                "step_id": "study_recovery_proof",
                "title": "证明 live study recovery / progress supervision 成立",
                "surface_kind": "launch_study",
                "command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "step_id": "inspect_study_progress",
                "title": "读取 study-progress proof",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "doctor.external_runtime_contract",
                "command": "uv run python -m med_autoscience.cli doctor --profile " + str(profile_ref.resolve()),
            },
            {
                "surface_kind": "study_runtime_status.autonomous_runtime_notice",
                "command": (
                    "uv run python -m med_autoscience.cli study-runtime-status --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "surface_kind": "runtime_watch",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_watch" / "latest.json"),
            },
            {
                "surface_kind": "runtime_supervision",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_supervision" / "latest.json"),
            },
            {
                "surface_kind": "controller_decisions",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            },
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    }
    assert payload["phase4_backend_deconstruction"] == {
        "surface_kind": "phase4_backend_deconstruction_lane",
        "summary": "Phase 4 只保留 future upstream source intake / historical fixture governance；MDS 不再是 runtime substrate。",
        "substrate_targets": [
            {
                "capability_id": "session_run_watch_recovery",
                "owner": "MAS Runtime OS",
                "summary": "session / run / watch / recovery / scheduling / interruption 默认由 MAS Runtime OS 承接。",
            },
            {
                "capability_id": "backend_generic_runtime_contract",
                "owner": "MedAutoScience controller boundary",
                "summary": "controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            },
        ],
        "backend_retained_now": [
            "frozen MedDeepScientist source archive",
            "historical oracle fixtures",
            "explicit archive import / backend-audit reference",
        ],
        "current_backend_chain": [
            "med_autoscience runtime surfaces -> MAS-owned Runtime OS / Artifact OS / Quality OS",
            "historical med_deepscientist fixture/provenance refs only",
        ],
        "optional_executor_proofs": [
            {
                "executor_kind": "hermes_agent",
                "entrypoint": "optional hosted runtime adapter",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        "promotion_rules": [
            "no claim of platform runtime ingest without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "do not restore external MDS as a default runtime dependency",
        ],
        "deconstruction_map_ref": "program:med_deepscientist_deconstruction_map",
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    }
    phase5 = payload["phase5_platform_target"]
    assert phase5["surface_kind"] == "phase5_platform_target"
    assert phase5["summary"] == (
        "Phase 5 已完成 MAS functional monolith closeout；后续平台工作只剩 optional hosted/federated "
        "frontend 与 future upstream intake，不再以 external MDS runtime core 为默认运行条件。"
    )
    assert phase5["sequence_scope"] == "monorepo_landing_readiness"
    assert phase5["current_readiness_summary"] == (
        "MAS 默认运行、进度、诊断、artifact/quality parity、workspace helpers 与 OPL handoff 都已切到 MAS-owned surfaces；"
        "external MDS 只保留 frozen archive / historical fixture / explicit archive import reference。"
    )
    assert phase5["north_star_topology"] == {
        "domain_gateway": "Med Auto Science",
        "runtime_owner": "mas_runtime_os",
        "runtime_substrate": "mas_runtime_core",
        "controlled_research_backend": "MAS-owned Runtime OS / Artifact OS / Quality OS",
        "monorepo_status": "functional_monolith_completion_landed",
    }
    assert phase5["target_internal_modules"] == [
        "controller_charter",
        "runtime",
        "eval_hygiene",
    ]
    assert [item["step_id"] for item in phase5["landing_sequence"]] == [
        "freeze_gateway_runtime_truth",
        "stabilize_user_product_loop",
        "clear_multi_workspace_host_gate",
        "freeze_backend_deconstruction_boundary",
        "mds_no_history_absorb",
        "runtime_core_ingest",
        "functional_monolith_completion",
        "optional_hosted_frontend_packaging",
        "future_upstream_source_intake_review",
    ]
    assert phase5["landing_sequence"][4]["status"] == "completed"
    assert phase5["landing_sequence"][5]["status"] == "completed"
    assert phase5["landing_sequence"][6]["status"] == "completed"
    assert phase5["completed_step_ids"] == [
        "freeze_gateway_runtime_truth",
        "mds_no_history_absorb",
        "runtime_core_ingest",
        "functional_monolith_completion",
    ]
    assert phase5["remaining_step_ids"] == [
        "optional_hosted_frontend_packaging",
        "future_upstream_source_intake_review",
    ]
    assert phase5["promotion_gates"] == [
        "phase_1_mainline_established",
        "phase_2_user_product_loop",
        "phase_3_multi_workspace_host_clearance",
        "phase_4_backend_deconstruction",
    ]
    assert phase5["land_now"] == [
        "repo-tracked product-entry shell and family orchestration companions",
        "controller-owned runtime/progress/recovery truth",
        "CLI/MCP/controller entry surfaces that already support real work",
        "MAS-owned Progress Portal and OPL handoff refs",
    ]
    assert phase5["not_yet"] == [
        "mature hosted standalone medical frontend",
        "future upstream source intake beyond historical fixture/provenance refs",
    ]
    assert phase5["recommended_phase_command"] == (
        "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_federation_platform_maturation"
    )
    assert payload["product_entry_shell"]["workspace_cockpit"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["product_entry_shell"]["product_entry_status"]["command"].endswith(
        "product-entry-status --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_shell"]["submit_study_task"]["command"].endswith(
        "submit-study-task --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --task-intent '<task_intent>'"
    )
    assert payload["product_entry_shell"]["launch_study"]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["product_entry_shell"]["study_progress"]["command"].endswith(
        "study-progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --format json"
    )
    assert payload["shared_handoff"]["direct_entry_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode direct"
    )
    assert payload["shared_handoff"]["opl_handoff_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode opl-handoff"
    )
    assert payload["family_orchestration"]["human_gates"] == [
        {"gate_id": "study_user_decision_gate", "title": "Study user decision gate"},
        {"gate_id": "publication_release_gate", "title": "Publication release gate"},
    ]
    assert payload["family_orchestration"]["action_graph_ref"] == {
        "ref_kind": "json_pointer",
        "ref": "/family_orchestration/action_graph",
        "label": "mas family action graph",
    }
    assert payload["family_orchestration"]["action_graph"]["graph_id"] == (
        "mas_workspace_product_entry_study_runtime_graph"
    )
    assert payload["family_orchestration"]["action_graph"]["target_domain_id"] == "med-autoscience"

def _assert_phase4_backend_deconstruction_lane(*, module, payload, profile, profile_ref) -> None:
    assert [node["node_id"] for node in payload["family_orchestration"]["action_graph"]["nodes"]] == [
        "step:open_product_entry",
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert payload["family_orchestration"]["action_graph"]["edges"] == [
        {
            "from": "step:open_product_entry",
            "to": "step:submit_task",
            "on": "new_task",
        },
        {
            "from": "step:open_product_entry",
            "to": "step:continue_study",
            "on": "resume_study",
        },
        {
            "from": "step:open_product_entry",
            "to": "step:inspect_progress",
            "on": "inspect_status",
        },
        {
            "from": "step:submit_task",
            "to": "step:continue_study",
            "on": "task_written",
        },
        {
            "from": "step:continue_study",
            "to": "step:inspect_progress",
            "on": "progress_refresh",
        },
    ]
    assert payload["family_orchestration"]["action_graph"]["entry_nodes"] == [
        "step:open_product_entry",
    ]
    assert payload["family_orchestration"]["action_graph"]["exit_nodes"] == [
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert payload["family_orchestration"]["action_graph"]["human_gates"] == [
        {
            "gate_id": "study_user_decision_gate",
            "legacy_gate_id": "study_physician_decision_gate",
            "trigger_nodes": ["step:continue_study"],
            "blocking": True,
        },
        {
            "gate_id": "publication_release_gate",
            "trigger_nodes": ["step:inspect_progress"],
            "blocking": True,
        },
    ]
    assert payload["family_orchestration"]["action_graph"]["checkpoint_policy"] == {
        "mode": "explicit_nodes",
        "checkpoint_nodes": [
            "step:submit_task",
            "step:continue_study",
            "step:inspect_progress",
        ],
    }
    assert payload["family_orchestration"]["resume_contract"] == {
        "surface_kind": "launch_study",
        "session_locator_field": "study_id",
        "checkpoint_locator_field": "controller_decision_path",
    }
    assert payload["family_orchestration"]["event_envelope_surface"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
        "label": "runtime watch event companion",
    }
    assert payload["family_orchestration"]["checkpoint_lineage_surface"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        "label": "controller checkpoint lineage companion",
    }
    assert payload["product_entry_quickstart"]["resume_contract"] == payload["family_orchestration"]["resume_contract"]
    assert payload["product_entry_quickstart"]["human_gate_ids"] == [
        "study_user_decision_gate",
        "publication_release_gate",
    ]
    assert payload["product_entry_start"]["surface_kind"] == "product_entry_start"
    assert payload["product_entry_start"]["recommended_mode_id"] == "open_product_entry"
    assert [mode["mode_id"] for mode in payload["product_entry_start"]["modes"]] == [
        "open_product_entry",
        "submit_task",
        "continue_study",
    ]

def _assert_phase5_platform_target(*, module, payload, profile, profile_ref) -> None:
    assert payload["product_entry_start"]["modes"][0]["command"].endswith(
        "product-entry-status --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_start"]["modes"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_start"]["modes"][2]["surface_kind"] == "launch_study"
    assert payload["product_entry_start"]["resume_surface"] == payload["family_orchestration"]["resume_contract"]
    assert payload["product_entry_start"]["human_gate_ids"] == [
        "study_user_decision_gate",
        "publication_release_gate",
    ]
    assert "standalone medical product entry" in payload["remaining_gaps"][0]
    start_markdown = module.render_product_entry_start_markdown(payload["product_entry_start"])
    assert "当前摘要" in start_markdown
    assert "建议入口" in start_markdown
    assert "恢复入口" in start_markdown
    assert "可用入口" in start_markdown
    assert "recommended_mode_id:" not in start_markdown
    assert "resume_surface:" not in start_markdown

def assert_manifest_phase_and_readiness_surfaces(*, module, payload, profile, profile_ref) -> None:
    _assert_phase3_clearance_lane(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_phase4_backend_deconstruction_lane(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_phase5_platform_target(module=module, payload=payload, profile=profile, profile_ref=profile_ref)

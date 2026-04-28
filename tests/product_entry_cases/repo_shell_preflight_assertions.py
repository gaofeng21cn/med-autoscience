from __future__ import annotations


def assert_manifest_preflight_and_guardrail_surfaces(*, module, payload, profile, profile_ref) -> None:
        assert payload["product_entry_preflight"] == {
            "surface_kind": "product_entry_preflight",
            "summary": "当前 product-entry 前置检查已通过，可以先复核 doctor 输出，再进入 research frontdesk。",
            "ready_to_try_now": True,
            "recommended_check_command": (
                "uv run python -m med_autoscience.cli doctor --profile "
                + str(profile_ref.resolve())
            ),
            "recommended_start_command": (
                "uv run python -m med_autoscience.cli product-frontdesk --profile "
                + str(profile_ref.resolve())
            ),
            "blocking_check_ids": [],
            "checks": [
                {
                    "check_id": "workspace_root_exists",
                    "title": "Workspace Root Exists",
                    "status": "pass",
                    "blocking": True,
                    "summary": "workspace 根目录已就位。",
                    "command": (
                        "uv run python -m med_autoscience.cli doctor --profile "
                        + str(profile_ref.resolve())
                    ),
                },
                {
                    "check_id": "runtime_root_exists",
                    "title": "Runtime Root Exists",
                    "status": "pass",
                    "blocking": True,
                    "summary": "runtime root 已就位。",
                    "command": (
                        "uv run python -m med_autoscience.cli doctor --profile "
                        + str(profile_ref.resolve())
                    ),
                },
                {
                    "check_id": "studies_root_exists",
                    "title": "Studies Root Exists",
                    "status": "pass",
                    "blocking": True,
                    "summary": "studies 根目录已就位。",
                    "command": (
                        "uv run python -m med_autoscience.cli doctor --profile "
                        + str(profile_ref.resolve())
                    ),
                },
                {
                    "check_id": "portfolio_root_exists",
                    "title": "Portfolio Root Exists",
                    "status": "pass",
                    "blocking": True,
                    "summary": "portfolio 根目录已就位。",
                    "command": (
                        "uv run python -m med_autoscience.cli doctor --profile "
                        + str(profile_ref.resolve())
                    ),
                },
                {
                    "check_id": "research_backend_runtime_ready",
                    "title": "Research Backend Runtime Ready",
                    "status": "pass",
                    "blocking": True,
                    "summary": "受控 research backend runtime 已就位。",
                    "command": (
                        "uv run python -m med_autoscience.cli doctor --profile "
                        + str(profile_ref.resolve())
                    ),
                },
                {
                    "check_id": "medical_overlay_ready",
                    "title": "Medical Overlay Ready",
                    "status": "pass",
                    "blocking": True,
                    "summary": "medical overlay 已 ready。",
                    "command": (
                        "uv run python -m med_autoscience.cli doctor --profile "
                        + str(profile_ref.resolve())
                    ),
                },
                {
                    "check_id": "external_runtime_contract_ready",
                    "title": "External Runtime Contract Ready",
                    "status": "pass",
                    "blocking": True,
                    "summary": "external Hermes runtime contract 已 ready。",
                    "command": (
                        "uv run python -m med_autoscience.cli doctor --profile "
                        + str(profile_ref.resolve())
                    ),
                },
                {
                    "check_id": "workspace_supervision_contract_ready",
                    "title": "Workspace Supervision Contract Ready",
                    "status": "pass",
                    "blocking": True,
                    "summary": "workspace supervision owner 已收敛到 canonical Hermes supervision。",
                    "command": (
                        "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                        + str(profile_ref.resolve())
                    ),
                },
            ],
        }

        assert payload["product_entry_guardrails"] == {
            "surface_kind": "product_entry_guardrails",
            "summary": (
                "把卡住、没进度、监管掉线、需要人工决策和质量阻塞显式投影成可执行恢复回路，"
                "避免研究主线失去监管。"
            ),
            "guardrail_classes": [
                {
                    "guardrail_id": "workspace_supervision_gap",
                    "trigger": "workspace-cockpit attention queue / study-progress supervisor freshness",
                        "symptom": "Hermes-hosted supervision 未在线、supervisor tick stale/missing、托管恢复真相不再新鲜。",
                    "recommended_command": (
                        "uv run python -m med_autoscience.cli watch --runtime-root "
                        + str(profile.runtime_root)
                        + " --profile "
                        + str(profile_ref.resolve())
                        + " --ensure-study-runtimes --apply"
                    ),
                },
                {
                    "guardrail_id": "study_progress_gap",
                    "trigger": "study-progress progress_freshness / workspace-cockpit attention queue",
                    "symptom": "当前 study 进度 stale 或 missing，疑似卡住、空转或没有新的明确推进证据。",
                    "recommended_command": (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                },
                {
                    "guardrail_id": "user_decision_gate",
                    "trigger": "study-progress needs_user_decision / controller decision gate",
                    "symptom": "当前已前移到用户或 publication release 的人工判断节点。",
                    "recommended_command": (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                },
                {
                    "guardrail_id": "runtime_recovery_required",
                    "trigger": "study-progress intervention_lane / runtime_supervision health_status / workspace-cockpit attention queue",
                    "symptom": "托管运行恢复失败、健康降级或长期停在恢复态，当前必须优先处理 runtime recovery。",
                    "recommended_command": (
                        "uv run python -m med_autoscience.cli launch-study --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                },
                {
                    "guardrail_id": "quality_floor_blocker",
                    "trigger": "study-progress intervention_lane / runtime watch figure-loop alerts / publication gate",
                    "symptom": "研究输出质量、figure/reference floor 或 publication gate 出现硬阻塞，不能继续盲目长跑。",
                    "recommended_command": (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                },
            ],
            "recovery_loop": [
                {
                    "step_id": "inspect_workspace_inbox",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile " + str(profile_ref.resolve()),
                    "surface_kind": "workspace_cockpit",
                },
                {
                    "step_id": "refresh_supervision",
                    "command": (
                        "uv run python -m med_autoscience.cli watch --runtime-root "
                        + str(profile.runtime_root)
                        + " --profile "
                        + str(profile_ref.resolve())
                        + " --ensure-study-runtimes --apply"
                    ),
                    "surface_kind": "runtime_watch_refresh",
                },
                {
                    "step_id": "inspect_study_progress",
                    "command": (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                    "surface_kind": "study_progress",
                },
                {
                    "step_id": "continue_or_relaunch",
                    "command": (
                        "uv run python -m med_autoscience.cli launch-study --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                    "surface_kind": "launch_study",
                },
            ],
        }

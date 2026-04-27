# DeepScientist Learning Intake 2026-04-28

这份记录对应维护者触发的“学习一下 DeepScientist 的最新更新”。本轮按 [DeepScientist Latest-Update Learning Protocol](./deepscientist_latest_update_learning_protocol.md) 执行：fresh upstream audit、decision matrix、MDS/MAS owner surface 分类、落地、验证、吸收回 main。

## Fresh Upstream Range

- upstream_range: `bfc8675..d22165e`
- upstream_head: `d22165e` `docs: explain workspace explorer file visibility`
- MDS comparison before landing: `main@0e09065` vs `upstream/main@d22165e`
- MDS local code landing: `df714e6b3831e044f9f56100412089d1c74a1f7f`

## Decision Matrix

| Upstream lesson | Owner surface | Decision | Landing / verification target |
| --- | --- | --- | --- |
| path-aware workspace search | `runtime` + `workspace_projection` | `adopt_code_slice` | MDS `QuestService.search_files(...)` now finds path matches and normalizes simple wrapping globs. MAS consumes this as better operator-visible workspace projection, without changing study authority. |
| start setup planning session | `controller_charter` + `workspace_projection` | `adopt_code_slice` | MDS `artifact.prepare_start_setup_form(...)` persists both `form_patch` and `session_patch` into startup context. MAS treats this as a setup-intake durability lesson, not as a new MAS study-quality owner. |
| manuscript coverage gate | `eval_hygiene` | `adopt_code_slice` + `adopt_contract` | MDS added `artifact.validate_manuscript_coverage(...)`; MAS maps the lesson to publication/submission hygiene: `submission_ready` must be a checked state, not an agent narration claim. |
| duplicate ready evidence selection | `eval_hygiene` | `adopt_code_slice` | MDS paper contract health now prefers ready main-text duplicate ledger rows over stale pending rows. MAS consumes the lesson as evidence-ledger consistency discipline. |
| bounded await discipline | `runtime` | `adopt_template` | MDS system/skills now prefer `bash_exec(mode='await', id=..., wait_timeout_seconds=1800)` followed by log inspection. MAS maps this to runtime supervision discipline: timeout windows are checkpoints, not automatic failure proof. |
| provider / UI product surface | none | `reject` / `watch_only` | 本轮不把 Claude / Kimi runner 扩面升级成 MAS 主线；本轮不追随 upstream UI / Settings / Lab canvas 大包。 |

## MAS Learned Contract

本轮 MAS 真正学习到的是三条 owner-level 规则：

1. `runtime`: 长时间运行中的等待必须是 bounded await + read-and-judge；不能把等待窗口结束误写成失败，也不能用重复 sleep 堆出假监督。
2. `workspace_projection`: workspace 搜索和 setup planning 都要服务用户可见接管点；路径、表单草案、fit assessment、missing confirmations 这些内容应成为 durable projection。
3. `eval_hygiene`: full manuscript、review package、submission package 要分层；`artifact.validate_manuscript_coverage` 和 `submission_ready` 这类 callable truth 比“看起来像完成”更可信。

这些 lesson 继续落在 MAS 的 `controller_charter`、`runtime`、`eval_hygiene` 与 `workspace_projection` 四个 owner 面。MDS 本轮只作为 controlled backend / behavior oracle / upstream intake buffer 承接代码 slice。

## Watch / Reject Rationale

本轮明确不吸收以下上游面作为 MAS 主线：

- Provider runner 扩面：Claude / Kimi / MCP timeout default 变化仍属于 upstream product/runtime-provider breadth，不改变 MAS 当前 Codex-profile-based controlled backend contract。
- UI shell / Settings / Lab canvas：这些增强有产品体验价值，但不应升级成 MAS behavior、contract 或 packet。
- 大规模 stage skill restructuring：只吸收其中与当前 runtime/eval gate 直接相关的 bounded await 和 manuscript coverage discipline；其余 stage packet 变化继续观察，后续按 owner 面拆成小 slice。
- Install / DeepXiv hardening：当前不改变 MAS study owner、runtime governance 或 publication gate。

## Verification

MDS focused verification:

```bash
uv run pytest -q tests/test_init_and_quest.py::test_search_files_matches_paths_and_normalizes_simple_globs tests/test_mcp_servers.py::test_start_setup_profile_artifact_server_exposes_prepare_form_only tests/test_mcp_servers.py::test_artifact_mcp_server_tools_cover_core_flows tests/test_memory_and_artifact.py::test_validate_manuscript_coverage_blocks_short_memo_as_full_paper tests/test_memory_and_artifact.py::test_get_paper_contract_health_prefers_ready_duplicate_ledger_item tests/test_prompt_builder.py::test_prompt_builder_includes_paper_contract_health_block tests/test_skill_contracts.py::test_system_prompt_strengthens_bash_exec_only_terminal_contract tests/test_skill_contracts.py::test_experiment_and_analysis_skills_require_smoke_then_detach_tail_monitoring
```

Result: `8 passed in 17.05s`.

MAS meta verification for this record:

```bash
uv run pytest -q tests/test_deepscientist_learning_policy.py::test_2026_04_28_intake_records_latest_update_landing_decisions
```

## Completion Meaning

This intake round is considered learned only after both repos carry their own records:

- `MDS`: code slice, focused tests, `docs/upstream_intake_round_2026_04_28.md`, fork manifest, medical fork baseline.
- `MAS`: this owner-surface intake record plus meta-test coverage.

The mainline lesson is not “follow upstream faster”. The mainline lesson is to keep turning upstream research-workspace improvements into MAS-owned runtime, projection, and evaluation contracts with small, verified landing slices.

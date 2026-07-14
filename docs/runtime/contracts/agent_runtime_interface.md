# Agent Runtime Interface

Owner: `MedAutoScience`
Purpose: `agent_runtime_entry_and_boundary`
State: `active_support`
Machine boundary: 可执行真相归 V2 action catalog、Stage manifest、closed handler registry、OPL generated interfaces与 OPL StageRun/Attempt ledger；医学真相归 MAS owner results与 canonical artifacts。

## Current topology

| Layer | Owner | Responsibility |
| --- | --- | --- |
| Declarative medical pack | MAS | six Stage semantics、prompts、knowledge、quality policy、schemas与 environment requirements |
| Generic execution | OPL Runway / Temporal | StageRun、Attempt、session、retry、resume、queue、human-gate transport与 transition materialization |
| Provider/package/workspace | OPL Connect / Pack / Workspace | provider receipts、package closure、Skill materialization、locator、StateIndex与 lifecycle shell |
| Medical authority | MAS | study/source semantics、quality/publication/artifact/memory decisions、owner receipt、typed blocker、human gate与 route-back |

`Codex CLI` 是第一公民 executor。其他 executor 只能通过显式 OPL adapter接入，不承诺行为或质量等价。

## Stable entries

用户可见 action 只有：

- `direction_and_route_selection`
- `baseline_and_evidence_setup`
- `bounded_analysis_campaign`
- `manuscript_authoring`
- `review_and_quality_gate`
- `finalize_and_publication_handoff`

具体 CLI/MCP/Skill/product UI 由 OPL 从 catalog/schema/manifest 生成。`paper_mission_authority_evaluate` 是 closed registry 内部 action，没有用户 surface。MAS 不维护 parser、JSON-RPC transport、workspace wrapper、status shell或 workbench renderer。

## Attempt and route contract

每个 StageRun 由 OPL 持有 durable invocation/spec identity。Primary-only Stage 的 producer或 formal Review 的终局 reviewer/re-reviewer是 decisive Attempt；其余角色只能给 recommendation。Attempt 只返回 artifact/source/rubric/lineage refs、quality outcome与 route impact。OPL controller只校验并物化 declared transition，不拥有医学 route approval。

Review 必须是独立 Attempt/session，并绑定 exact artifact hashes与 no-context-inheritance evidence。Attempt 不生成 review receipt verdict；controller负责 receipt materialization。

## Authority handler

`contracts/domain_handler_registry.json` 只绑定 `evaluate_paper_mission_authority`。该函数校验 host 注入的 exact refs并返回医学 owner result；它不访问文件或网络、不 spawn进程、不维护 session/lifecycle/storage、不提交 provider request，也不物化 Stage transition。

## Readback

OPL status/workbench可以展示 StageRun、Attempt、package/provider receipts、artifact refs、owner results、typed blockers与 human gates。Projection不得写 MAS truth、artifact/memory body、publication verdict或 current package，也不得把 queue/provider completion解释成 paper progress。

## Package and workspace

安装、更新、修复与 scope materialization使用 `opl packages install|update|status|repair`。Workspace/quest locator与 lifecycle归 OPL；MAS只消费显式 profile/study/source/artifact refs。不存在 repo-local bootstrap、environment builder、runtime service或 install fallback。

## Verification

运行 `scripts/verify.sh fast`、`scripts/verify.sh meta`，并在冻结 OPL Framework读取 pack-compiler、interfaces、conformance、default-callers、residue-decisions与 source-closure。Live claim仍需 fresh StageRun、Review receipt、MAS owner result与 artifact evidence。

# Program 历史归档

Owner: `MedAutoScience`
Purpose: `program_history_index`
State: `history_index`
Machine boundary: 人读 program/process 历史索引。当前执行顺序、gap、runtime truth 和 owner boundary 继续归 active owner docs、核心五件套、contracts、source、runtime/controller surfaces 和 owner receipts。

本目录不是单纯的“已退役”桶。它保存已退役 program 记录、已落地 closeout、周期性支持线的 dated intake 快照、activation package 和已被新主线覆盖的旧计划。

当前 program 治理入口是：

- [Program Portfolio Consolidation](../../active/program_portfolio_consolidation.md)
- [MAS Current Development Lines](../../active/current-development-lines.md)
- [AI-first Paper Autonomy Closure Program](../../active/ai_first_paper_autonomy_closure_program.md)
- [OPL App MAS Runtime Workbench Program](../../active/opl_app_mas_runtime_workbench_program.md)
- [MAS/MDS Owner Boundary Contract](../../policies/runtime-governance/mas_mds_owner_boundary_contract.md)
- [Domain Authority Refs Index Guard](../../runtime/domain_authority_refs_index_guard.md)

## 主题级索引

本索引只保留主题级 provenance，避免恢复逐日 closeout / activation package / intake 快照长清单。完整历史文件仍保留在本目录；需要精确追溯时用文件名、git history 或 `git ls-files 'docs/history/program/*.md'` 读取。

| Theme | Compressed read | Current owner |
| --- | --- | --- |
| Docs lifecycle and portfolio governance | Docs lifecycle audits, closeouts, MAS broader portfolio SSOT closeout, Display Pack wording foldback, and old part-ledger foldback only preserve how docs were routed into current owners. | `docs/docs_portfolio_consolidation.md`, `docs/history/docs-portfolio-coverage-ledger/README.md`, active plan, core docs |
| Paper readiness, owner-route currentness and progress projection | DM002/DM003 pause/readiness, progress projection alias/command retirement, current executable owner action split, stop-loss/request-packet follow-through, gate-clearing facade retirement, and relaunch verification are historical proof of platform/currentness repair. | `docs/active/mas-ideal-state-gap-plan.md`, runtime/controller source, owner-route/read-model surfaces, workspace receipts |
| Runtime lifecycle, OPL App/workbench and Temporal retirement | OPL App MAS runtime workbench, Temporal retirement, runtime lifecycle SQLite migration, supervisor dispatch helper retirement, Hermes / integration activation packages, and runtime closeout ledgers are provenance for the current MAS/OPL owner split. | core docs, `docs/runtime/**`, `docs/product/**`, runtime/controller surfaces, OPL read-model refs |
| AI-first paper autonomy and closeout governance | AI-first autonomy full records, operationalization, usable closeout projection, closeout handoff, progress-first throughput and plan completion records are historical closeout/handoff material, not active quality or submission gates. | active plan, AI-first paper autonomy owner doc, independent reviewer/auditor records, owner receipts / typed blockers |
| MDS / DeepScientist / external learning intake | DeepScientist, PaperOrchestra, open auto research, Research Harness and external orchestration snapshots remain upstream-learning provenance only. | `docs/references/**`, MAS/OPL owner split in core docs, source/runtime contracts |
| MAS/MDS absorb and retired old programs | MAS/MDS absorb full records, landed guard, old MAS/MDS autonomy/unified enhancement plans, Hermes continuation, Open Harness freeze, Research Foundry maps, Journal upgrade plans and upstream Hermes cutover boards are historical or tombstone context. | active plan, core docs, policies/runtime-governance, `docs/history/**` provenance |

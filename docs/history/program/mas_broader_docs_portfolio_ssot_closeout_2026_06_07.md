# MAS broader docs portfolio SSOT closeout 2026-06-07

Owner: `MedAutoScience`
Purpose: `broader_docs_portfolio_ssot_closeout`
State: `history_provenance`
Machine boundary: 本文是人读文档组合治理 closeout。当前 MAS truth、runtime truth、owner receipts、typed blockers、artifact authority、quality verdict、source truth 和 production readiness 继续归 `contracts/`、source、tests、runtime/controller surfaces、study workspace artifacts、owner receipts 和 typed blockers。

## Scope

本轮按 OPL Doc 的 SSOT-first 方式复核 MAS broader docs portfolio：先确定语义主题的 Single Source of Truth，再按内容层面对 README 与 `docs/**/*.md` 做 current owner、support、history/provenance、retired/tombstone 和 stale-risk 分类。

覆盖清单：

- 根入口：`README.md`、`README.zh-CN.md`。
- `docs/**/*.md`：274 个，其中非 history 132 个、history 142 个。
- 当前核心：`docs/README.md`、`docs/project.md`、`docs/status.md`、`docs/architecture.md`、`docs/invariants.md`、`docs/decisions.md`、`docs/docs_portfolio_consolidation.md`。
- Active owner 层：`docs/active/mas-ideal-state-gap-plan.md`、`docs/active/current-development-lines.md`、`docs/active/program_portfolio_consolidation.md`、paper autonomy、OPL App workbench、stage standardization、MDS absorb、Stage Native 和 related active guard docs。
- Support/history 层：`docs/public/`、`docs/product/`、`docs/runtime/`、`docs/delivery/`、`docs/source/`、`docs/policies/`、`docs/specs/`、`docs/references/`、`docs/history/`。

本轮没有修改 source、contracts、tests、runtime state、study workspace、owner receipt、typed blocker、publication eval、controller decision、paper/package artifact 或 OPL provider state。

## SSOT Owners

| Theme | Single Source of Truth | Peer docs disposition |
| --- | --- | --- |
| Docs lifecycle and taxonomy | `docs/docs_portfolio_consolidation.md` | `docs/README.md` 和 history closeouts 只作入口、导航和 provenance。 |
| Current active gap / completion plan | `docs/active/mas-ideal-state-gap-plan.md` | `docs/status.md` 只作 current summary；`current-development-lines.md` 只作 execution map；program docs 不维护第二 gap matrix。 |
| Active execution map | `docs/active/current-development-lines.md` | Program docs 只声明各自 owner role 和 gate，不冻结 proof ledger 或第二 backlog。 |
| Program document lifecycle | `docs/active/program_portfolio_consolidation.md` | `docs/history/program/**` 保存 full record、activation package、closeout、旧 board 和 dated process。 |
| Paper autonomy acceptance | `docs/active/ai_first_paper_autonomy_closure_program.md` | 本文只定义 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker 的验收口径；不持有总 plan。 |
| North-star target state | `docs/references/positioning/mas_ideal_state.md` | Active plan 从它反推差距；它不记录 live proof、receipt 流水或当前 backlog。 |
| Machine truth | `agent/`、`contracts/`、source、tests、CLI/MCP/API、runtime/controller durable surfaces、真实 workspace evidence、owner receipts、typed blockers | Prose docs 解释、导航、治理和 provenance，不制造第二真相源。 |

## Classification

| Content class | Current disposition |
| --- | --- |
| Current MAS identity, authority split, default runtime, OPL/MAS owner boundary | Covered by core five、`docs/status.md`、`docs/architecture.md`、`docs/invariants.md` and the active gap plan. |
| Active gaps, current completion, evidence tail, next-round agent prompt | Covered by `docs/active/mas-ideal-state-gap-plan.md`; peer docs must point back rather than duplicate. |
| Program lifecycle and role map | Covered by `docs/active/program_portfolio_consolidation.md`; dated full records and branch/proof logs stay in `docs/history/program/`. |
| Paper autonomy acceptance | More-specific detail retained in `docs/active/ai_first_paper_autonomy_closure_program.md` as an acceptance owner. Its `State` was narrowed from `active_plan` to `active_target_and_acceptance_owner` so it no longer competes with the single active truth plan. |
| Runtime, delivery, source, policy, spec and reference support docs | Retained as support owners where they have one durable role and machine boundary; they do not override contracts/source/tests/runtime truth. |
| Historical increment lists, dated attempts, branch/SHA notes, old phase tables, receipt/worklist ledgers | History/provenance only; active docs keep current conclusions, open gates and next owner prompt. |
| Stale modules/interfaces/tests/workflows/entries such as old MAS-local scheduler, `runtime_transport`, `mas_runtime_core`, Hermes/MDS/DeepScientist default backend, `progress-projection` aliases, wrappers/facades/fallbacks and compatibility surfaces | Already bounded as negative guards, support references, tombstones or history/provenance in the current docs and contracts reviewed in this tranche. If future no-active-caller evidence closes a remaining candidate, the target state is direct retirement without compatibility alias, wrapper, facade or aggregate compatibility test. |

## Change

- `docs/active/ai_first_paper_autonomy_closure_program.md` now uses `State: active_target_and_acceptance_owner`, matching its already-declared status and `program_portfolio_consolidation.md` role.
- `docs/history/program/README.md` now indexes this closeout.

No other current docs needed content rewrite in this tranche. The broader portfolio already has a clear SSOT split: lifecycle owner, active truth owner, execution map, program lifecycle map, north-star reference, machine truth and history/provenance each have distinct roles.

## Verification

Docs-only verification for this closeout:

```bash
rtk git diff --check
rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" README*.md docs
rtk rg -n "State: .active_plan." docs/active/*.md
rtk opl-doc-doctor doctor /Users/gaofeng/workspace/med-autoscience-mas-broader-docs-portfolio --format json
```

Expected active-plan scan after this tranche:

- `docs/active/mas-ideal-state-gap-plan.md` remains the only `State: active_plan` document in `docs/active/*.md`.
- `docs/active/current-development-lines.md` remains `active_plan_index`, not a gap plan.
- `docs/active/ai_first_paper_autonomy_closure_program.md` remains an acceptance owner, not a competing active plan.

## Remaining Risk

- This closeout records a broader semantic tranche, not physical deletion of every stale candidate. Stale-surface retirement still requires no-active-caller, replacement owner and tombstone/provenance evidence per `docs/docs_portfolio_consolidation.md` and `docs/active/program_portfolio_consolidation.md`.
- History/provenance docs intentionally retain legacy wording. They cannot be used as current truth.
- Any answer about MAS live readiness, paper progress, production readiness, artifact authority or quality verdict must fresh-read live source, contracts, tests, runtime/controller surfaces, workspace evidence, owner receipts and typed blockers.
